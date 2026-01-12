import datetime
import inspect
import logging
import os
from collections import namedtuple
from dataclasses import dataclass
from typing import Any, List, Optional

import qasync
import yaml
from PyQt5.QtCore import QAbstractItemModel, QSettings
from PyQt5.QtGui import QColor
from geoalchemy2 import WKBElement, WKTElement

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSortFilterProxyModel, pyqtSlot, QModelIndex, QRegExp, pyqtSignal
from qgis.PyQt.QtWidgets import QHeaderView, QLineEdit
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface
from sqlalchemy import select
from sqlalchemy.orm import class_mapper, RelationshipProperty

from SAGisXPlanung import BASE_DIR, Session, Base, SessionAsync
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_AbstraktesPraesentationsobjekt
from SAGisXPlanung.XPlan.codelists import CodeListValue
from SAGisXPlanung.XPlan.data_types import XP_ExterneReferenz
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich
from SAGisXPlanung.core.helper import update_field_value, is_mapped, is_mapped_instance, base_models
from SAGisXPlanung.core.mixins.mixins import ElementOrderMixin, FeatureType
from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import xplan_tooltip, export_version
from SAGisXPlanung.gui.XPEditAttributeDialog import XPEditAttributeDialog
from SAGisXPlanung.gui.commands import AttributeChangedCommand
from SAGisXPlanung.gui.style import load_svg, ApplicationColor
from SAGisXPlanung.gui.style.styles import SeparatorDelegate, HighlightRowProxyStyle
from SAGisXPlanung.gui.widgets.inputs.QRelationDropdowns import QAddRelationDropdown

FORM_CLASS, CLS = uic.loadUiType(os.path.join(BASE_DIR, 'ui/attribute_edit.ui'))
logger = logging.getLogger(__name__)

ObjectRole = Qt.UserRole + 1
NodeRole = Qt.UserRole + 2

style = """
QToolButton[objectName="button_flash"], QToolButton[objectName="button_zoom"] {{
    background: palette(window); 
    border: 0px;
    padding: 5px;
    border-radius: 5px;
}}
QToolButton:hover[objectName="button_flash"], QToolButton:hover[objectName="button_zoom"] {{
    background-color: {_button_hover_bg};
}}

#title-label {{
    font-size: 12px;
    font-family: 'Consolas', 'Monaco', 'Lucida Console', 'Liberation Mono', 'DejaVu Sans Mono', 'Bitstream Vera Sans Mono', 'Courier New', monospace;
    font-weight: 600;
    margin: 0px;
    padding: 0px;
}}

#subtitle-label {{
    font-weight: 400;
    color: {_label_color_mute};
    margin: 0px;
    padding: 0px;
}}

QLineEdit[objectName="search_edit"] {{
    padding: 8px 8px 8px 8px;
    border: 1px solid #d1d5db;
    border-radius: 3px;
    background-color: white;
}}
QLineEdit:focus[objectName="search_edit"] {{
    border-color: #3b82f6;
}}

QToolButton[class=type_button] {{
    border: none;
    border-radius: 5px;
    background-color: palette(window);
    padding: 5px;
}}
QToolButton:checked[class=type_button] {{
    border: 1px solid #d1d5db;
    background-color: white;
}}
QToolButton[class=type_button]:hover:!checked {{
    background-color: #e5e7eb;
}}
"""



@dataclass
class TreeNode:

    name: str
    value: Any = None
    children: List['TreeNode'] = None
    node_type: str = "attribute"  # "attribute", "relation", "section"
    icon_type: str = None  # "attribute", "link", "expand"

    def __post_init__(self):
        if self.children is None:
            self.children = []

    def child_count(self) -> int:
        return len(self.children)

    def child(self, row: int) -> Optional['TreeNode']:
        if 0 <= row < len(self.children):
            return self.children[row]
        return None

    def add_child(self, child: 'TreeNode'):
        self.children.append(child)

    @staticmethod
    def create_section(name: str, objects: List[Any]) -> 'TreeNode':
        count = len(objects)
        section = TreeNode(
            name=name,
            value=f"{count} Objekte" if count != 1 else "1 Objekt",
            node_type="section"
        )

        for i, obj in enumerate(objects):
            ref_node = TreeNode(
                name=f'Objekt {i + 1}',
                value=XPlanungItem(xid=str(obj.id), xtype=obj.__class__),
                node_type="relation"
            )
            section.add_child(ref_node)

        return section


