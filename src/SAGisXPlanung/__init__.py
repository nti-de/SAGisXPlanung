import importlib
import json
import logging
import os.path
import os
import platform
import sys
import asyncio
from enum import Enum
from io import StringIO
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication, QT_VERSION_STR
from qgis.core import Qgis, QgsApplication
from qgis.PyQt.uic import compiler

import SAGisXPlanung
from SAGisXPlanung.log_handler import setup_logger

logger = logging.getLogger(__name__)


PYQT5 = PYQT6 = False
if "PyQt5" in sys.modules:
    PYQT5 = True
elif "PyQt6" in sys.modules:
    PYQT6 = True

def qt_version_tuple():
    return tuple(map(int, QT_VERSION_STR.split('.')))


# ================ LOG UNCAUGHT EXCEPTIONS ====================
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


# ================ SETUP ASYNCIO EVENT LOOP ====================
def setup_asyncio():
    try:
        from qasync import QEventLoop

        __app = QCoreApplication.instance()
        __loop = QEventLoop(__app, already_running=True)
        asyncio.set_event_loop(__loop)
    except Exception as e:
        logger.error(e)


# ================ COMPILE UI FILES ======================

# workaround for compiling ui files with uic which have a custom widget class as top level widget
# uic assumes that all widgets reside within QtWidgets namespace which is not true for custom widgets
# this workaround simply removes the call to `getattr(QtWidgets, winfo["baseclass"])`
# all base classes must therefore be specified manually when loading ui form classes with this function
#
# some comments on the issue by qgis devs here:
# https://lists.osgeo.org/pipermail/qgis-developer/2018-January/051342.html
def compile_ui_file(ui_file):
    code_string = StringIO()
    if PYQT5:
        winfo = compiler.UICompiler().compileUi(ui_file, code_string, False, '_rc', '.')
    else:
        winfo = compiler.UICompiler().compileUi(ui_file, code_string)

    ui_globals = {}
    exec(code_string.getvalue(), ui_globals)
    return ui_globals[winfo["uiclass"]]


# ================ PYTHON DEBUG CONFIG ====================
try:
    import pydevd_pycharm

    pydevd_pycharm.settrace('localhost', port=51599, stdoutToServer=True, stderrToServer=True, suspend=False)
except Exception as e:
    logger.info('Python debug config failed')
    logger.error(e)

# =========================================================

VERSION = '2.13.0'
RELEASE = True
COMPATIBLE_DB_REVISIONS = ['2b1452b49cc5']
DEPENDENCIES = [
    'requests',
    'packaging',
    'lxml',
    'SQLAlchemy==2.0.46',
    'GeoAlchemy2>=0.12.5',
    'shapely>=2.0.2',
    'qasync==0.22.0',
    'asyncpg==0.31.0'
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSISTENT_CONFIG_DIR = os.path.join(QgsApplication.qgisSettingsDirPath(), "NTI", "SAGisXPlanung")

if not os.path.exists(PERSISTENT_CONFIG_DIR):
    os.makedirs(PERSISTENT_CONFIG_DIR)

Base = None
Session = None
SessionAsync = None


def setup_sqlalchemy():
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.orm import declarative_base, sessionmaker

        global Base
        global Session
        global SessionAsync
        Base = declarative_base()
        Session = sessionmaker()
        SessionAsync = sessionmaker(expire_on_commit=False, class_=AsyncSession)
    except Exception as e:
        logger.error(e)


if os.environ.get('CI'):
    setup_sqlalchemy()


class XPlanVersion(Enum):
    FIVE_THREE = '5.3'
    SIX = '6.0'

    @classmethod
    def from_namespace(cls, ns: str):
        if ns == "http://www.xplanung.de/xplangml/6/0":
            return cls.SIX
        elif ns.startswith("http://www.xplanung.de/xplangml/5/"):
            return cls.FIVE_THREE
        raise ValueError(f'XPlanung Version {ns} nicht unterstützt.')

    def short_id(self) -> str:
        return str(self.value).replace('.', '')

    def __str__(self):
        return self.value


def system_info():
    try:
        info = {
            'platform': platform.system(),
            'platform-release': platform.release(),
            'platform-version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
        }
        return json.dumps(info)
    except Exception as ex:
        logging.exception(ex)


def qgis_info():
    try:
        qgs_info = {
            'xplanung_version': VERSION,
            'qgis_version': Qgis.version(),
            'geos_version': Qgis.geosVersion(),
        }
        return json.dumps(qgs_info)
    except Exception as ex:
        logging.exception(ex)


def classFactory(iface):
    setup_logger(BASE_DIR, "SAGisXPlanung" if not RELEASE else "SAGisXPlanung_pro")

    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('qasync').setLevel(logging.ERROR)
    logging.getLogger('PyQt5.uic.uiparser').setLevel(logging.ERROR)
    logging.getLogger('PyQt5.uic.properties').setLevel(logging.ERROR)
    logging.getLogger('PyQt6.uic.uiparser').setLevel(logging.ERROR)
    logging.getLogger('PyQt6.uic.properties').setLevel(logging.ERROR)

    logger.info(system_info())
    logger.info(qgis_info())

    py_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    deps = Path(BASE_DIR) / "dependencies" / f"{py_tag}"
    if deps.exists():
        sys.path.insert(0, str(deps))

    from SAGisXPlanung.config.dependencies import check
    re = check(DEPENDENCIES)
    if not re:
        # create anonymous object so that qgis can call initGui and unload without crashing
        return type('', (object,), {"initGui": (lambda self: None), "unload": (lambda self: None)})()

    setup_asyncio()
    setup_sqlalchemy()
    # reload config module required so that new configured `Base` is used
    importlib.reload(SAGisXPlanung.config)

    from SAGisXPlanung.core.connection import establish_session
    establish_session(Session)
    establish_session(SessionAsync)

    from SAGisXPlanung.XPlanungPlugin import XPlanung
    return XPlanung(iface)
