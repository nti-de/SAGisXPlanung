import logging
import os

import qasync
from qgis.PyQt.QtGui import QCloseEvent, QIcon, QPen, QColor, QFontMetrics, QClipboard
from qgis.PyQt.QtCore import QSettings, QSize, pyqtSignal
from qgis.PyQt.QtWidgets import (QStyledItemDelegate, QListView, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
                                 QApplication)
from qgis.PyQt.QtCore import QModelIndex, QAbstractListModel, Qt, QRect

from SAGisXPlanung import BASE_DIR, XPlanVersion
from SAGisXPlanung.ext.toast import Toaster
from SAGisXPlanung.gui.style import load_svg, ApplicationColor, SVGButtonEventFilter, HighlightRowProxyStyle
from SAGisXPlanung.gui.widgets.inputs.input_widgets import QStringInput
from SAGisXPlanung.config import (QgsConfig, GeometryValidationConfig, GeometryCorrectionMethod, export_version,
                                  XPlanung24Account)

from .basepage import SettingsPage


logger = logging.getLogger(__name__)


class CommonConfigPage(SettingsPage):
    def __init__(self, parent=None):
        super(CommonConfigPage, self).__init__(parent)
        self.ui = None

    def setup_ui(self, ui):
        self.ui = ui

        self.ui.checkPath.stateChanged.connect(lambda state: self.ui.tbPath.setEnabled((not bool(state))))
        self.ui.checkbox_clean_geometry.stateChanged.connect(self.checkbox_clean_geometry_state_changed)

        self.ui.cbXPlanVersion.addItems([e.value for e in XPlanVersion])
        self.ui.cbXPlanVersion.currentIndexChanged.connect(self.on_xplan_version_changed)
        self.set_xplan_version()

        info_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/info-outline.svg'),
                                   color=ApplicationColor.Grey600))
        self.info_button_highlight_filter = SVGButtonEventFilter(ApplicationColor.Grey600, ApplicationColor.Tertiary)
        self.ui.info_clean_geometry.setIcon(info_icon)
        self.ui.info_preserve_topology.setIcon(info_icon)
        self.ui.info_repeated_points.setIcon(info_icon)
        self.ui.info_clean_geometry.installEventFilter(self.info_button_highlight_filter)
        self.ui.info_preserve_topology.installEventFilter(self.info_button_highlight_filter)
        self.ui.info_repeated_points.installEventFilter(self.info_button_highlight_filter)
        self.ui.info_clean_geometry.setToolTip(
            '<qt>Beim Erfassen neuer Geometrien, wird automatisch der Umlaufsinn aller Stützpunkte angepasst und eventuell doppelt erfasste Stützpunkte werden entfernt.</qt>')
        self.ui.info_preserve_topology.setToolTip(
            '<qt>Die Geometriebereinigung erhält die topologische Struktur der Geometrien. Es werden nur doppelte, aufeinanderfolgende Stützpunkte entfernt.</qt>')
        self.ui.info_repeated_points.setToolTip(
            '<qt>Eine genauere Erkennung doppelter Stützpunkte wird angewendet. Die Geometriebereinigung entfernt auch doppelte Stützpunkte, die nicht aufeinanderfolgend sind. Dies kann jedoch zu Änderungen in der Topologie führen.</qt>')
        self.ui.status_label.hide()

        self.set_validation_options()


        button_style = '''
            QToolButton {
                border: 0px;
            }
        '''
        self.ui.validation_options_group.setStyleSheet(button_style)
        self.ui.xplan24_group.setStyleSheet(button_style)

        self.ui.xplan24_icon.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/xplanung24-logo.svg')))

        accounts = QgsConfig.xplan24_accounts()
        self.list_page = AccountListView(accounts, self)
        self.list_page.editClicked.connect(self.edit_xplan24_item)
        self.form_page = AccountEditForm()
        self.form_page.save_button.clicked.connect(self.on_xplan24form_saved)
        self.form_page.cancel_button.clicked.connect(lambda: self.ui.xplan24_page_stack.setCurrentIndex(0))
        self.ui.xplan24_page_stack.insertWidget(0, self.list_page)
        self.ui.xplan24_page_stack.insertWidget(1, self.form_page)
        self.ui.xplan24_page_stack.setCurrentIndex(0)

        self.ui.add_account_button.clicked.connect(self.on_add_xplan24account_clicked)

    def setup_data(self):
        self.set_xplan_version()
        self.set_validation_options()

    def closeEvent(self, event: QCloseEvent):
        self.ui.status_label.setText('')
        self.ui.status_action.setText('')

        self.save()

    @qasync.asyncSlot()
    async def on_xplan_version_changed(self):
        QSettings().setValue(f"plugins/xplanung/export_version", self.ui.cbXPlanVersion.currentText())

        # refresh attribute config when version changed
        self.ui.tabs.widget(1).setup_data()

        # invalidate cache of export_version
        export_version.cache_clear()

    @qasync.asyncSlot(int)
    async def checkbox_clean_geometry_state_changed(self, state):
        for row in range(1, 3):
            for column in range(self.ui.validation_options_group.layout().columnCount()):
                widget = self.ui.validation_options_group.layout().itemAtPosition(row, column)
                if widget is not None:
                    widget.widget().setEnabled(state != 0)

    def set_xplan_version(self):
        s = QSettings()
        default_version = s.value(f"plugins/xplanung/export_version", '')
        index = self.ui.cbXPlanVersion.findText(str(default_version))
        if index >= 0:
            self.ui.cbXPlanVersion.setCurrentIndex(index)

    def set_validation_options(self):
        validation_config = QgsConfig.geometry_validation_config()
        self.ui.checkbox_clean_geometry.setChecked(validation_config.correct_geometries)
        if validation_config.correct_method == GeometryCorrectionMethod.PreserveTopology:
            self.ui.radiobutton_preserve_topology.setChecked(True)
        else:
            self.ui.radiobutton_repeated_points.setChecked(True)

    def save(self):
        qs = QSettings()
        if self.ui.checkPath.isChecked():
            qs.setValue(f"plugins/xplanung/export_path", '')
        else:
            qs.setValue(f"plugins/xplanung/export_path", self.ui.tbPath.text())

        validation_config = GeometryValidationConfig(
            correct_geometries=self.ui.checkbox_clean_geometry.isChecked(),
            correct_method=GeometryCorrectionMethod.PreserveTopology if self.ui.radiobutton_preserve_topology.isChecked() else GeometryCorrectionMethod.RigorousRemoval
        )
        QgsConfig.set_geometry_validation_config(validation_config)

    def edit_xplan24_item(self, index):
        account = index.data(Qt.DisplayRole)
        self.form_page.set_account(index, account)
        self.ui.xplan24_page_stack.setCurrentIndex(1)

    def on_add_xplan24account_clicked(self):
        self.form_page.set_account(None, None)
        self.ui.xplan24_page_stack.setCurrentIndex(1)

    def on_xplan24form_saved(self):
        if not self.form_page.is_form_valid():
            return

        title = self.form_page.name_input.text()
        api_key = self.form_page.api_key_input.text()

        model = self.list_page.model()
        if self.form_page._index:  # Edit existing
            row = self.form_page._index.row()
            account = model._accounts[row]
            account.name = title
            account.api_key = api_key
            model.dataChanged.emit(self.form_page._index, self.form_page._index)
        else:  # Add new
            new_account = XPlanung24Account(name=title, api_key=api_key)
            model.beginInsertRows(QModelIndex(), model.rowCount(), model.rowCount())
            model._accounts.append(new_account)
            model.endInsertRows()

        QgsConfig.set_xplan24_accounts(model._accounts)
        self.ui.xplan24_page_stack.setCurrentIndex(0)


