import functools
import html
import logging
from enum import Enum
import yaml

from qgis.PyQt.QtGui import QFontMetrics, QIcon, QCloseEvent
from qgis.PyQt.QtCore import (QAbstractItemModel, Qt, QModelIndex, QSettings, QSortFilterProxyModel,
                              pyqtSlot, QObject, QEvent, QPoint, QSize)
from qgis.PyQt.QtWidgets import (QTreeView, QHeaderView, QAbstractItemView, QToolTip, QMenu, QAction, QLineEdit)
from sqlalchemy import inspect

from SAGisXPlanung.config import export_version
from SAGisXPlanung.XPlan.mixins import ElementOrderMixin
from SAGisXPlanung.config import xplan_tooltip
from SAGisXPlanung.gui.style import TagStyledDelegate, HighlightRowProxyStyle
from SAGisXPlanung.utils import CLASSES

from .basepage import SettingsPage

logger = logging.getLogger(__name__)


class AttributeConfigPage(SettingsPage):
    def __init__(self, parent=None):
        super(AttributeConfigPage, self).__init__(parent)
        self.ui = None

    def setupUi(self, ui):
        self.ui = ui
        self.ui.attribute_view = QAttributeConfigView()
        self.ui.tab_attributes.layout().addWidget(self.ui.attribute_view)
        self.ui.filter_edit.setPlaceholderText('Suchen...')
        self.ui.filter_edit.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.LeadingPosition)
        self.ui.filter_edit.textChanged.connect(self.ui.attribute_view.onFilterTextChanged)

    def setupData(self):
        self.ui.attribute_view.setupModelData()

    def closeEvent(self, event: QCloseEvent):
        conf = self.ui.attribute_view.config_dict()
        s = QSettings()
        s.setValue(f"plugins/xplanung/attribute_config", yaml.dump(conf, default_flow_style=False))


class QAttributeConfigView(QTreeView):

    def __init__(self, parent=None):
        super(QAttributeConfigView, self).__init__(parent)

        self._model = AttributeConfigModel()

        self.proxy = SortProxyModel(self)
        self.proxy.setSourceModel(self._model)
        self.setModel(self.proxy)

        self.setItemDelegate(TagStyledDelegate())
        self.proxy_style = HighlightRowProxyStyle('Fusion')
        self.proxy_style.setParent(self)
        self.setStyle(self.proxy_style)
        self.setMouseTracking(True)

        self.viewport().installEventFilter(QToolTipper(self))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenuRequested)

        # header setup
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.Stretch)

        # model setup
        self.setupModelData()

    def setupModelData(self):
        self.clear()

        s = QSettings()
        config = yaml.safe_load(s.value(f"plugins/xplanung/attribute_config", '')) or {}

        for xplan_class_name, xplan_class in CLASSES.items():
            if hasattr(xplan_class, 'xp_versions') and export_version() not in xplan_class.xp_versions:
                continue

            node = AttributeTreeNode(xplan_class_name, '', False)

            if not issubclass(xplan_class, ElementOrderMixin):
                continue

            cols = inspect(xplan_class).columns
            for attribute in xplan_class.element_order(include_base=False, only_columns=True,
                                                       version=export_version()):
                try:
                    index = cols.keys().index(attribute)
                    nullable = cols[index].nullable
                except ValueError:
                    nullable = True

                desc = xplan_tooltip(xplan_class, attribute, plain=True)
                unchecked = attribute in config.get(xplan_class_name, [])
                attribute_node = AttributeTreeNode(attribute, desc, not unchecked, required=not nullable)
                node.addChild(attribute_node)
            self._model.addChild(node)

        self.expandAll()

    def sizeHint(self):
        size = super(QAttributeConfigView, self).sizeHint()
        return QSize(size.width(), 80)

    def clear(self):
        self._model.clear()

    @pyqtSlot(str)
    def onFilterTextChanged(self, text: str):
        self.proxy.setFilterRegularExpression(text)

    def config_dict(self):
        config = {}

        for top_node in self._model._root._children:
            config[top_node.name] = [node.name for node in top_node._children if not node.is_checked]

        return config

    @pyqtSlot(QPoint)
    def onContextMenuRequested(self, pos: QPoint):
        """ context menu to select/deselect all attributes within a category """
        index = self.proxy.mapToSource(self.indexAt(pos))

        # return if index is not a top level item (category items are always top-level)
        if index.parent().isValid():
            return

        menu = QMenu()
        menu.setToolTipsVisible(True)

        select_all_action = QAction(QIcon(':/images/themes/default/mActionSelectAllTree.svg'), 'Alles wählen')
        select_all_action.setToolTip('Alle Attribute dieser Objektklasse wählen.')
        select_all_action.triggered.connect(functools.partial(self.onSelectCategoryTriggered, index, True))
        menu.addAction(select_all_action)

        deselect_all_action = QAction(QIcon(':/images/themes/default/mActionDeselectAllTree.svg'), 'Alles abwählen')
        deselect_all_action.setToolTip('Alle Attribute dieser Objektklasse abwählen. Verpflichtende Attribute werden nicht abgewählt.')
        deselect_all_action.triggered.connect(functools.partial(self.onSelectCategoryTriggered, index, False))
        menu.addAction(deselect_all_action)

        menu.exec_(self.viewport().mapToGlobal(pos))

    @pyqtSlot(QModelIndex, bool, bool)
    def onSelectCategoryTriggered(self, index: QModelIndex, select: bool, checked: bool):
        node = index.internalPointer()

        for i in range(node.childCount()):
            match = self._model.index(i, 0, index)
            self._model.setData(match.siblingAtColumn(2), select, Qt.CheckStateRole)


