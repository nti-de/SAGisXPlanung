import logging

from qgis.PyQt.QtCore import pyqtSlot
from qgis.core import edit, QgsFeatureRequest, QgsProject

from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.widgets.QAttributeEdit import QAttributeEdit

logger = logging.getLogger(__name__)


class QAttributeEditSymbolRenderer(QAttributeEdit):

    def __init__(self, xplanung_item: XPlanungItem, data, parent=None):
        super(QAttributeEditSymbolRenderer, self).__init__(xplanung_item, data, parent)

        self.styleGroup.setVisible(True)

        self._layer = MapLayerRegistry().layerByXid(self._xplanung_item, geom_type=xplanung_item.geom_type)
        self._feature = None
        if self._layer:
            QgsProject.instance().layerStore().layerWillBeRemoved.connect(self.onLayerRemoved)
            self.get_feature()

        # set initial form values
        self.set_form_values()
        self.initialize_listeners()

    def get_feature(self):
        for feat in self._layer.getFeatures(
                QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setNoAttributes()):
            id_prop = self._layer.customProperties().value(f'xplanung/feat-{feat.id()}')
            if id_prop == self._xplanung_item.xid:
                self._feature = feat
                break

    @pyqtSlot(str)
    def onLayerRemoved(self, layer_id):
        if self._layer is None:
            return
        if layer_id == self._layer.id():
            self._layer = None

    @pyqtSlot(int)
    def onSliderValueChanged(self, value: int):
        scale = (value - 1) / (99 - 1)
        if not self._layer:
            return

        field_idx = self._layer.fields().indexOf(self.ATTRIBUTE_SIZE)
        with edit(self._layer):
            self._layer.changeAttributeValue(self._feature.id(), field_idx, str(scale))

    @pyqtSlot(int)
    def onDialValueChanged(self, value: int):
        self.angleEdit.setText(f'{value}°')
        if not self._layer:
            return

        field_idx = self._layer.fields().indexOf(self.ATTRIBUTE_ANGLE)
        with edit(self._layer):
            self._layer.changeAttributeValue(self._feature.id(), field_idx, str(value))
