from qgis.PyQt import QtWidgets, QtCore

from SAGisXPlanung.XPlan.feature_types import XP_Objekt
from SAGisXPlanung.XPlan.mixins import LineGeometry, PolygonGeometry, PointGeometry, MixedGeometry
from SAGisXPlanung.utils import CLASSES


class QObjectTypeSelectionTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, *args, **kwargs):
        super(QObjectTypeSelectionTreeWidget, self).__init__(*args, **kwargs)

        self.setColumnCount(1)
        self.setHeaderLabel('Objektart')

    def sizeHint(self):
        size = super(QObjectTypeSelectionTreeWidget, self).sizeHint()
        return QtCore.QSize(size.width(), 100)

    def setup(self, cls_type):
        self.clear()
        plan_type_prefix = cls_type.__name__[:2]
        self.iterateSubclass(CLASSES[f'{plan_type_prefix}_Objekt'])
        if plan_type_prefix != 'SO':
            self.iterateSubclass(CLASSES['SO_Objekt'])

    def iterateSubclass(self, cls):
        for derived in cls.__subclasses__():  # type: XP_Objekt
            if derived.hidden:
                continue
            if issubclass(derived, (LineGeometry, PolygonGeometry, PointGeometry, MixedGeometry)):
                module_name = derived.__module__.split('.')[-2]
                items = self.findItems(module_name, QtCore.Qt.MatchFixedString)
                if items:
                    node = QtWidgets.QTreeWidgetItem(items[0], [derived.__name__])
                    node.setIcon(0, derived.previewIcon())
                else:
                    top_node = QtWidgets.QTreeWidgetItem(self, [module_name])
                    # noinspection PyTypeChecker
                    top_node.setFlags(top_node.flags() & ~QtCore.Qt.ItemIsSelectable)
                    node = QtWidgets.QTreeWidgetItem(top_node, [derived.__name__])
                    node.setIcon(0, derived.previewIcon())
            self.iterateSubclass(derived)
