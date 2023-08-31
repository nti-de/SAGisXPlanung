import logging
from enum import Enum

from qgis.PyQt.QtCore import (QAbstractItemModel, Qt, QModelIndex, QPoint, QAbstractProxyModel, QSortFilterProxyModel,
                              pyqtSlot, QPersistentModelIndex, QItemSelection, QSize)
from qgis.PyQt.QtWidgets import (QTreeView)

from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.style import TagStyledDelegate, HighlightRowProxyStyle, FlagNewRole

XID_ROLE = Qt.UserRole + 2

logger = logging.getLogger(__name__)


class SortOptions(Enum):
    SortHierarchy = 0
    SortAlphabet = 1
    SortCategory = 2


class QExplorerView(QTreeView):

    def __init__(self, parent=None):
        super(QExplorerView, self).__init__(parent)
        self.model = ExplorerTreeModel()

        self.proxy = SortProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.setModel(self.proxy)

        self.setItemDelegate(TagStyledDelegate())
        self.proxy_style = HighlightRowProxyStyle('Fusion')
        self.proxy_style.setParent(self)
        self.setStyle(self.proxy_style)
        self.setMouseTracking(True)

        self.sorting = SortOptions.SortHierarchy

    def sizeHint(self):
        size = super(QExplorerView, self).sizeHint()
        return QSize(size.width(), 80)

    def clear(self):
        self.model.clear()

    def itemAtPosistion(self, position: QPoint):
        index = self.indexAt(position)
        item = index.model().itemAtIndex(index)
        return item

    def invisibleRootItem(self):
        return self.model._root

    def removeItem(self, node):
        index = self.model.indexForTreeItem(node)
        self.model.removeRows(node.row(), 1, index.parent())

    def selectedItems(self):
        indices = self.selectedIndexes()
        return [index.model().itemAtIndex(index) for index in indices]

    def sort(self, opts: int):
        if SortOptions(opts) == SortOptions.SortAlphabet:
            proxy1 = FlatProxyModel()
            proxy1.setSourceModel(self.model)
            self.proxy.setSourceModel(proxy1)
            self.proxy.sort(0, Qt.AscendingOrder)
            self.sorting = SortOptions.SortAlphabet
        elif SortOptions(opts) == SortOptions.SortCategory:
            proxy1 = CategoryProxyModel()
            proxy1.setSourceModel(self.model)
            self.proxy.setSourceModel(proxy1)
            self.proxy.sort(-1)
            self.sorting = SortOptions.SortCategory
        else:
            self.proxy.setSourceModel(self.model)
            self.proxy.sort(-1)
            self.sorting = SortOptions.SortHierarchy
            self.expandAll()

    def filter(self, filter_text):
        self.proxy.setFilterRegularExpression(filter_text)

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        if not deselected.indexes():
            return
        index = deselected.indexes()[0]
        if index.data(FlagNewRole):
            while not isinstance(index.model(), ExplorerTreeModel):
                index = index.model().mapToSource(index)
            self.model.setData(index, False, role=FlagNewRole)
            
        super(QExplorerView, self).selectionChanged(selected, deselected)


