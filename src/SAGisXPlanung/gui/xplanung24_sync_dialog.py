import asyncio
import logging
import os
from datetime import datetime

import qasync
import requests
from lxml import etree
from qgis.PyQt.QtGui import QIcon, QStandardItemModel, QStandardItem
from qgis.PyQt.QtCore import QStringListModel, Qt, QMetaObject, Q_ARG, QItemSelectionModel, QDateTime
from qgis.PyQt.QtWidgets import QDialog, QAbstractItemView, QListView, QMessageBox, QHeaderView
from qgis.PyQt import uic
from qgis.utils import iface
from sqlalchemy import select

from SAGisXPlanung import BASE_DIR, SessionAsync
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.config.qgis_config import QgsConfig
from SAGisXPlanung.core.converter_tasks import export_plan, GMLInputData, import_plan
from SAGisXPlanung.ext.spinner import loading_animation
from SAGisXPlanung.gui.style import (HighlightRowDelegate, HighlightRowProxyStyle, load_svg, ApplicationColor,
                                     EmptyStateFilter, RemoveFrameFocusProxyStyle, DateTimeDisplayDelegate)

logger = logging.getLogger(__name__)
FORM_CLASS_XPLAN24, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/xplan24-sync-dialog.ui'))


style = """
QLabel[objectName="upload_status_label"], QLabel[objectName="download_status_label"] {{
    color: {_label_color_mute};
}}
QLabel[objectName="upload_count_label"], QLabel[objectName="available_plan_count_label"] {{
    background-color: palette(alternate-base);
    border-radius: 5px;
    padding: 5px;
    margin-right: 2.5px;
    font-weight: bold;
}}
QToolButton[objectName="upload_status_icon"], QToolButton[objectName="download_status_icon"] {{
    background-color: palette(window); 
}}
QToolButton:hover[objectName="upload_status_icon"], QToolButton[objectName="download_status_icon"] {{
    background-color: palette(window); 
}}

QTabBar::tab {{
    border: none;
    border-radius: 5px;
    min-width: 20ex;
    background-color: palette(window);
    padding: 10px;
    cursor: pointer;
}}

QTabBar::tab:hover {{
    background-color: #e5e7eb;
}}

QTabBar::tab:selected {{
    border: 1px solid #d1d5db;
    background-color: palette(base);
}}

QProgressBar {{
    background-color: {_progress_bg_color};
    border: none;
    padding: 0px;
    border-radius: 2px;
    max-height: 4px;
    height: 4px;
}}
QProgressBar::chunk {{
    background: {_progress_chunk_bg_color};
    border-radius: 2px;
    max-height: 4px;
    height: 4px;
    width: 10px;
    margin-right: -2px;
}}
"""


