import asyncio
import logging
import os

import qasync

from qgis.core import Qgis
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtGui import QIcon, QCursor, QKeySequence
from qgis.PyQt.QtCore import Qt, pyqtSlot, QItemSelectionModel, QUrl, QDir
from qgis.PyQt.QtWidgets import QAbstractItemView, QApplication
from qgis.gui import QgsDockWidget
from qgis.utils import iface

from SAGisXPlanung import compile_ui_file
from SAGisXPlanung.core.converter_tasks import import_plan, export_action, ActionCanceledException
from SAGisXPlanung.Tools.ContextMenuTool import ContextMenuTool
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.nexus_dialog import NexusDialog
from SAGisXPlanung.gui.style import with_color_palette, ApplicationColor, apply_color
from SAGisXPlanung.gui.widgets import QBuildingTemplateEdit
from SAGisXPlanung.gui.widgets.QExplorerView import XID_ROLE
from SAGisXPlanung.utils import CLASSES
from SAGisXPlanung.gui.XPCreatePlanDialog import XPCreatePlanDialog
from SAGisXPlanung.gui.XPPlanDetailsDialog import XPPlanDetailsDialog
# don't remove following dependency, it is needed for promoting a ComboBox to QPlanComboBox via qt designer
from SAGisXPlanung.gui.widgets.QPlanComboBox import QPlanComboBox

uifile = os.path.join(os.path.dirname(__file__), '../ui/XPlanung_dialog_base.ui')
FORM_CLASS = compile_ui_file(uifile)

logger = logging.getLogger(__name__)


