import datetime
import functools
import html
import inspect
import logging
import os
from collections import namedtuple
from dataclasses import dataclass
from typing import Any, List, Optional

import qasync
import yaml
from geoalchemy2 import WKBElement, WKTElement

from qgis.PyQt import uic
from qgis.PyQt.QtCore import (Qt, QSortFilterProxyModel, pyqtSlot, QModelIndex, pyqtSignal, QAbstractItemModel,
                              QSettings, QSize, QAbstractListModel, QRect, QEvent)
from qgis.PyQt.QtWidgets import (QHeaderView, QLineEdit, QWidget, QMenu, QSizePolicy, QListView, QStyledItemDelegate,
                                 QHBoxLayout, QToolButton, QStyleOptionViewItem, QStyle, QAction)
from qgis.PyQt.QtGui import QIcon, QColor, QFontMetrics, QPen, QPainter, QPalette, QBrush
from qgis.utils import iface
from sqlalchemy import select, inspect as sa_inspect
from sqlalchemy.orm import class_mapper, RelationshipProperty, load_only, MANYTOMANY, MANYTOONE

from SAGisXPlanung import BASE_DIR, Session, Base, SessionAsync, qt_version_tuple, PYQT5
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_AbstraktesPraesentationsobjekt
from SAGisXPlanung.XPlan.codelists import CodeListValue
from SAGisXPlanung.XPlan.data_types import XP_ExterneReferenz
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich
from SAGisXPlanung.core.helper import update_field_value, base_models, find_true_class
from SAGisXPlanung.core.mixins.mixins import ElementOrderMixin, FeatureType
from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import xplan_tooltip, export_version
from SAGisXPlanung.gui.XPEditAttributeDialog import XPEditAttributeDialog
from SAGisXPlanung.gui.commands import AttributeChangedCommand, ObjectsDeletedCommand, CommandType, StackChangeType
from SAGisXPlanung.gui.style import load_svg, ApplicationColor, SVGButtonEventFilter
from SAGisXPlanung.gui.style.styles import HighlightRowProxyStyle
from SAGisXPlanung.gui.widgets.commons.tooltip import ToolTip
from SAGisXPlanung.gui.widgets.inputs.QRelationDropdowns import QAddRelationDropdown

FORM_CLASS, CLS = uic.loadUiType(os.path.join(BASE_DIR, 'ui/attribute_edit.ui'))
logger = logging.getLogger(__name__)

ObjectRole = Qt.ItemDataRole.UserRole + 1
NodeRole = Qt.ItemDataRole.UserRole + 2

