import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

from qgis.PyQt.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
)
from qgis.PyQt.QtCore import Qt, QObject, QEvent


class ValidationTrigger(Enum):
    FOCUS_OUT = auto()
    MANUAL = auto()


@dataclass
class ValidationRule:
    validator: Callable[[str], bool]
    error_message: str
    trigger: ValidationTrigger


class RegexValidator:

    def __init__(self, pattern: str):
        self.regex = re.compile(pattern)

    def __call__(self, text: str) -> bool:
        return bool(self.regex.fullmatch(text))


class ValidationEventFilter(QObject):

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def eventFilter(self, obj, event):

        if event.type() == QEvent.Type.FocusOut:
            self.manager.validate_widget(
                obj,
                ValidationTrigger.FOCUS_OUT
            )

        return False


class ValidationManager:

    def __init__(self):
        self.rules = {}

        self.error_handler = ErrorDisplayHandler()
        self.event_filter = ValidationEventFilter(self)

    def register(
        self,
        widget,
        validator,
        error_message,
        trigger=ValidationTrigger.FOCUS_OUT
    ):
        self.rules[widget] = ValidationRule(
            validator=validator,
            error_message=error_message,
            trigger=trigger
        )

        widget.installEventFilter(self.event_filter)

    def validate_widget(self, widget, trigger=None):

        if widget not in self.rules:
            return True

        rule = self.rules[widget]

        if trigger and trigger != rule.trigger:
            return True

        valid = rule.validator(widget.text())

        if valid:
            self.error_handler.clear_error(widget)
        else:
            self.error_handler.show_error(
                widget,
                rule.error_message
            )

        return valid

    def validate_all(self):

        valid = True

        for widget in self.rules:
            if not self.validate_widget(widget):
                valid = False

        return valid


class ErrorDisplayHandler:

    def __init__(self):
        self._containers = {}

    def show_error(self, widget, message):
        if widget in self._containers:
            return

        parent_layout = widget.parentWidget().layout()

        container = QWidget()
        container.setObjectName("validationWrapper")
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        parent_layout.replaceWidget(widget, container)

        widget.setParent(container)

        layout.addWidget(widget)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("""
            font-weight: bold;
            font-size: 7pt;
            color: #991B1B;
        """)

        layout.addWidget(label)

        container.setStyleSheet("""
            QWidget#validationWrapper {
                background-color: #ffb0b0;
                border: 1px solid red;
                border-radius: 3px;
            }
        """)

        self._containers[widget] = (container, label)

    def clear_error(self, widget):
        if widget not in self._containers:
            return

        container, _label = self._containers.pop(widget)

        parent_layout = container.parentWidget().layout()

        parent_layout.replaceWidget(container, widget)

        widget.setParent(container.parentWidget())

        container.deleteLater()