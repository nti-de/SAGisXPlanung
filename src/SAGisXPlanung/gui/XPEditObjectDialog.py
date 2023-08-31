import logging

from qgis.PyQt.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox

from SAGisXPlanung import Session
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.widgets.QXPlanTabWidget import QXPlanTabWidget

logger = logging.getLogger(__name__)


class XPEditObjectDialog(QDialog):
    """ Dialog zum Ändern von Attributen eines XPlanung-Objekts. Nur für einfache Objekte ohne Relationen!"""

    def __init__(self, xplan_item: XPlanungItem, parent=None):
        """
        Parameters
        ----------
        xplan_item: str
            XPlanungItem des zu bearbeitenden Objekts
        """
        super(XPEditObjectDialog, self).__init__(parent)
        self.setWindowTitle(f'{xplan_item.xtype.__name__} bearbeiten')

        self.xplan_item = xplan_item
        self.layout = QVBoxLayout(self)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.tab_widget = QXPlanTabWidget(self.xplan_item.xtype)

        # fill original values
        with Session.begin() as session:
            obj = session.query(self.xplan_item.xtype).get(self.xplan_item.xid)
            for label, input_element in self.tab_widget.widget(0).fields.items():
                attribute_value = getattr(obj, label)
                input_element.setDefault(attribute_value)

        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

        self.adjustSize()

    def accept(self):
        content = self.tab_widget.populateContent()
        if not content:
            return

        with Session.begin() as session:
            obj = session.query(self.xplan_item.xtype).get(self.xplan_item.xid)

            # copy over attributes
            for attr in obj.element_order(include_base=False, only_columns=True, export=True):
                setattr(obj, attr, getattr(content, attr))

        super(XPEditObjectDialog, self).accept()