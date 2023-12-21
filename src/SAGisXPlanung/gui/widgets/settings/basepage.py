from qgis.PyQt.QtGui import QCloseEvent
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QWidget


class SettingsPage(QWidget):

    # signal to notify parent dialog to refresh a settings page of given type
    requestPageRefresh = pyqtSignal(object)  # parameter of type SettingsPage

    def setupUi(self, ui):
        raise NotImplementedError('Abstract. Should be implemented in subclass.')

    def setupData(self):
        raise NotImplementedError('Abstract. Should be implemented in subclass.')

    def closeEvent(self, event: QCloseEvent):
        pass