# --- Custom XPlan24 View Widget ---
class AccountListView(QListView):

    editClicked = pyqtSignal(QModelIndex)

    def __init__(self, accounts, parent=None):
        super().__init__(parent)

        self.model_ = AccountListModel(accounts)
        self.setModel(self.model_)

        delegate = AccountDelegate(self)
        self.setItemDelegate(delegate)

        delegate.copyClicked.connect(self.copy_api_key)
        delegate.editClicked.connect(self.editClicked.emit)
        delegate.deleteClicked.connect(self.remove_account)

        self.setSelectionMode(QListView.SingleSelection)

        self.proxy_style = HighlightRowProxyStyle('Fusion')
        self.proxy_style.setParent(self)
        self.setStyle(self.proxy_style)
        self.setMouseTracking(True)

    def add_account(self, account: XPlanung24Account):
        self.model_.beginInsertRows(QModelIndex(), self.model_.rowCount(), self.model_.rowCount())
        self.model_.accounts.append(account)
        self.model_.endInsertRows()

    def remove_account(self, index):
        if index.isValid():
            self.model().removeRow(index.row())

        QgsConfig.set_xplan24_accounts(self.model()._accounts)

    def copy_api_key(self, index):
        account = index.data(Qt.DisplayRole)
        QApplication.clipboard().setText(account.api_key, QClipboard.Clipboard)

        Toaster.showMessage(self, message='API Schlüssel kopiert!', corner=Qt.BottomRightCorner,
                            margin=20, icon=None, closable=False, color='#ffffff', background_color='#404040',
                            timeout=3000)


