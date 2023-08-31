import logging
from collections import defaultdict
from typing import Union

from qgis.PyQt import QtCore
from qgis.gui import QgsMapCanvasItem
from qgis.core import QgsVectorLayer, QgsProject, QgsMapLayer, QgsAnnotationLayer, QgsWkbTypes, Qgis
from qgis.utils import iface

from SAGisXPlanung import Session
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.XPlanungItem import XPlanungItem

logger = logging.getLogger(__name__)


class Singleton(QtCore.QObject):
    def __new__(cls, *args, **kwargs):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = QtCore.QObject.__new__(cls)
        it.init(*args, **kwargs)
        return it

    def init(self, *args, **kwargs):
        pass


class MapLayerRegistry(Singleton):
    _layers = []
    _canvasItems = defaultdict(list)

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

    def canvasItemsAtFeat(self, feat_xid: str):
        return self._canvasItems.get(feat_xid, [])

    def addCanvasItem(self, item: QgsMapCanvasItem, feat_xid: str):
        # if building template already exists replace with new one
        self.removeCanvasItems(feat_xid)
        self._canvasItems[feat_xid].append(item)

    def removeCanvasItems(self, feat_xid: str):
        items = self._canvasItems.pop(feat_xid, [])
        for item in items:
            iface.mapCanvas().scene().removeItem(item)
            item.updateCanvas()
            del item

    def addLayer(self, layer: QgsMapLayer, group=None, add_to_legend=True):
        if not (isinstance(layer, QgsVectorLayer) or isinstance(layer, QgsAnnotationLayer)):
            return

        if layer in self._layers:
            return

        self._layers.append(layer)

        if add_to_legend:
            QgsProject.instance().addMapLayer(layer, False)
            if group and isinstance(layer, QgsVectorLayer):
                group.addLayer(layer)
            elif group and isinstance(layer, QgsAnnotationLayer):
                group.insertLayer(0, layer)

        if isinstance(layer, QgsVectorLayer):
            layer.committedGeometriesChanges.connect(self.onGeometriesChanged)

    def removeLayer(self, layer_id):
        layer = self.layerById(layer_id)
        if not layer:
            return

        # remove template items from canvas
        if layer.customProperty('xplanung/type') == 'BP_BaugebietsTeilFlaeche':
            for key in layer.customPropertyKeys():
                if 'xplanung/feat-' not in key:
                    continue
                feat_id = layer.customProperty(key)
                self.removeCanvasItems(feat_id)

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

    def layerByFeature(self, feat_xid: str) -> Union[None, QgsVectorLayer, QgsAnnotationLayer]:
        for lyr in self._layers:
            for key in lyr.customPropertyKeys():
                if 'xplanung/feat-' not in key:
                    continue
                if lyr.customProperty(key) == feat_xid:
                    return lyr

    def layerByXid(self, xplan_item: XPlanungItem, geom_type: GeometryType = None) -> Union[None, QgsVectorLayer, QgsAnnotationLayer]:
        for lyr in self._layers:
            xtype = lyr.customProperty('xplanung/type')
            xid = lyr.customProperty('xplanung/plan-xid')
            if xtype == xplan_item.xtype.__name__ and xid == xplan_item.plan_xid:
                # make sure only layers of correct geometry type are returned (for vector layers only)
                if geom_type is not None and isinstance(lyr, QgsVectorLayer) and geom_type != lyr.geometryType():
                    continue
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
                plan_content = session.query(cls).get(xplanung_id)
                plan_content.setGeometry(geometry)
