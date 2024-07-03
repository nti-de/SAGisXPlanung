import asyncio
import logging
import os

import qasync
from qgis.PyQt import QtGui, QtCore, QtWidgets, uic
from qgis.core import Qgis

from SAGisXPlanung.gui.widgets.QXPlanTabWidget import QXPlanTabWidget
from SAGisXPlanung.utils import save_to_db_async

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/XPlanung_create.ui'))
logger = logging.getLogger(__name__)


class XPCreatePlanDialog(QtWidgets.QDialog, FORM_CLASS):

    contentSaved = QtCore.pyqtSignal()

    def __init__(self, iface, cls_type, parent_type=None, parent=None):
        super(XPCreatePlanDialog, self).__init__(parent=iface.mainWindow())
        self.setupUi(self)
        self.class_type = cls_type
        self.parent_type = parent_type

        self.setWindowTitle(f"Neues {self.class_type.__name__}-Objekt anlegen")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.buttons_hbox = QtWidgets.QHBoxLayout()
        self.b_create = QtWidgets.QPushButton(f"{self.class_type.__name__} erstellen")
        self.b_create.clicked.connect(self.createObject)
        self.b_cancel = QtWidgets.QPushButton("Abbrechen")
        self.b_cancel.clicked.connect(lambda: self.reject())
        self.buttons_hbox.addWidget(self.b_create)
        self.buttons_hbox.addWidget(self.b_cancel)
        self.buttons_hbox.setContentsMargins(0, 10, 0, 10)
        self.vbox.addLayout(self.buttons_hbox)

        self.content = self.class_type()
        self.iface = iface

        self.tabs = QXPlanTabWidget(self.class_type, parent_type=self.parent_type)
        self.vbox.insertWidget(0, self.tabs)

    @qasync.asyncSlot()
    async def createObject(self):
        try:
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))

            self.content = self.tabs.populateContent()
            if not self.content:
                return

            await save_to_db_async(self.content)

            self.iface.messageBar().pushMessage("XPlanung", "Datensatz wurde gespeichert", level=Qgis.Success)
            self.contentSaved.emit()
            self.accept()

        except Exception as e:
            logger.exception(f"error {e}")
            self.iface.messageBar().pushMessage("XPlanung Fehler", "Datensatz konnte nicht gespeichert werden!",
                                                str(e), level=Qgis.Critical)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
