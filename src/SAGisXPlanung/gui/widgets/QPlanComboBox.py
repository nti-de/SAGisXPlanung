import logging
import re

from qgis.PyQt.QtGui import QPaintEvent
from qgis.PyQt.QtWidgets import QStyleOptionComboBox, QStylePainter, QStyle, QComboBox
from qgis.PyQt.QtCore import Qt
from sqlalchemy.orm import load_only

from SAGisXPlanung import Session
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.gui.widgets.commons import GenericPicker, PickerItem

logger = logging.getLogger(__name__)


class QPlanComboBox(GenericPicker):
    def __init__(self, *args, **kwargs):
        super(QPlanComboBox, self).__init__(*args, **kwargs)

        self.setPlaceholderText('Keine Pläne verfügbar...')
        self.add_category("BP_Plan", "BP_Plan")
        self.add_category("FP_Plan", "FP_Plan")
        self.add_category("LP_Plan", "LP_Plan")
        self.add_category("RP_Plan", "RP_Plan")
        self.refresh()

    def refresh(self):
        try:
            self.clear()
            with Session.begin() as session:
                plans = session.query(XP_Plan).options(
                    load_only(XP_Plan.id, XP_Plan.name, XP_Plan.type)
                ).all()
                picker_items = []
                for plan in plans:
                    picker_item = PickerItem(
                        id=str(plan.id),
                        text=plan.name,
                        category=plan.__class__.__name__,
                        search_terms=tuple(
                            search_val
                            for obj in plan.gemeinde
                            for search_val in (obj.gemeindeName, obj.ortsteilName)
                        )
                    )
                    picker_items.append(picker_item)
                self.set_picker_items(picker_items)
        except Exception as e:
            logger.exception(e)

    def set_current_plan(self, xid: str):
        index = self.findData(xid)
        if index >= 0:
            self.setCurrentIndex(index)

    def current_plan_id(self):
        return self.currentData()
