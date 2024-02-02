import asyncio
import functools
import logging
import os

import qasync
import yaml

from qgis.core import QgsDataSourceUri, QgsProviderRegistry
from qgis.utils import iface

from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSlot, QSettings, Qt, QTimer
from qgis.PyQt.QtGui import QIcon, QShowEvent, QCloseEvent
from qgis.PyQt.QtWidgets import QLineEdit, QDialog, QMessageBox, QPushButton
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DatabaseError, DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine


from SAGisXPlanung import Session, VERSION, COMPATIBLE_DB_REVISIONS, SessionAsync, BASE_DIR, XPlanVersion
from SAGisXPlanung.config import QgsConfig
from SAGisXPlanung.core.connection import establish_session, attempt_connection
from SAGisXPlanung.ext.spinner import WaitingSpinner
# don't remove following import: all classes need to be imported at plugin startup for ORM to work correctly
from SAGisXPlanung.gui.widgets import QAttributeConfigView

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/settings.ui'))
logger = logging.getLogger(__name__)


class Settings(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        self.setupUi(self)

        self.versionLabel.setText(VERSION)

        self.checkPath.stateChanged.connect(lambda state: self.tbPath.setEnabled((not bool(state))))

        self.cbXPlanVersion.addItems([e.value for e in XPlanVersion])
        self.setXPlanVersion()
        self.cbXPlanVersion.currentIndexChanged.connect(self.onXPlanVersionChanged)

        self.status_label.hide()

        # initialize UI on all settings pages
        for i in range(1, self.tabs.count()):
            self.tabs.widget(i).setupUi(self)

        self.tabs.setCurrentIndex(0)

    def showEvent(self, e: QShowEvent):
        super(Settings, self).showEvent(e)
        self.setXPlanVersion()

        for i in range(1, self.tabs.count()):
            self.tabs.widget(i).setupData()

    def closeEvent(self, e: QCloseEvent):
        super(Settings, self).closeEvent(e)

        self.status_label.setText('')
        self.status_action.setText('')

        self.saveSettings()

        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            tab.closeEvent(e)

    @qasync.asyncSlot()
    async def onXPlanVersionChanged(self):
        QSettings().setValue(f"plugins/xplanung/export_version", self.cbXPlanVersion.currentText())

        # refresh attribute config when version changed
        self.tabs.widget(1).setupData()

    def setXPlanVersion(self):
        s = QSettings()
        default_version = s.value(f"plugins/xplanung/export_version", '')
        index = self.cbXPlanVersion.findText(str(default_version))
        if index >= 0:
            self.cbXPlanVersion.setCurrentIndex(index)

    def saveSettings(self):
        conn_name = str(self.cbConnections.currentText())
        qs = QSettings()
        qs.setValue(f"plugins/xplanung/export_version", self.cbXPlanVersion.currentText())
        if self.checkPath.isChecked():
            qs.setValue(f"plugins/xplanung/export_path", '')
        else:
            qs.setValue(f"plugins/xplanung/export_path", self.tbPath.text())
        qs.setValue(f"plugins/xplanung/connection", conn_name)
        qs.setValue(f"PostgreSQL/connections/{conn_name}/username", self.tbUsername.text())
        qs.setValue(f"PostgreSQL/connections/{conn_name}/password", self.tbPassword.text())
        establish_session(Session)
        establish_session(SessionAsync)
        self.accept()
