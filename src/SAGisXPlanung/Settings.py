import asyncio
import functools
import logging
import os

import qasync

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QShowEvent, QCloseEvent
from qgis.PyQt.QtWidgets import QDialog

from SAGisXPlanung import VERSION, XPlanVersion
from SAGisXPlanung.config import QgsConfig, GeometryValidationConfig, GeometryCorrectionMethod
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
        qs = QSettings()
        qs.setValue(f"plugins/xplanung/export_version", self.cbXPlanVersion.currentText())
        if self.checkPath.isChecked():
            qs.setValue(f"plugins/xplanung/export_path", '')
        else:
            qs.setValue(f"plugins/xplanung/export_path", self.tbPath.text())

        validation_config = GeometryValidationConfig(
            correct_geometries=self.checkbox_clean_geometry.isChecked(),
            correct_method=GeometryCorrectionMethod.PreserveTopology if self.radiobutton_preserve_geometry.isChecked() else GeometryCorrectionMethod.RigorousRemoval
        )
        logger.debug(validation_config.correct_method)
        QgsConfig.set_geometry_validation_config(validation_config)

        self.accept()