@dataclass
class NavigationItem:
    """Represents a step in the navigation history"""
    xplan_item: XPlanungItem
    relation_name: Optional[str] = None  # The relation used to navigate here
    display_name: Optional[str] = None  # Display name for breadcrumb

    def __str__(self):
        return self.display_name or self.xplan_item.xtype.__name__


class QAttributeEdit(CLS, FORM_CLASS):
    nameChanged = pyqtSignal(str)

    ICON_DEFAULT_SIZE = 24
    TEXT_DEFAULT_SIZE = 6
    ATTRIBUTE_SIZE = 'skalierung'
    ATTRIBUTE_ANGLE = 'drehwinkel'

    @staticmethod
    def create(xplanung_item: XPlanungItem, parent):
        if issubclass(xplanung_item.xtype, XP_AbstraktesPraesentationsobjekt):
            from SAGisXPlanung.gui.widgets.QAttributeEditAnnotationItem import QAttributeEditAnnotationItem
            return QAttributeEditAnnotationItem(xplanung_item, parent)
        else:
            return QAttributeEdit(xplanung_item, parent)

    @staticmethod
    def _load_tree_node(xplan_item: XPlanungItem) -> TreeNode:
        with Session() as session:
            xtype = xplan_item.xtype
            plan_content = session.query(xtype).get(xplan_item.xid)
            base_classes = base_models(xtype)

            attribute_config = yaml.safe_load(QSettings().value(f"plugins/xplanung/attribute_config", '')) or {}

            def skip_column(attr):
                for mro_member in base_classes:
                    if attr in attribute_config.get(mro_member.__name__, []):
                        return True
                return False

            root_node = TreeNode("root", node_type="root")
            for (attr, mapper_property) in xtype.element_order(version=export_version(), ret_fmt='sqla'):
                if skip_column(attr):
                    continue

                value = getattr(plan_content, attr)
                xplan_attribute_name = xtype.xplan_attribute_name(attr)

                if isinstance(mapper_property, RelationshipProperty):
                    form_type = mapper_property.info.get('form-type')
                    if form_type == 'inline':
                        root_node.add_child(TreeNode(xplan_attribute_name, value, node_type="attribute"))
                    elif value is not None and isinstance(value, list):
                        root_node.add_child(TreeNode.create_section(xplan_attribute_name, value))
                    else:
                        root_node.add_child(
                            TreeNode(
                                xplan_attribute_name,
                                XPlanungItem(xid=str(value.id), xtype=value.__class__) if value is not None else '',
                                node_type="relation"
                            )
                        )
                else:
                    root_node.add_child(TreeNode(xplan_attribute_name, value, node_type="attribute"))

            return root_node

    def __init__(self, xplanung_item: XPlanungItem, parent):
        super(QAttributeEdit, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self._xplanung_item = xplanung_item

        # info header setup
        self.label_object_name.setObjectName("title-label")
        self.label_object_type.setObjectName("subtitle-label")
        self._update_view()

        enabled = issubclass(self._xplanung_item.xtype, FeatureType)
        self.button_flash.setEnabled(enabled)
        self.button_zoom.setEnabled(enabled)

        self.button_flash.setToolTip("Objekt auf Karte aufleuchten lassen")
        self.button_zoom.setToolTip("Zu Objekt zoomen")
        self.button_flash.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/flare.svg'),
                                            color=ApplicationColor.Tertiary))
        self.button_zoom.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/zoom-to.svg'),
                                                  color=ApplicationColor.Tertiary))
        self.button_zoom.clicked.connect(self.on_button_zoom_clicked)
        self.button_flash.clicked.connect(self.on_button_flash_clicked)

        # search setup
        self.search_edit.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.LeadingPosition)
        self.search_edit.textChanged.connect(self.onFilterTextChanged)

        # filter setup
        self.filter_attribute.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/short_text.svg'), color=ApplicationColor.Tertiary))
        self.filter_relation.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/link.svg'), color=ApplicationColor.Tertiary))
        self.filter_all.setProperty('class', 'type_button')
        self.filter_attribute.setProperty('class', 'type_button')
        self.filter_relation.setProperty('class', 'type_button')
        self.filter_all.clicked.connect(lambda: self.proxyModel.set_node_type_filter(None))
        self.filter_attribute.clicked.connect(lambda: self.proxyModel.set_node_type_filter("attribute"))
        self.filter_relation.clicked.connect(lambda: self.proxyModel.set_node_type_filter("relation"))

        # model
        root_node = QAttributeEdit._load_tree_node(self._xplanung_item)
        self.model = EntityTreeModel(root_node, self._xplanung_item)
        self.proxyModel = AttributeTreeFilterProxyModel(self.treeView)
        self.proxyModel.setSourceModel(self.model)
        self.treeView.setModel(self.proxyModel)

        # header setup
        header = self.treeView.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignCenter)

        self.treeView.doubleClicked.connect(self.on_double_clicked)

        # -------------- STYLE -------------
        self.link_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/next.svg'), color=ApplicationColor.Tertiary)
        self.delegate = SeparatorDelegate(self.link_icon, self.treeView)
        self.delegate.link_clicked.connect(self.on_relation_clicked)
        self.treeView.setItemDelegate(self.delegate)
        self.proxy_style = HighlightRowProxyStyle('Fusion')
        self.proxy_style.setParent(self.treeView)
        self.treeView.setStyle(self.proxy_style)
        self.treeView.setMouseTracking(True)

        self.setStyleSheet(style.format(
            _button_hover_bg=ApplicationColor.Grey300,
            _label_color_mute=ApplicationColor.Grey600
        ))
        self.treeView.setStyleSheet("QTreeView::item { padding: 10px;}")

    def _update_view(self):
        def _object_category_name(xtype: type) -> str:
            if issubclass(xtype, XP_AbstraktesPraesentationsobjekt):
                return 'Präsentationsobjekt'
            elif issubclass(xtype, FeatureType):
                return 'FeatureType'
            else:
                return 'DataType'

        self.label_object_name.setText(self._xplanung_item.xtype.__name__)
        self.label_object_type.setText(_object_category_name(self._xplanung_item.xtype))

    def model_index(self, attr: str):
        indices = self.model.match(self.model.index(0, 0), Qt.DisplayRole, attr, 1, Qt.MatchFixedString)
        if not indices:
            return QModelIndex()
        return indices[0].siblingAtColumn(1)

    @qasync.asyncSlot(bool)
    async def on_button_zoom_clicked(self, checked: bool):
        async with SessionAsync.begin() as session:
            xtype = self._xplanung_item.xtype
            orm_id = self._xplanung_item.xid
            stmt = select(getattr(xtype, xtype.__geometry_column_name__)).filter_by(id=orm_id)
            res = await session.execute(stmt)
            db_result = res.scalar_one()

            geom = geometry_from_spatial_element(db_result)
            iface.mapCanvas().zoomToFeatureExtent(geom.boundingBox())
            iface.mapCanvas().refresh()

    @qasync.asyncSlot(bool)
    async def on_button_flash_clicked(self, checked: bool):
        async with SessionAsync.begin() as session:
            xtype = self._xplanung_item.xtype
            orm_id = self._xplanung_item.xid
            stmt = select(getattr(xtype, xtype.__geometry_column_name__)).filter_by(id=orm_id)
            res = await session.execute(stmt)
            db_result = res.scalar_one()

            geom = geometry_from_spatial_element(db_result)
            iface.mapCanvas().flashGeometries([geom])

    @pyqtSlot(str)
    def onFilterTextChanged(self, text: str):
        self.proxyModel.setFilterFixedString(text)

    @pyqtSlot(QModelIndex)
    def on_relation_clicked(self, index: QModelIndex):
        attribute_name = index.siblingAtColumn(0).data()
        related_xplan_item = index.data(role=ObjectRole)
        display_name = related_xplan_item.xtype.__name__

        nav_item = NavigationItem(
            xplan_item=related_xplan_item,
            relation_name=attribute_name,
            display_name=display_name
        )

        self.navigate_to(nav_item)

    @pyqtSlot(QModelIndex)
    def on_double_clicked(self, index: QModelIndex):
        if index.column() == 0:
            return

        if not index.flags() & Qt.ItemIsSelectable or not index.flags() & Qt.ItemIsEnabled:
            return

        index = self.proxyModel.mapToSource(index)
        attribute_name = index.siblingAtColumn(0).data()

        rel = class_mapper(self._xplanung_item.xtype).get_property(attribute_name)
        if isinstance(rel, RelationshipProperty):
            dlg = XPEditAttributeDialog(attribute_name, None, index.data(role=ObjectRole), self._xplanung_item,
                                        set_default=False, parent=self)
            stub = namedtuple('stub', ['cls_type'])
            cb = QAddRelationDropdown(stub(cls_type=self._xplanung_item.xtype), (attribute_name, rel), parent=self)
            if (d := index.data(role=ObjectRole)) is not None:
                cb.setDefault(d)

            dlg.control.hide()
            dlg.hl1.addWidget(cb)
            dlg.control = cb
        else:
            base_classes = [c for c in list(inspect.getmro(self._xplanung_item.xtype)) if issubclass(c, Base)]
            cls = next(c for c in base_classes if hasattr(c, attribute_name) and c.attr_fits_version(attribute_name, export_version()))
            field_type = getattr(cls, attribute_name).property.columns[0].type
            dlg = XPEditAttributeDialog(attribute_name, field_type, index.data(role=ObjectRole),
                                        self._xplanung_item, parent=self)

        dlg.attributeChanged.connect(lambda original, value, a=attribute_name, i=index:
                                     self.pushAttributeChangedCommand(original, value, a, i))
        dlg.exec_()

    def pushAttributeChangedCommand(self, original_value, new_value, attr, index):
        command = AttributeChangedCommand(
            xplanung_item=self._xplanung_item,
            attribute=attr,
            previous_value=original_value,
            new_value=new_value,
            model_index=index
        )
        command.signal_proxy.changeApplied.connect(self.apply_field_change)
        self.parent.undo_stack.push(command)

    @pyqtSlot(QModelIndex, str, object)
    def apply_field_change(self, index, attr, value):
        if index is not None:
            self.model.setData(index, value)
            update_field_value(self._xplanung_item, attr, value)

        # send name changes to update other ui components
        if issubclass(self._xplanung_item.xtype, XP_Plan) and attr == 'name':
            self.nameChanged.emit(value)

    def navigate_to(self, nav_item: NavigationItem):
        root_node = self._load_tree_node(nav_item.xplan_item)
        self.model.set_source_data(root_node, nav_item.xplan_item)

        self._xplanung_item = nav_item.xplan_item
        self._update_view()


