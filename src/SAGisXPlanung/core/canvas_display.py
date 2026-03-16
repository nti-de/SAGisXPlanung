import asyncio
import logging
import tempfile
import traceback
from collections import defaultdict
from urllib.parse import urlencode, quote_plus

import qasync
from osgeo import gdal
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsRasterLayer, QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsVectorLayer, \
    QgsAnnotationLayer, QgsWkbTypes
from qgis.utils import iface
from sqlalchemy import select, func, or_, and_, exists
from sqlalchemy.orm import with_polymorphic, selectin_polymorphic

from SAGisXPlanung import Session
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_AbstraktesPraesentationsobjekt
from SAGisXPlanung.XPlan.XP_Raster.feature_types import XP_Rasterdarstellung
from SAGisXPlanung.XPlan.data_types import XP_ExterneReferenz, XP_SpezExterneReferenz
from SAGisXPlanung.XPlan.enums import XP_ExterneReferenzArt
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich
from SAGisXPlanung.config import export_version
from SAGisXPlanung.ext.spinner import loading_animation
from SAGisXPlanung.utils import createXPlanungIndicators, BEREICH_BASE_TYPES, OBJECT_BASE_TYPES

logger = logging.getLogger(__name__)


@qasync.asyncSlot(str)
async def plan_to_map(plan_xid: str, *_):
    """
    Ein bereits auf der Karte gerenderter Plan wird neu geladen. Sollte der Plan noch nicht auf der Karte bestehen,
    wird er erstmals geladen.
    """
    layers = QgsProject.instance().layerTreeRoot().findGroups(recursive=True)
    for group in layers:
        if not isinstance(group, QgsLayerTreeGroup) or 'xplanung_id' not in group.customProperties():
            continue

        if group.customProperty('xplanung_id') == plan_xid:
            await load_on_canvas(plan_xid, layer_group=group)
            return

    await load_on_canvas(plan_xid)


# @profile_it(sort_by='tottime')
async def load_on_canvas(plan_xid: str, layer_group: QgsLayerTreeGroup=None):

    try:
        async with loading_animation(iface.layerTreeView()):
            with Session.begin() as session:

                plan: XP_Plan = session.get(XP_Plan, plan_xid)
                if plan is None:
                    raise Exception(f'plan with id {plan_xid} not found')

                root = QgsProject.instance().layerTreeRoot()

                if not layer_group:
                    layer_group = root.insertGroup(0, plan.name)
                    layer_group.setCustomProperty('xplanung_id', str(plan.id))

                    xp_indicator, reload_indicator = createXPlanungIndicators()
                    reload_indicator.clicked.connect(lambda i, p=plan_xid: plan_to_map(p))

                    iface.layerTreeView().addIndicator(layer_group, xp_indicator)
                    iface.layerTreeView().addIndicator(layer_group, reload_indicator)
                else:
                    for tree_layer in layer_group.findLayers():  # type: QgsLayerTreeLayer
                        map_layer = tree_layer.layer()
                        is_xplan_layer = map_layer.customProperty('xplanung/type') is not None
                        if not is_xplan_layer:
                            continue

                        if isinstance(map_layer, QgsVectorLayer):
                            truncate_success = map_layer.dataProvider().truncate()
                            if not truncate_success:
                                logger.warning(f'Could not truncate features of vector layer {map_layer.name()}')
                        elif isinstance(map_layer, QgsAnnotationLayer):
                            map_layer.clear()
                        elif isinstance(map_layer, QgsRasterLayer):
                            QgsProject.instance().removeMapLayer(map_layer)
                            continue

                        for key in map_layer.customPropertyKeys():
                            if 'xplanung/feat-' in key:
                                map_layer.removeCustomProperty(key)

                new_layers = await asyncio.to_thread(collect_layers, plan, plan_xid, session)

            for layer in new_layers:
                MapLayerRegistry().addLayer(layer, group=layer_group)

    except Exception as e:
        logger.debug(f'Error while loading plan: {e}')
        logger.error(traceback.format_exc())
        iface.statusBarIface().showMessage(f'Fehler beim Laden des Plans: {e}')


