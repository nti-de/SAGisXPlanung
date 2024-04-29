import asyncio
import datetime
import json
import logging
import os
from operator import attrgetter
from typing import List

import qasync

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QLineEdit, QHeaderView, QAbstractItemView, QMessageBox
from qgis.PyQt.QtGui import QIcon, QStandardItemModel, QStandardItem
from qgis.PyQt.QtCore import QAbstractTableModel, Qt, QModelIndex, QItemSelection, pyqtSlot, pyqtSignal
from qgis.core import Qgis
from qgis.utils import iface
from sqlalchemy import select, inspect, func, delete, text
from sqlalchemy.orm import selectin_polymorphic, defer, load_only, with_polymorphic

from SAGisXPlanung import Session, BASE_DIR, SessionAsync
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.core.converter_tasks import export_action, ActionCanceledException
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.config import QgsConfig
from SAGisXPlanung.core.canvas_display import plan_to_map
from SAGisXPlanung.ext.spinner import loading_animation
from SAGisXPlanung.ext.toast import Toaster
from SAGisXPlanung.gui.style import ApplicationColor, load_svg, HighlightRowProxyStyle, \
    HighlightRowDelegate
from SAGisXPlanung.gui.style.styles import RemoveFrameFocusProxyStyle
from SAGisXPlanung.utils import PLAN_BASE_TYPES

FORM_CLASS_NEXUS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/nexus_dialog.ui'))
FORM_CLASS_NEXUS_SETTINGS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/nexus_settings_dialog.ui'))
logger = logging.getLogger(__name__)


XID_ROLE = Qt.UserRole + 1
NAME_ROLE = Qt.UserRole + 2


