import logging
import os
from qgis.core import QgsMessageLog, Qgis


class QgisLogHandler(logging.Handler):
    LEVEL_MAP = {
        logging.DEBUG: Qgis.Info,
        logging.INFO: Qgis.Info,
        logging.WARNING: Qgis.Warning,
        logging.ERROR: Qgis.Critical,
        logging.CRITICAL: Qgis.Critical,
    }

    def __init__(self, tag="SAGisXPlanung", level=logging.ERROR):
        super().__init__(level)
        self.tag = tag

    def emit(self, record):
        try:
            msg = self.format(record)
            qgis_level = self.LEVEL_MAP.get(record.levelno, Qgis.Info)
            QgsMessageLog.logMessage(msg, self.tag, qgis_level)
        except Exception:
            self.handleError(record)


def setup_logger(base_dir):
    root_module_name = __name__.partition(".")[0]
    logger = logging.getLogger(root_module_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(
        os.path.join(base_dir, "XPlanung.log"),
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    qgis_handler = QgisLogHandler()
    qgis_handler.setLevel(logging.WARNING)
    qgis_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(qgis_handler)