def collect_layers(plan, plan_xid, session):
    xp_bereich_poly = with_polymorphic(XP_Bereich, BEREICH_BASE_TYPES)
    stmt = select(xp_bereich_poly).where(
        or_(*[cls.gehoertZuPlan_id == plan_xid for cls in BEREICH_BASE_TYPES])
    )
    bereich_list = session.execute(stmt).scalars().all()
    bereich_ids = [b.id for b in bereich_list]

    grouped_features = defaultdict(lambda: defaultdict(list))
    all_features_id_list = []
    for object_base in OBJECT_BASE_TYPES:
        stmt = select(
            object_base,
            func.ST_Dimension(object_base.position)
        ).where(
            object_base.gehoertZuBereich_id.in_(bereich_ids)
        ).options(
            selectin_polymorphic(object_base, object_base.__subclasses__())
        )

        for obj, dim in session.execute(stmt):
            all_features_id_list.append(obj.id)
            grouped_features[type(obj)][dim].append(obj)

    for object_base in XP_AbstraktesPraesentationsobjekt.__subclasses__():
        stmt = select(
            object_base,
            func.ST_Dimension(object_base.position)
        ).where(object_base.dientZurDarstellungVon_id.in_(all_features_id_list))

        for obj, dim in session.execute(stmt):
            grouped_features[type(obj)][dim].append(obj)

    grouped_features[type(plan)][2].append(plan)
    for b in bereich_list:
        if b.geltungsbereich is not None:
            grouped_features[type(b)][2].append(b)

    new_layers = []

    for cls, features_by_dim in grouped_features.items():
        if hasattr(cls, 'xp_versions') and export_version() not in cls.xp_versions:
            continue

        for geom_dim, orm_features in features_by_dim.items():

            qgs_geom_type = QgsWkbTypes.GeometryType(geom_dim)
            layer = MapLayerRegistry().layer_by_plan_orm_id(plan_xid=plan_xid, xtype=cls, geom_type=qgs_geom_type)
            if not layer:
                srid = plan.srs().postgisSrid()
                layer = cls.asLayer(srid, plan_xid, name=cls.__name__, geom_type=qgs_geom_type)

            feat_map = {}
            for orm_feat in orm_features:
                qgis_feat = orm_feat.asFeature(layer.fields())
                feat_map[orm_feat.id] = qgis_feat

            dp = layer.dataProvider()
            layer.startEditing()
            _, new_features = dp.addFeatures(list(feat_map.values()))
            layer.commitChanges()

            for orm_id, qgis_feat in zip(feat_map.keys(), new_features):
                layer.setCustomProperty(f'xplanung/feat-{qgis_feat.id()}', str(orm_id))

            # move layer to main thread (otherwise causes some non-stable issues with geometry editing)
            layer.moveToThread(QApplication.instance().thread())
            new_layers.append(layer)

    # load external references
    ref_poly = with_polymorphic(XP_ExterneReferenz, [XP_SpezExterneReferenz])
    stmt = select(ref_poly).where(
        and_(
            ref_poly.art == XP_ExterneReferenzArt.PlanMitGeoreferenz,
            or_(
                ref_poly.bereich_id.in_(bereich_ids),
                ref_poly.XP_SpezExterneReferenz.plan_id == plan_xid,
                exists(
                    select(1)
                    .where(
                        and_(
                            XP_Rasterdarstellung.id == ref_poly.xp_rasterdarstellung_scan_id,
                            XP_Rasterdarstellung.bereich_id.in_(bereich_ids),
                        )
                    )
                )
            )
        )
    )
    ref_objects = session.scalars(stmt).all()
    for ref in ref_objects:
        for filename, file_data in ref.get_file_data().items():
            if file_data is not None:
                vsi_path = f'/vsimem/{filename}'
                gdal.FileFromMemBuffer(vsi_path, file_data)

        raster_layer = QgsRasterLayer(f'/vsimem/{ref.referenzURL}', ref.referenzName or ref.referenzURL, "gdal")
        raster_layer.setCustomProperty('xplanung/type', 'XP_ExterneReferenz')
        raster_layer.setCustomProperty('xplanung/feat_id', str(ref.id))
        new_layers.append(raster_layer)

    return new_layers
