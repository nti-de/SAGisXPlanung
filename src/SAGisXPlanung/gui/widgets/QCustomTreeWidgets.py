import logging

from qgis.PyQt.QtCore import QSize
from qgis.PyQt import QtWidgets, QtCore
from qgis.core import QgsWkbTypes, QgsSymbolLayerUtils

from SAGisXPlanung.XPlan.feature_types import XP_Objekt
from SAGisXPlanung.XPlan.mixins import LineGeometry, PolygonGeometry, PointGeometry, MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.utils import CLASSES

logger = logging.getLogger(__name__)


class QObjectTypeSelectionTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, *args, **kwargs):
        super(QObjectTypeSelectionTreeWidget, self).__init__(*args, **kwargs)

        self.geometry_type = QgsWkbTypes.UnknownGeometry
        self.setColumnCount(1)
        self.setHeaderLabel('Objektart')

    def sizeHint(self):
        size = super(QObjectTypeSelectionTreeWidget, self).sizeHint()
        return QtCore.QSize(size.width(), 100)

    def setup(self, cls_type, layer_type: GeometryType):
        self.clear()
        self.geometry_type = layer_type

        plan_type_prefix = cls_type.__name__[:2]
        try:
            self.iterateSubclass(CLASSES[f'{plan_type_prefix}_Objekt'])
        except KeyError as e:
            logger.exception(e)
        if plan_type_prefix != 'SO':
            self.iterateSubclass(CLASSES['SO_Objekt'])

    def iterateSubclass(self, cls):
        for derived in cls.__subclasses__():  # type: XP_Objekt
            if derived.hidden:
                continue
            if issubclass(derived, (LineGeometry, PolygonGeometry, PointGeometry, MixedGeometry)):
                if not issubclass(derived, MixedGeometry) and derived.__geometry_type__ != self.geometry_type:
                    continue
                module_name = derived.__module__.split('.')[-2]
                items = self.findItems(module_name, QtCore.Qt.MatchFixedString)
                icon = derived.preview_icon(self.geometry_type)
                if items:
                    node = QtWidgets.QTreeWidgetItem(items[0], [derived.__name__])
                    node.setIcon(0, icon)
                else:
                    top_node = QtWidgets.QTreeWidgetItem(self, [module_name])
                    # noinspection PyTypeChecker
                    top_node.setFlags(top_node.flags() & ~QtCore.Qt.ItemIsSelectable)
                    node = QtWidgets.QTreeWidgetItem(top_node, [derived.__name__])
                    node.setIcon(0, icon)
            self.iterateSubclass(derived)
