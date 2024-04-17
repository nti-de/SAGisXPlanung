import datetime
import logging
import os
from typing import List

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QItemSelection, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from PyQt5.QtWidgets import QHeaderView, QAbstractItemView
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QLineEdit
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface
from sqlalchemy import select, inspect
from sqlalchemy.orm import selectin_polymorphic, defer, load_only

from SAGisXPlanung import Session, BASE_DIR
from SAGisXPlanung.XPlan.codelists import CodeListValue
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.XPlan.mixins import XPlanungEnumMixin, ElementOrderMixin
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import QgsConfig
from SAGisXPlanung.gui.style import ApplicationColor, SVGButtonEventFilter, load_svg
from SAGisXPlanung.utils import PLAN_BASE_TYPES

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/nexus_dialog.ui'))
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


class NexusDialog(QDialog, FORM_CLASS):
    """ Dialog that provides an overview on all plans within the database and additional actions """

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

        self.button_reload.setCursor(Qt.PointingHandCursor)
        self.button_xplan_export.setCursor(Qt.PointingHandCursor)
        self.button_edit.setCursor(Qt.PointingHandCursor)
        self.button_delete.setCursor(Qt.PointingHandCursor)
        self.button_settings.setCursor(Qt.PointingHandCursor)
        self.enable_plan_actions(0)

        self.select_all_check.nextCheckState = self.next_check_state
        self.select_all_check.stateChanged.connect(self.on_select_all_check_state_changed)

        # ------------- MODEL -----------------
        self.model = None
        self.setup_model()
        self.nexus_view.setModel(self.model)
        self.nexus_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.nexus_view.horizontalHeader().setStretchLastSection(True)
        self.nexus_view.horizontalHeader().setMaximumSectionSize(360)
        self.nexus_view.horizontalHeader().setDefaultSectionSize(180)

        self.nexus_view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        self.nexus_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

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
        with Session.begin() as session:
            stmt = select(XP_Plan).options(
                selectin_polymorphic(XP_Plan, PLAN_BASE_TYPES),
                load_only(*[col.name for col in XP_Plan.__table__.c if not col.name.endswith('_id')]),
                defer(XP_Plan.raeumlicherGeltungsbereich)
            )
            objects = session.scalars(stmt).all()

            for o in objects:
                logger.debug(object_as_dict(o).keys())

            self.model = NexusTableModel([object_as_dict(o) for o in objects])

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


class NexusTableModel(QAbstractTableModel):
    def __init__(self, data: List[dict]):
        super(NexusTableModel, self).__init__()
        self._data = data

        unique_keys = list(set().union(*(d.keys() for d in self._data)))
        self._horizontal_header = unique_keys

    @staticmethod
    def parser(value):
        if isinstance(value, datetime.date):
            return value.strftime("%d.%m.%Y")
        return str(value)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            column_name = self._horizontal_header[index.column()]
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
            return self._horizontal_header[col]
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return col + 1

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._horizontal_header)