class ExplorerTreeModel(QAbstractItemModel):
    def __init__(self, nodes=None):
        super(ExplorerTreeModel, self).__init__()
        if nodes is None:
            nodes = []
        self._horizontal_header = ['Objektbaum']

        self._root = CustomNode()
        for node in nodes:
            self._root.addChild(node)

    def clear(self):
        self.beginResetModel()
        for i in range(self._root.childCount()):
            item = self._root.child(i)
            del item
        self._root._children.clear()
        self.endResetModel()

    def addChild(self, node, _parent=QModelIndex(), row=None):
        if isinstance(_parent, ClassNode):
            _parent = self.indexForTreeItem(_parent)

        if row is None:
            row = self.rowCount(_parent)
        if not _parent or not _parent.isValid():
            parent = self._root
        else:
            parent = _parent.internalPointer()
        self.beginInsertRows(_parent, row, row)
        parent.addChild(node, row=row)
        self.endInsertRows()

    def removeRows(self, row: int, count: int, parent: QModelIndex = None) -> bool:
        self.beginRemoveRows(parent, row, row + count - 1)
        parent_item = self.itemAtIndex(parent)
        for i in range(count):
            parent_item.removeChild(row + i)
        self.endRemoveRows()
        return True

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == Qt.DisplayRole:
            return node.data(index.column())
        if role == FlagNewRole:
            return node.flag_new
        if role == XID_ROLE and isinstance(node, ClassNode):
            return node.xplanItem().xid
        return None

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if role == FlagNewRole:
            node = index.internalPointer()
            if not node:
                return
            node.flag_new = value
            self.dataChanged.emit(index, index)

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._horizontal_header[col]

    def indexForTreeItem(self, node):
        index = self.createIndex(node.row(), 0, node)
        return index

    def itemAtIndex(self, index: QModelIndex):
        if not index.isValid():
            return self._root

        return index.internalPointer()

    def index(self, row, column, _parent=QModelIndex()):
        if _parent.isValid() and _parent.column() != 0:
            return QModelIndex()

        parentItem = self.itemAtIndex(_parent)
        child = parentItem.child(row)
        if child:
            return self.createIndex(row, column, child)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child = self.itemAtIndex(index)
        parentItem = child.parent()
        if parentItem == self._root:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, index):
        if index.isValid():
            return index.internalPointer().childCount()
        return self._root.childCount()

    def columnCount(self, index):
        return 1


class FlatProxyModel(QAbstractProxyModel):

    def __init__(self):
        self.index_lookup = []
        self.index_lookup_proxy = []

        super(FlatProxyModel, self).__init__()

    def setSourceModel(self, model: QAbstractItemModel):
        self.buildSourceMap(model)
        super(FlatProxyModel, self).setSourceModel(model)

        self.sourceModel().rowsRemoved.connect(self.onRowsChanged)
        self.sourceModel().rowsInserted.connect(self.onRowsChanged)
        self.sourceModel().dataChanged.connect(self.sourceDataChanged)

    @pyqtSlot(QModelIndex, QModelIndex)
    def sourceDataChanged(self, top_left, bottom_right):
        self.dataChanged.emit(self.mapFromSource(top_left), self.mapFromSource(bottom_right))

    @pyqtSlot(QModelIndex, int, int)
    def onRowsChanged(self, parent: QModelIndex, first: int, last: int):
        self.layoutAboutToBeChanged.emit()
        self.index_lookup = []
        self.index_lookup_proxy = []
        self.buildSourceMap(self.sourceModel())
        self.layoutChanged.emit()

    def buildSourceMap(self, model, parent=QModelIndex()):
        rows = model.rowCount(parent)
        for r in range(rows):
            index = model.index(r, 0, parent)

            proxy_index = QPersistentModelIndex(self.createIndex(len(self.index_lookup), 0, index.internalPointer()))
            self.index_lookup.append(QPersistentModelIndex(index))
            self.index_lookup_proxy.append(proxy_index)

            if model.itemAtIndex(index).childCount() > 0:
                self.buildSourceMap(model, index)

    def itemAtIndex(self, index: QModelIndex):
        if not self.sourceModel():
            return
        index = self.mapToSource(index)
        return self.sourceModel().itemAtIndex(index)

    def mapFromSource(self, source_index: QModelIndex):
        if not source_index.isValid() or QPersistentModelIndex(source_index) not in self.index_lookup:
            return QModelIndex()
        row = self.index_lookup.index(QPersistentModelIndex(source_index))
        proxy_index = self.index_lookup_proxy[row]
        return QModelIndex(proxy_index)

    def mapToSource(self, proxy_index: QModelIndex):
        if not proxy_index.isValid() or proxy_index.row() > len(self.index_lookup) - 1:
            return QModelIndex()

        return QModelIndex(self.index_lookup[proxy_index.row()])

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()

        source_index = QModelIndex(self.index_lookup[row])
        return self.createIndex(row, column, source_index.internalPointer())

    def parent(self, index):
        return QModelIndex()

    def hasChildren(self, index=QModelIndex()):
        return self.rowCount(index) > 0

    def rowCount(self, index):
        if not index.isValid():
            return len(self.index_lookup)
        return 0

    def columnCount(self, index):
        return 1