style = """
QToolButton[objectName="button_flash"], QToolButton[objectName="button_zoom"] {{
    background: transparent; 
    border: 0px;
    padding: 5px;
    border-radius: 5px;
}}
QToolButton:hover[objectName="button_flash"], QToolButton:hover[objectName="button_zoom"] {{
    background-color: {_button_hover_bg};
}}
QToolButton[objectName="back_button"] {{
    background-color: transparent; 
    border: 0px;
    padding: 3px;
    border-radius: 3px;;
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
    relation_preview: str = None

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
        section = TreeNode(name=name, node_type="section")

        for i, obj in enumerate(objects):
            ref_node = TreeNode(
                name=f'Objekt {i + 1}',
                value=XPlanungItem(xid=str(obj.id), xtype=obj.__class__),
                node_type="relation"
            )
            ref_node.create_preview(obj)
            section.add_child(ref_node)

        return section

    def create_preview(self, rel_obj):
        attributes = []
        for key, val in vars(rel_obj).items():
            if '_' in key or key in ('id', 'type'):
                continue
            if not val:
                continue
            if isinstance(val, (list, dict, set, tuple)) and len(val) == 0:
                continue
            if isinstance(val, str) and val.strip() == "":
                continue

            attributes.append((key, val))
            if len(attributes) == 3:
                break

        if not attributes:
            return

        rows = []
        for key, val in attributes:
            rows.append(
                f"<tr><th>{html.escape(str(key))}</th>"
                f"<td>{html.escape(str(val))}</td></tr>"
            )

        self.relation_preview = f'<b>{rel_obj.__class__.__name__}</b><br><table class="relation-preview" border="none" cellspacing="0" cellpadding="3">' + "".join(rows) + "</table>"


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
    def create(xplanung_item: XPlanungItem, parent, undo_stack):
        if issubclass(xplanung_item.xtype, XP_AbstraktesPraesentationsobjekt):
            from SAGisXPlanung.gui.widgets.QAttributeEditAnnotationItem import QAttributeEditAnnotationItem
            return QAttributeEditAnnotationItem(xplanung_item, parent, undo_stack)
        else:
            return QAttributeEdit(xplanung_item, parent, undo_stack)

    @staticmethod
    def _load_tree_node(xplan_item: XPlanungItem) -> TreeNode:
        with Session() as session:
            xtype = xplan_item.xtype
            plan_content = session.get(xtype, xplan_item.xid)
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

    def __init__(self, xplanung_item: XPlanungItem, parent, undo_stack):
        super(QAttributeEdit, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self._xplanung_item = xplanung_item
        self.undo_stack = undo_stack
        self.undo_stack.stack_changed.connect(self.on_undo_stack_changed)

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
        self.search_edit.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.ActionPosition.LeadingPosition)
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
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # nav bar setup
        self.nav_stack = NavigationStack()
        self.breadcrumbs = BreadcrumbBar(self)
        self.breadcrumbs.hide()
        self.breadcrumbs.crumbClicked.connect(self.on_breadcrumb_clicked)
        self.layout().insertWidget(0, self.breadcrumbs)
        root_item = NavigationItem(
            xplan_item=self._xplanung_item,
            display_name=self._xplanung_item.xtype.__name__
        )
        self.nav_stack.push(root_item)
        self._update_breadcrumbs()

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

    def _update_breadcrumbs(self):
        self.breadcrumbs.set_items(self.nav_stack.items())

    def model_index(self, attr: str):
        indices = self.model.match(self.model.index(0, 0), Qt.ItemDataRole.DisplayRole, attr, 1, Qt.MatchFlag.MatchFixedString)
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
        self.proxyModel.setFilterRegularExpression(text)

    @pyqtSlot(QModelIndex, QEvent)
    def on_relation_clicked(self, index: QModelIndex, event: QEvent):
        attribute_name = index.siblingAtColumn(0).data()
        related_xplan_item = index.data(role=ObjectRole)
        display_name = related_xplan_item.xtype.__name__

        if event.button() == Qt.MouseButton.LeftButton:
            nav_item = NavigationItem(
                xplan_item=related_xplan_item,
                relation_name=attribute_name,
                display_name=display_name
            )

            self.navigate_to(nav_item)
        else:
            # for relationship sections, get the attribute name from the parent row
            if index.parent().isValid():
                attribute_name = index.parent().siblingAtColumn(0).data()
                attribute_name = self._xplanung_item.xtype.attribute_by_version(attribute_name, export_version())

            rel = sa_inspect(self._xplanung_item.xtype).relationships[attribute_name]

            menu = QMenu(self)
            if rel.direction is MANYTOONE:
                return

            delete_action = QAction(load_svg(os.path.join(BASE_DIR, 'gui/resources/delete.svg')), 'Objekt löschen')
            delete_action.triggered.connect(functools.partial(
                self.on_delete_action_triggered,
                related_xplan_item,
                index
            ))
            menu.addAction(delete_action)
            if rel.direction is MANYTOMANY:
                unlink_action = QAction(load_svg(os.path.join(BASE_DIR, 'gui/resources/link-off.svg')), 'Beziehung auflösen')
                # menu.addAction(unlink_action) TODO: make unlink functional
            menu.exec(self.treeView.viewport().mapToGlobal(event.pos()))

    def on_delete_action_triggered(self, item_to_delete: XPlanungItem, index: QModelIndex, state):
        source_index = self.proxyModel.mapToSource(index)

        command = ObjectsDeletedCommand([(item_to_delete, None, source_index)], self)
        self.undo_stack.push(command)

    @qasync.asyncSlot(int, StackChangeType)
    async def on_undo_stack_changed(self, idx: int, change_type: StackChangeType):
        if change_type == StackChangeType.REDO:
            command = self.undo_stack.command(idx - 1)
        else:
            command = self.undo_stack.command(idx)

        if hasattr(command, 'command_type') and command.command_type == CommandType.OBJECT_DELETED:
            if change_type == StackChangeType.REDO:
                for delete_item in command.delete_items:
                    self.model.remove_node(delete_item.attribute_view_index)
            else:
                for delete_item in command.delete_items:
                    attr_name = delete_item.attribute_name
                    # find parent, to add object
                    parent_index_list = self.model.match(
                        self.model.index(0, 0),
                        Qt.ItemDataRole.DisplayRole,
                        attr_name,
                        -1,
                        Qt.MatchFlag.MatchWildcard | Qt.MatchFlag.MatchRecursive
                    )

                    if not parent_index_list:
                        return

                    parent_node = parent_index_list[0].internalPointer()

                    if parent_node.node_type == 'section':
                        insert_row = parent_node.child_count()
                        self.model.beginInsertRows(parent_index_list[0], insert_row, insert_row)
                        parent_node.add_child(TreeNode('', delete_item.xplan_item, node_type="relation"))
                        self.model.endInsertRows()
                    else:
                        parent_node.value = delete_item.xplan_item

    @pyqtSlot(QModelIndex)
    def on_double_clicked(self, index: QModelIndex):
        if index.column() == 0:
            return

        if not index.flags() & Qt.ItemFlag.ItemIsSelectable or not index.flags() & Qt.ItemFlag.ItemIsEnabled:
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
        dlg.fileChanged.connect(lambda file_content, a=attribute_name: self.on_file_content_changed(a, file_content))
        dlg.exec()

    def on_file_content_changed(self, attribute: str, file_content: bytes):
        with Session.begin() as session:
            cls = find_true_class(self._xplanung_item.xtype, attribute)
            load_opts = [load_only(getattr(cls, 'id'))]
            orm_instance = session.get(cls, self._xplanung_item.xid, options=load_opts)
            orm_instance.set_file_data(attribute, file_content)

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

    def navigate_to(self, nav_item: NavigationItem, push_history: bool = True):
        if push_history:
            self.nav_stack.push(nav_item)

        root_node = self._load_tree_node(nav_item.xplan_item)
        self.model.set_source_data(root_node, nav_item.xplan_item)

        self._xplanung_item = nav_item.xplan_item
        self._update_view()
        self._update_breadcrumbs()

    def on_breadcrumb_clicked(self, index: int):
        nav_item = self.nav_stack.pop_to(index)
        self.navigate_to(nav_item, push_history=False)


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
                parent = index.parent()
                if parent.isValid():
                    parent_node = parent.internalPointer()
                    if parent_node.node_type == "section":
                        return f"Objekt {index.row() + 1}"
                return node.name
            elif index.column() == 1:
                if node.node_type == "section":
                    count = node.child_count()
                    return f"{count} Objekte" if count != 1 else "1 Objekt"
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

        elif role == Qt.ItemDataRole.ToolTipRole:
            # show tooltips for first column, which are the xplanung attributes
            if index.column() != 0:
                return
            return xplan_tooltip(self._xplanung_item.xtype, node.name)

        elif role == Qt.ItemDataRole.DecorationRole:
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

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
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
            return current_flags & ~Qt.ItemFlag.ItemIsEnabled
        if index.column() == 0 or is_section_head or is_link:
            return current_flags & ~Qt.ItemFlag.ItemIsSelectable
        return current_flags

    @staticmethod
    def parser(value):
        if isinstance(value, datetime.date):
            return value.strftime("%d.%m.%Y")
        return str(value)

    def remove_node(self, index: QModelIndex):
        parent_index = self.parent(index)
        row = index.row()

        if not parent_index.isValid():
            # if it's a single row (uselist=False), set the value to empty
            node = index.internalPointer()
            node.value = None
            return

        self.beginRemoveRows(parent_index, row, row)
        parent_node = parent_index.internalPointer() if parent_index.isValid() else self._root
        parent_node.children.pop(row)
        self.endRemoveRows()

        parent_node = parent_index.internalPointer()
        if parent_node.node_type == "section":
            badge_index = self.createIndex(parent_index.row(), 1, parent_node)
            self.dataChanged.emit(badge_index, badge_index)


class AttributeTreeFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setRecursiveFilteringEnabled(True)
        # TODO: QT6 new property autoAcceptChildRows: self.setAutoAcceptChildRows(True)

        self._node_type_filter = None

    def set_node_type_filter(self, node_type: Optional[str]):
        self._node_type_filter = node_type
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if qt_version_tuple() < (5, 12, 0):
            filter_regex = self.filterRegExp()
        else:
            filter_regex = self.filterRegularExpression()

        if not filter_regex.pattern() and self._node_type_filter is None:
            return True

        source_model = self.sourceModel()

        index_col0 = source_model.index(source_row, 0, source_parent)
        index_col1 = source_model.index(source_row, 1, source_parent)
        # Get node to check its type
        node = source_model.data(index_col0, NodeRole)

        # Check text filter match
        text_matches = True
        if filter_regex.pattern():
            attribute_name = source_model.data(index_col0, Qt.ItemDataRole.DisplayRole)
            value = source_model.data(index_col1, Qt.ItemDataRole.DisplayRole)

            attribute_text = str(attribute_name) if attribute_name else ""
            value_text = str(value) if value else ""

            try:
                match = filter_regex.match(attribute_text)
                matches_attribute = match.hasMatch()
                match = filter_regex.match(value_text)
                matches_value = match.hasMatch()
            except AttributeError:
                # try match QRegExp for qt < 5.12
                matches_attribute = filter_regex.indexIn(attribute_text) >= 0
                matches_value = filter_regex.indexIn(value_text) >= 0

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


class NavigationStack:
    def __init__(self):
        self._items: List[NavigationItem] = []

    def _same_item(self, a: NavigationItem, b: NavigationItem) -> bool:
        return (
            a.xplan_item.xid == b.xplan_item.xid
            and a.xplan_item.xtype == b.xplan_item.xtype
        )

    def push(self, item: NavigationItem):
        """ Push item unless it already exists in the stack. If it exists, truncate to its first occurrence. """
        for i, existing in enumerate(self._items):
            if self._same_item(existing, item):
                self._items = self._items[: i + 1]
                return

        self._items.append(item)

    def pop_to(self, index: int) -> NavigationItem:
        self._items = self._items[: index + 1]
        return self._items[-1]

    def current(self) -> Optional[NavigationItem]:
        return self._items[-1] if self._items else None

    def items(self) -> List[NavigationItem]:
        return list(self._items)

    def clear(self):
        self._items.clear()


class BreadcrumbModel(QAbstractListModel):

    IsSeparatorRole = Qt.ItemDataRole.UserRole + 1
    IsEllipsisRole = Qt.ItemDataRole.UserRole + 2
    ItemIndexRole = Qt.ItemDataRole.UserRole + 3
    IsActiveRole = Qt.ItemDataRole.UserRole + 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []  # List of NavigationItem objects
        self._display_mode = "full"  # "full" or "collapsed"
        self._visible_indices = []  # Which items to show in collapsed mode

    def set_items(self, items: List):
        self.beginResetModel()
        self._items = items
        self._display_mode = "full"
        self._visible_indices = list(range(len(items)))
        self.endResetModel()

    def set_display_mode(self, mode: str, visible_indices: List[int] = None):
        """Switch between full and collapsed display."""
        if self._display_mode == mode and visible_indices == self._visible_indices:
            return

        self.beginResetModel()
        self._display_mode = mode
        if visible_indices is not None:
            self._visible_indices = visible_indices
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0

        if self._display_mode == "full":
            return len(self._items) * 2 - 1 if self._items else 0
        else:
            visible_count = len(self._visible_indices)
            if visible_count > 0:
                return (visible_count + 1) * 2 - 1 # (visible_items + ellipsis) * 2 - 1
            return 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()

        if self._display_mode == "full":
            # even indices are items, odd indices are separators
            is_separator = row % 2 == 1

            if role == self.IsSeparatorRole:
                return is_separator

            if is_separator:
                if role == Qt.ItemDataRole.DisplayRole:
                    return "›"
                return None

            # It's an item
            item_idx = row // 2
            if item_idx >= len(self._items):
                return None

            item = self._items[item_idx]

            if role == Qt.ItemDataRole.DisplayRole:
                return item.display_name or item.xplan_item.xtype.__name__
            elif role == self.ItemIndexRole:
                return item_idx
            elif role == self.IsActiveRole:
                return item_idx == len(self._items) - 1

        else:  # collapsed mode
            is_separator = row % 2 == 1

            if role == self.IsSeparatorRole:
                return is_separator

            is_ellipsis = row == 2
            if role == self.IsEllipsisRole:
                return is_ellipsis
            if role == Qt.ItemDataRole.DisplayRole and is_ellipsis:
                return "…"
            if role == Qt.ItemDataRole.DisplayRole and is_separator:
                return "›"

            # It's a visible item
            item_idx = self._row_to_item_index(row)
            item = self._items[item_idx]

            if role == Qt.ItemDataRole.DisplayRole:
                return item.display_name or item.xplan_item.xtype.__name__
            elif role == self.ItemIndexRole:
                return item_idx
            elif role == self.IsActiveRole:
                return item_idx == len(self._items) - 1

        return None

    def _row_to_item_index(self, row: int) -> int:
        if self._display_mode == "full":
            return row // 2
        else:
            if row == 0:
                return 0
            actual_idx = (row - 2) // 2
            return self._visible_indices[actual_idx]

    def get_hidden_items(self):
        """Get items that are hidden in collapsed mode (for ellipsis menu)."""
        if self._display_mode != "collapsed":
            return []

        all_indices = set(range(len(self._items)))
        visible = set(self._visible_indices)
        hidden_indices = sorted(all_indices - visible)

        return [(idx, self._items[idx]) for idx in hidden_indices]

    def item_count(self) -> int:
        return len(self._items)


class BreadcrumbDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hover_row = -1

    def set_hover_row(self, row: int):
        self._hover_row = row

    def paint(self, painter, option, index):
        painter.save()

        is_separator = index.data(BreadcrumbModel.IsSeparatorRole)
        is_active = index.data(BreadcrumbModel.IsActiveRole)
        text = index.data(Qt.ItemDataRole.DisplayRole)

        normal_color = QColor("#6b7280")
        hover_color = QColor("#111827")
        active_color = QColor("#111827")
        hover_bg = QColor("#f3f4f6")

        rect = option.rect

        if is_separator:
            painter.setPen(QPen(normal_color))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        else:
            # draw clickable breadcrumb
            is_hovered = self._hover_row == index.row()

            # Background for hover
            if is_hovered and not is_active:
                painter.fillRect(rect, hover_bg)

            # Text color
            if is_active:
                painter.setPen(QPen(active_color))
            elif is_hovered:
                painter.setPen(QPen(hover_color))
            else:
                painter.setPen(QPen(normal_color))

            text_rect = rect.adjusted(4, 0, -4, 0)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)

        painter.restore()

    def sizeHint(self, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole)

        fm = QFontMetrics(option.font)
        width = fm.horizontalAdvance(text)
        height = fm.height()

        return QSize(width + 8, height)

    def editorEvent(self, event, model, option, index):
        # We handle clicks in the view, so just return False
        return False


class BreadcrumbListView(QListView):

    itemClicked = pyqtSignal(int)  # emits the actual item index
    ellipsisClicked = pyqtSignal(list)  # emits list of hidden items

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QListView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.setFrameShape(QListView.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.viewport().setAutoFillBackground(False)

        self._delegate = BreadcrumbDelegate(self)
        self.setItemDelegate(self._delegate)

        self.setMouseTracking(True)

        self._hover_index = QModelIndex()

    def view_options(self):
        if PYQT5:
            option = self.viewOptions()
        else:
            option = QStyleOptionViewItem()
            self.initViewItemOption(option)

        return option

    def mouseMoveEvent(self, event):
        index = self.indexAt(event.pos())

        if index != self._hover_index:
            self._hover_index = index

            # Update delegate's hover state
            if index.isValid():
                is_separator = index.data(BreadcrumbModel.IsSeparatorRole)
                is_active = index.data(BreadcrumbModel.IsActiveRole)
                if not is_separator and not is_active:
                    self._delegate.set_hover_row(index.row())
                    self.viewport().update()
                    return

            self._delegate.set_hover_row(-1)
            self.viewport().update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_index = QModelIndex()
        self._delegate.set_hover_row(-1)
        self.viewport().update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                is_separator = index.data(BreadcrumbModel.IsSeparatorRole)
                is_ellipsis = index.data(BreadcrumbModel.IsEllipsisRole)
                is_active = index.data(BreadcrumbModel.IsActiveRole)

                if is_ellipsis:
                    # Show menu with hidden items
                    hidden_items = self.model().get_hidden_items()
                    self.ellipsisClicked.emit(hidden_items)
                elif not is_separator and not is_active:
                    # Regular breadcrumb click
                    item_index = index.data(BreadcrumbModel.ItemIndexRole)
                    if item_index is not None:
                        self.itemClicked.emit(item_index)

        super().mousePressEvent(event)

    def sizeHint(self):
        # calculate minimum height based on content
        if self.model() and self.model().rowCount() > 0:
            index = self.model().index(0, 0)
            item_size = self.itemDelegate().sizeHint(self.view_options(), index)
            return QSize(200, item_size.height())
        return QSize(200, 5)

    def minimumSizeHint(self):
        return self.sizeHint()


class BreadcrumbBar(QWidget):

    crumbClicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._ellipsis_menu = QMenu(self)

        self._back_button = QToolButton(self)
        self._back_button.setObjectName("back_button")
        self._back_button.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/arrow_back.svg'),
                                           color=ApplicationColor.Tertiary))
        self._back_hover_filter = SVGButtonEventFilter(ApplicationColor.Grey600, ApplicationColor.Tertiary)
        self._back_button.installEventFilter(self._back_hover_filter)
        self._layout.addWidget(self._back_button)

        # Create model and view
        self._model = BreadcrumbModel(self)
        self._list_view = BreadcrumbListView(self)
        self._list_view.setModel(self._model)

        self._list_view.setSizePolicy(self._list_view.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Maximum)

        self._list_view.itemClicked.connect(self.crumbClicked.emit)
        self._list_view.ellipsisClicked.connect(self._show_ellipsis_menu)
        self._back_button.clicked.connect(self.on_back_button_clicked)

        self._layout.addWidget(self._list_view)

    @pyqtSlot()
    def on_back_button_clicked(self):
        self.crumbClicked.emit(self._list_view.model().item_count() - 2) # len-1 is current item, -2 is previous

    def set_items(self, items: List):
        self._model.set_items(items)
        # only show breadcrumbs if there are 2 or more items (user has navigated)
        if len(items) < 2:
            self.hide()
        else:
            self.show()
            self._update_display_mode()

    def _calculate_full_width(self):
        """Calculate total width needed for full display."""
        total = 0
        for row in range(self._model.rowCount()):
            index = self._model.index(row, 0)
            size = self._list_view.itemDelegate().sizeHint(
                self._list_view.view_options(), index
            )
            total += size.width()
        return total

    def _update_display_mode(self):
        if self._model.rowCount() == 0:
            return

        available_width = self.width()
        needed_width = self._calculate_full_width()

        if needed_width <= available_width:
            self._model.set_display_mode("full")
        else:
            items_count = (self._model.rowCount() + 1) // 2

            if items_count <= 2:
                visible = list(range(items_count))
            else:
                visible = [0, items_count - 2, items_count - 1]

                self._model.set_display_mode("collapsed", visible)
                # try if collapse state is enough, otherwise collapse one further history item
                collapsed_width = self._calculate_full_width()
                if collapsed_width <= available_width:
                    return
                visible = [0, items_count - 1]

            self._model.set_display_mode("collapsed", visible)

    def _show_ellipsis_menu(self, hidden_items):
        """Show menu with hidden breadcrumb items."""
        self._ellipsis_menu.clear()

        for idx, item in hidden_items:
            display_name = item.display_name or item.xplan_item.xtype.__name__
            action = self._ellipsis_menu.addAction(display_name)
            action.triggered.connect(lambda _, i=idx: self.crumbClicked.emit(i))

        ellipsis_index = self._model.index(1, 0)
        if ellipsis_index.isValid():
            rect = self._list_view.visualRect(ellipsis_index)
            global_pos = self._list_view.mapToGlobal(rect.bottomLeft())
            self._ellipsis_menu.exec(global_pos)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display_mode()


class SeparatorDelegate(QStyledItemDelegate):
    """Custom delegate that draws separators between rows"""

    link_clicked = pyqtSignal(QModelIndex, QEvent)  # index, event

    def __init__(self, link_icon: QIcon, parent=None):
        super().__init__(parent)
        self.separator_color = QColor(200, 200, 200)  # Light gray
        self.separator_thickness = 1

        self.link_icon = link_icon

        # Badge styling
        self.badge_bg_color = QColor(220, 220, 220)  # Light gray background
        self.badge_text_color = QColor(80, 80, 80)   # Dark gray text
        self.badge_padding = 6
        self.badge_height = 20
        self.badge_radius = 10

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        if not index.isValid():
            return super().paint(painter, option, index)

        option.palette.setBrush(QPalette.ColorRole.HighlightedText, QBrush(Qt.GlobalColor.black))
        option.palette.setBrush(QPalette.ColorRole.Highlight, QColor('#CBD5E1'))

        is_last_column = index.column() == index.model().columnCount(index.parent()) - 1
        node = index.data(Qt.ItemDataRole.UserRole + 2)
        index_text = index.data(Qt.ItemDataRole.DisplayRole)

        if is_last_column and node.node_type == "section":
            # Custom rendering for section badges
            painter.save()

            # Draw the selection/hover background if needed
            if option.state & QStyle.StateFlag.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            # Calculate badge dimensions
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.horizontalAdvance(index_text)
            badge_width = text_width + 2 * self.badge_padding

            # Center the badge vertically in the cell
            badge_rect = option.rect.adjusted(
                self.badge_padding,
                (option.rect.height() - self.badge_height) // 2,
                -option.rect.width() + badge_width + self.badge_padding,
                -(option.rect.height() - self.badge_height) // 2
            )

            # Draw badge background (rounded rectangle)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(self.badge_bg_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, self.badge_radius, self.badge_radius)

            # Draw badge text
            painter.setPen(self.badge_text_color)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, index_text)

            painter.restore()

        elif is_last_column and node and node.node_type == "relation" and node.value:
            # Custom rendering for relation links with chevron
            painter.save()
            option.palette.setBrush(QPalette.ColorRole.HighlightedText, QColor(100, 150, 255))
            if option.state & QStyle.StateFlag.State_MouseOver:
                font = option.font
                font.setUnderline(True)
                painter.setFont(font)
            super().paint(painter, option, index)

            if self.link_icon:
                icon_size = 12
                # Position icon at the right side of the text
                font_metrics = painter.fontMetrics()
                text_width = font_metrics.horizontalAdvance(index_text)

                icon_x = option.rect.left() + text_width + 8
                icon_y = option.rect.top() + (option.rect.height() - icon_size) // 2

                icon_rect = option.rect.adjusted(
                    icon_x - option.rect.left(),
                    icon_y - option.rect.top(),
                    -(option.rect.width() - icon_size - (icon_x - option.rect.left())),
                    -(option.rect.bottom() - icon_y - icon_size)
                )

                self.link_icon.paint(painter, icon_rect)

            painter.restore()
        else:
            # Standard rendering for other items
            super().paint(painter, option, index)

        # Only draw the separator in the last column to avoid multiple overlapping lines
        if is_last_column:
            painter.save()
            pen = QPen(self.separator_color, self.separator_thickness)
            painter.setPen(pen)

            # Get the view to calculate full row width
            view = self.parent()
            y = option.rect.bottom()
            viewport_rect = view.viewport().rect()
            painter.drawLine(0, y, viewport_rect.right(), y)

            painter.restore()

    def editorEvent(self, event, model, option, index):
        node = index.data(Qt.ItemDataRole.UserRole + 2)
        is_relation = node and node.node_type == "relation" and index.column() == 1

        if is_relation and node.value:
            if event.type() == QEvent.Type.MouseButtonRelease:
                self.link_clicked.emit(index, event)
                return True

        return False

    def helpEvent(self, event, view, option, index):
        if event is None or view is None:
            return False

        node = index.data(Qt.ItemDataRole.UserRole + 2)
        is_last_column = index.column() == index.model().columnCount(index.parent()) - 1

        if not is_last_column or not node or node.node_type != "relation" or not node.value:
            return super().helpEvent(event, view, option, index)

        text = index.data(Qt.ItemDataRole.DisplayRole)
        fm = option.fontMetrics
        text_width = fm.horizontalAdvance(text)
        text_rect = QRect(option.rect.left(),  option.rect.top(), text_width + 10, option.rect.height())

        if not text_rect.contains(event.pos()):
            return False

        # TODO: rework tooltip: which attributes to show, formatting, etc.
        # tooltip = ToolTip(node.relation_preview, view.window())
        # tooltip.adjust_pos(view, index)
        # tooltip.show()
        return True