# --- Custom Model ---
class AccountListModel(QAbstractListModel):
    def __init__(self, accounts, parent=None):
        super().__init__(parent)
        self._accounts = accounts

    def rowCount(self, parent=QModelIndex()):
        return len(self._accounts)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._accounts[index.row()]
        return None

    def removeRows(self, row, count, parent=QModelIndex()):
        if 0 <= row < len(self._accounts):
            self.beginRemoveRows(parent, row, row + count - 1)
            del self._accounts[row:row + count]
            self.endRemoveRows()
            return True
        return False


# --- Custom Delegate ---
class AccountDelegate(QStyledItemDelegate):

    copyClicked = pyqtSignal(QModelIndex)
    editClicked = pyqtSignal(QModelIndex)
    deleteClicked = pyqtSignal(QModelIndex)

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.copy_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/copy.svg'),
                               color=ApplicationColor.Grey600))
        self.edit_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/edit.svg'),
                                        color=ApplicationColor.Grey600))
        self.delete_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/delete.svg'),
                                        color=ApplicationColor.Grey600))

    def paint(self, painter, option, index):
        account = index.data(Qt.DisplayRole)
        if not account:
            return

        painter.save()

        # --- Layout Constants ---
        padding = 10
        spacing = 6

        # --- Fonts ---
        title_font = option.font
        title_font.setBold(True)

        subtitle_font = option.font

        # --- Font Metrics ---
        painter.setFont(title_font)
        title_metrics = painter.fontMetrics()
        title_height = title_metrics.height()

        painter.setFont(subtitle_font)
        subtitle_metrics = painter.fontMetrics()
        subtitle_height = subtitle_metrics.height()

        content_height = title_height + spacing + subtitle_height
        content_top = option.rect.top() + (option.rect.height() - content_height) // 2

        # --- Rects ---
        title_rect = QRect(option.rect.left() + padding, content_top,
                           option.rect.width() - 2 * padding, title_height)

        redacted = account.api_key[:6] + "..."
        api_text = f"API-Key: {redacted}"
        api_text_width = subtitle_metrics.width(api_text)
        subtitle_top = title_rect.bottom() + spacing
        subtitle_rect = QRect(option.rect.left() + padding, subtitle_top,
                              api_text_width, subtitle_height)

        icon_rects = self.get_icon_rects(option, index)

        # --- Draw Title ---
        painter.setFont(title_font)
        painter.setPen(Qt.black)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, account.name)

        # --- Draw Subtitle (API Key) ---
        painter.setFont(subtitle_font)
        subtitle_color = ApplicationColor.Grey400.value
        painter.setPen(QPen(QColor(subtitle_color)))
        painter.drawText(subtitle_rect, Qt.AlignLeft | Qt.AlignVCenter, api_text)

        # --- Draw Icon ---
        self.copy_icon.paint(painter, icon_rects['copy'])
        self.edit_icon.paint(painter, icon_rects['edit'])
        self.delete_icon.paint(painter, icon_rects['delete'])

        painter.restore()

    def sizeHint(self, option, index):
        # Use consistent font for both lines
        painter_font = option.font
        metrics = QFontMetrics(painter_font)

        padding = 10
        spacing = 6
        height = padding + metrics.height() + spacing + metrics.height() + padding
        return QSize(option.rect.width(), height)

    def editorEvent(self, event, model, option, index):
        if event.type() == event.MouseButtonRelease and event.button() == Qt.LeftButton:
            icon_rects = self.get_icon_rects(option, index)
            pos = event.pos()

            if icon_rects["copy"].contains(pos):
                self.copyClicked.emit(index)
                return True
            elif icon_rects["edit"].contains(pos):
                self.editClicked.emit(index)
                return True
            elif icon_rects["delete"].contains(pos):
                self.deleteClicked.emit(index)
                return True

        return super().editorEvent(event, model, option, index)

    def get_icon_rects(self, option, index):
        text_font = option.font
        text_metrics = QFontMetrics(text_font)
        text_height = text_metrics.height()
        icon_size = text_height
        padding = 10
        spacing = 6
        icon_gap = 8

        redacted = index.data(Qt.DisplayRole).api_key[:6] + "..."
        api_text_width = text_metrics.width(f"API-Key: {redacted}")

        subtitle_top = option.rect.top() + padding + text_metrics.height() + spacing
        subtitle_baseline = subtitle_top + text_metrics.ascent()

        copy_icon_rect = QRect(option.rect.left() + padding + api_text_width + icon_gap,
                               subtitle_baseline - icon_size,
                               icon_size, icon_size)

        delete_icon_rect = QRect(option.rect.right() - padding - icon_size,
                                 option.rect.top() + (option.rect.height() - icon_size) // 2,
                                 icon_size, icon_size)

        edit_icon_rect = QRect(delete_icon_rect.left() - icon_gap - icon_size,
                               delete_icon_rect.top(),
                               icon_size, icon_size)

        return {
            "copy": copy_icon_rect,
            "edit": edit_icon_rect,
            "delete": delete_icon_rect
        }

class AccountEditForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        self.save_button = QPushButton("Speichern")
        self.cancel_button = QPushButton("Abbrechen")

        self.input_container = QWidget()
        self.input_layout = QVBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(0, 0, 0, 0)

        self.name_input = QStringInput()
        self.api_key_input = QStringInput()

        # Add inputs into the input_container
        self.input_layout.addWidget(QLabel("Account Name:"))
        self.input_layout.addWidget(self.name_input)

        self.input_layout.addWidget(QLabel("API Key:"))
        self.input_layout.addWidget(self.api_key_input)

        self.layout.addWidget(self.input_container)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.save_button)

        self.layout.addLayout(button_row)
        self.layout.addStretch()

        self._index = None  # model index being edited, or None for new

    def is_form_valid(self):
        ret = True
        if not self.name_input.validate_widget(True):
            self.name_input.setInvalid(True)
            ret = False
        if not self.api_key_input.validate_widget(True):
            self.api_key_input.setInvalid(True)
            ret = False
        return ret

    def set_account(self, index=None, account=None):
        """Pass index (for editing) or None (for new)."""
        self._index = index
        self.name_input.setText(account.name if account else "")
        self.api_key_input.setText(account.api_key if account else "")


