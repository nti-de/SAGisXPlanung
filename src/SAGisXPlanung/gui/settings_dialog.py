import asyncio
import logging
import os

from typing import Union
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QShowEvent, QCloseEvent
from qgis.PyQt.QtWidgets import QDialog

from SAGisXPlanung import VERSION, XPlanVersion, BASE_DIR
from SAGisXPlanung.config.layer_symbology import load_symbol_defaults
# don't remove following import: all classes need to be imported at plugin startup for ORM to work correctly
from SAGisXPlanung.gui.widgets import QAttributeConfigView
from SAGisXPlanung.gui.widgets.settings.basepage import SettingsPage

FORM_CLASS, _ = uic.loadUiType(os.path.join(BASE_DIR, 'ui/settings.ui'))
logger = logging.getLogger(__name__)


class Settings(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        self.setupUi(self)

        self.versionLabel.setText(VERSION)

        # initialize UI on all settings pages
        for i in range(0, self.tabs.count()):
            self.tabs.widget(i).setup_ui(self)

        # additional settings setup
        coro = asyncio.to_thread(load_symbol_defaults)
        asyncio.create_task(coro)

        self.tabs.setCurrentIndex(0)

    def navigate_to_page(self, page_type: type) -> Union[None, SettingsPage]:
        if not issubclass(page_type, SettingsPage):
            return

        for i in range(0, self.tabs.count()):
            page = self.tabs.widget(i)
            if isinstance(page, page_type):
                self.tabs.setCurrentIndex(i)
                return page

    def showEvent(self, e: QShowEvent):
        super(Settings, self).showEvent(e)
        for i in range(0, self.tabs.count()):
            self.tabs.widget(i).setup_data()

    def closeEvent(self, e: QCloseEvent):
        super(Settings, self).closeEvent(e)

        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            tab.closeEvent(e)
