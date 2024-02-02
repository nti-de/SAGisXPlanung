import asyncio
import functools
import logging
import os

import qasync
from qgis.core import QgsDataSourceUri, QgsProviderRegistry
from qgis.utils import iface

from qgis.PyQt.QtCore import pyqtSlot, QSettings, Qt, QTimer
from qgis.PyQt.QtWidgets import QLineEdit
from qgis.PyQt.QtGui import QIcon

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DatabaseError, DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from SAGisXPlanung import BASE_DIR, VERSION, Session, SessionAsync
from SAGisXPlanung.core.connection import verify_db_connection, establish_session
from SAGisXPlanung.ext.spinner import loading_animation
from SAGisXPlanung.gui.style import load_svg, ApplicationColor, with_color_palette, apply_color
from .basepage import SettingsPage

logger = logging.getLogger(__name__)


class DatabaseConfigPage(SettingsPage):
    def __init__(self, parent=None):
        super(DatabaseConfigPage, self).__init__(parent)
        self.ui = None

        self.check_icon_base = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/check.svg'),
                                              color=ApplicationColor.Grey400))

    def setupUi(self, ui):
        self.ui = ui

        self.ui.tab_database_actions.tabBar().setCursor(Qt.PointingHandCursor)
        self.ui.tab_database_actions.setCurrentIndex(0)
        self.db_create_options = [w for w in self.ui.db_create_group.children() if isinstance(w, QLineEdit)]
        self.ui.db_create.setEnabled(False)
        self.ui.db_create.clicked.connect(self.on_database_create_clicked)
        for w in self.db_create_options:
            w.textChanged.connect(self.db_create_options_changed)

        self.ui.connnection_test_status_icon.setIcon(self.check_icon_base)
        # schedule asyncio task and return None, so that void return type of sip method is satisfied
        # otherwise throws a lot of TypeError: invalid argument to sipBadCatcherResult()
        self.ui.connection_test_label.mousePressEvent = lambda e: asyncio.create_task(self.test_connection()) and None

        self.ui.tab_database_actions.setStyleSheet('''
            QToolButton {
                border: 0px;
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
        with_color_palette(self.ui.tab_database_actions, [
            ApplicationColor.Primary, ApplicationColor.Error, ApplicationColor.Success, ApplicationColor.Grey600
        ], class_='QLabel')

    def setupData(self):
        self.fill_connections()

    @qasync.asyncSlot()
    async def on_database_create_clicked(self):
        async with loading_animation(self.ui.tab_database) as spinner:
            self.ui.db_create.setEnabled(False)
            db = self.ui.db_name.text()
            username = self.ui.db_username.text()
            password = self.ui.db_password.text()
            host = self.ui.db_host.text()
            port = self.ui.db_port.text()

            self.ui.status_label.show()
            self.ui.status_label.setText('Datenbank erstellen...')
            self.ui.status_action.setText('')
            engine = create_async_engine(f"postgresql+asyncpg://{username}:{password}@{host}:{port}/postgres",
                                         isolation_level='AUTOCOMMIT')
            try:
                async with engine.connect() as conn:
                    await conn.execute(text(f'CREATE DATABASE {db}'))

                self.ui.status_label.setText('XPlanung Schema erstellen...')

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
                self.ui.status_label.setText(str(e))
                return
            except Exception as e:
                logger.exception(e)
                self.ui.status_label.setText(str(e))
                return
            finally:
                self.ui.db_create.setEnabled(True)
                spinner.stop()

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

            self.ui.status_label.setText('Datenbank erstellt...')
            self.ui.status_action.setText('<a href="..link">Neue Konfiguration anwenden</a>')
            self.ui.status_action.mousePressEvent = functools.partial(self.status_action_apply_clicked, f"SAGis XPlanung: {db}")

    def db_create_options_changed(self, t):
        self.ui.db_create.setEnabled(not any(e.text() == '' for e in self.db_create_options))

    def status_action_apply_clicked(self, new_connection_name: str, event):
        QSettings().setValue(f"plugins/xplanung/connection", new_connection_name)
        self.fill_connections()

        self.ui.status_action.setText('')
        self.ui.status_label.setText(f'Neue Konfiguration {new_connection_name} ausgewählt.')
        QTimer.singleShot(5000, lambda: self.ui.status_label.setText(''))

        self.ui.status_action.mousePressEvent = lambda _: None
        self.ui.tab_database_actions.setCurrentIndex(0)

    def fill_connections(self):
        self.ui.cbConnections.clear()

        qs = QSettings()
        qs.beginGroup("PostgreSQL/connections")
        conn_names = [cn for cn in qs.childGroups()]
        qs.endGroup()

        self.ui.cbConnections.addItems(conn_names)
        self.ui.cbConnections.currentIndexChanged.connect(self.on_connection_index_changed)

        index = 0
        for conn in conn_names:
            if conn == qs.value(f"plugins/xplanung/connection"):
                index = self.ui.cbConnections.findText(conn)
                break

        if index >= 0:
            self.ui.cbConnections.setCurrentIndex(index)
        elif conn_names:
            self.ui.cbConnections.setCurrentIndex(0)
        self.on_connection_index_changed()


    @qasync.asyncSlot()
    async def on_connection_index_changed(self):
        self.ui.connnection_test_status_icon.setIcon(self.check_icon_base)
        self.ui.connection_test_result_label.setText(f'Verbindungstatus unbekannt')
        apply_color(self.ui.connection_test_result_label, ApplicationColor.Grey600)

        conn_name = str(self.ui.cbConnections.currentText())
        qs = QSettings()
        username = qs.value(f"PostgreSQL/connections/{conn_name}/username", '')
        password = qs.value(f"PostgreSQL/connections/{conn_name}/password", '')
        self.ui.tbUsername.setText(username)
        self.ui.tbPassword.setText(password)

        qs.setValue(f"plugins/xplanung/connection", conn_name)
        establish_session(Session)
        establish_session(SessionAsync)

    async def test_connection(self):

        def _test_connection():
            logger.debug('call verification')
            result, meta = verify_db_connection(raise_exeptions=True)

            self.ui.connection_test_result_label.setText(f'XPlan-Datenbank: {meta.revision}')
            apply_color(self.ui.connection_test_result_label, ApplicationColor.Primary)

        spinner_args = {
            'radius': 4,
            'lines': 16,
            'line_length': 4,
        }
        async with loading_animation(self.ui.connnection_test_status_icon, **spinner_args) as spinner:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _test_connection)

                check_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/check.svg'),
                                            color=ApplicationColor.Success))
                self.ui.connnection_test_status_icon.setIcon(check_icon)

            except Exception as e:
                error_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/error-outline.svg'),
                                            color=ApplicationColor.Error))
                self.ui.connnection_test_status_icon.setIcon(error_icon)
                logger.debug(e)

            apply_color(self.ui.connection_test_result_label, ApplicationColor.Primary)