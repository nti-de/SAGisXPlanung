import logging
from dataclasses import dataclass
from typing import Union, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from SAGisXPlanung.config import QgsConfig

logger = logging.getLogger(__name__)


class IncompatibleDatabaseVersion(Exception):
    def __init__(self, message, current_revision, expected_revisions):
        self.message = message
        self.current_revision = current_revision
        self.expected_revisions = expected_revisions
        super(IncompatibleDatabaseVersion, self).__init__(message)


@dataclass
class ConnectionMeta:
    revision: str = None
    error: str = None


def establish_session(session_maker: sessionmaker):
    try:
        conn = QgsConfig.connection_params()
        if conn["service"]:
            conn_arguments = f"/?service={conn['service']}"
        else:
            conn_arguments = f"{conn['username']}:{conn['password']}@{conn['host']}:{conn['port']}/{conn['db']}"

        if session_maker.class_._is_asyncio:
            async_db_str = f"postgresql+asyncpg://{conn_arguments}"
            async_engine = create_async_engine(async_db_str)
            session_maker.configure(bind=async_engine)
        else:
            db_str = f"postgresql://{conn_arguments}"
            engine = create_engine(db_str)
            session_maker.configure(bind=engine)

        return True
    except Exception as ex:
        logger.exception(f'Error on session config: {ex}')
        return False


def attempt_connection():
    conn = QgsConfig.connection_params()
    if conn["service"]:
        conn_arguments = f"/?service={conn['service']}"
    else:
        conn_arguments = f"{conn['username']}:{conn['password']}@{conn['host']}:{conn['port']}/{conn['db']}"
    db_str = f"postgresql://{conn_arguments}"
    ngn = create_engine(db_str)
    ngn.connect()


def verify_db_connection(raise_exeptions=False) -> Tuple[bool, ConnectionMeta]:
    try:
        attempt_connection()
    except Exception as e:
        if raise_exeptions:
            raise e
        return False, ConnectionMeta(error='Keine Verbindung mit der Datenbank möglich')

    from SAGisXPlanung import Session, COMPATIBLE_DB_REVISIONS
    ngn = Session().get_bind()
    with ngn.connect() as conn:
        try:
            res = conn.execute(text('SELECT version_num FROM alembic_version'))
            db_version_row = res.first()
            if db_version_row and db_version_row[0] in COMPATIBLE_DB_REVISIONS:
                return True, ConnectionMeta(revision=db_version_row[0])

            msg = f'Die Version der QGIS-Erweiterung ist inkompatibel mit der aktuell angegebenen Datenbank! <ul>'
            msg += f"<li>Aktuelle Datenbankversion: <code>{db_version_row[0]}</code></li>"
            msg += f"<li>Erwartete Datenbankversion: <code>{', '.join(COMPATIBLE_DB_REVISIONS)}</code></li>"
            msg += '</ul>'
            if raise_exeptions:
                raise IncompatibleDatabaseVersion(msg, db_version_row[0], COMPATIBLE_DB_REVISIONS)
            return False, ConnectionMeta(error=msg)
        except DatabaseError as e:
            if raise_exeptions:
                raise e
            msg = f'Die angegebene Datenbank ist nicht kompatibel mit SAGis XPlanung! Bitte konfigurieren Sie' \
                  f' eine neue Verbindung in den Einstellungen.'
            return False, ConnectionMeta(error=msg)
