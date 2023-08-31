import logging

from qgis.PyQt.QtGui import QPaintEvent
from qgis.PyQt.QtWidgets import QStyleOptionComboBox, QStylePainter, QStyle, QComboBox
from qgis.PyQt.QtCore import Qt
from sqlalchemy.orm import load_only

from SAGisXPlanung import Session
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.gui.widgets.QXPlanInputElement import QComboBoxNoScroll

logger = logging.getLogger(__name__)


class QPlanComboBox(QComboBoxNoScroll):
    """ Combobox zur Auswahl eines in der Datenbank erfassten Plans """
    def __init__(self, *args, **kwargs):
        super(QPlanComboBox, self).__init__(*args, **kwargs)

        self.setMinimumContentsLength(20)
        self.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)

        self.refresh()

    def refresh(self):
        """ Aktualisiert die Combobox mit den aktuell gespeicherten Plänen """
        try:
            self.clear()
            with Session.begin() as session:
                plans = session.query(XP_Plan).options(
                    load_only(XP_Plan.id, XP_Plan.name, XP_Plan.type)
                ).order_by(XP_Plan.name).all()
                for plan in plans:
                    self.addItem(f'{plan.name} ({plan.type})', str(plan.id))
        except Exception as e:
            logger.exception(e)

    def setCurrentPlan(self, xid: str):
        index = self.findData(xid)
        if index >= 0:
            self.setCurrentIndex(index)

    def setPlanName(self, xid: str, name: str):
        index = self.findData(xid)
        if index >= 0:
            prev_name = self.itemText(index)
            self.setItemText(index, f'{name} {prev_name[prev_name.find("("):]}')

    def currentPlanId(self):
        return self.currentData()

    def paintEvent(self, e: QPaintEvent):
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        p = QStylePainter(self)
        p.drawComplexControl(QStyle.CC_ComboBox, opt)

        text_rect = self.style().subControlRect(QStyle.CC_ComboBox, opt, QStyle.SC_ComboBoxEditField)
        opt.currentText = p.fontMetrics().elidedText(opt.currentText, Qt.ElideRight, text_rect.width())
        p.drawControl(QStyle.CE_ComboBoxLabel, opt)