class CategoryProxyModel(QAbstractProxyModel):

    def __init__(self):
        self.categories = []
        self.category_model_indices = {}
        self.category_items = {}
        self.category_items_proxy = {}

        super(CategoryProxyModel, self).__init__()

    def setSourceModel(self, model: QAbstractItemModel):
        self.buildSourceMap(model)
        for i, cat in enumerate(self.categories):
            self.category_model_indices[cat] = QPersistentModelIndex(self.createIndex(i, 0))
        super(CategoryProxyModel, self).setSourceModel(model)

        self.sourceModel().rowsRemoved.connect(self.onRowsChanged)
        self.sourceModel().rowsInserted.connect(self.onRowsChanged)
        self.sourceModel().dataChanged.connect(self.sourceDataChanged)

    @pyqtSlot(QModelIndex, QModelIndex)
    def sourceDataChanged(self, top_left, bottom_right):
        self.dataChanged.emit(self.mapFromSource(top_left), self.mapFromSource(bottom_right))

    @pyqtSlot(QModelIndex, int, int)
    def onRowsChanged(self, parent: QModelIndex, first: int, last: int):
        self.layoutAboutToBeChanged.emit()
        self.categories = []
        self.category_model_indices = {}
        self.category_items = {}
        self.category_items_proxy = {}
        self.buildSourceMap(self.sourceModel())
        for i, cat in enumerate(self.categories):
            self.category_model_indices[cat] = QPersistentModelIndex(self.createIndex(i, 0))
        self.layoutChanged.emit()

    def buildSourceMap(self, model, parent=QModelIndex()):
        rows = model.rowCount(parent)
        for r in range(rows):
            index = model.index(r, 0, parent)

            item = model.itemAtIndex(index)
            if item.xplan_module not in self.categories:
                self.categories.append(item.xplan_module)
                self.category_items[item.xplan_module] = [QPersistentModelIndex(index)]
                new_index = QPersistentModelIndex(self.createIndex(0, 0, index.internalPointer()))
                self.category_items_proxy[item.xplan_module] = [new_index]
            else:
                self.category_items[item.xplan_module].append(QPersistentModelIndex(index))
                prev_row = len(self.category_items_proxy[item.xplan_module])
                new_index = QPersistentModelIndex(self.createIndex(prev_row, 0, index.internalPointer()))
                self.category_items_proxy[item.xplan_module].append(new_index)

            if item.childCount() > 0:
                self.buildSourceMap(model, index)

    def itemAtIndex(self, index: QModelIndex):
        if not self.sourceModel():
            return
        index = self.mapToSource(index)
        return self.sourceModel().itemAtIndex(index)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.parent().isValid() and index.row() < len(self.categories):
            if role == Qt.DisplayRole:
                return self.categories[index.row()]

        return self.sourceModel().data(self.mapToSource(index), role)

    def mapFromSource(self, source_index: QModelIndex):
        if not source_index.isValid():
            return QModelIndex()

        source_item = source_index.internalPointer()
        category = source_item.xplan_module
        persistent_index = QPersistentModelIndex(source_index)
        row = self.category_items[category].index(persistent_index)
        proxy_index = self.category_items_proxy[category][row]

        return QModelIndex(proxy_index)

    def mapToSource(self, proxy_index: QModelIndex):
        if not proxy_index.isValid():
            return QModelIndex()

        proxy_item = proxy_index.internalPointer()
        if not proxy_item:
            return QModelIndex()
        category = proxy_item.xplan_module
        persistent_index = QPersistentModelIndex(proxy_index)
        row = self.category_items_proxy[category].index(persistent_index)
        source_index = self.category_items[category][row]

        return QModelIndex(source_index)

    def index(self, row: int, column: int, parent=QModelIndex()):
        if not parent.isValid():
            return self.createIndex(row, column)

        # get category from category persistent index (parent)
        category = next((cat for cat, index in self.category_model_indices.items()
                         if index == QPersistentModelIndex(parent)), None)

        if category is None:
            return QModelIndex()

        source_index = QModelIndex(self.category_items[category][row])
        return self.createIndex(row, column, source_index.internalPointer())

    def parent(self, index: QModelIndex = None):
        # if category node was found, source index is invalid
        if not index.isValid() or index.internalPointer() is None:
            return QModelIndex()

        item = index.internalPointer()
        category = item.xplan_module
        category_persistent_index = self.category_model_indices[category]
        return QModelIndex(category_persistent_index)

    def hasChildren(self, index=QModelIndex()):
        return self.rowCount(index) > 0

    def rowCount(self, index):
        if not index.isValid():
            return len(self.categories)

        if index.parent().isValid():
            return 0

        category_row = index.row()
        category = self.categories[category_row]
        count = len(self.category_items[category])
        return count

    def columnCount(self, index):
        return 1


class SortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setRecursiveFilteringEnabled(True)

    def itemAtIndex(self, index: QModelIndex):
        if not self.sourceModel():
            return
        index = self.mapToSource(index)
        return self.sourceModel().itemAtIndex(index)

    def setSourceModel(self, model: QAbstractItemModel):
        super(SortProxyModel, self).setSourceModel(model)

        self.sourceModel().dataChanged.connect(lambda index1, index2: self.invalidateFilter())
        self.sourceModel().rowsInserted.connect(lambda p, f, l: self.invalidate())

    def filterAcceptsRow(self, source_row: int, parent: QModelIndex):
        index = self.sourceModel().index(source_row, 0, parent)
        if not index.isValid():
            return True

        # dont filter for category nodes/ invalid nodes
        if index.internalPointer() is None:
            return False
        return self.filterRegularExpression().pattern().lower() in str(self.sourceModel().data(index)).lower() or \
            self.filterRegularExpression().pattern().lower() in str(index.internalPointer().id()).lower()


# ****************** NODES ****************************


class CustomNode:
    def __init__(self, new=False):
        self._children = []
        self._parent = None
        self._row = 0

        self.flag_new = new
        self.column_count = 1

    def data(self, column):
        pass

    def id(self):
        pass

    def childCount(self):
        return len(self._children)

    def child(self, row):
        if 0 <= row < self.childCount():
            return self._children[row]

    def parent(self):
        return self._parent

    def row(self):
        return self._row

    def addChild(self, child, row=None):
        child._parent = self
        if row is not None:
            child._row = row
            self._children.insert(row, child)

            # update child rows to reflect changes
            for i in range(len(self._children)):
                self.child(i)._row = i
        else:
            child._row = len(self._children)
            self._children.append(child)

    def removeChild(self, row):
        if row < 0 or row > len(self._children):
            return
        child = self._children.pop(row)
        child._parent = None

        # update child rows to reflect changes
        for i in range(len(self._children)):
            c = self.child(i)._row = i


class ClassNode(CustomNode):
    def __init__(self, data: XPlanungItem, new=False):
        super(ClassNode, self).__init__(new=new)
        self._data = data

        self.xplan_module = self._data.xtype.__module__.split('.')[-2]

    def data(self, column):
        return self._data.xtype.__name__

    def id(self):
        return self._data.xid

    def xplanItem(self):
        return self._data


class CategoryNode(CustomNode):
    def __init__(self, category_name):
        self.category_name = category_name

        super(CategoryNode, self).__init__()

    def data(self, column):
        return self.category_name
