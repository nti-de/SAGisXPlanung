import asyncio
import logging
import os.path

from qgis.PyQt import QtWidgets, sip
from qgis.PyQt.QtCore import Qt, pyqtSlot, QObject, QSizeF, QUrl, QDir
from qgis.PyQt.QtGui import QIcon, QPageLayout, QPainter
from qgis.PyQt.QtWidgets import QAction, QMenu, QFileDialog, QStyleOptionGraphicsItem, QToolBar, QMessageBox
from qgis.PyQt.QtPrintSupport import QPrinter

from qgis.core import (QgsMapLayerType, QgsProject, QgsLayerTreeGroup, QgsAnnotationLayer, Qgis,
                       QgsMapRendererCustomPainterJob, QgsRenderContext, QgsApplication, QgsVectorLayer)
from qgis.gui import QgsMapLayerAction
from qgis import processing

import qasync

from SAGisXPlanung.BuildingTemplateItem import BuildingTemplateItem
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.Settings import Settings
from SAGisXPlanung.core.connection import attempt_connection, verify_db_connection
from SAGisXPlanung.gui.XPEditPreFilledObjects import XPEditPreFilledObjectsDialog
from SAGisXPlanung.core.canvas_display import plan_to_map, load_on_canvas
from SAGisXPlanung.gui.XPlanungDialog import XPlanungDialog
from SAGisXPlanung.gui.widgets import DatabaseConfigPage
from SAGisXPlanung.processing.provider import SAGisProvider
from SAGisXPlanung.utils import createXPlanungIndicators, full_version_required_warning, CLASSES

logger = logging.getLogger(__name__)