class XPlanungDialog(QgsDockWidget, FORM_CLASS):
    """
    Hauptdialog der Anwendung.
    """

    def __init__(self, parent=None):
        super(XPlanungDialog, self).__init__(parent)
        self.setupUi(self)
        self.setAllowedAreas(self.allowedAreas() | Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.iface = iface
        self.export_task = None
        self.import_task = None
        self.nexus_dialog = None

        self.bCreate.clicked.connect(lambda: self.showCreateForm())
        self.bExport.clicked.connect(lambda: self.export())
        self.bImport.clicked.connect(lambda: self.importGML())
        self.bInfo.setIcon(QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources/info.svg'))))
        self.bInfo.clicked.connect(self.openDetails)

        self.identifyTool = ContextMenuTool(self.iface.mapCanvas(), self)
        self.identifyTool.accessAttributesRequested.connect(self.showObjectAttributes)
        self.identifyTool.highlightObjectTreeRequested.connect(self.selectTreeItem)
        self.identifyTool.featureSaved.connect(self.onFeatureSaved)
        self.identifyTool.editBuildingTemplateRequested.connect(self.showTemplateEdit)
        self.bIdentify.setIcon(QIcon(':/images/themes/default/mActionIdentify.svg'))
        self.bIdentify.clicked.connect(self.onIdentifyClicked)
        self.bIdentify_shortcut = QtWidgets.QShortcut(QKeySequence(Qt.ALT | Qt.Key_Q), self)
        self.bIdentify_shortcut.activated.connect(lambda: self.bIdentify.click())
        self.iface.mapCanvas().mapToolSet.connect(self.onMapToolChanged)

        self.details_dialog = XPPlanDetailsDialog(parent=iface.mainWindow())
        self.details_dialog.planDeleted.connect(self.cbPlaene.refresh)
        self.details_dialog.nameChanged.connect(self.onPlanNameChanged)

        self.progress_widget.setVisible(False)

        self.opened.connect(self.onOpened)
        self.closed.connect(self.onClosed)
        self.cbPlaene.currentIndexChanged.connect(self.onIndexChanged)

        self.fwImportPath.fileChanged.connect(lambda file_path: self.bImport.setEnabled(bool(file_path)))

        self.button_show_all.clicked.connect(self.on_show_all_clicked)

        with_color_palette(self, [
            ApplicationColor.Secondary
        ], class_='QPushButton')
        apply_color(self.button_show_all, ApplicationColor.Secondary)

    def __del__(self):
        try:
            self.iface.mapCanvas().mapToolSet.disconnect(self.onMapToolChanged)
        except TypeError:
            pass

    def selectedPlan(self):
        return self.cbPlaene.currentPlanId()

    @qasync.asyncSlot()
    async def onOpened(self):
        # TODO: maybe disconnect slot after first call
        await self.onIndexChanged(self.cbPlaene.currentIndex())

    def onClosed(self):
        self.details_dialog.hide()

    @qasync.asyncSlot(int)
    async def onIndexChanged(self, i):
        self.bExport.setEnabled(False)
        self.bInfo.setEnabled(False)
        if i != -1:
            xid = self.cbPlaene.currentPlanId()
            await self.details_dialog.initPlanData(xid)
        else:
            self.details_dialog.hide()

        self.bInfo.setDisabled(i == -1)
        self.bExport.setDisabled(i == -1)

    @qasync.asyncSlot(str, str)
    async def onPlanNameChanged(self, xid: str, updated_name: str):
        self.cbPlaene.setPlanName(xid, updated_name)

    def onIdentifyClicked(self, checked: bool):
        if checked:
            self.iface.mapCanvas().setMapTool(self.identifyTool)
        elif self.iface.mapCanvas().mapTool() == self.identifyTool:
            self.iface.mapCanvas().unsetMapTool(self.identifyTool)

    def onMapToolChanged(self, new_tool, old_tool):
        if old_tool == self.identifyTool and self.bIdentify.isChecked():
            self.bIdentify.setChecked(False)

    def on_show_all_clicked(self, checked: bool):
        # Check if a NexusDialog instance is already created and visible
        if self.nexus_dialog is not None and self.nexus_dialog.isVisible():
            self.nexus_dialog.deleteLater()

        self.nexus_dialog = NexusDialog(self)
        self.nexus_dialog.accessAttributesRequested.connect(self.showObjectAttributes)
        self.nexus_dialog.deletionOccurred.connect(self.cbPlaene.refresh)
        self.nexus_dialog.show()

    def showCreateForm(self):
        """
        Startet den Dialog zum Erstellen eines neuen Planinhalts aus dem augewählten Layer.
        """

        def _show_dialog(d):
            d.finished.connect(lambda: self.cbPlaene.refresh())
            d.show()

        if self.rbBPlan.isChecked():
            _show_dialog(XPCreatePlanDialog(iface, CLASSES['BP_Plan']))
        elif self.rbFPlan.isChecked():
            _show_dialog(XPCreatePlanDialog(iface, CLASSES['FP_Plan']))
        elif self.rbRPlan.isChecked():
            _show_dialog(XPCreatePlanDialog(iface, CLASSES['RP_Plan']))
        elif self.rbLPlan.isChecked():
            _show_dialog(XPCreatePlanDialog(iface, CLASSES['LP_Plan']))
        else:
            self.iface.messageBar().pushMessage("XPlanung Fehler", "Keine Planart ausgewählt",
                                                level=Qgis.Warning)

    @qasync.asyncSlot()
    async def export(self):
        """
        Wandelt einen in der ComboBox gewählten Planinhalt in ein XPlanGML-Dokument um.
        Nutzt die aktive PostgreSQL-Verbindung die über das XPlanung-Einstellungsmenü konfiguriert wurde.
        """
        self.bExport.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.bExport.repaint()

        try:
            plan_xid = str(self.cbPlaene.currentPlanId())
            out_file_format = "gml" if self.rbGML.isChecked() else "zip"

            file_name = await export_action(self, plan_xid, out_file_format)

            url = QUrl.fromLocalFile(file_name)
            path = QDir.toNativeSeparators(file_name)
            iface.messageBar().pushMessage("XPlanung", f"Planwerk erfolgreich exportiert! <a href=\"{url}\">{path}</a>",
                                           level=Qgis.Success)
        except ActionCanceledException:
            pass
        except Exception as e:
            logger.exception(e)
            iface.messageBar().pushMessage("XPlanung Fehler", "XPlanGML-Dokument konnte nicht umgewandelt werden!",
                                           str(e), level=Qgis.Critical)

        finally:
            self.bExport.setEnabled(True)
            QtWidgets.QApplication.restoreOverrideCursor()

    @qasync.asyncSlot()
    async def importGML(self):
        """
        Wandelt ein XPlanGML-Dokument in einen PostgreSQL-Datensatz um.
        Nutzt die aktive PostgreSQL-Verbindung die über das XPLanung-Einstellungsmenü konfiguriert wurde.
        """
        filepath = self.fwImportPath.filePath()
        if not filepath:
            self.iface.messageBar().pushMessage("XPlanung Fehler", "Kein Pfad zur XPlanGML-Datei angegeben",
                                                level=Qgis.Critical)
            return

        self.bImport.setEnabled(False)
        QtWidgets.QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.bImport.repaint()
        self.progress_widget.setVisible(True)

        try:
            loop = asyncio.get_running_loop()
            plan_name = await loop.run_in_executor(None, import_plan, filepath, self.import_progress)

            self.fwImportPath.setFilePath("")
            self.cbPlaene.refresh()
            iface.messageBar().pushMessage("XPlanung", f"Planwerk {plan_name} erfolgreich importiert!",
                                           level=Qgis.Success)

        except Exception as e:
            logger.exception(e)
            iface.messageBar().pushMessage("XPlanung Fehler", "XPlanGML-Dokument konnte nicht importiert werden!",
                                           str(e), level=Qgis.Critical)

        finally:
            self.bImport.setEnabled(True)
            QtWidgets.QApplication.restoreOverrideCursor()
            self.progress_widget.setVisible(False)

    def import_progress(self, progress):
        self.progress_label.setText(f'{progress[0]}/{progress[1]}')

    @pyqtSlot()
    def openDetails(self):
        self.details_dialog.show()
        self.details_dialog.setUserVisible(True)

    @qasync.asyncSlot(XPlanungItem)
    async def showObjectAttributes(self, xplan_item: XPlanungItem):
        await self.selectTreeItem(xplan_item)

        # open attributes page
        self.details_dialog.stackedWidget.setCurrentIndex(0)
        self.details_dialog.showAttributesPage()
        self.openDetails()

    @qasync.asyncSlot(XPlanungItem)
    async def selectTreeItem(self, xplan_item: XPlanungItem):
        # setup details page, if not already present
        if self.details_dialog.plan_xid != xplan_item.plan_xid:
            await self.details_dialog.initPlanData(xplan_item.plan_xid)

        # find object
        proxy_model = self.details_dialog.objectTree.proxy
        index_list = proxy_model.match(proxy_model.index(0, 0), XID_ROLE, xplan_item.xid, -1,
                                       Qt.MatchWildcard | Qt.MatchRecursive)
        if not index_list:
            return

        selection_model = self.details_dialog.objectTree.selectionModel()
        selection_model.select(index_list[0], QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

        self.details_dialog.objectTree.scrollTo(index_list[0], QAbstractItemView.PositionAtCenter)

    @qasync.asyncSlot(XPlanungItem)
    async def onFeatureSaved(self, xplan_item: XPlanungItem):
        # details window of plan is not currently open
        if self.details_dialog.plan_xid != xplan_item.plan_xid:
            return

        # parent is either specific parent item or bereich, or plan (if adding a bereich object)
        parent_id = xplan_item.parent_xid or xplan_item.bereich_xid or xplan_item.plan_xid

        # find parent, to add object
        model = self.details_dialog.objectTree.model
        index_list = model.match(model.index(0, 0), XID_ROLE, parent_id, -1, Qt.MatchWildcard | Qt.MatchRecursive)

        if not index_list:
            return

        await self.details_dialog.addExplorerItem(model.itemAtIndex(index_list[0]), xplan_item)

    @qasync.asyncSlot(QBuildingTemplateEdit)
    async def showTemplateEdit(self, edit_widget: QBuildingTemplateEdit):
        self.details_dialog.insertWidgetIntoNewPage(edit_widget)
        self.openDetails()