def object_as_dict(obj, exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = []

    return {
        c.key: getattr(obj, c.key)
        for c in inspect(obj).mapper.column_attrs
        if not any(pattern in c.key for pattern in exclude_patterns)
    }


style = """
QTableView {{	
	background-color: white;
	gridline-color: {_grid_color};
	color: {_color};
}}
QTableView::item {{
	padding-left: 5px;
	padding-right: 5px;
	border: none;
	border-style: none;
}}
QTableView::item:selected {{
	color: {_selected_color};
	background-color: {_selected_bg_color};
}}
QTableView::item:hover {{
	color: {_hover_color};
}}

QToolButton {{
    background: palette(window); 
    border: 0px;
    padding: 5px;
    border-radius: 5px;
}}
QToolButton:hover {{
    background-color: {_button_hover_bg};
}}

QCheckBox {{
    background: palette(window); 
    border: 0px;
    padding-left: 5px;
    padding-top: 5px;
    padding-bottom: 5px;
    border-radius: 5px;
}}
QCheckBox:hover {{
    background-color: {_button_hover_bg};
}}

QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    border: none;
    margin: 1px;
    margin-top: 5px;
    margin-bottom: 5px;
    background: {_grid_color};
}}
"""


class NexusDialog(QDialog, FORM_CLASS_NEXUS):
    """ Dialog that provides an overview on all plans within the database and additional actions """

    PAGE_COUNT_LABEL_PATTERN = "{_start_index}-{_end_index} von {_total}"

    accessAttributesRequested = pyqtSignal(XPlanungItem)
    deletionOccurred = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(NexusDialog, self).__init__(parent)
        self.setupUi(self)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)

        self.nexus_search.setPlaceholderText('Suchen...')
        self.nexus_search.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.LeadingPosition)
        self.nexus_search.setMaximumWidth(360)
        self.nexus_search.editingFinished.connect(self.on_search_entered)

        self.button_reload.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/refresh.svg'),
                                            color=ApplicationColor.Tertiary))
        self.button_xplan_export.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/export_gml.svg'),
                                                  color=ApplicationColor.Tertiary))
        self.button_edit.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/edit.svg'),
                                          color=ApplicationColor.Tertiary))
        self.button_map.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/map.svg'),
                                         color=ApplicationColor.Tertiary))
        self.button_delete.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/delete.svg'),
                                            color=ApplicationColor.Tertiary))
        self.button_settings.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/settings.svg'),
                                              color=ApplicationColor.Tertiary))
        self.button_before.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/before.svg'),
                                            color=ApplicationColor.Tertiary))
        self.button_next.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/next.svg'),
                                          color=ApplicationColor.Tertiary))

        self.button_reload.setCursor(Qt.PointingHandCursor)
        self.button_xplan_export.setCursor(Qt.PointingHandCursor)
        self.button_edit.setCursor(Qt.PointingHandCursor)
        self.button_map.setCursor(Qt.PointingHandCursor)
        self.button_delete.setCursor(Qt.PointingHandCursor)
        self.button_settings.setCursor(Qt.PointingHandCursor)
        self.button_before.setCursor(Qt.PointingHandCursor)
        self.button_next.setCursor(Qt.PointingHandCursor)

        self.button_before.setDisabled(True)
        self.button_next.setDisabled(True)
        self.button_before.clicked.connect(self.on_pagination_backward)
        self.button_next.clicked.connect(self.on_pagination_forward)

        self.button_settings.clicked.connect(self.on_settings_clicked)
        self.button_map.clicked.connect(self.on_map_load_clicked)
        self.button_xplan_export.clicked.connect(self.on_export_clicked)
        self.button_edit.clicked.connect(self.on_edit_clicked)
        self.button_reload.clicked.connect(self.on_reload_clicked)
        self.button_delete.clicked.connect(self.on_delete_clicked)

        self.enable_plan_actions(0)

        self.select_all_check.nextCheckState = self.next_check_state
        self.select_all_check.stateChanged.connect(self.on_select_all_check_state_changed)

        self.combo_plan_type.addItem("Alle Pläne", PLAN_BASE_TYPES)
        for plan_base_type in PLAN_BASE_TYPES:
            self.combo_plan_type.addItem(plan_base_type.__name__, [plan_base_type])

        self.combo_plan_type.currentIndexChanged.connect(self.on_plan_type_filter_changed)

        # ------------- LOGIC -----------------
        self.current_page_index = 0
        self.total_pages = None
        if (s := QgsConfig.nexus_settings()) is not None:
            self.table_settings = TableSettings.from_json(s)
        else:
            self.table_settings = TableSettings(max_entries_per_page=10)

        # ------------- MODEL -----------------
        self.model = None
        self.setup_model()
        self.nexus_view.setModel(self.model)
        self.nexus_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.nexus_view.setSortingEnabled(True)
        self.nexus_view.sortByColumn(self.table_settings.sort_column_index(), Qt.AscendingOrder)

        self.nexus_view.horizontalHeader().setStretchLastSection(True)
        self.nexus_view.horizontalHeader().setMaximumSectionSize(360)
        self.nexus_view.horizontalHeader().setDefaultSectionSize(180)
        self.nexus_view.horizontalHeader().sortIndicatorChanged.connect(self.on_sort_changed)
        self.nexus_view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        self.table_proxy_style = RemoveFrameFocusProxyStyle('Fusion')
        self.table_proxy_style.setParent(self)
        self.nexus_view.setStyle(self.table_proxy_style)

        self.nexus_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # ------------- STYLESHEET -----------------
        self.setStyleSheet(style.format(
            _grid_color=ApplicationColor.Grey400,
            _color=ApplicationColor.Grey600,
            _hover_color=ApplicationColor.Primary,
            _selected_color=ApplicationColor.Primary,
            _selected_bg_color=ApplicationColor.SecondaryLight,
            _button_hover_bg=ApplicationColor.Grey300,
            _check_indicator_color=ApplicationColor.Tertiary
        ))

    def setup_model(self):
        count, data = self.fetch_database(self.current_page_index)

        self.label_result_count.setText(self.PAGE_COUNT_LABEL_PATTERN.format(
            _start_index=self.current_page_index + 1,
            _end_index=self.table_settings.max_entries_per_page,
            _total=count
        ))

        self.model = NexusTableModel(data)
        if self.table_settings.columns:
            self.model.set_column_header(self.table_settings.header_labels())
        else:
            self.table_settings.columns = [ColumnConfig(col_name, i)
                                           for i, col_name in enumerate(self.model._horizontal_header_keys)]

        self.enable_pagination_buttons()

    def paginate(self):
        count, data = self.fetch_database(self.current_page_index)
        if not data and self.current_page_index > 0:
            self.current_page_index -= 1
            self.paginate()
            return
        self.model.set_source_data(data)

        self.enable_pagination_buttons()
        self.select_all_check.setCheckState(Qt.Unchecked)
        self.enable_plan_actions(0)
        max_per_page = self.table_settings.max_entries_per_page
        self.label_result_count.setText(self.PAGE_COUNT_LABEL_PATTERN.format(
            _start_index=self.current_page_index * max_per_page + 1,
            _end_index=min(count, self.current_page_index * max_per_page + max_per_page),
            _total=count
        ))

    def _with_filter(self, query):
        filter_class = self.combo_plan_type.currentData()
        if len(filter_class) == 1:  # filter for specific plan type
            query = query.where(XP_Plan.type == str(filter_class[0].__name__).lower())

        search_text = self.nexus_search.text()
        if search_text:
            query = query.where(text("_sa_search_col @@ to_tsquery('german', :s) ").bindparams(s=search_text))

        return query

    def _sort_attr(self, polymorphic, attr_name):
        for class_type in PLAN_BASE_TYPES:
            try:
                attr = attrgetter(f'{class_type.__name__}.{attr_name}')(polymorphic)
                return attr
            except AttributeError:
                pass

    def fetch_database(self, page: int = 0) -> (int, List[dict]):
        with (Session.begin() as session):
            count = session.execute(self._with_filter(select(func.count(XP_Plan.id)))).scalar_one()

            max_per_page = self.table_settings.max_entries_per_page
            xp_plan_poly = with_polymorphic(XP_Plan, PLAN_BASE_TYPES)
            stmt = self._with_filter(select(xp_plan_poly).options(
                defer(getattr(xp_plan_poly, 'raeumlicherGeltungsbereich'))
            ))
            sort_by, sort_dir = self.table_settings.sort_column, self.table_settings.sort_order
            sort_attr = self._sort_attr(xp_plan_poly, sort_by)
            _order_by = getattr(sort_attr, sort_dir)()
            stmt = stmt.order_by(_order_by).offset(page * max_per_page).fetch(max_per_page)
            objects = session.scalars(stmt).all()

            self.total_pages = (count + max_per_page - 1) // max_per_page
            return count, [object_as_dict(o, exclude_patterns=['bereich', '_id']) for o in objects]

    @pyqtSlot(QItemSelection, QItemSelection)
    def on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        selected_rows = self.nexus_view.selectionModel().selectedRows()
        if len(selected_rows) == self.model.rowCount(QModelIndex()):
            self.select_all_check.setCheckState(Qt.Checked)
        elif len(selected_rows) > 0:
            self.select_all_check.setCheckState(Qt.PartiallyChecked)
        else:
            self.select_all_check.setCheckState(Qt.Unchecked)
        self.enable_plan_actions(len(selected_rows))

    @pyqtSlot(int, Qt.SortOrder)
    def on_sort_changed(self, logical_index: int, order: Qt.SortOrder):
        self.table_settings.set_sort(logical_index, order)
        self.paginate()

    @pyqtSlot()
    def on_search_entered(self):
        self.current_page_index = 0
        self.paginate()

    @pyqtSlot(int)
    def on_select_all_check_state_changed(self, state: int):
        if state == Qt.PartiallyChecked:
            return
        if state == Qt.Unchecked:
            self.nexus_view.clearSelection()
        else:
            self.nexus_view.selectAll()

    @pyqtSlot()
    def on_pagination_forward(self):
        self.current_page_index += 1
        self.paginate()

    @pyqtSlot()
    def on_pagination_backward(self):
        self.current_page_index -= 1
        self.paginate()

    @pyqtSlot()
    def on_map_load_clicked(self):
        selected_indices = self.nexus_view.selectionModel().selectedRows()
        if not selected_indices:
            return

        plan_xid = selected_indices[0].data(XID_ROLE)
        plan_to_map(plan_xid)

    @qasync.asyncSlot()
    async def on_export_clicked(self):
        async with loading_animation(self):
            selected_indices = self.nexus_view.selectionModel().selectedRows()
            if not selected_indices:
                return

            plan_xid = selected_indices[0].data(XID_ROLE)

            try:
                await export_action(self, plan_xid)

                Toaster.showMessage(self, message='Planwerk erfolgreich exportiert!', corner=Qt.BottomRightCorner,
                                    margin=20, icon=None, closable=False, color='#ffffff', background_color='#404040',
                                    timeout=3000)
            except ActionCanceledException:
                pass
            except Exception as e:
                logger.error(e)
                iface.messageBar().pushMessage("XPlanung Fehler", "XPlanGML-Dokument konnte nicht exportiert werden!",
                                               str(e), level=Qgis.Critical)

    @qasync.asyncSlot()
    async def on_delete_clicked(self):
        def _delete():
            with Session.begin() as session:
                statement = select(XP_Plan).where(XP_Plan.id.in_(selected_xplan_indices))
                objects = session.execute(statement).scalars().all()
                for o in objects:
                    session.delete(o)
            # following would be more efficient, but does not cascade correctly,
            # therefore it is required to load ORM-Instances first.
            # ###
            # statement = delete(XP_Plan).where(XP_Plan.id.in_(selected_xplan_indices))
            # result = await session.execute(statement)
            # print(result.rowcount)

        async with loading_animation(self):
            selected_indices = self.nexus_view.selectionModel().selectedRows()
            if not selected_indices:
                return

            selected_xplan_indices = [str(i.data(XID_ROLE)) for i in selected_indices]
            selected_plan_names = [i.data(NAME_ROLE) for i in selected_indices]

            msg = QMessageBox()
            msg.setWindowTitle("Löschvorgang bestätigen")
            names_text = "\n".join(selected_plan_names)
            msg.setText(f"Ausgewählte Pläne unwiderruflich löschen?\n\n{names_text}")
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            reply = msg.exec_()
            if reply == QMessageBox.No:
                return

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _delete)

            self.paginate()  # refresh views
            self.deletionOccurred.emit()  # notify other views

    @pyqtSlot()
    def on_reload_clicked(self):
        self.paginate()

    @pyqtSlot()
    def on_edit_clicked(self):
        selected_indices = self.nexus_view.selectionModel().selectedIndexes()
        if not selected_indices:
            return

        plan_xid = str(selected_indices[0].data(XID_ROLE))
        xplan_item = XPlanungItem(xid=plan_xid, xtype=XP_Plan, plan_xid=plan_xid)
        self.accessAttributesRequested.emit(xplan_item)

    @pyqtSlot()
    def on_settings_clicked(self):
        settings_dialog = NexusSettingsDialog(self.table_settings)
        settings_dialog.accepted.connect(self.on_settings_accepted)
        settings_dialog.exec()

    @pyqtSlot()
    def on_settings_accepted(self):
        self.model.set_column_header(self.table_settings.header_labels())

        self.current_page_index = 0
        self.paginate()

        QgsConfig.set_nexus_settings(self.table_settings.settings_json())

    @pyqtSlot(int)
    def on_plan_type_filter_changed(self, index: int):
        self.current_page_index = 0
        self.paginate()

    def next_check_state(self):
        if self.select_all_check.checkState() == Qt.Unchecked:
            self.select_all_check.setCheckState(Qt.Checked)
        else:
            self.select_all_check.setCheckState(Qt.Unchecked)

    def enable_plan_actions(self, selection_count: int):
        if selection_count == 0:
            self.button_xplan_export.setEnabled(False)
            self.button_edit.setEnabled(False)
            self.button_map.setEnabled(False)
            self.button_delete.setEnabled(False)
        elif selection_count == 1:
            self.button_xplan_export.setEnabled(True)
            self.button_edit.setEnabled(True)
            self.button_map.setEnabled(True)
            self.button_delete.setEnabled(True)
        else:
            self.button_xplan_export.setEnabled(False)
            self.button_edit.setEnabled(False)
            self.button_map.setEnabled(False)
            self.button_delete.setEnabled(True)

    def enable_pagination_buttons(self):
        self.button_next.setEnabled(self.current_page_index != self.total_pages - 1)
        self.button_before.setEnabled(self.current_page_index > 0)


