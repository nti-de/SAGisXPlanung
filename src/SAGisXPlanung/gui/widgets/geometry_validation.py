import asyncio
import json
import logging
import os
import re

from enum import Enum
from typing import List

import qasync

from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtCore import QAbstractTableModel, QModelIndex, Qt, QPointF, QRectF, pyqtSlot, pyqtSignal, QSize
from qgis.PyQt.QtGui import QIcon, QColor, QPainter
from qgis.PyQt.QtWidgets import (QTreeView, QAbstractItemView, QMenu, QAction, QLabel, QWidget, QVBoxLayout,
                                 QHBoxLayout, QPushButton, QToolButton, QSpacerItem, QSizePolicy, QActionGroup,
                                 QWidgetAction)
from qgis.PyQt import sip

from qgis.gui import QgsGeometryRubberBand
from qgis.core import (QgsPolygon, QgsWkbTypes, QgsPoint, QgsLineString, QgsMultiLineString, QgsMultiPolygon, QgsGeometry,
                       QgsCircularString, QgsCompoundCurve, QgsCurvePolygon, QgsMultiCurve, QgsMultiSurface, QgsMultiPoint)
from qgis.utils import iface
from requests import HTTPError
from sqlalchemy.orm import load_only

from SAGisXPlanung import BASE_DIR, Session, PYQT5
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.config import QgsConfig
from SAGisXPlanung.core.geometry_validation import ValidationResult, INTERNAL_VALIDATION_FUNCTIONS, \
    validate_geometric_xplan_validator, XPlanValidationError
from SAGisXPlanung.ext.spinner import loading_animation
from SAGisXPlanung.gui.style import HighlightRowDelegate, HighlightRowProxyStyle, ApplicationColor, load_svg, \
    SVGButtonEventFilter
from SAGisXPlanung.utils import full_version_required_warning

if PYQT5:
    from qgis.PyQt.QtWidgets import QUndoCommand
else:
    from qgis.PyQt.QtGui import QUndoCommand

logger = logging.getLogger(__name__)


class ValidationState(Enum):
    UNKNOWN = ""
    PENDING = "Validierung..."
    ERROR = "Interner Fehler..."
    SUCCESS = "Keine Fehler gefunden"
    VALIDATOR_ERROR = "Syntaktischer Fehler im XPlanGML. Keine Validierung möglich."
    HTTP_ERROR = "HTTP-Fehler beim Upload zum XPlanValidator"


class ValidationMethod(Enum):
    INTERNAL = 1
    XPLANVALIDATOR = 2


def _error_detail_message(validation_result: ValidationResult) -> str:
    detail_message = f'<qt>{validation_result.error_msg}'
    if validation_result.other_xid and validation_result.other_xtype:
        detail_message += (f'<br><br>Betroffene Objekte: <ul>'
                           f'<li>{validation_result.xtype.__name__}: {validation_result.xid}</li>'
                           f'<li>{validation_result.other_xtype.__name__}: {validation_result.other_xid}</li>'
                           f'</ul>')

    detail_message += '</qt>'
    return detail_message


