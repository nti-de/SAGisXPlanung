import logging

import qasync

from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import (QAbstractItemModel, Qt, QModelIndex, QSize)
from qgis.PyQt.QtWidgets import (QTreeView)
from qgis.gui import QgsHighlight
from qgis.core import QgsVectorLayer
from qgis.utils import iface

from SAGisXPlanung.GML.geometry import geometry_drop_z
from SAGisXPlanung.gui.style import TagStyledDelegate, HighlightRowProxyStyle

logger = logging.getLogger(__name__)


class QSelectedGeometriesView(QTreeView):

    def __init__(self, data, layer: QgsVectorLayer, parent=None):
        super(QSelectedGeometriesView, self).__init__(parent)
        self.model = SelectedGeometriesTableModel(data)
        self.setModel(self.model)

        self.layer = layer
        self.highlight = None

        self.setItemDelegate(TagStyledDelegate())
        self.proxy_style = HighlightRowProxyStyle('Fusion')
        self.proxy_style.setParent(self)
        self.setStyle(self.proxy_style)
        self.setMouseTracking(True)

        self.entered.connect(self.onItemHovered)

    def sizeHint(self):
        size = super(QSelectedGeometriesView, self).sizeHint()
        return QSize(size.width(), 80)

    def leaveEvent(self, *args, **kwargs):
        self.delete_highlight()
        super(QSelectedGeometriesView, self).leaveEvent(*args, **kwargs)

    def geometries(self):
        feat_ids = [self.model.data(self.model.index(i, 0)) for i in range(self.model.rowCount(QModelIndex()))]
        geometries = [geometry_drop_z(self.layer.getGeometry(fid)) for fid in feat_ids]

        return geometries

    def itemCount(self) -> int:
        return self.model.rowCount(QModelIndex())

    @qasync.asyncSlot(QModelIndex)
    async def onItemHovered(self, index: QModelIndex):
        if not index.isValid():
            return

        feat_id = self.model._data[index.row()][0]
        feat = self.layer.getFeature(feat_id)

        self.delete_highlight()
        self.highlight = QgsHighlight(iface.mapCanvas(), feat, self.layer)
        self.highlight.setColor(QColor(255, 0, 0, 125))
        self.highlight.setBuffer(0.1)
        self.highlight.show()

    def delete_highlight(self):
        if not self.highlight:
            return

        self.highlight.hide()
        iface.mapCanvas().scene().removeItem(self.highlight)
        self.highlight = None


class SelectedGeometriesTableModel(QAbstractItemModel):
    def __init__(self, data):
        super(SelectedGeometriesTableModel, self).__init__()
        self._data = data
        self._horizontal_header = ['Feature-Id']

    def addChild(self, data, _parent=QModelIndex()):
        row = self.rowCount(_parent)
        self.beginInsertRows(_parent, row, row)
        self._data.append(data)
        self.endInsertRows()

    def removeRows(self, row: int, count: int, parent=QModelIndex()) -> bool:
        self.beginRemoveRows(parent, row, row + count - 1)
        del self._data[row: row + count]
        self.endRemoveRows()
        return True

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            return value

    def index(self, row, column, _parent=QModelIndex()):
        return self.createIndex(row, column)

    def parent(self, index):
        return QModelIndex()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._horizontal_header[col]

    def hasChildren(self, index=QModelIndex()):
        return self.rowCount(index) > 0

    def rowCount(self, index):
        if index.isValid():
            return 0
        return len(self._data)

    def columnCount(self, index):
        return 1