class XPlanung(QObject):
    def __init__(self, iface):
        super(XPlanung, self).__init__()
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # Declare instance attributes
        self.main_action = None
        self.data_action = None
        self.snapshot_action = None
        self.processing_menu = None
        self.menu_name = 'SAGis XPlanung'
        self.tool = None
        self.provider = None

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        self.sagis_menu = self.iface.mainWindow().findChild(QMenu, 'sagis_menu')
        if not self.sagis_menu:
            self.sagis_menu = QMenu('&SAGis', self.iface.mainWindow().menuBar())
            self.sagis_menu.setObjectName('sagis_menu')
            actions = self.iface.mainWindow().menuBar().actions()
            if len(actions) > 3:
                self.iface.mainWindow().menuBar().insertMenu(actions[-2], self.sagis_menu)

        self.sagis_toolbar = self.iface.mainWindow().findChild(QToolBar, 'sagis_toolbar')
        if not self.sagis_toolbar:
            self.sagis_toolbar = QToolBar('SAGis Toolbar', self.iface.mainWindow().menuBar())
            self.sagis_toolbar.setToolTip('SAGis Tools')
            self.sagis_toolbar.setObjectName('sagis_toolbar')
            self.iface.addToolBar(self.sagis_toolbar)

        self.menu = self.sagis_menu.addMenu(self.menu_name)
        self.menu.aboutToShow.connect(self.onXPlanungMenuAboutToShow)

        self.dockWidget = XPlanungDialog(parent=iface.mainWindow())
        self.dockWidget.setMaximumWidth(1000)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockWidget.details_dialog)
        self.iface.addTabifiedDockWidget(Qt.RightDockWidgetArea, self.dockWidget, ['xplanung-details'], raiseTab=True)
        self.dockWidget.hide()
        self.dockWidget.details_dialog.hide()

        self.settings = Settings()

        # TODO: hackish solution, because there currently is no signal on project loaded:
        # see https://github.com/qgis/QGIS/issues/40483
        QgsProject.instance().homePathChanged.connect(self.onProjectLoaded)

        self.iface.layerTreeView().layerTreeModel().rowsInserted.connect(self.onRowsInserted)

    def initProcessing(self):
        self.menu.addSeparator()
        self.processing_menu = self.menu.addMenu('Verarbeitungswerkzeuge')

        self.provider = SAGisProvider()
        self.provider.algorithmsLoaded.connect(self.onProcessingAlgorithmsLoaded)

        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        xp_icon = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gui/resources/sagis_icon.png'))
        settings_icon = ':/images/themes/default/mActionOptions.svg'
        self.main_action = QAction(QIcon(xp_icon), 'SAGis XPlanung', self.iface.mainWindow())
        self.main_action.setToolTip('Plugin zum Erfassen von XPlanung konformen Bauleitplänen')
        self.main_action.triggered.connect(self.run)
        self.sagis_toolbar.addAction(self.main_action)

        self.menu.addAction(self.main_action)

        settings_action = QAction(QIcon(settings_icon), 'Einstellungen', self.iface.mainWindow())
        settings_action.setToolTip('SAGis XPlanung konfigurieren')
        settings_action.triggered.connect(self.showSettings)
        self.menu.addAction(settings_action)

        self.menu.addSeparator()

        self.data_action = QAction('Allgemeine Daten bearbeiten...', self.iface.mainWindow())
        self.data_action.triggered.connect(self.showEditPreFilledObjects)
        self.menu.addAction(self.data_action)

        self.snapshot_action = QAction('Aktuellen Kartenauschnitt als PDF exportieren...', self.iface.mainWindow())
        self.snapshot_action.triggered.connect(self.onSnapshotActionTriggered)
        self.menu.addAction(self.snapshot_action)

        self.add_config_content_action()
        QtWidgets.QApplication.restoreOverrideCursor()

        self.initProcessing()

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item, icons and dialogs from QGIS GUI."""
        self.sagis_toolbar.removeAction(self.main_action)
        self.menu.deleteLater()
        if self.sagis_menu.isEmpty():
            self.sagis_menu.deleteLater()

        MapLayerRegistry().unload()

        self.tool.identifyMenu().removeCustomActions()
        QgsProject.instance().homePathChanged.disconnect(self.onProjectLoaded)
        self.iface.layerTreeView().layerTreeModel().rowsInserted.disconnect(self.onRowsInserted)

        self.iface.removeDockWidget(self.dockWidget.details_dialog)
        self.iface.removeDockWidget(self.dockWidget)
        self.dockWidget.details_dialog.deleteLater()
        self.dockWidget.deleteLater()

        # unload processing
        if not sip.isdeleted(self.provider):
            QgsApplication.processingRegistry().removeProvider(self.provider)

    @pyqtSlot()
    def run(self):
        if self.is_valid_db():
            if self.first_start:
                self.dockWidget.cbPlaene.refresh()
            self.dockWidget.show()

        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start:
            self.first_start = False

    @pyqtSlot()
    def showSettings(self):
        self.settings.exec_()

        self.dockWidget.details_dialog.hide()
        if not self.is_valid_db():
            self.dockWidget.hide()

        self.dockWidget.cbPlaene.refresh()

    @pyqtSlot(bool)
    def showEditPreFilledObjects(self, checked):
        d = XPEditPreFilledObjectsDialog(parent=self.iface.mainWindow())
        d.exec()

    @qasync.asyncSlot()
    async def onXPlanungMenuAboutToShow(self):
        try:
            attempt_connection()
            self.data_action.setDisabled(False)
        except Exception:
            self.data_action.setDisabled(True)

    @qasync.asyncSlot()
    async def onProcessingAlgorithmsLoaded(self):
        for alg in self.provider.algorithms():
            a = QAction(QIcon(':/images/themes/default/processingAlgorithm.svg'), alg.displayName(), self.processing_menu)
            a.triggered.connect(lambda checked, alg_id=alg.id(): processing.execAlgorithmDialog(alg_id, {}))
            self.processing_menu.addAction(a)

        self.provider.algorithmsLoaded.disconnect(self.onProcessingAlgorithmsLoaded)

    @qasync.asyncSlot(bool)
    async def onSnapshotActionTriggered(self, checked):
        filename = QFileDialog.getSaveFileName(self.iface.mainWindow(),
                                               'Speicherort auswählen', directory=f'export.pdf', filter=f'*.pdf')

        settings = self.iface.mapCanvas().mapSettings()
        settings.setFlag(Qgis.MapSettingsFlag.Antialiasing, True)
        settings.setFlag(Qgis.MapSettingsFlag.ForceVectorOutput, True)

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFileName(filename[0])
        printer.setOutputFormat(QPrinter.PdfFormat)

        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        outputSize = settings.outputSize()
        printer.setPaperSize(QSizeF(outputSize * 25.4 / settings.outputDpi()), QPrinter.Millimeter)
        printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
        printer.setResolution(settings.outputDpi())

        dest_painter = QPainter(printer)

        render_job = QgsMapRendererCustomPainterJob(settings, dest_painter)
        render_job.prepare()
        render_job.renderPrepared()

        context = QgsRenderContext.fromMapSettings(settings)
        context.setPainter(dest_painter)

        option = QStyleOptionGraphicsItem()
        option.initFrom(self.iface.mapCanvas())

        dest_painter.begin(printer)

        for canvas_item in self.iface.mapCanvas().items():
            if isinstance(canvas_item, BuildingTemplateItem):
                dest_painter.save()
                itemScenePos = canvas_item.scenePos()
                dest_painter.translate(itemScenePos.x(), itemScenePos.y())
                canvas_item.paint(dest_painter, option)
                dest_painter.restore()

        dest_painter.end()

        del dest_painter
        del printer

        url = QUrl.fromLocalFile(filename[0])
        path = QDir.toNativeSeparators(filename[0])
        self.iface.messageBar().pushMessage("Als PDF Speichern",
                                            f"Kartenausschnitt erfolgreich unter <a href=\"{url}\">{path}</a> gespeichert",
                                            level=Qgis.Success)

    def add_config_content_action(self):
        """Add the new action to the identify menu"""

        xp_icon = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gui/resources/xplanung_icon.png'))
        action = [a for a in self.iface.attributesToolBar().actions() if a.objectName() == 'mActionIdentify'][0]
        # action.triggered.disconnect()

        action.trigger()
        self.tool = self.iface.mapCanvas().mapTool()

        menu = self.tool.identifyMenu()
        xp_action = QgsMapLayerAction("Als Planinhalt konfigurieren", menu, QgsMapLayerType.VectorLayer,
                                      QgsMapLayerAction.SingleFeature, QIcon(xp_icon))
        xp_action.triggeredForFeature.connect(self.onActionTriggered)
        menu.addCustomAction(xp_action)

        self.iface.actionPan().trigger()

    def onActionTriggered(self, layer, feat):
        full_version_required_warning()

    def onProjectLoaded(self):
        logger.debug('project loaded')
        layers = QgsProject.instance().layerTreeRoot().findGroups(recursive=True)
        for group in layers:
            if not isinstance(group, QgsLayerTreeGroup) or 'xplanung_id' not in group.customProperties():
                continue

            try:
                for tree_layer in group.findLayers():
                    if isinstance(tree_layer.layer(), QgsAnnotationLayer):
                        QgsProject().instance().removeMapLayer(tree_layer.layer())
                        continue
                    MapLayerRegistry().addLayer(tree_layer.layer(), add_to_legend=False)
                load_on_canvas(group.customProperty('xplanung_id'), layer_group=group)
            except Exception as e:
                logger.exception(e)

    def onRowsInserted(self, parent, first, last):
        model = self.iface.layerTreeView().layerTreeModel()
        index = model.index(first, 0, parent)
        node = model.index2node(index)

        if not isinstance(node, QgsLayerTreeGroup) or 'xplanung_id' not in node.customProperties():
            return

        if not self.iface.layerTreeView().indicators(node):
            xp_indicator, reload_indicator = createXPlanungIndicators()
            plan_xid = node.customProperty('xplanung_id')
            reload_indicator.clicked.connect(lambda i, p=plan_xid: plan_to_map(p))

            self.iface.layerTreeView().addIndicator(node, xp_indicator)
            self.iface.layerTreeView().addIndicator(node, reload_indicator)

    def is_valid_db(self) -> bool:
        result, meta = verify_db_connection()
        if result:
            return True

        msg_box = QMessageBox()
        msg_box.setWindowTitle('Inkompatiblität mit der Datenbank')
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(meta.error)
        settings_button = msg_box.addButton('Einstellungen', QMessageBox.YesRole)
        msg_box.addButton(QMessageBox.Cancel)
        msg_box.setEscapeButton(QMessageBox.Cancel)
        msg_box.exec()
        if msg_box.clickedButton() == settings_button:
            db_page = self.settings.navigate_to_page(DatabaseConfigPage)
            if db_page:
                db_page.setupData()
                asyncio.create_task(db_page.test_connection())
            self.settings.exec()
        return False
