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
        configureSession()
        self.accept()

    @staticmethod
    def connectionParams():
        qs = QSettings()
        conn_name = qs.value(f"plugins/xplanung/connection")
        return {
            "username": qs.value(f"PostgreSQL/connections/{conn_name}/username"),
            "password": qs.value(f"PostgreSQL/connections/{conn_name}/password"),
            "host": qs.value(f"PostgreSQL/connections/{conn_name}/host"),
            "port": qs.value(f"PostgreSQL/connections/{conn_name}/port"),
            "db": qs.value(f"PostgreSQL/connections/{conn_name}/database")
        }


def configureSession():
    try:
        conn = Settings.connectionParams()
        db_str = f"postgresql://{conn['username']}:{conn['password']}@{conn['host']}:{conn['port']}/{conn['db']}"
        engine = create_engine(db_str)
        Session.configure(bind=engine)

        async_db_str = f"postgresql+asyncpg://{conn['username']}:{conn['password']}@{conn['host']}:{conn['port']}/{conn['db']}"
        async_engine = create_async_engine(async_db_str)
        SessionAsync.configure(bind=async_engine)
        return True
    except Exception as ex:
        logger.exception(f'Error on session config: {ex}')
        return False


def tryConnect():
    conn = Settings.connectionParams()
    db_str = f"postgresql://{conn['username']}:{conn['password']}@{conn['host']}:{conn['port']}/{conn['db']}"
    ngn = create_engine(db_str)
    ngn.connect()


def checkDbConnection():
    try:
        tryConnect()
        return True
    except Exception:
        msgBox = QMessageBox()
        msgBox.setWindowTitle('Verbindungsfehler')
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText('Keine Verbindung mit der Datenbank möglich')
        msgBox.addButton(QPushButton('Einstellungen'), QMessageBox.YesRole)
        msgBox.addButton(QMessageBox.Ok)
        msgBox.setEscapeButton(QMessageBox.Ok)
        ret = msgBox.exec_()
        if not ret:
            Settings().exec_()
        return False


def is_valid_db():
    if not checkDbConnection():
        return False

    ngn = Session().get_bind()
    with ngn.connect() as conn:
        try:
            res = conn.execute(text('SELECT version_num FROM alembic_version'))
            db_version_row = res.first()
            if db_version_row and db_version_row[0] in COMPATIBLE_DB_REVISIONS:
                return True

            msg = f'Die Version der QGIS-Erweiterung ist inkompatibel mit der aktuell angegebenen Datenbank! <ul>'
            msg += f"<li>Aktuelle Datenbankversion: <code>{db_version_row[0]}</code></li>"
            msg += f"<li>Erwartete Datenbankversion: <code>{', '.join(COMPATIBLE_DB_REVISIONS)}</code></li>"
            msg += '</ul>'
        except DatabaseError as e:
            msg = f'Die angegebene Datenbank ist nicht kompatibel mit SAGis XPlanung! Bitte konfigurieren Sie' \
                  f' eine neue Verbindung in den Einstellungen.'

    msgBox = QMessageBox()
    msgBox.setWindowTitle('Inkompatiblität mit der Datenbank')
    msgBox.setIcon(QMessageBox.Warning)
    msgBox.setText(msg)
    settings_button = msgBox.addButton('Einstellungen', QMessageBox.YesRole)
    msgBox.addButton(QMessageBox.Cancel)
    ret = msgBox.exec()
    if msgBox.clickedButton() == settings_button:
        Settings().exec()
    return False

