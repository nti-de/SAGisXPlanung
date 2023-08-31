import datetime
import logging
import os

from qgis.PyQt import QtWidgets, uic, QtCore
from sqlalchemy import Date

from SAGisXPlanung.config import xplan_tooltip
from SAGisXPlanung.gui.widgets.QXPlanInputElement import QXPlanInputElement, QFileInput

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/XPlanung_edit_attribute.ui'))
logger = logging.getLogger(__name__)


class XPEditAttributeDialog(QtWidgets.QDialog, FORM_CLASS):
    """ Dialog zum Ändern des Wertes eines XPlanung-Attributs. Sendet bei Änderung den angepassten Wert
    über das attributeChanged-Signal """

    attributeChanged = QtCore.pyqtSignal(object, object)  # old_value, new_value
    fileChanged = QtCore.pyqtSignal(object)

    def __init__(self, attribute_name, field_type, original_value, parent_xtype, parent=None):
        """
        Parameters
        ----------
        attribute_name: str
            Name des XPlanung-Attributs
        field_type: any
            Spaltentyp, entweder aus sqlalchemy.types oder XPlanung.XPlan.types
        original_value:
            Wert des Attributs vor einer Änderung
        parent_xtype:
            XPlanung-Objektklasse
        """
        super(XPEditAttributeDialog, self).__init__(parent)

        self.parent_xtype = parent_xtype
        self.setupUi(self)
        self.attribute_name = attribute_name
        self.field_type = field_type
        self.original_value = original_value

        self.discard_button = self.buttonBox.button(QtWidgets.QDialogButtonBox.Discard)
        self.discard_button.clicked.connect(lambda s: self.setOriginalValue())

        if isinstance(self.field_type, Date) and self.original_value:
            self.original_value = datetime.datetime.strptime(self.original_value, "%d.%m.%Y")

        self.control: QXPlanInputElement = QXPlanInputElement.create(self.field_type, self)
        self.setOriginalValue()

        self.hl1.addWidget(self.control)

        self.gbAttribute.setTitle(self.attribute_name)
        self.gbAttribute.installEventFilter(self)

        if self.parent_xtype and self.attribute_name:
            tooltip = xplan_tooltip(self.parent_xtype, self.attribute_name)
            self.gbAttribute.setToolTip(tooltip)

    def setOriginalValue(self):
        if self.original_value is not None:
            self.control.setDefault(self.original_value)

    def accept(self):
        if not self.control.validate_widget(False):
            self.control.setInvalid(True)
            return

        value = self.control.value()
        if value != self.original_value:
            self.attributeChanged.emit(self.original_value, value)

        if isinstance(self.control, QFileInput):
            self.fileChanged.emit(self.control.file())

        super(XPEditAttributeDialog, self).accept()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.ToolTip and isinstance(source, QtWidgets.QGroupBox):
            options = QtWidgets.QStyleOptionGroupBox()
            source.initStyleOption(options)
            control = source.style().hitTestComplexControl(QtWidgets.QStyle.CC_GroupBox, options, event.pos())
            if control != QtWidgets.QStyle.SC_GroupBoxLabel and control != QtWidgets.QStyle.SC_GroupBoxCheckBox:
                QtWidgets.QToolTip.hideText()
                return True
        return super().eventFilter(source, event)

