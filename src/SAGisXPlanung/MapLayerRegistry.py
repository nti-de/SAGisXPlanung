import logging
from typing import Union

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt import QtCore
from qgis.core import (QgsVectorLayer, QgsProject, QgsMapLayer, QgsAnnotationLayer, QgsLayerTreeGroup, QgsRasterLayer)
from qgis.utils import iface

from SAGisXPlanung import Session
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import QgsConfig

logger = logging.getLogger(__name__)


class Singleton(type(QtCore.QObject), type):
    def __init__(cls, name, bases, dict):
        super().__init__(name, bases, dict)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
            if hasattr(cls._instance, "init"):
                cls._instance.init(*args, **kwargs)
        return cls._instance


class MapLayerRegistry(QtCore.QObject, metaclass=Singleton):
    _layers = []

    features_deleted = pyqtSignal(QgsVectorLayer, list)
    committed_features_removed = pyqtSignal(QgsVectorLayer, list)
    after_rollback = pyqtSignal()

    def init(self):
        QgsProject.instance().layerStore().layerWillBeRemoved.connect(self.removeLayer)

    def unload(self):
        try:
            QgsProject.instance().layerStore().layerWillBeRemoved.disconnect(self.removeLayer)
        except Exception:
            pass

    @property
    def layers(self):
        return self._layers

    def addLayer(self, layer: QgsMapLayer, group=None, add_to_legend=True):
        if layer in self._layers:
            return

        if add_to_legend:
            QgsProject.instance().addMapLayer(layer, False)
            if group and isinstance(layer, QgsVectorLayer):
                # respect layer order from config
                xplan_class = layer.customProperty('xplanung/type')
                layer_priority_type = layer.customProperty("xplanung/layer-priority")

                layer_priority = QgsConfig.layer_priority(xplan_class, layer.geometryType())
                layer.setCustomProperty('xplanung/custom-layer-priority', 0 if not layer_priority else int(layer_priority))

                if LayerPriorityType.Top in layer_priority_type:
                    group.insertLayer(0, layer)
                elif layer_priority is None or LayerPriorityType.Bottom in layer_priority_type:
                    group.addLayer(layer)
                else:
                    # find index that corresponds to the layer-priority following the priority of the layer that is
                    # to be inserted.
                    next_index = next((i for i, group_layer in enumerate(group.children())
                                       if group_layer.layer().customProperty('xplanung/plan-xid') == layer.customProperty('xplanung/plan-xid')
                                       and not (cp := group_layer.layer().customProperty('xplanung/custom-layer-priority')) is None
                                       and cp > int(layer_priority)), None)

                    # if no following index could be found, insert layer at the end
                    # otherwise insert layer before (next_index is the i-th layer -> insertLayer(i, lyr) inserts before)
                    if next_index is None:
                        group.addLayer(layer)
                    else:
                        group.insertLayer(next_index, layer)

            elif group is not None:
                group.addLayer(layer)

        if isinstance(layer, QgsVectorLayer):
            layer.committedGeometriesChanges.connect(self.onGeometriesChanged)
            layer.featuresDeleted.connect(
                lambda deleted_fids, lyr=layer: self.on_features_deleted(lyr, deleted_fids)
            )
            layer.committedFeaturesRemoved.connect(self.on_committed_features_removed)
            layer.afterRollBack.connect(self.after_rollback.emit)

        self._layers.append(layer)

    def removeLayer(self, layer_id):
        layer = self.layerById(layer_id)
        if not layer:
            return

        self._layers.remove(layer)

    def layerById(self, layer_id) -> Union[QgsVectorLayer, QgsAnnotationLayer]:
        for lyr in self._layers:
            if lyr.id() == layer_id:
                return lyr

    def featureIsShown(self, feat_xid: str) -> bool:
        for lyr in self._layers:
            for key in lyr.customPropertyKeys():
                if 'xplanung/feat-' not in key:
                    continue
                if lyr.customProperty(key) == feat_xid:
                    return True
        return False

    def layer_by_orm_id(self, orm_xid: str) -> Union[None, QgsVectorLayer, QgsRasterLayer]:
        for lyr in self._layers:
            if isinstance(lyr, QgsRasterLayer):
                if lyr.customProperty("xplanung/feat_id") == orm_xid:
                    return lyr
                continue
            if isinstance(lyr, QgsVectorLayer):
                for key in lyr.customPropertyKeys():
                    if 'xplanung/feat-' not in key:
                        continue
                    if lyr.customProperty(key) == orm_xid:
                        return lyr
        return None

    def layerByXid(self, xplan_item: XPlanungItem, geom_type: GeometryType = None) -> Union[None, QgsVectorLayer, QgsAnnotationLayer]:
        # if not already defined, try if geom type is available on the given xplan item
        if geom_type is None:
            geom_type = xplan_item.geom_type

        for lyr in self._layers:
            xtype = lyr.customProperty('xplanung/type')
            xid = lyr.customProperty('xplanung/plan-xid')
            if xtype == xplan_item.xtype.__name__ and xid == xplan_item.plan_xid:
                # make sure only layers of correct geometry type are returned (for vector layers only)
                if geom_type is not None and isinstance(lyr, QgsVectorLayer) and geom_type != lyr.geometryType():
                    continue
                return lyr

    def layer_by_plan_orm_id(self, plan_xid: str, xtype: type, geom_type: GeometryType) -> Union[None, QgsVectorLayer]:
        for lyr in self._layers:
            if lyr is None:
                continue
            _xtype = lyr.customProperty('xplanung/type')
            _xid = lyr.customProperty('xplanung/plan-xid')
            if _xtype == xtype.__name__ and _xid == plan_xid:
                # make sure only layers of correct geometry type are returned (for vector layers only)
                if isinstance(lyr, QgsVectorLayer) and geom_type != lyr.geometryType():
                    continue
                return lyr

    def layer_by_display_name(self, display_name: str, plan_xid: str) -> Union[None, QgsVectorLayer, QgsAnnotationLayer]:
        for lyr in self._layers:
            xid = lyr.customProperty('xplanung/plan-xid')
            if display_name == lyr.name() and xid == plan_xid:
                return lyr

    def onGeometriesChanged(self, layer_id, changed_geometries):
        layer = self.layerById(layer_id)
        for feat_id, geometry in changed_geometries.items():
            if not layer.customProperties().contains(f'xplanung/feat-{feat_id}'):
                raise KeyError('Geometrieänderung einer XPlanung Fläche detektiert, '
                               'aber kein zugehöriges Objekt gefunden ')
            xplanung_id = layer.customProperties().value(f'xplanung/feat-{feat_id}')
            xplanung_type = layer.customProperties().value('xplanung/type')

            from SAGisXPlanung.utils import CLASSES
            from SAGisXPlanung.XPlan.feature_types import XP_Objekt

            if issubclass(cls := CLASSES[xplanung_type], XP_Objekt):
                return

            with Session.begin() as session:
                plan_content = session.get(CLASSES[xplanung_type], xplanung_id)
                plan_content.setGeometry(geometry)

    def on_features_deleted(self, lyr, deleted_fids):
        self.features_deleted.emit(lyr, deleted_fids)

    def on_committed_features_removed(self, layer_id, deleted_fids):
        layer = self.layerById(layer_id)
        self.committed_features_removed.emit(layer, deleted_fids)