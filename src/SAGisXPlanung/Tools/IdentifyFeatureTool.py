import logging
import math
import os

from qgis.core import QgsApplication
from qgis.gui import QgsMapToolIdentify
from qgis.core import QgsFeature, QgsMapLayer, Qgis
from qgis.utils import iface
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QCursor, QIcon

from SAGisXPlanung import BASE_DIR

logger = logging.getLogger(__name__)


class IdentifyFeatureTool(QgsMapToolIdentify):
    noFeatureSelected = pyqtSignal()
    featureIdentified = pyqtSignal(QgsFeature)

    def __init__(self, canvas, layer=None, keep_selection=False):
        self.canvas = canvas
        self.iface = iface
        self.layer = layer
        self.keep_selection = keep_selection
        super(IdentifyFeatureTool, self).__init__(self.canvas)

        cursor = QgsApplication.getThemeCursor(QgsApplication.CrossHair)
        self.setCursor(cursor)

    def activate(self):
        iface.mainWindow().statusBar().showMessage('Feature auf der Karte auswählen')
        super(IdentifyFeatureTool, self).activate()

    def deactivate(self):
        iface.mainWindow().statusBar().clearMessage()
        super(IdentifyFeatureTool, self).deactivate()

    def setLayer(self, vl):
        self.layer = vl
        # super(IdentifyFeatureTool, self).setLayer(vl)

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.RightButton or not self.layer:
            self.canvas.unsetMapTool(self)
            return

        # event.snapPoint(QgsMapMouseEvent.SnapProjectConfig)
        found_features = self.identify(event.x(), event.y(), [self.layer], QgsMapToolIdentify.LayerSelection)

        if not self.keep_selection:
            layers = self.iface.mapCanvas().layers()
            for l in layers:
                if l.type() == QgsMapLayer.VectorLayer:
                    l.removeSelection()

        if len(found_features) > 0:
            feature = found_features[0].mFeature
            layer = found_features[0].mLayer
            layer.select([feature.id()])
            self.featureIdentified.emit(feature)
        else:
            self.noFeatureSelected.emit()

        super(IdentifyFeatureTool, self).canvasReleaseEvent(event)
