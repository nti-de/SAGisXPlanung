import asyncio
import os

import qasync
import requests
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QStringListModel
from qgis.PyQt.QtWidgets import QDialog, QAbstractItemView, QListView
from qgis.PyQt import uic
from qgis.utils import iface

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.config.qgis_config import QgsConfig
from SAGisXPlanung.core.converter_tasks import export_plan
from SAGisXPlanung.ext.spinner import loading_animation
from SAGisXPlanung.gui.style import HighlightRowDelegate, HighlightRowProxyStyle, load_svg, ApplicationColor

FORM_CLASS_XPLAN24, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/xplan24-sync-dialog.ui'))


style = """
QLabel[objectName="upload_status_label"] {{
    color: {_label_color_mute};
}}
QToolButton[objectName="upload_status_icon"] {{
    background-color: palette(base); 
}}
QToolButton:hover[objectName="upload_status_icon"] {{
    background-color: palette(base); 
}}
"""


class XPlanung24SyncDialog(QDialog, FORM_CLASS_XPLAN24):
    def __init__(self, parent=iface.mainWindow(), selected_plans=None):
        super().__init__(parent)
        self.setupUi(self)
        self.selected_plans = selected_plans or {}

        self.accounts = QgsConfig.xplan24_accounts()

        for account in self.accounts:
            self.select_account.addItem(account.name, account.api_key)
        self.select_account.setPlaceholderText("Account auswählen...")
        self.select_account.setCurrentIndex(-1)
        self.select_account.currentIndexChanged.connect(self.update_upload_button_state)

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

        self.check_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/check.svg'), color=ApplicationColor.Success))
        self.error_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/error-outline.svg'), color=ApplicationColor.Error))
        self.upload_status_icon.setIcon(self.check_icon)
        self.upload_status_icon.setVisible(False)

        self.update_upload_button_state()
        self.button_upload.clicked.connect(self.on_upload_clicked)
        self.button_cancel.clicked.connect(self.reject)

        self.tab_upload.setStyleSheet(style.format(
            _label_color_mute=ApplicationColor.Grey600,
        ))

    def update_upload_button_state(self):
        has_selected_plans = bool(self.selected_plans)
        has_selected_account = self.select_account.currentIndex() != -1

        self.button_upload.setEnabled(has_selected_plans and has_selected_account)

    @qasync.asyncSlot()
    async def on_upload_clicked(self):
        self.upload_status_icon.setVisible(True)
        self.upload_status_label.setText("Hochladen...")

        try:
            async with loading_animation(self):
                response, plan_name = await asyncio.to_thread(self.upload_selected_plans)

                # Handle response
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
            # Convert plan to GML format
            gml_data = export_plan(out_file_format="gml", plan_xid=plan_id, raw=True)

            files = {
                "gml": (f"{plan_name}.gml", gml_data, "application/gml+xml")
            }

            # Send HTTP POST request
            r = requests.post(upload_url, headers=headers, files=files)

            return r, plan_name