class NexusTableModel(QAbstractTableModel):
    def __init__(self, data: List[dict]):
        super(NexusTableModel, self).__init__()
        self._data = data

        exclude_patterns = ['bereich', '_id']

        filtered_keys = set()
        for d in self._data:
            filtered_keys.update(key for key in d.keys() if not any(pattern in key for pattern in exclude_patterns))

        self._horizontal_header_keys = list(filtered_keys)

    def set_column_header(self, header_keys: List[str]):
        self._horizontal_header_keys = header_keys
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(self._horizontal_header_keys))

    def set_source_data(self, source_data: List[dict]):
        self.beginResetModel()
        self._data = source_data
        self.endResetModel()

    @staticmethod
    def parser(value):
        if isinstance(value, datetime.date):
            return value.strftime("%d.%m.%Y")
        return str(value)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            column_name = self._horizontal_header_keys[index.column()]
            value = self._data[index.row()].get(column_name, "")
            if value is None:
                return
            if isinstance(value, datetime.date):
                return value.strftime("%d.%m.%Y")
            if isinstance(value, list):
                return ", ".join(map(NexusTableModel.parser, value))
            return str(value)

        if role == XID_ROLE:
            return self._data[index.row()].get('id', None)
        if role == NAME_ROLE:
            return self._data[index.row()].get('name', None)

    def setData(self, index: QModelIndex, value, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)

    def headerData(self, col, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._horizontal_header_keys[col]
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return col + 1

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._horizontal_header_keys)


