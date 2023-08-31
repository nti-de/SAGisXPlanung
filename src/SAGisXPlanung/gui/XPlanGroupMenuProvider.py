import logging

from qgis.PyQt.QtWidgets import QMenu
from qgis.core import QgsVectorLayer, QgsRasterLayer
from qgis.gui import QgsLayerTreeViewMenuProvider
from qgis.utils import iface

logger = logging.getLogger(__name__)


# TODO: https://gis.stackexchange.com/questions/382780/qgis-contextual-menu-overriding
class XPlanGroupMenuProvider(QgsLayerTreeViewMenuProvider):

    def __init__(self, view):
        super(XPlanGroupMenuProvider, self).__init__()
        self.view = view
        self.defaultActions = view.defaultActions()

    def createContextMenu(self):
        if not self.view.currentLayer():
            return None
        # m = super().createContextMenu() # TODO: this call is the problem, see above link
        m = QMenu()
        m.addAction("Open layer properties", self.openLayerProperties)
        m.addSeparator()

        if type(self.view.currentLayer()) == QgsVectorLayer:
            m.addAction("Show Feature Count", self.featureCount)
            m.addAction("Another vector-specific action", self.vectorAction)
        elif type(self.view.currentLayer()) == QgsRasterLayer:
            m.addAction("Zoom 100%", self.zoom100)
            m.addAction("Another raster-specific action", self.rasterAction)
        return m

    def openLayerProperties(self):
        iface.showLayerProperties(self.view.currentLayer())

    def featureCount(self):
        self.defaultActions.actionShowFeatureCount().trigger()

    def vectorAction(self):
        pass

    def zoom100(self):
        iface.actionZoomActualSize().trigger()

    def rasterAction(self):
        pass