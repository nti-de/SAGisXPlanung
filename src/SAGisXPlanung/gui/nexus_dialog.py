import datetime
import json
import logging
import os
from typing import List, Tuple

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QItemSelection, pyqtSlot
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from PyQt5.QtWidgets import QHeaderView, QAbstractItemView
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QLineEdit
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface
from sqlalchemy import select, inspect, func
from sqlalchemy.orm import selectin_polymorphic, defer, load_only

from SAGisXPlanung import Session, BASE_DIR
from SAGisXPlanung.XPlan.codelists import CodeListValue
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.XPlan.mixins import XPlanungEnumMixin, ElementOrderMixin
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import QgsConfig
from SAGisXPlanung.gui.style import ApplicationColor, SVGButtonEventFilter, load_svg, HighlightRowProxyStyle, \
    HighlightRowDelegate
from SAGisXPlanung.gui.style.styles import RemoveFrameFocusProxyStyle
from SAGisXPlanung.utils import PLAN_BASE_TYPES

FORM_CLASS_NEXUS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/nexus_dialog.ui'))
FORM_CLASS_NEXUS_SETTINGS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/nexus_settings_dialog.ui'))
logger = logging.getLogger(__name__)


def object_as_dict(obj):
    return {
        c.key: getattr(obj, c.key)
        for c in inspect(obj).mapper.column_attrs
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

    def __init__(self, parent=iface.mainWindow()):
        super(NexusDialog, self).__init__(parent)
        self.setupUi(self)

        self.nexus_search.setPlaceholderText('Suchen...')
        self.nexus_search.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.LeadingPosition)
        self.nexus_search.setMaximumWidth(360)

        self.button_reload.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/refresh.svg'),
                                            color=ApplicationColor.Tertiary))
        self.button_xplan_export.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/export_gml.svg'),
                                                  color=ApplicationColor.Tertiary))
        self.button_edit.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/edit.svg'),
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
        self.button_delete.setCursor(Qt.PointingHandCursor)
        self.button_settings.setCursor(Qt.PointingHandCursor)
        self.button_before.setCursor(Qt.PointingHandCursor)
        self.button_next.setCursor(Qt.PointingHandCursor)

        self.button_before.setDisabled(True)
        self.button_next.setDisabled(True)
        self.button_before.clicked.connect(self.on_pagination_backward)
        self.button_next.clicked.connect(self.on_pagination_forward)

        self.button_settings.clicked.connect(self.on_settings_clicked)

        self.enable_plan_actions(0)

        self.select_all_check.nextCheckState = self.next_check_state
        self.select_all_check.stateChanged.connect(self.on_select_all_check_state_changed)

        self.combo_plan_type.addItems(["Alle Pläne", "BP_Plan", "FP_Plan", "LP_Plan", "RP_Plan"])

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

        self.nexus_view.horizontalHeader().setStretchLastSection(True)
        self.nexus_view.horizontalHeader().setMaximumSectionSize(360)
        self.nexus_view.horizontalHeader().setDefaultSectionSize(180)
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
        self.model.set_source_data(data)

        self.enable_pagination_buttons()
        self.select_all_check.setCheckState(Qt.Unchecked)
        max_per_page = self.table_settings.max_entries_per_page
        self.label_result_count.setText(self.PAGE_COUNT_LABEL_PATTERN.format(
            _start_index=self.current_page_index*max_per_page + 1,
            _end_index=min(count, self.current_page_index*max_per_page + max_per_page),
            _total=count
        ))

    def fetch_database(self, page: int = 0) -> (int, List[dict]):
        with Session.begin() as session:
            count = session.execute(func.count(XP_Plan.id)).scalar_one()

            max_per_page = self.table_settings.max_entries_per_page
            stmt = select(XP_Plan).options(
                selectin_polymorphic(XP_Plan, PLAN_BASE_TYPES),
                load_only(*[col.name for col in XP_Plan.__table__.c if not col.name.endswith('_id')]),
                defer(XP_Plan.raeumlicherGeltungsbereich)
            ).order_by(XP_Plan.id).offset(page*max_per_page).fetch(max_per_page)
            objects = session.scalars(stmt).all()

            self.total_pages = (count + max_per_page - 1) // max_per_page
            return count, [object_as_dict(o) for o in objects]

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

    def next_check_state(self):
        if self.select_all_check.checkState() == Qt.Unchecked:
            self.select_all_check.setCheckState(Qt.Checked)
        else:
            self.select_all_check.setCheckState(Qt.Unchecked)

    def enable_plan_actions(self, selection_count: int):
        if selection_count == 0:
            self.button_xplan_export.setEnabled(False)
            self.button_edit.setEnabled(False)
            self.button_delete.setEnabled(False)
        elif selection_count == 1:
            self.button_xplan_export.setEnabled(True)
            self.button_edit.setEnabled(True)
            self.button_delete.setEnabled(True)
        else:
            self.button_xplan_export.setEnabled(False)
            self.button_edit.setEnabled(False)
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
    def __init__(self, columns: List[ColumnConfig] = None, max_entries_per_page=50):
        self.columns = columns
        self.max_entries_per_page = max_entries_per_page

    @classmethod
    def from_json(cls, json_config: str):
        config = json.loads(json_config)
        columns = []
        for column_name, visible in config["columns"]:
            columns.append(ColumnConfig(column_name, visible))
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

    def settings_json(self) -> str:
        return json.dumps({
            "columns": [(column.name, column.visible) for column in self.columns],
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