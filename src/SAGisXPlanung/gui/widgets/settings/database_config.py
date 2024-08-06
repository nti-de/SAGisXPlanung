import asyncio
import functools
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import qasync
from PyQt5.QtGui import QCloseEvent
from qgis.core import QgsDataSourceUri, QgsProviderRegistry
from qgis.utils import iface

from qgis.PyQt.QtCore import pyqtSlot, QSettings, Qt, QTimer
from qgis.PyQt.QtWidgets import QLineEdit
from qgis.PyQt.QtGui import QIcon

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DatabaseError, DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from SAGisXPlanung import BASE_DIR, VERSION, Session, SessionAsync
from SAGisXPlanung.core.connection import verify_db_connection, establish_session, IncompatibleDatabaseVersion
from SAGisXPlanung.ext.spinner import loading_animation
from SAGisXPlanung.ext.toast import Toaster
from SAGisXPlanung.gui.style import load_svg, ApplicationColor, with_color_palette, apply_color
from .basepage import SettingsPage

logger = logging.getLogger(__name__)


@dataclass
class RevisionMeta:
    current_revision: str = None
    expected_revision: str = None

    def is_valid(self) -> bool:
        return self.current_revision == self.expected_revision


style = '''
QToolButton[objectName="connnection_test_status_icon"], 
QToolButton[objectName="button_alert_icon"] {{
    border: 0px;
}}
QTabWidget::pane {{
    border: none;
    border-top: 1px solid #e5e7eb;
    position: absolute;
}}
/* Style the tab using the tab sub-control. Note that
    it reads QTabBar _not_ QTabWidget */
QTabBar::tab {{
    border: none;
    min-width: 20ex;
    padding: 15px;
    color: #4b5563;
    cursor: pointer;
}}

QTabBar::tab:hover {{
    background-color: #e5e7eb;
    color: #111827;
}}

QTabBar::tab:selected {{
    border-bottom: 2px solid #93C5FD;
    background-color: #eff6ff;
    color: #111827;
}}

QLabel[objectName="label_upgrade"] {{
    color: {_label_color_mute};
}}
'''


class DatabaseConfigPage(SettingsPage):
    def __init__(self, parent=None):
        super(DatabaseConfigPage, self).__init__(parent)
        self.ui = None
        self.database_revision = RevisionMeta()

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

        self.ui.button_alert_icon.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/warning.svg'),
                                                   color=ApplicationColor.Grey600))
        self.ui.button_upgrade.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/upgrade.svg'),
                                                color=ApplicationColor.Tertiary))
        self.ui.button_upgrade.setCursor(Qt.PointingHandCursor)

        self.ui.database_version_frame.hide()
        self.ui.button_upgrade.clicked.connect(self.on_revision_update_clicked)

        self.ui.label_extra_info.hide()

        self.ui.tab_database_actions.setStyleSheet(style.format(
            _label_color_mute=ApplicationColor.Grey600
        ))
        with_color_palette(self.ui.tab_database_actions, [
            ApplicationColor.Primary, ApplicationColor.Error, ApplicationColor.Success, ApplicationColor.Grey600
        ], class_='QLabel')

    def setupData(self):
        self.fill_connections()

    def closeEvent(self, event: QCloseEvent):
        self.save_settings()

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

    def save_settings(self):
        qs = QSettings()
        conn_name = str(self.ui.cbConnections.currentText())
        qs.setValue(f"plugins/xplanung/connection", conn_name)
        qs.setValue(f"PostgreSQL/connections/{conn_name}/username", self.ui.tbUsername.text())
        qs.setValue(f"PostgreSQL/connections/{conn_name}/password", self.ui.tbPassword.text())
        establish_session(Session)
        establish_session(SessionAsync)

    @qasync.asyncSlot()
    async def on_connection_index_changed(self):
        self.ui.connnection_test_status_icon.setIcon(self.check_icon_base)
        self.ui.connection_test_result_label.setText(f'Verbindungstatus unbekannt')
        apply_color(self.ui.connection_test_result_label, ApplicationColor.Grey600)
        self.ui.database_version_frame.hide()

        conn_name = str(self.ui.cbConnections.currentText())
        qs = QSettings()
        username = qs.value(f"PostgreSQL/connections/{conn_name}/username", '')
        password = qs.value(f"PostgreSQL/connections/{conn_name}/password", '')
        service = qs.value(f"PostgreSQL/connections/{conn_name}/service", '')
        self.ui.tbUsername.setText(username)
        self.ui.tbPassword.setText(password)
        self.ui.label_extra_info.setVisible(service != '')
        if service:
            t = f'PG Service Konfiguration <span style="color: {ApplicationColor.Secondary};">{service}</span> angewendet...'
            self.ui.label_extra_info.setText(t)

        qs.setValue(f"plugins/xplanung/connection", conn_name)
        establish_session(Session)
        establish_session(SessionAsync)

    @qasync.asyncSlot()
    async def on_revision_update_clicked(self):
        async with loading_animation(self.ui.tab_database):
            if self.database_revision.is_valid():
                return

            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.upgrade_database_revision)

                Toaster.showMessage(self, message='Datenbank erfolgreich aktualisiert!', corner=Qt.BottomRightCorner,
                                    margin=20, icon=None, closable=False, color='#ffffff', background_color='#404040',
                                    timeout=3000)
                self.ui.database_version_frame.hide()
                self.database_revision.current_revision = self.database_revision.expected_revision

            except Exception as e:
                apply_color(self.ui.connection_test_result_label, ApplicationColor.Error)
                self.ui.connection_test_result_label.setText(str(e))
                logger.error(e)

            await self.test_connection()

    def upgrade_database_revision(self):
        rev = self.database_revision.current_revision
        target_rev = self.database_revision.expected_revision

        sql_dir = Path(BASE_DIR) / Path('database')
        migration_files = [f.stem for f in sql_dir.iterdir() if f.is_file() and '_' in f.stem]

        engine = Session().get_bind()
        with engine.connect() as connection:
            revision_sequence = self._find_revision_sequence(migration_files, rev, target_rev)
            for revision_file in revision_sequence:
                with open(os.path.join(sql_dir, f'{revision_file}.sql'), 'r') as file:
                    sql_content = file.read()
                    connection.execute(sql_content)

    def _find_revision_sequence(self, sequence, start, end):
        result = []
        current = start

        # Create a dictionary to quickly look up the next revision in the sequence
        lookup = {item.split('_')[0]: item for item in sequence}

        # Continue adding items to the result until the end revision is reached
        while current != end:
            if current in lookup:
                result.append(lookup[current])
                current = lookup[current].split('_')[1]
            else:
                break  # if there's no matching string for the current revision, exit the loop

        return result

    async def test_connection(self):
        self.save_settings()

        def _test_connection():
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
                apply_color(self.ui.connection_test_result_label, ApplicationColor.Primary)

            except Exception as e:
                error_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/error-outline.svg'),
                                            color=ApplicationColor.Error))
                self.ui.connnection_test_status_icon.setIcon(error_icon)
                apply_color(self.ui.connection_test_result_label, ApplicationColor.Error)
                self.ui.connection_test_result_label.setText(str(e))
                logger.error(e)

                if isinstance(e, IncompatibleDatabaseVersion):
                    self.database_revision.current_revision = e.current_revision
                    self.database_revision.expected_revision = e.expected_revisions[0]
                    self.ui.database_version_frame.show()
