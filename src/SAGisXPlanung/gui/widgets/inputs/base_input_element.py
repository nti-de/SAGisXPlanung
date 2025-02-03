from abc import ABC, abstractmethod

from qgis.PyQt.QtCore import Qt, QObject
from qgis.PyQt.QtWidgets import QLabel, QWidget, QVBoxLayout


class BaseInputElement(ABC):
    """ Abstrakte Basisklasse für alle Eingabeformulare.
        Mit der Factory-Methode `create` kann ein zum Datentyp passendes Eingabefeld genereriert werden"""

    background_widget = None
    invalid = False
    error_message = None

    @abstractmethod
    def value(self):
        pass

    @abstractmethod
    def setDefault(self, default):
        pass

    @abstractmethod
    def validate_widget(self, required):
        pass

    def setInvalid(self, set_invalid):
        if set_invalid:
            self.insert_background_widget()
            self.invalid = True
        else:
            self.remove_background_widget()
            self.invalid = False

    def error_message_label(self) -> QLabel:
        error_label = QLabel(self.error_message)
        error_label.setWordWrap(True)
        error_label.setStyleSheet("font-weight: bold; font-size: 7pt; color: #991B1B")
        return error_label

    def insert_background_widget(self):
        if self.invalid:
            return

        self.background_widget = QWidget()
        parent = self.parentWidget().layout()
        parent.replaceWidget(self, self.background_widget)

        vbox = QVBoxLayout()
        vbox.setSpacing(3)
        vbox.addWidget(self)
        if self.error_message:
            vbox.addWidget(self.error_message_label())

        self.background_widget.setLayout(vbox)
        self.background_widget.setObjectName("back")
        self.background_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.background_widget.layout().setContentsMargins(5, 5, 5, 5)
        self.background_widget.setStyleSheet(
            'QWidget#back {background-color: #ffb0b0; border: 1px solid red; border-radius: 3px;}')

    def remove_background_widget(self):
        if not self.invalid:
            return

        layout = self.parentWidget().parentWidget().layout()
        layout.replaceWidget(self.background_widget, self)
        self.background_widget.deleteLater()
        self.error_message = None
        self.setFocus()

    @staticmethod
    def create(field_type, parent=None) -> 'BaseInputElement':
        from SAGisXPlanung.gui.widgets.inputs.widget_factory import create_widget
        return create_widget(field_type, parent)


class XPlanungInputMeta(type(QObject), type(BaseInputElement)):
    # workaround for mixin in abstract base class together with QObject
    # https://stackoverflow.com/questions/28720217/multiple-inheritance-metaclass-conflict
    pass