class XPlanung24SyncDialog(QDialog, FORM_CLASS_XPLAN24):

    PLAN_ID_ROLE = Qt.UserRole + 1
    PLAN_DATA_ROLE = Qt.UserRole + 2

    def __init__(self, parent=iface.mainWindow(), selected_plans=None):
        super().__init__(parent)
        self.setupUi(self)
        self.selected_plans = selected_plans or {}
        if self.selected_plans:
            self.tab_widget.setCurrentIndex(0)
        else:
            self.tab_widget.setCurrentIndex(1)

        self.accounts = QgsConfig.xplan24_accounts()

        for account in self.accounts:
            self.select_account.addItem(account.name, account.api_key)
        self.select_account.setPlaceholderText("Account auswählen...")
        self.select_account.setCurrentIndex(-1)
        self.select_account.currentIndexChanged.connect(self.on_account_changed)

        plan_names = list(self.selected_plans.values())
        model = QStringListModel(plan_names)
        self.selected_plan_list.setModel(model)
        self.selected_plan_list.setMouseTracking(True)
        self.selected_plan_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.selected_plan_list.setSelectionMode(QListView.NoSelection)
        self.selected_plan_list.setStyleSheet("QListView::item { padding: 5px; }")
        self.selected_plan_list.setItemDelegate(HighlightRowDelegate())
        self.list_proxy_style = HighlightRowProxyStyle('Fusion')
        self.list_proxy_style.setParent(self)
        self.selected_plan_list.setStyle(self.list_proxy_style)
        self.empty_state_display = EmptyStateFilter(self.selected_plan_list)
        self.empty_state_display.set_icon(os.path.join(BASE_DIR, 'gui/resources/error-outline.svg')) \
            .set_icon_size(16) \
            .set_title("Keine Pläne ausgewählt") \
            .set_subtitle("Wählen Sie Pläne in der Tabelle aus, um sie hochzuladen.")

        # Setup account plans list
        account_model = QStandardItemModel()
        account_model.setHorizontalHeaderLabels(["Bezeichnung", "Nummer", "Erstellt am"])
        account_model.itemChanged.connect(self.on_plan_check_changed)
        self.account_plan_table.setModel(account_model)
        self.account_plan_table.setMouseTracking(True)
        self.account_plan_table.setSortingEnabled(True)
        self.account_plan_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.account_plan_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.account_plan_table.setSelectionMode(QAbstractItemView.NoSelection)
        # self.account_plan_table.setStyleSheet("QTableView::item { padding: 5px; }")
        self.account_plan_table.setItemDelegateForColumn(2, DateTimeDisplayDelegate(self))
        self.account_plan_table.horizontalHeader().setStretchLastSection(False)
        self.account_plan_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.account_plan_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.account_plan_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.account_plan_table.verticalHeader().setVisible(False)
        account_proxy_style = RemoveFrameFocusProxyStyle('Fusion')
        account_proxy_style.setParent(self)
        self.account_plan_table.setStyle(account_proxy_style)
        self.account_empty_state = EmptyStateFilter(self.account_plan_table)
        self.account_empty_state.set_icon(os.path.join(BASE_DIR, 'gui/resources/download.svg')) \
            .set_icon_size(16) \
            .set_title("Keine Pläne verfügbar") \
            .set_subtitle("Wählen Sie einen Account aus, um Pläne anzuzeigen.")

        self.upload_count_label.setText(str(len(plan_names)))
        self.available_plan_count_label.setText("0")
        self.download_progress.setVisible(False)
        self.download_progress.setMinimum(0)
        self.download_progress.setMaximum(100)

        self.refresh_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/refresh.svg'), color=ApplicationColor.Tertiary))
        self.check_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/check.svg'), color=ApplicationColor.Success))
        self.error_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/error-outline.svg'), color=ApplicationColor.Error))
        self.upload_status_icon.setIcon(self.check_icon)
        self.upload_status_icon.setVisible(False)
        self.download_status_icon.setIcon(self.check_icon)
        self.download_status_icon.setVisible(False)
        self.refresh_remote_button.setIcon(self.refresh_icon)
        self.refresh_remote_button.setDisabled(True)
        self.refresh_remote_button.setToolTip("Pläne aus XPlanung24 abrufen...")
        self.refresh_remote_button.clicked.connect(self.on_account_changed)

        self.select_all_checkbox.nextCheckState = self.next_check_state
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)

        self.update_upload_button_state()
        self.update_download_button_state()
        self.button_upload.clicked.connect(self.on_upload_clicked)
        self.button_download.clicked.connect(self.on_download_clicked)
        self.button_cancel.clicked.connect(self.reject)
        self.button_cancel_download.clicked.connect(self.reject)

        self.tab_widget.tabBar().setDocumentMode(True)
        self.tab_widget.tabBar().setExpanding(True)

        upload_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/upload.svg'), color=ApplicationColor.Tertiary)
        download_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/download.svg'), color=ApplicationColor.Tertiary)
        self.tab_widget.tabBar().setTabIcon(0, upload_icon)
        self.tab_widget.tabBar().setTabIcon(1, download_icon)

        qss = style.format(
            _progress_bg_color=ApplicationColor.Grey300,
            _progress_chunk_bg_color=ApplicationColor.Secondary,
            _label_color_mute=ApplicationColor.Grey600,
        )
        self.setStyleSheet(qss)
        self.tab_upload.setStyleSheet(qss)
        self.tab_download.setStyleSheet(qss)

    def next_check_state(self):
        if self.select_all_checkbox.checkState() == Qt.Unchecked:
            self.select_all_checkbox.setCheckState(Qt.Checked)
        else:
            self.select_all_checkbox.setCheckState(Qt.Unchecked)

    def update_upload_button_state(self):
        has_selected_plans = bool(self.selected_plans)
        has_selected_account = self.select_account.currentIndex() != -1

        self.button_upload.setEnabled(has_selected_plans and has_selected_account)

    def update_download_button_state(self):
        model = self.account_plan_table.model()
        checked_count = 0

        for i in range(model.rowCount()):
            checkbox_item = model.item(i, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                checked_count += 1

        if checked_count > 0:
            self.button_download.setText(f"Herunterladen ({checked_count})")
            self.button_download.setEnabled(True)
        else:
            self.button_download.setText("Herunterladen")
            self.button_download.setEnabled(False)

        self.refresh_remote_button.setDisabled(self.select_account.currentIndex() == -1)

    def on_plan_check_changed(self, item):
        row = item.row()
        selection_model = self.account_plan_table.selectionModel()
        model = self.account_plan_table.model()

        # Select/deselect the entire row based on checkbox state
        if item.checkState() == Qt.Checked:
            selection_model.select(model.index(row, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)
        else:
            selection_model.select(model.index(row, 0), QItemSelectionModel.Deselect | QItemSelectionModel.Rows)

        self.update_download_button_state()
        self.update_select_all_checkbox_state()

    def update_select_all_checkbox_state(self):
        model = self.account_plan_table.model()
        if model.rowCount() == 0:
            self.select_all_checkbox.setChecked(False)
            return

        checked_count = 0
        for i in range(model.rowCount()):
            checkbox_item = model.item(i, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                checked_count += 1

        # Block signals to avoid recursion
        self.select_all_checkbox.blockSignals(True)
        if checked_count == 0:
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
        elif checked_count == model.rowCount():
            self.select_all_checkbox.setCheckState(Qt.Checked)
        else:
            self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)
        self.select_all_checkbox.blockSignals(False)

    def on_select_all_changed(self, state):
        model = self.account_plan_table.model()
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        selection_model = self.account_plan_table.selectionModel()

        model.itemChanged.disconnect(self.on_plan_check_changed)
        for i in range(model.rowCount()):
            checkbox_item = model.item(i, 0)
            if checkbox_item:
                checkbox_item.setCheckState(check_state)
                if check_state == Qt.Checked:
                    selection_model.select(model.index(i, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)
                else:
                    selection_model.select(model.index(i, 0), QItemSelectionModel.Deselect | QItemSelectionModel.Rows)

        model.itemChanged.connect(self.on_plan_check_changed)

        self.update_download_button_state()

    def format_timestamp(self, timestamp_ms):
        try:
            timestamp_sec = int(timestamp_ms) / 1000
            dt = datetime.fromtimestamp(timestamp_sec)
            return dt.strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            return ""

    @qasync.asyncSlot()
    async def on_account_changed(self):

        self.update_upload_button_state()
        self.account_empty_state.set_subtitle("Keine Pläne im XPlanung24-Account gefunden.")

        if self.select_account.currentIndex() == -1:
            self.account_plan_table.model().clear()
            self.available_plan_count_label.setText("")
            self.account_empty_state.set_subtitle("Wählen Sie einen Account aus, um Pläne anzuzeigen.")
            return

        api_key = self.select_account.itemData(self.select_account.currentIndex())

        self.account_empty_state.set_active(False)
        self.account_plan_table.setEnabled(False)

        try:
            async with loading_animation(self.account_plan_table, text='Pläne laden...'):
                remote_plans = await asyncio.to_thread(self.fetch_remote_plans, api_key)

                model = self.account_plan_table.model()
                # clear the view: don't use model.clear(), as it also removes header setup
                model.removeRows(0, model.rowCount())

                for plan in remote_plans:
                    name_item = QStandardItem(plan.get('name', ''))
                    name_item.setCheckable(True)
                    name_item.setCheckState(Qt.Unchecked)
                    name_item.setData(plan['id'], self.PLAN_ID_ROLE)
                    name_item.setData(plan, self.PLAN_DATA_ROLE)
                    plan_id_item = QStandardItem(plan.get('planId', ''))
                    plan_id_item.setEditable(False)
                    created_at = QDateTime.fromMSecsSinceEpoch(int(plan.get('createdAt', 0)))
                    date_item = QStandardItem()
                    date_item.setData(created_at, Qt.DisplayRole)
                    date_item.setEditable(False)
                    model.appendRow([name_item, plan_id_item, date_item])

                self.available_plan_count_label.setText(str(len(remote_plans)))

        except Exception as e:
            logger.error(f"Error fetching remote plans: {str(e)}")
            self.available_plan_count_label.setText("0")

        finally:
            self.account_empty_state.set_active(True)
            self.account_plan_table.setEnabled(True)
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
            self.update_download_button_state()

    def fetch_remote_plans(self, api_key):
        url = 'https://6tkb6m5vzc.execute-api.eu-central-1.amazonaws.com/dev/rest/public/2.0/plans'
        headers = {"Authorization": api_key}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return data.get('data', [])

    def download_remote_plan(self, plan, api_key) -> GMLInputData:
        plan_id = plan.get('id')
        if not plan_id:
            raise ValueError(f"Plan has no ID: {plan}")

        url = f'https://6tkb6m5vzc.execute-api.eu-central-1.amazonaws.com/dev/rest/public/2.0/plan/{plan_id}/planfile'
        headers = {"Authorization": api_key}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        download_url = data.get('data')

        if not download_url:
            raise ValueError(f"No download URL in response for plan {plan_id}")

        gml_response = requests.get(download_url)
        gml_response.raise_for_status()

        return GMLInputData(
            gml_content=gml_response.content,
            files={},
            filepath=f"{plan.get('name', 'plan')}.gml"
        )

    @qasync.asyncSlot()
    async def on_download_clicked(self):
        self.download_status_icon.setVisible(False)
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)

        model = self.account_plan_table.model()
        checked_plans = []

        for i in range(model.rowCount()):
            checkbox_item = model.item(i, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                plan_data = checkbox_item.data(self.PLAN_DATA_ROLE)
                checked_plans.append(plan_data)

        api_key = self.select_account.itemData(self.select_account.currentIndex())

        try:
            async with loading_animation(self.account_plan_table):
                for i, plan in enumerate(checked_plans):
                    plan_id = plan['id']
                    plan_name = plan['name']
                    self.download_progress.setValue(0)
                    self.download_status_label.setText(f"Plan {i+1}/{len(checked_plans)} wird heruntergeladen...")

                    gml_input_data = await asyncio.to_thread(self.download_remote_plan, plan, api_key)

                    # Check if plan exists, confirm with user
                    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
                    root = etree.fromstring(gml_input_data.gml_content, parser=parser)
                    root.nsmap.pop(None, None)
                    plan_element = root.xpath(".//xplan:*[contains(name(),'_Plan')][1]", namespaces=root.nsmap)[0]
                    if id_nodes := plan_element.xpath('@gml:id', namespaces=root.nsmap):
                        gml_id = id_nodes[0]
                        gml_id = gml_id[gml_id.find('_') + 1:]
                    else:
                        raise ValueError(f"Fehler beim Auslesen der GML-ID im Plan {plan_name}.")

                    overwrite = False
                    async with SessionAsync.begin() as session:
                        stmt = select(XP_Plan).filter_by(id=gml_id)
                        res = await session.execute(stmt)
                        db_result = res.scalar_one_or_none()

                        if db_result:
                            msg = QMessageBox()
                            msg.setIcon(QMessageBox.Warning)
                            msg.setText(f"Plan existiert bereits in der Datenbank.")
                            msg.setWindowTitle("XPlanGML Import unterbrochen")
                            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
                            button_yes = msg.button(QMessageBox.Yes)
                            button_yes.setText("Überschreiben")
                            msg.setDefaultButton(QMessageBox.Cancel)
                            ret = msg.exec_()
                            if ret == QMessageBox.Cancel:
                                self.download_status_label.setText('')
                                return
                            overwrite = True

                    self.download_status_label.setText(f"Plan {i + 1}/{len(checked_plans)} wird importiert...")

                    def progress_callback(progress_tuple):
                        current, total = progress_tuple
                        if total > 0:
                            percentage = int((current / total) * 100)
                            QMetaObject.invokeMethod(
                                self.download_progress,
                                "setValue",
                                Qt.QueuedConnection,
                                Q_ARG(int, percentage)
                            )

                    await asyncio.to_thread(import_plan, gml_input_data, progress_callback, overwrite)
                    self.download_progress.setValue(100)

            self.download_status_icon.setIcon(self.check_icon)
            self.download_status_icon.setVisible(True)
            if len(checked_plans) > 1:
                self.download_status_label.setText(f'{len(checked_plans)} Pläne heruntergeladen.')
            else:
                self.download_status_label.setText('Plan heruntergeladen.')
        except Exception as e:
            logger.error(f"Error downloading plan {plan_id}/{plan_name}: {str(e)}")

            self.download_status_icon.setIcon(self.error_icon)
            self.download_status_icon.setVisible(True)
            self.download_status_label.setText(str(e))
        finally:
            self.download_progress.setVisible(False)


    @qasync.asyncSlot()
    async def on_upload_clicked(self):
        self.upload_status_icon.setVisible(True)
        self.upload_status_label.setText("Hochladen...")

        try:
            async with loading_animation(self):
                response, plan_name = await asyncio.to_thread(self.upload_selected_plans)

                if response.status_code == 202:
                    self.upload_status_icon.setIcon(self.check_icon)
                    self.upload_status_icon.setVisible(True)
                    self.upload_status_label.setText(f'Plan "{plan_name}" erfolgreich hochgeladen!')
                else:
                    self.upload_status_icon.setIcon(self.error_icon)
                    self.upload_status_icon.setVisible(True)
                    self.upload_status_label.setText(f'Upload des Plans "{plan_name}" fehlgeschlagen: {response.text}')

        except Exception as e:
            self.upload_status_icon.setIcon(self.error_icon)
            self.upload_status_label.setText(f'Upload des Plans fehlgeschlagen: {str(e)}')

    def upload_selected_plans(self):
        """ Convert selected plans to GML and upload to web portal. """
        api_key = self.select_account.itemData(self.select_account.currentIndex())

        upload_url = 'https://6tkb6m5vzc.execute-api.eu-central-1.amazonaws.com/dev/rest/public/customer/plan/1.0'
        headers = {"Authorization": api_key}

        for plan_id, plan_name in self.selected_plans.items():
            gml_data = export_plan(out_file_format="gml", plan_xid=plan_id, raw=True)

            files = {
                "gml": (f"{plan_name}.gml", gml_data, "application/gml+xml")
            }

            r = requests.post(upload_url, headers=headers, files=files)

            return r, plan_name
