import asyncio
import logging
import os

import qasync
import requests
from PyQt5.QtCore import QMetaObject, Q_ARG
from PyQt5.QtWidgets import QMessageBox
from lxml import etree
from qgis.PyQt.QtGui import QIcon, QStandardItemModel, QStandardItem
from qgis.PyQt.QtCore import QStringListModel, Qt
from qgis.PyQt.QtWidgets import QDialog, QAbstractItemView, QListView
from qgis.PyQt import uic
from qgis.utils import iface
from sqlalchemy import select

from SAGisXPlanung import BASE_DIR, SessionAsync
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.config.qgis_config import QgsConfig
from SAGisXPlanung.core.converter_tasks import export_plan, GMLInputData, import_plan
from SAGisXPlanung.ext.spinner import loading_animation
from SAGisXPlanung.gui.style import HighlightRowDelegate, HighlightRowProxyStyle, load_svg, ApplicationColor
from SAGisXPlanung.gui.style.styles import EmptyStateFilter

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

    def __init__(self, parent=iface.mainWindow(), selected_plans=None):
        super().__init__(parent)
        self.setupUi(self)
        self.selected_plans = selected_plans or {}

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
        account_model.itemChanged.connect(self.on_plan_check_changed)
        self.account_plan_list.setModel(account_model)
        self.account_plan_list.setMouseTracking(True)
        self.account_plan_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.account_plan_list.setSelectionMode(QListView.NoSelection)
        self.account_plan_list.setStyleSheet("QListView::item { padding: 5px; }")
        self.account_plan_list.setItemDelegate(HighlightRowDelegate())
        account_proxy_style = HighlightRowProxyStyle('Fusion')
        account_proxy_style.setParent(self)
        self.account_plan_list.setStyle(account_proxy_style)
        self.account_empty_state = EmptyStateFilter(self.account_plan_list)
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
        model = self.account_plan_list.model()
        checked_count = 0

        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked_count += 1

        if checked_count > 0:
            self.button_download.setText(f"Herunterladen ({checked_count})")
            self.button_download.setEnabled(True)
        else:
            self.button_download.setText("Herunterladen")
            self.button_download.setEnabled(False)

    def on_plan_check_changed(self, item):
        self.update_download_button_state()
        self.update_select_all_checkbox_state()

    def update_select_all_checkbox_state(self):
        model = self.account_plan_list.model()
        if model.rowCount() == 0:
            self.select_all_checkbox.setChecked(False)
            return

        checked_count = 0
        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
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
        model = self.account_plan_list.model()
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked

        model.itemChanged.disconnect(self.on_plan_check_changed)
        for i in range(model.rowCount()):
            item = model.item(i)
            if item:
                item.setCheckState(check_state)
        model.itemChanged.connect(self.on_plan_check_changed)

        self.update_download_button_state()

    @qasync.asyncSlot()
    async def on_account_changed(self):
        print("Account changed")
        self.update_upload_button_state()
        self.account_empty_state.set_subtitle("Keine Pläne im XPlanung24-Account gefunden.")

        if self.select_account.currentIndex() == -1:
            self.account_plan_list.model().setStringList([])
            self.available_plan_count_label.setText("")
            self.account_empty_state.set_subtitle("Wählen Sie einen Account aus, um Pläne anzuzeigen.")
            return

        api_key = self.select_account.itemData(self.select_account.currentIndex())

        self.account_empty_state.set_active(False)
        self.account_plan_list.setEnabled(False)

        try:
            async with loading_animation(self.account_plan_list, text='Pläne laden...'):
                self.remote_plans = await asyncio.to_thread(self.fetch_remote_plans, api_key)

                model = self.account_plan_list.model()
                model.clear()

                for plan in self.remote_plans:
                    display_name = f"{plan['planId']} - {plan['name']}" if plan.get('planId') else plan['name']
                    item = QStandardItem(display_name)
                    item.setCheckable(True)
                    item.setCheckState(Qt.Unchecked)
                    item.setData(plan['id'], self.PLAN_ID_ROLE)
                    model.appendRow(item)

                self.available_plan_count_label.setText(str(len(self.remote_plans)))

        except Exception as e:
            logger.error(f"Error fetching remote plans: {str(e)}")
            self.available_plan_count_label.setText("0")
            self.remote_plans = []

        finally:
            self.account_empty_state.set_active(True)
            self.account_plan_list.setEnabled(True)
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

        # url = f'https://6tkb6m5vzc.execute-api.eu-central-1.amazonaws.com/dev/rest/public/2.0/plan/{plan_id}/planfile'
        # headers = {"Authorization": api_key}
        #
        # response = requests.get(url, headers=headers)
        # response.raise_for_status()
        # data = response.json()
        # download_url = data.get('data')
        download_url = "https://gitlab.opencode.de/xleitstelle/xplanung/testdaten/-/raw/main/valide/5_3/bp/BPlan001_5-3.gml"

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

        model = self.account_plan_list.model()
        checked_plans = []

        for i in range(model.rowCount()):
            item = model.item(i)
            if item and item.checkState() == Qt.Checked:
                checked_plans.append(self.remote_plans[i])

        api_key = self.select_account.itemData(self.select_account.currentIndex())

        try:
            async with loading_animation(self.account_plan_list):
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
                        print(f"GML ID: {gml_id}")
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
