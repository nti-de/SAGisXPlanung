import asyncio
import functools
import logging
import os
from typing import Union

import qasync

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QShowEvent, QCloseEvent, QIcon
from qgis.PyQt.QtWidgets import QDialog

from SAGisXPlanung import VERSION, XPlanVersion, BASE_DIR
from SAGisXPlanung.config import QgsConfig, GeometryValidationConfig, GeometryCorrectionMethod
from SAGisXPlanung.gui.style import load_svg, ApplicationColor, SVGButtonEventFilter
# don't remove following import: all classes need to be imported at plugin startup for ORM to work correctly
from SAGisXPlanung.gui.widgets import QAttributeConfigView
from SAGisXPlanung.gui.widgets.settings.basepage import SettingsPage

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/settings.ui'))
logger = logging.getLogger(__name__)


class Settings(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)
        self.setupUi(self)

        self.versionLabel.setText(VERSION)

        self.checkPath.stateChanged.connect(lambda state: self.tbPath.setEnabled((not bool(state))))
        self.checkbox_clean_geometry.stateChanged.connect(self.checkbox_clean_geometry_state_changed)

        self.cbXPlanVersion.addItems([e.value for e in XPlanVersion])
        self.cbXPlanVersion.currentIndexChanged.connect(self.onXPlanVersionChanged)
        self.setXPlanVersion()

        info_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/info-outline.svg'),
                                   color=ApplicationColor.Grey600))
        self.info_button_highlight_filter = SVGButtonEventFilter(ApplicationColor.Grey600, ApplicationColor.Tertiary)
        self.info_clean_geometry.setIcon(info_icon)
        self.info_preserve_topology.setIcon(info_icon)
        self.info_repeated_points.setIcon(info_icon)
        self.info_clean_geometry.installEventFilter(self.info_button_highlight_filter)
        self.info_preserve_topology.installEventFilter(self.info_button_highlight_filter)
        self.info_repeated_points.installEventFilter(self.info_button_highlight_filter)
        self.info_clean_geometry.setToolTip('<qt>Beim Erfassen neuer Geometrien, wird automatisch der Umlaufsinn aller Stützpunkte angepasst und eventuell doppelt erfasste Stützpunkte werden entfernt.</qt>')
        self.info_preserve_topology.setToolTip('<qt>Die Geometriebereinigung erhält die topologische Struktur der Geometrien. Es werden nur doppelte, aufeinanderfolgende Stützpunkte entfernt.</qt>')
        self.info_repeated_points.setToolTip('<qt>Eine genauere Erkennung doppelter Stützpunkte wird angewendet. Die Geometriebereinigung entfernt auch doppelte Stützpunkte, die nicht aufeinanderfolgend sind. Dies kann jedoch zu Änderungen in der Topologie führen.</qt>')
        self.set_validation_options()

        self.status_label.hide()

        # initialize UI on all settings pages
        for i in range(1, self.tabs.count()):
            self.tabs.widget(i).setupUi(self)

        self.tabs.setCurrentIndex(0)

        self.validation_options_group.setStyleSheet('''
            QToolButton {
                border: 0px;
            }
        ''')

    def navigate_to_page(self, page_type: type) -> Union[None, SettingsPage]:
        if not issubclass(page_type, SettingsPage):
            return

        for i in range(1, self.tabs.count()):
            page = self.tabs.widget(i)
            if isinstance(page, page_type):
                self.tabs.setCurrentIndex(i)
                return page

    def showEvent(self, e: QShowEvent):
        super(Settings, self).showEvent(e)
        self.setXPlanVersion()
        self.set_validation_options()

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

    @qasync.asyncSlot(int)
    async def checkbox_clean_geometry_state_changed(self, state):
        for row in range(1, 3):
            for column in range(self.validation_options_group.layout().columnCount()):
                widget = self.validation_options_group.layout().itemAtPosition(row, column)
                if widget is not None:
                    widget.widget().setEnabled(state != 0)

    def setXPlanVersion(self):
        s = QSettings()
        default_version = s.value(f"plugins/xplanung/export_version", '')
        index = self.cbXPlanVersion.findText(str(default_version))
        if index >= 0:
            self.cbXPlanVersion.setCurrentIndex(index)

    def set_validation_options(self):
        validation_config = QgsConfig.geometry_validation_config()
        self.checkbox_clean_geometry.setChecked(validation_config.correct_geometries)
        if validation_config.correct_method == GeometryCorrectionMethod.PreserveTopology:
            self.radiobutton_preserve_topology.setChecked(True)
        else:
            self.radiobutton_repeated_points.setChecked(True)

    def saveSettings(self):
        qs = QSettings()
        qs.setValue(f"plugins/xplanung/export_version", self.cbXPlanVersion.currentText())
        if self.checkPath.isChecked():
            qs.setValue(f"plugins/xplanung/export_path", '')
        else:
            qs.setValue(f"plugins/xplanung/export_path", self.tbPath.text())

        validation_config = GeometryValidationConfig(
            correct_geometries=self.checkbox_clean_geometry.isChecked(),
            correct_method=GeometryCorrectionMethod.PreserveTopology if self.radiobutton_preserve_topology.isChecked() else GeometryCorrectionMethod.RigorousRemoval
        )
        QgsConfig.set_geometry_validation_config(validation_config)

        self.accept()