# --------- TABLE SETTINGS ----------

class ColumnConfig:
    def __init__(self, name, column_index, visible=True):
        self.name = name
        self.column_index = column_index
        self.visible = visible


class TableSettings:
    def __init__(self, columns: List[ColumnConfig] = None,
                 max_entries_per_page=50,
                 sort_column: str = 'id',
                 sort_order: str = 'asc'):
        self.columns = columns
        self.max_entries_per_page = max_entries_per_page
        self.sort_column = sort_column
        self.sort_order = sort_order

    @classmethod
    def from_json(cls, json_config: str):
        config = json.loads(json_config)
        columns = []
        for column_name, column_idx, visible in config["columns"]:
            columns.append(ColumnConfig(column_name, column_idx, visible))
        return cls(columns, config["max_entries_per_page"])

    def set_column_visibility(self, column_name, visibility):
        for column in self.columns:
            if column.name == column_name:
                column.visible = visibility
                break

    def set_max_entries_per_page(self, max_entries_per_page):
        self.max_entries_per_page = max_entries_per_page

    def header_labels(self) -> List[str]:
        return [col.name for col in self.columns if col.visible]

    def sort_column_index(self):
        return self.header_labels().index(self.sort_column)

    def set_sort(self, col: int, sort_order: Qt.SortOrder):
        self.sort_column = self.header_labels()[col]
        if sort_order == Qt.AscendingOrder:
            self.sort_order = 'asc'
        else:
            self.sort_order = 'desc'

    def settings_json(self) -> str:
        return json.dumps({
            "columns": [(column.name, column.column_index, column.visible) for column in self.columns],
            "max_entries_per_page": self.max_entries_per_page
        })


