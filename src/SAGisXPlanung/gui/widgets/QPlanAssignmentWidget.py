import logging
import uuid

from qgis.core import QgsGeometry
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from sqlalchemy.orm import load_only

from SAGisXPlanung import Session
from SAGisXPlanung.XPlan.enums import XP_BedeutungenBereich
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.widgets.QPlanComboBox import QPlanComboBox
from SAGisXPlanung.gui.widgets.QXPlanInputElement import QComboBoxNoScroll

logger = logging.getLogger(__name__)


class QPlanAssignmentWidget(QtWidgets.QGroupBox):
    """ Widget zur Auswahl eines Plans und zugehörigen Bereich """

    addedBereich = pyqtSignal(XPlanungItem)
    planChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QPlanAssignmentWidget, self).__init__(*args, **kwargs)

        self.selectedPlan = None
        self.plan_id = None
        self.plan_cls_type = None
        self.bereich_ids = []
        self.geom = None

        self.setTitle('Zuordnung zu einem erfassten Plan')
        self.verticalLayout = QtWidgets.QVBoxLayout()

        self.hl1 = QtWidgets.QHBoxLayout()
        label1 = QtWidgets.QLabel('Plan')
        label1.setFixedWidth(60)
        self.cbPlaene = QPlanComboBox()
        self.cbPlaene.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.hl1.addWidget(label1)
        self.hl1.addWidget(self.cbPlaene)

        self.hl2 = QtWidgets.QHBoxLayout()
        label2 = QtWidgets.QLabel('Bereich')
        label2.setFixedWidth(60)
        self.cbBereich = QComboBoxNoScroll()
        self.cbBereich.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.hl2.addWidget(label2)
        self.hl2.addWidget(self.cbBereich)

        self.verticalLayout.addLayout(self.hl1)
        self.verticalLayout.addLayout(self.hl2)

        self.setLayout(self.verticalLayout)

        self.cbPlaene.currentIndexChanged.connect(lambda i: self.onPlanChanged(i))
        if self.cbPlaene.currentIndex() != -1:
            self.onPlanChanged(self.cbPlaene.currentIndex())

    def setCurrentSelection(self, xid: str):
        self.cbPlaene.setCurrentPlan(xid)

    def onPlanChanged(self, i):
        self.validate_geometry()
        with Session.begin() as session:
            self.selectedPlan = session.query(XP_Plan).options(
                load_only('id'),
            ).get(self.cbPlaene.currentPlanId())
            names = [f'Bereich {bereich.nummer} - {bereich.name}' for bereich in self.selectedPlan.bereich]
            self.bereich_ids = [bereich.id for bereich in self.selectedPlan.bereich]
            self.plan_id = self.selectedPlan.id
            self.plan_cls_type = self.selectedPlan.__class__

        self.cbBereich.clear()
        self.cbBereich.addItems(names)

        self.planChanged.emit()

    def bereich_id(self):
        return self.bereich_ids[self.cbBereich.currentIndex()]

    def removeErrorMessage(self):
        if self.verticalLayout.count() < 3:
            return
        item = self.verticalLayout.takeAt(2)
        while item.count():
            child = item.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def validate_geometry(self, geom: QgsGeometry = None):
        if not geom and not self.geom:
            return
        elif geom:
            self.geom = geom

        with Session.begin() as session:
            plan: XP_Plan = session.query(XP_Plan).get(self.cbPlaene.currentPlanId())
            valid = self.geom.within(plan.geometry())

            self.removeErrorMessage()
            if valid:
                return

            hbox = QHBoxLayout()
            hbox.addItem((QSpacerItem(70, 10, QSizePolicy.Fixed, QSizePolicy.Expanding)))
            label = QLabel('Ausgewählte Geometrie liegt nicht im Geltungsbereich des gewählten Planwerks!')
            label.setStyleSheet("color: #F59E0B")
            hbox.addWidget(label)
            self.verticalLayout.addLayout(hbox)

    def validate_assignment(self):
        if self.cbBereich.currentIndex() != -1:
            return True

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)

        msg.setText(f"Das ausgewählte Planwerk enthält keinen Bereich. Soll ein Standardbereich automatisch erstellt"
                    f"werden, um die Zuordnung auszuführen?")
        msg.setWindowTitle("Fehlender XP_Bereich")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        ret = msg.exec_()
        if ret == QtWidgets.QMessageBox.No:
            return False

        self.addDefaultXP_Bereich()
        return True

    def addDefaultXP_Bereich(self):
        with Session.begin() as session:
            self.selectedPlan = session.query(XP_Plan).get(self.cbPlaene.currentPlanId())
            cls_type = getattr(self.selectedPlan.__class__, 'bereich').property.entity.class_
            bereich_obj = cls_type()
            bereich_obj.id = uuid.uuid4()
            bereich_obj.name = 'Geltungsbereich'
            bereich_obj.nummer = '0'
            bereich_obj.bedeutung = XP_BedeutungenBereich.Teilbereich
            bereich_obj.geltungsbereich = self.selectedPlan.raeumlicherGeltungsbereich
            self.selectedPlan.bereich.append(bereich_obj)

            self.bereich_ids.append(bereich_obj.id)
            self.cbBereich.addItems([f'Bereich {bereich_obj.nummer} - {bereich_obj.name}'])
            self.cbBereich.setCurrentIndex(0)

            self.addedBereich.emit(XPlanungItem(xid=str(bereich_obj.id), xtype=cls_type,
                                                plan_xid=str(self.cbPlaene.currentPlanId())))


