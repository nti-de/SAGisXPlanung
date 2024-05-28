import logging
import tempfile

from qgis.core import QgsRasterLayer, QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsVectorLayer, \
    QgsAnnotationLayer
from qgis.utils import iface

from SAGisXPlanung import Session
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.enums import XP_ExterneReferenzArt
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.utils import createXPlanungIndicators

logger = logging.getLogger(__name__)


def create_raster_layer(layer_name, file, group=None):
    """
    Fügt dem aktuellen QGIS-Projekt ein neuen Rasterlayer hinzu

    Parameters
    ----------
    layer_name: str
        Name des Layers, wird im LayerTree angezeigt
    file: bytes
        Inhalt des Rasterbilds
    group: QgsLayerTreeGroup, optional
        Layer wird dieser Gruppe im LayerTree hinzugefügt
    """

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file)

        layer = QgsRasterLayer(tmp.name, layer_name)
        if group:
            QgsProject.instance().addMapLayer(layer, False)
            group.addLayer(layer)
        else:
            QgsProject.instance().addMapLayer(layer)


def plan_to_map(plan_xid):
    """
    Ein bereits auf der Karte gerenderter Plan wird neu geladen. Sollte der Plan noch nicht auf der Karte bestehen,
    wird er erstmals geladen.
    """
    layers = QgsProject.instance().layerTreeRoot().findGroups(recursive=True)
    for group in layers:
        if not isinstance(group, QgsLayerTreeGroup) or 'xplanung_id' not in group.customProperties():
            continue

        if group.customProperty('xplanung_id') == plan_xid:
            load_on_canvas(plan_xid, layer_group=group)
            return

    load_on_canvas(plan_xid)


def load_on_canvas(plan_xid, layer_group=None):
    """
    Fügt den aktuell gewählten Plan als Layer zur Karte hinzu
    """
    iface.mainWindow().statusBar().showMessage('Planwerk wird geladen...')
    with Session.begin() as session:
        plan: XP_Plan = session.query(XP_Plan).get(plan_xid)
        if plan is None:
            raise Exception(f'plan with id {plan_xid} not found')

        root = QgsProject.instance().layerTreeRoot()

        if not layer_group:
            layer_group = root.insertGroup(0, plan.name)
            layer_group.setCustomProperty('xplanung_id', str(plan.id))
            layer_group.visibilityChanged.connect(MapLayerRegistry().on_group_node_visibility_changed)

            xp_indicator, reload_indicator = createXPlanungIndicators()
            reload_indicator.clicked.connect(lambda i, p=plan_xid: plan_to_map(p))

            iface.layerTreeView().addIndicator(layer_group, xp_indicator)
            iface.layerTreeView().addIndicator(layer_group, reload_indicator)
        else:
            for tree_layer in layer_group.findLayers():  # type: QgsLayerTreeLayer
                map_layer = tree_layer.layer()
                if isinstance(map_layer, QgsVectorLayer):
                    truncate_success = map_layer.dataProvider().truncate()
                    if not truncate_success:
                        logger.warning(f'Could not truncate features of vector layer {map_layer.name()}')
                    else:
                        for key in map_layer.customPropertyKeys():
                            if 'xplanung/feat-' in key:
                                map_layer.removeCustomProperty(key)
                elif isinstance(map_layer, QgsAnnotationLayer):
                    map_layer.clear()
                elif isinstance(map_layer, QgsRasterLayer):
                    QgsProject.instance().removeMapLayer(map_layer)

        plan.toCanvas(layer_group)

        for b in [b for b in plan.bereich]:  # if b.geltungsbereich? only load if geltungsbereich has geom
            for planinhalt in b.planinhalt:
                planinhalt.toCanvas(layer_group, plan_xid=plan.id)

            # display "free" annotations which are not bound to a 'planinhalt'
            for po in b.praesentationsobjekt:
                if po.dientZurDarstellungVon_id:
                    continue
                po.toCanvas(layer_group, plan_xid=plan.id)

            for simple_object in b.simple_geometry:
                simple_object.toCanvas(layer_group, plan_xid=plan.id)

            if b.geltungsbereich:
                b.toCanvas(layer_group, plan_xid=plan.id)

            for refScan in b.refScan:
                if refScan.art == XP_ExterneReferenzArt.PlanMitGeoreferenz and refScan.file is not None:
                    create_raster_layer(refScan.referenzName, refScan.file, group=layer_group)

        for ext_ref in plan.externeReferenz:
            if ext_ref.art == XP_ExterneReferenzArt.PlanMitGeoreferenz and ext_ref.file is not None:
                create_raster_layer(ext_ref.referenzName, ext_ref.file, group=layer_group)

    iface.mainWindow().statusBar().showMessage('Planwerk auf der Karte geladen.')