class AttributeConfigModel(QAbstractItemModel):
    def __init__(self, nodes=None):
        super(AttributeConfigModel, self).__init__()
        if nodes is None:
            nodes = []
        self._horizontal_header = ['XPlanung-Attribut', 'Beschreibung', 'Anzeigen']

        self._root = AttributeTreeNode()
        for node in nodes:
            self._root.addChild(node)

    def clear(self):
        self.beginResetModel()
        for i in range(self._root.childCount()):
            item = self._root.child(i)
            del item
        self._root._children.clear()
        self.endResetModel()

    def addChild(self, node, _parent=QModelIndex()):
        row = self.rowCount(_parent)
        if not _parent or not _parent.isValid():
            parent = self._root
        else:
            parent = _parent.internalPointer()
        self.beginInsertRows(_parent, row, row)
        parent.addChild(node)
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
        if role == Qt.ToolTipRole:
            return '<qt>{}</qt>'.format(html.escape(node.data(index.column())))
        if role == Qt.CheckStateRole and index.column() == 2 and index.parent().isValid():
            return node.checked()
        return None

    def flags(self, index: QModelIndex):
        current_flags = super(AttributeConfigModel, self).flags(index)
        flags = current_flags & ~Qt.ItemIsSelectable

        if not index.parent().isValid():
            return flags & ~Qt.ItemIsEnabled

        node = index.internalPointer()
        if node.required:
            return flags & ~Qt.ItemIsEnabled
        if index.column() == 2:
            return flags | Qt.ItemIsUserCheckable

        return flags

    def setData(self, index, value, role=Qt.EditRole):
        if index.column() == 2:
            if role == Qt.EditRole:
                return False
            if role == Qt.CheckStateRole:
                item = self.itemAtIndex(index)
                if item.required:
                    return True
                item.is_checked = value
                self.dataChanged.emit(index, index)
                return True

        return super(AttributeConfigModel, self).setData(index, value, role)

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._horizontal_header[col]

    def itemAtIndex(self, index: QModelIndex):
        if not index.isValid():
            return self._root

        return index.internalPointer()

    def index(self, row, column, _parent=QModelIndex()):
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
        return 3


class SortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setRecursiveFilteringEnabled(True)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)

    def filterAcceptsRow(self, source_row: int, parent: QModelIndex):
        index = self.sourceModel().index(source_row, 0, parent)

        # accept if any of the parents is accepted
        while parent.isValid():
            if self.filterAcceptsRow(parent.row(), parent.parent()):
                return True
            parent = parent.parent()

        return self.filterRegularExpression().pattern().lower() in str(self.sourceModel().data(index)).lower()


# ****************** NODES ****************************

class AttributeTreeNode:
    def __init__(self, name: str = None, description: str = None, is_checked: bool = None, required=False):
        self._children = []
        self._parent = None
        self._row = 0

        self.name = name
        self.description = description
        self.is_checked = is_checked
        self.column_count = 3

        self.required = required

    def data(self, column):
        if column == 0:
            return self.name
        if column == 1:
            return self.description

    def checked(self):
        if self.required:
            return Qt.Checked
        return Qt.Checked if self.is_checked else Qt.Unchecked

    def childCount(self):
        return len(self._children)

    def child(self, row):
        if 0 <= row < self.childCount():
            return self._children[row]

    def parent(self):
        return self._parent

    def row(self):
        return self._row

    def addChild(self, child):
        child._parent = self
        child._row = len(self._children)
        self._children.append(child)

    def removeChild(self, row):
        if row < 0 or row > len(self._children):
            return
        child = self._children.pop(row)
        child._parent = None

        # update child rows to reflect changes
        for i in range(len(self._children)):
            self.child(i)._row = i


# ****************** EVENT FILTER ****************************

class QToolTipper(QObject):

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.ToolTip:
            view: QAbstractItemView = obj.parent()
            if not view:
                return False
            index = view.indexAt(event.pos())
            if not index.isValid():
                return False

            item_text = view.model().data(index)
            fm = QFontMetrics(view.font())
            item_text_width = fm.width(item_text)
            rect = view.visualRect(index)
            if len(item_text) != 0 and item_text_width > rect.width():
                tooltip = view.model().data(index, Qt.ToolTipRole)
                QToolTip.showText(event.globalPos(), tooltip, view, rect)
            else:
                QToolTip.hideText()
            return True
        return False