class ValidationWidget(QWidget):

    style = '''   
    QLabel[objectName="validation_result_label"], 
    QLabel[objectName="validation_completed_label"]
    {{
        color: {_label_color_mute};
    }}
    
    QPushButton[objectName="reset_validation_button"]
    {{
        border: none;
        padding: 5px;
        border-radius: 5px;
        color: {_label_color_mute};
    }}
    QPushButton[objectName="reset_validation_button"]:hover
    {{
        color: {_label_color_foreground};
        background-color: {_bg_color_hover};
    }}
    QToolButton::menu-indicator {{
        image: none;
    }}
    QToolButton[objectName="menu_settings_button"] {{
        border: none;
        padding: 5px;
        border-radius: 5px;
    }}
    QToolButton[objectName="menu_settings_button"]:hover {{
        color: {_label_color_foreground};
        background-color: {_bg_color_hover};
    }}
    '''

    fill_geometric_completed = pyqtSignal(list)  # List[XPlanungItem]
    revertible_action_completed = pyqtSignal(QUndoCommand)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.plan_xid = None
        self.plan_type = None

        validation_settings_str = QgsConfig.geometry_validation_settings()
        if validation_settings_str is not None:
            validation_settings = json.loads(validation_settings_str)
            self.validation_method = ValidationMethod(validation_settings.get('validation_method'))
        else:
            self.validation_method = ValidationMethod.INTERNAL

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._header_layout = QHBoxLayout()
        self._layout.addLayout(self._header_layout)

        self._validation_result_label = QLabel('')
        self._validation_result_label.setObjectName('validation_result_label')
        self._validation_start_button = QPushButton('Prüfung starten')
        self._validation_start_button.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/play_arrow.svg'),
                                            color=ApplicationColor.Tertiary))
        self._validation_start_button.clicked.connect(self.start_validation)

        self._menu_action_button = QToolButton()
        self._menu_action_button.setText('Aktionen')
        self._menu_action_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._menu_action_button.setArrowType(Qt.ArrowType.DownArrow)
        self._menu_action_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._menu_action_button.setStyleSheet('')
        self._actions_menu = QMenu(self._menu_action_button)
        self._actions_menu.setToolTipsVisible(True)
        layers_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/layers.svg'), color=ApplicationColor.Tertiary)
        refresh_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/refresh.svg'), color=ApplicationColor.Tertiary)
        crop_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/crop_free.svg'), color=ApplicationColor.Tertiary)
        fill_action = self._actions_menu.addAction(layers_icon, 'Flächenschluss erzwingen', self.fill_geometric)
        fill_action.setToolTip('<qt>Füllt alle Lücken in der Flächenschlussebene mit einem Platzhalter ohne Festsetzung auf</qt>')
        crop_action = self._actions_menu.addAction(crop_icon, 'Geltungsbereich aus Planinhalten berechnen', self.crop_plan_to_content)
        crop_action.setToolTip('<qt>Berechnet den Geltungsbereich neu aus dem Zusammenschluss (Vereinigung) aller Planinhalte der Flächenschlussebene</qt>')
        self._actions_menu.addSeparator()
        self._actions_menu.addAction(refresh_icon, 'Zurücksetzen', self.reset_validation)
        self._menu_action_button.setMenu(self._actions_menu)

        self._menu_settings_button = QToolButton()
        self._menu_settings_button.setObjectName('menu_settings_button')
        self._menu_settings_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._menu_settings_button.setArrowType(Qt.ArrowType.NoArrow)
        settings_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/settings.svg'), color=ApplicationColor.Tertiary)
        self._menu_settings_button.setIcon(settings_icon)
        self._settings_menu = QMenu(self._menu_settings_button)
        self._settings_menu.setToolTipsVisible(True)
        title_action = QWidgetAction(self._settings_menu)
        label = QLabel("Validierungsmethode")
        label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                padding: 4px 8px;
            }
        """)
        title_action.setDefaultWidget(label)
        self._settings_menu.addAction(title_action)
        self._settings_menu.addSeparator()
        self.validation_method_action_group = QActionGroup(self._settings_menu)
        self.validation_method_action_group.setExclusive(True)
        internal_validation_action = self.validation_method_action_group.addAction(
            self._settings_menu.addAction("Intern")
        )
        internal_validation_action.setObjectName('internal_validation_action')
        internal_validation_action.setCheckable(True)
        xplan_validation_action = self.validation_method_action_group.addAction(
            self._settings_menu.addAction("XPlanValidator")
        )
        xplan_validation_action.setCheckable(True)
        xplan_validation_action.setObjectName('xplan_validation_action')
        if self.validation_method == ValidationMethod.XPLANVALIDATOR:
            xplan_validation_action.setChecked(True)
        else:
            internal_validation_action.setChecked(True)

        self._settings_menu.addActions(self.validation_method_action_group.actions())
        self.validation_method_action_group.triggered.connect(self.on_validation_method_changed)
        self._menu_settings_button.setMenu(self._settings_menu)

        self._header_layout.addWidget(self._validation_result_label)
        self._header_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self._header_layout.addWidget(self._menu_action_button)
        self._header_layout.addWidget(self._validation_start_button)
        self._header_layout.addWidget(self._menu_settings_button)
        self._layout.addLayout(self._header_layout)

        self._validation_result_view = ValidationTreeView()
        self._layout.addWidget(self._validation_result_view)

        self._footer_widget = QWidget()
        self._footer_widget.hide()
        self._footer_layout = QHBoxLayout()
        self._footer_layout.setContentsMargins(0, 0, 0, 0)
        self._footer_widget.setLayout(self._footer_layout)
        self._validation_completed_label = QLabel('Geometrieprüfung abgeschlossen')
        self._validation_completed_label.setObjectName('validation_completed_label')
        self._footer_layout.addWidget(self._validation_completed_label)
        self._footer_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self._reset_validation_button = QPushButton('Zurücksetzen')
        self._reset_validation_button.setObjectName('reset_validation_button')
        self._reset_validation_button.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/refresh.svg'),
                                                       color=ApplicationColor.Tertiary))
        self._reset_validation_button.clicked.connect(self.reset_validation)
        self._hover_filter_reset_button = SVGButtonEventFilter(ApplicationColor.Grey600, ApplicationColor.Tertiary)
        self._reset_validation_button.installEventFilter(self._hover_filter_reset_button)
        self._footer_layout.addWidget(self._reset_validation_button)
        self._layout.addWidget(self._footer_widget)

        self.setStyleSheet(self.style.format(
            _label_color_mute=ApplicationColor.Grey600,
            _label_color_foreground=ApplicationColor.Tertiary,
            _bg_color_hover=ApplicationColor.Grey300
        ))

    def on_validation_method_changed(self, action: QAction):
        if action.objectName() == 'xplan_validation_action':
            self.validation_method = ValidationMethod.XPLANVALIDATOR
        else:
            self.validation_method = ValidationMethod.INTERNAL
        QgsConfig.set_geometry_validation_settings(json.dumps({
            "validation_method": self.validation_method.value
        }))

    def set_plan_info(self, plan_xid: str, plan_type: type):
        self.reset_validation()

        self.plan_xid = plan_xid
        self.plan_type = plan_type

    @pyqtSlot()
    def reset_validation(self):
        self._validation_result_view.clear()
        self._validation_result_label.setText('')
        self._footer_widget.hide()

    @qasync.asyncSlot()
    async def start_validation(self):
        async with loading_animation(self) as load_animation:

            self._validation_start_button.setEnabled(False)
            self._validation_result_label.setText('')
            self._validation_result_view.clear()

            validation_state = ValidationState.UNKNOWN

            try:
                await asyncio.to_thread(self.validate_plan_geometric, load_animation.update_text)
            except XPlanValidationError as e:
                validation_state = ValidationState.VALIDATOR_ERROR
                logger.error(e)
            except HTTPError as e:
                validation_state = ValidationState.HTTP_ERROR
                logger.error(e)
            except Exception as e:
                validation_state = ValidationState.ERROR
                logger.error(e)
            finally:
                error_count = self._validation_result_view.item_count()
                print(validation_state, error_count)
                if validation_state == ValidationState.UNKNOWN and error_count == 0:
                    validation_state = ValidationState.SUCCESS
                self._validation_result_view.set_validation_state(validation_state)

                self._validation_result_label.setText(f'{error_count} Fehler gefunden'
                                                      if error_count else 'Keine Fehler gefunden')
                self._validation_start_button.setEnabled(True)
                self._footer_widget.show()

    @qasync.asyncSlot()
    async def fill_geometric(self):
        async with loading_animation(self):
            with Session.begin() as session:
                plan: XP_Plan = session.get(XP_Plan, self.plan_xid)
                xplan_items = await asyncio.to_thread(plan.enforceFlaechenschluss)
            self.fill_geometric_completed.emit(xplan_items)

    def validate_plan_geometric(self, set_status):
        """
        Validate geometric correctness of the opened plan
        Tests for:
        -   All geometries are valid
        -   All geometries are within bounds of the plan
        -   There are no gaps/overlaps between geometries
        """
        short_plan_type = str(self.plan_type.__name__[:2]).lower()

        if self.validation_method == ValidationMethod.XPLANVALIDATOR:
            validation_results = validate_geometric_xplan_validator(self.plan_xid, set_status)
            self._validation_result_view.add_result_items(validation_results)
        else:
            for func in INTERNAL_VALIDATION_FUNCTIONS:
                validation_results = func(self.plan_xid, short_plan_type)
                self._validation_result_view.add_result_items(validation_results)

    @qasync.asyncSlot()
    async def crop_plan_to_content(self):
        full_version_required_warning()


class ValidationResultModel(QAbstractTableModel):
    def __init__(self, results: List[ValidationResult] = None, parent=None):
        super().__init__(parent)
        self.results = results or []
        self.headers = ["Objekt", "Fehler"]  # Column headers

    def rowCount(self, parent=QModelIndex()):
        return len(self.results)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            result = self.results[index.row()]
            if index.column() == 0:
                return result.xtype.__name__
            elif index.column() == 1:
                return result.error_msg if result.error_msg else ""
        if role == Qt.ItemDataRole.ToolTipRole:
            result = self.results[index.row()]
            return _error_detail_message(result)

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

    def clear(self):
        self.beginResetModel()
        self.results = []
        self.endResetModel()

    def add_item(self, result: ValidationResult):
        self.beginInsertRows(QModelIndex(), len(self.results), len(self.results))
        self.results.append(result)
        self.endInsertRows()

    def add_items(self, new_results: List[ValidationResult]):
        if not new_results:
            return

        start_row = len(self.results)
        end_row = start_row + len(new_results) - 1

        self.beginInsertRows(QModelIndex(), start_row, end_row)
        self.results.extend(new_results)
        self.endInsertRows()


class ValidationTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.validation_state = ValidationState.UNKNOWN
        self.rubber_band = None
        self._model = ValidationResultModel()
        self.setModel(self._model)

        self.setItemDelegate(HighlightRowDelegate())
        self.proxy_style = HighlightRowProxyStyle('Fusion')
        self.proxy_style.setParent(self)
        self.setStyle(self.proxy_style)
        self.setMouseTracking(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.icon_paths = {
            ValidationState.ERROR: os.path.join(BASE_DIR, 'gui/resources/error-outline.svg'),
            ValidationState.VALIDATOR_ERROR: os.path.join(BASE_DIR, 'gui/resources/error-outline.svg'),
            ValidationState.HTTP_ERROR: os.path.join(BASE_DIR, 'gui/resources/globe-x.svg'),
            ValidationState.SUCCESS: os.path.join(BASE_DIR, 'gui/resources/valid.svg'),
        }

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.destroyed.connect(self.__del__)

    def __del__(self):
        if not sip.isdeleted(iface.mapCanvas()):
            iface.mapCanvas().scene().removeItem(self.rubber_band)

    def set_validation_state(self, state: ValidationState):
        """ Update the validation state and repaint the view. """
        self.validation_state = state
        self.viewport().update()

    def add_result_items(self, result_items: List[ValidationResult]):
        self._model.add_items(result_items)

    def clear(self):
        self._model.clear()
        self.set_validation_state(ValidationState.UNKNOWN)

        if self.rubber_band and not sip.isdeleted(iface.mapCanvas()):
            iface.mapCanvas().scene().removeItem(self.rubber_band)

    def item_count(self) -> int:
        return self._model.rowCount()

    def show_context_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)
        flash_action = QAction(QIcon(':/images/themes/default/mActionScaleHighlightFeature.svg'),
                               'Geometriefehler auf Karte hervorheben')
        flash_action.triggered.connect(lambda: self.highlight_geometry_error(index))
        menu.addAction(flash_action)
        menu.exec(self.viewport().mapToGlobal(position))

    def highlight_geometry_error(self, index: QModelIndex):
        """ Copy the error message of the selected row to the clipboard """
        item = self._model.results[index.row()]

        # create geometry from wkt
        # copy of QgsGeometryFactory::geomFromWkt because it's not available in python bindings
        # QgsGeometry::fromWkt does not work here and crashes QGIS -> has something to do with the wkt cache
        # but currently not able to figure the exact problem.
        wkt = item.geom_wkt.strip()
        if re.match('Point', wkt, re.I):
            geometry = QgsPoint()
        elif re.match('MultiPoint', wkt, re.I):
            geometry = QgsMultiPoint()
        elif re.match('LineString', wkt, re.I):
            geometry = QgsLineString()
        elif re.match('MultiLineString', wkt, re.I):
            geometry = QgsMultiLineString()
        elif re.match('Polygon', wkt, re.I):
            geometry = QgsPolygon()
        elif re.match('MultiPolygon', wkt, re.I):
            geometry = QgsMultiPolygon()
        elif re.match('MultiSurface', wkt, re.I):
            geometry = QgsMultiSurface()
        elif re.match('MultiCurve', wkt, re.I):
            geometry = QgsMultiCurve()
        elif re.match('CurvePolygon', wkt, re.I):
            geometry = QgsCurvePolygon()
        elif re.match('CompoundCurve', wkt, re.I):
            geometry = QgsCompoundCurve()
        elif re.match('CircularString', wkt, re.I):
            geometry = QgsCircularString()
        else:
            raise ValueError(f'No matching abstract geometry type for wkt: {wkt}')

        geometry.fromWkt(wkt)

        self.rubber_band = QgsGeometryRubberBand(iface.mapCanvas(), QgsWkbTypes.geometryType(geometry.wkbType()))
        self.rubber_band.setFillColor(QColor(0, 0, 0, 0))
        self.rubber_band.setStrokeWidth(3)
        self.rubber_band.setGeometry(geometry)
        self.rubber_band.show()

        iface.mapCanvas().setCenter(self.rubber_band.rect().center())
        iface.mapCanvas().refresh()

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.highlight_geometry_error(index)

    def paintEvent(self, event):
        if self.model() and self.validation_state != ValidationState.UNKNOWN:
            painter = QPainter(self.viewport())
            self.draw_state_overlay(painter)
            painter.end()

        super().paintEvent(event)

    def draw_state_overlay(self, painter: QPainter):
        icon_path = self.icon_paths.get(self.validation_state, None)

        if not icon_path:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setPen(QColor(ApplicationColor.Grey600))

        renderer = QSvgRenderer(icon_path)
        view_rect = self.viewport().rect()
        icon_size = 24
        icon_rect = QRectF(0, 0, icon_size, icon_size)
        icon_rect.moveCenter(QPointF(view_rect.center()))
        icon_rect.translate(0, -10)

        renderer.render(painter, icon_rect)

        text = self.validation_state.value
        text_rect = painter.fontMetrics().boundingRect(text)
        text_rect.moveCenter(view_rect.center())
        text_rect.translate(0, int(icon_size / 2))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(size.width(), 150)