class NexusSettingsDialog(QDialog, FORM_CLASS_NEXUS_SETTINGS):
    """ Dialog that provides settings for organizing columns in the NexusDialog """

    def __init__(self, table_settings: TableSettings, parent=iface.mainWindow()):
        super(NexusSettingsDialog, self).__init__(parent)
        self.setupUi(self)
        self.table_settings = table_settings

        self.max_page_entries_edit.setValue(self.table_settings.max_entries_per_page)

        self.model = QStandardItemModel()
        self.columns_view.setModel(self.model)
        self.columns_view.setMouseTracking(True)
        self.columns_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.columns_view.setDragEnabled(True)
        self.columns_view.setAcceptDrops(True)
        self.columns_view.setDragDropOverwriteMode(False)
        self.columns_view.setDragDropMode(QAbstractItemView.InternalMove)
        self.columns_view.setDefaultDropAction(Qt.MoveAction)
        self.columns_view.setStyleSheet("QListView::item { padding: 5px; }")
        self.columns_view.setItemDelegate(HighlightRowDelegate())
        self.list_proxy_style = HighlightRowProxyStyle('Fusion')
        self.list_proxy_style.setParent(self)
        self.columns_view.setStyle(self.list_proxy_style)

        for column in self.table_settings.columns:
            item = QStandardItem(column.name)
            item.setCheckable(True)
            item.setData(Qt.Checked if column.visible else Qt.Unchecked, Qt.CheckStateRole)
            item.setFlags(item.flags() & ~Qt.ItemIsDropEnabled)

            self.model.appendRow(item)

    def accept(self):
        cols = []
        for index in range(self.model.rowCount()):
            item = self.model.item(index)

            col_config = ColumnConfig(
                name=item.data(Qt.DisplayRole),
                column_index=index,
                visible=item.data(Qt.CheckStateRole)
            )
            cols.append(col_config)

        self.table_settings.columns = cols
        self.table_settings.max_entries_per_page = self.max_page_entries_edit.value()

        super().accept()
