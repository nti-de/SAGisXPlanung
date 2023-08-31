import asyncio
import functools
import logging
import os

import asyncpg
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
        self.first_start = False
        self.versionLabel.setText(VERSION)

        self.checkPath.stateChanged.connect(lambda state: self.tbPath.setEnabled((not bool(state))))

        self.fillConnections()

        self.cbXPlanVersion.addItems([e.value for e in XPlanVersion])
        self.setXPlanVersion()

        self.status_label.hide()

        # page 2 - Attributes
        self.attribute_view = QAttributeConfigView()
        self.tabs.widget(1).layout().addWidget(self.attribute_view)
        self.filter_edit.setPlaceholderText('Suchen...')
        self.filter_edit.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.LeadingPosition)
        self.filter_edit.textChanged.connect(self.attribute_view.onFilterTextChanged)

        # page 3 - Database
        self.tab_database_actions.tabBar().setCursor(Qt.PointingHandCursor)
        self.tab_database_actions.setCurrentIndex(0)
        self.db_create_options = [w for w in self.db_create_group.children() if isinstance(w, QLineEdit)]
        self.db_create.setEnabled(False)
        self.db_create.clicked.connect(self.onDatabaseCreateClicked)
        for w in self.db_create_options:
            w.textChanged.connect(self.db_create_options_changed)

        self.db_tab_spinner = WaitingSpinner(self.tab_database_actions, disableParentWhenSpinning=True, radius=5,
                                             lines=20, line_length=5, line_width=1, color=(0, 6, 128))

        self.tab_database_actions.setStyleSheet('''
            QToolButton {
                border: 0px;
            }
            #category {
                text-transform: uppercase;
                font-weight: 400;
                color: #374151;
            }
            #name {
                font-size: 1.125rem;
                font-weight: 500;
                color: #1c1917;
            }
            #error_message{
                font-weight: bold; 
                font-size: 7pt; 
                color: #991B1B;
            }
            QTabWidget::pane {
                border: none;
                border-top: 1px solid #e5e7eb;
                position: absolute;
            }
            /* Style the tab using the tab sub-control. Note that
                it reads QTabBar _not_ QTabWidget */
            QTabBar::tab {
                border: none;
                min-width: 20ex;
                padding: 15px;
                color: #4b5563;
                cursor: pointer;
            }

            QTabBar::tab:hover {
                background-color: #e5e7eb;
                color: #111827;
            }

            QTabBar::tab:selected {
                border-bottom: 2px solid #93C5FD;
                background-color: #eff6ff;
                color: #111827;
            }
            ''')

        self.tabs.setCurrentIndex(0)

    def showEvent(self, e: QShowEvent):
        super(Settings, self).showEvent(e)
        self.fillConnections()
        self.setXPlanVersion()

        self.attribute_view.setupModelData()

    def closeEvent(self, e: QCloseEvent):
        super(Settings, self).closeEvent(e)

        self.status_label.setText('')
        self.status_action.setText('')

        conf = self.attribute_view.config_dict()
        s = QSettings()
        s.setValue(f"plugins/xplanung/attribute_config", yaml.dump(conf, default_flow_style=False))

        self.saveSettings()

    @qasync.asyncSlot()
    async def onDatabaseCreateClicked(self):
        self.db_tab_spinner.start()

        self.db_create.setEnabled(False)
        db = self.db_name.text()
        username = self.db_username.text()
        password = self.db_password.text()
        host = self.db_host.text()
        port = self.db_port.text()

        self.status_label.show()
        self.status_label.setText('Datenbank erstellen...')
        self.status_action.setText('')
        engine = create_async_engine(f"postgresql+asyncpg://{username}:{password}@{host}:{port}/postgres",
                                     isolation_level='AUTOCOMMIT')
        try:
            async with engine.connect() as conn:
                await conn.execute(text(f'CREATE DATABASE {db}'))

            self.status_label.setText('XPlanung Schema erstellen...')

            # TODO: sqlalchemy+asyncpg can not execute multiple queries (sql file), as it is always using a prepared
            #  statement, even if not required at all
            # therefore creating schema currently needs to be run in an executor
            # https://github.com/MagicStack/asyncpg/issues/1041
            # https://github.com/sqlalchemy/sqlalchemy/issues/6467
            def create_schema():
                engine = create_engine(f"postgresql://{username}:{password}@{host}:{port}/{db}")
                with engine.begin() as conn:
                    with open(os.path.join(BASE_DIR, f'database/create_v{VERSION}.sql')) as file:
                        conn.execute(file.read())

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, create_schema)

        except DBAPIError as e:
            logger.exception(e)
            # TODO: currently no way to access the original error message from asyncpg
            # https://github.com/sqlalchemy/sqlalchemy/issues/8047
            # if e.orig == asyncpg.exceptions.DuplicateDatabaseError:
            #     self.status_label.setText(f'FEHLER:  Datenbank »{db}« existiert bereits')
            #     return
            self.status_label.setText(str(e))
            return
        except Exception as e:
            logger.exception(e)
            self.status_label.setText(str(e))
            return
        finally:
            self.db_create.setEnabled(True)
            self.db_tab_spinner.stop()

        uri = QgsDataSourceUri()
        uri.setConnection(host, port, db, username, password)

        config = {
            "saveUsername": True,
            "savePassword": True,
            "estimatedMetadata": True,
            "metadataInDatabase": True,
        }

        metadata = QgsProviderRegistry.instance().providerMetadata('postgres')
        connection = metadata.createConnection(uri.uri(), config)
        connection.store(f"SAGis XPlanung: {db}")
        iface.browserModel().reload()

        self.status_label.setText('Datenbank erstellt...')
        self.status_action.setText('<a href="..link">Neue Konfiguration anwenden</a>')
        self.status_action.mousePressEvent = functools.partial(self.statusActionConfigApply, f"SAGis XPlanung: {db}")

    def statusActionConfigApply(self, new_connection_name: str, event):
        QSettings().setValue(f"plugins/xplanung/connection", new_connection_name)
        self.fillConnections()

        self.status_action.setText('')
        self.status_label.setText(f'Neue Konfiguration {new_connection_name} ausgewählt.')
        QTimer.singleShot(5000, lambda: self.status_label.setText(''))

        self.status_action.mousePressEvent = lambda _: None
        self.tab_database_actions.setCurrentIndex(0)

    def db_create_options_changed(self, t):
        self.db_create.setEnabled(not any(e.text() == '' for e in self.db_create_options))

    def setXPlanVersion(self):
        s = QSettings()
        default_version = s.value(f"plugins/xplanung/export_version", '')
        index = self.cbXPlanVersion.findText(str(default_version))
        if index >= 0:
            self.cbXPlanVersion.setCurrentIndex(index)

    def fillConnections(self):
        self.cbConnections.clear()

        qs = QSettings()
        qs.beginGroup("PostgreSQL/connections")
        conn_names = [cn for cn in qs.childGroups()]
        qs.endGroup()

        self.cbConnections.addItems(conn_names)
        self.cbConnections.currentIndexChanged.connect(self.connIndexChanged)

        self.first_start = qs.contains(f"plugins/xplanung/connection")

        index = 0
        for conn in conn_names:
            if conn == qs.value(f"plugins/xplanung/connection"):
                index = self.cbConnections.findText(conn)
                break

        if index >= 0:
            self.cbConnections.setCurrentIndex(index)
        elif conn_names:
            self.cbConnections.setCurrentIndex(0)
        self.connIndexChanged()

    @pyqtSlot()
    def connIndexChanged(self):
        conn_name = str(self.cbConnections.currentText())
        qs = QSettings()
        username = qs.value(f"PostgreSQL/connections/{conn_name}/username", '')
        password = qs.value(f"PostgreSQL/connections/{conn_name}/password", '')
        self.tbUsername.setText(username)
        self.tbPassword.setText(password)

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
        ret = msgBox.exec_()
        if not ret:
            Settings().exec_()
        return checkDbConnection()


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