class EntityTreeModel(QAbstractItemModel):
    def __init__(self, root_node: TreeNode, xplan_item: XPlanungItem, parent=None):
        super().__init__(parent)
        self._root = root_node
        self._xplanung_item = xplan_item
        self._edit_allowed = issubclass(self._xplanung_item.xtype, (XP_Plan, XP_Bereich, XP_ExterneReferenz))

        self.icon_relation = load_svg(os.path.join(BASE_DIR, 'gui/resources/link.svg'), color=ApplicationColor.Tertiary)
        self.icon_attribute = load_svg(os.path.join(BASE_DIR, 'gui/resources/short_text.svg'), color=ApplicationColor.Tertiary)
        self.icon_section = load_svg(os.path.join(BASE_DIR, 'gui/resources/data_array.svg'), color=ApplicationColor.Tertiary)

    def set_source_data(self, root_node: TreeNode, xplan_item: XPlanungItem):
        self.beginResetModel()
        self._root = root_node
        self.endResetModel()

        self._xplanung_item = xplan_item

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            return self._root.child_count()

        node = parent.internalPointer()
        return node.child_count()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2  # Name and Value columns

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return node.name
            elif index.column() == 1:
                value = node.value
                if node.node_type == 'relation' and isinstance(value, XPlanungItem):
                    return value.xtype.__name__
                if isinstance(value, (XPlanungEnumMixin, ElementOrderMixin, CodeListValue)):
                    return str(value)
                if isinstance(value, (WKBElement, WKTElement)):
                    return geometry_from_spatial_element(value).asWkt()
                if isinstance(value, datetime.date):
                    return value.strftime("%d.%m.%Y")
                if isinstance(value, list):
                    return ", ".join(map(EntityTreeModel.parser, value))
                return value

        elif role == Qt.ItemDataRole.ForegroundRole:
            # Blue color for links/relations
            if node.node_type == "relation" and index.column() == 1:
                return QColor(100, 150, 255)

        elif role == Qt.ToolTipRole:
            # show tooltips for first column, which are the xplanung attributes
            if index.column() != 0:
                return
            return xplan_tooltip(self._xplanung_item.xtype, node.name)

        elif role == Qt.DecorationRole:
            if index.column() == 0:
                if node.node_type == "relation":
                    return self.icon_relation
                if node.node_type == "section":
                    return self.icon_section
                return self.icon_attribute
        elif role == ObjectRole:
            return node.value
        elif role == NodeRole:
            return node

        return None

    def setData(self, index: QModelIndex, value, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            node = index.internalPointer()
            if index.column() == 0:
                node.name = value
            elif index.column() == 1:
                node.value = value
            self.dataChanged.emit(index, index)

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 0:
                return "XPlanung-Attribut"
            elif section == 1:
                return "Wert"
        return None

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            child = self._root.child(row)
        else:
            parent_node = parent.internalPointer()
            child = parent_node.child(row)

        if child:
            return self.createIndex(row, column, child)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_node = index.internalPointer()
        parent_node = self._find_parent(self._root, child_node)

        if parent_node is None or parent_node == self._root:
            return QModelIndex()

        grandparent = self._find_parent(self._root, parent_node)
        if grandparent is None:
            row = self._root.children.index(parent_node)
        else:
            row = grandparent.children.index(parent_node)

        return self.createIndex(row, 0, parent_node)

    def _find_parent(self, root: TreeNode, target: TreeNode) -> Optional[TreeNode]:
        if target in root.children:
            return root

        for child in root.children:
            result = self._find_parent(child, target)
            if result:
                return result

        return None

    def flags(self, index):
        current_flags = super(EntityTreeModel, self).flags(index)
        node = index.internalPointer()
        if node is None or index.isValid() is False:
            return current_flags
        if not self._edit_allowed:
            return current_flags & ~Qt.ItemIsEnabled

        xtype = self._xplanung_item.xtype
        is_readonly = hasattr(xtype, '__readonly_columns__') and node.name in xtype.__readonly_columns__
        is_section_head = node.node_type == "section"
        is_link = node.node_type == "relation"
        if is_readonly:
            return current_flags & ~Qt.ItemIsEnabled
        if index.column() == 0 or is_section_head or is_link:
            return current_flags & ~Qt.ItemIsSelectable
        return current_flags

    @staticmethod
    def parser(value):
        if isinstance(value, datetime.date):
            return value.strftime("%d.%m.%Y")
        return str(value)


class AttributeTreeFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setRecursiveFilteringEnabled(True)
        # TODO: QT6 new property autoAcceptChildRows: self.setAutoAcceptChildRows(True)

        self._node_type_filter = None

    def set_node_type_filter(self, node_type: Optional[str]):
        self._node_type_filter = node_type
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self.filterRegExp().pattern() and self._node_type_filter is None:
            return True

        source_model = self.sourceModel()

        index_col0 = source_model.index(source_row, 0, source_parent)
        index_col1 = source_model.index(source_row, 1, source_parent)
        # Get node to check its type
        node = source_model.data(index_col0, NodeRole)

        # Check text filter match
        text_matches = True
        if self.filterRegExp().pattern():
            attribute_name = source_model.data(index_col0, Qt.DisplayRole)
            value = source_model.data(index_col1, Qt.DisplayRole)

            attribute_text = str(attribute_name) if attribute_name else ""
            value_text = str(value) if value else ""

            filter_pattern = self.filterRegExp()
            matches_attribute = filter_pattern.indexIn(attribute_text) >= 0
            matches_value = filter_pattern.indexIn(value_text) >= 0

            text_matches = matches_attribute or matches_value

        # Check node type filter match
        type_matches = True
        if self._node_type_filter is not None and node is not None:
            if self._node_type_filter == "attribute":
                type_matches = node.node_type == "attribute"
            elif self._node_type_filter == "relation":
                type_matches = node.node_type == "relation"

        # Row must match both filters
        ret = text_matches and type_matches

        # custom implementation of qt 6.0 autoAcceptChildRows property
        if not ret:
            ret = self.recursiveParentAcceptsRow(source_parent)
        return ret

    def recursiveParentAcceptsRow(self, source_parent):
        if source_parent.isValid():
            index = source_parent.parent()
            if self.filterAcceptsRow(source_parent.row(), index):
                return True
            return self.recursiveParentAcceptsRow(index)

        return False

    def setFilterFixedString(self, pattern: str):
        super().setFilterFixedString(pattern)
        self.invalidateFilter()
