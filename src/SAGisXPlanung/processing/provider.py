import os

from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider

from .export_all import ExportAllAlgorithm
from .. import BASE_DIR


class SAGisProvider(QgsProcessingProvider):

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(ExportAllAlgorithm())

        try:
            from .import_civil import ImportCivil3DAlgorithm
            self.addAlgorithm(ImportCivil3DAlgorithm())
        except ImportError as e:
            pass

    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return 'sagis-xplanung'

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return 'SAGis XPlanung'

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(os.path.join(BASE_DIR, 'gui/resources/sagis_icon.png'))