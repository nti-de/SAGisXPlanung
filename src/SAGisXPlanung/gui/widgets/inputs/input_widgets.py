import os
import re
import sys
import datetime
from pathlib import Path

from qgis.PyQt.QtWidgets import (QLineEdit, QComboBox, QRadioButton, QTextEdit, QToolButton, QWidget,
                                 QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QPushButton, QButtonGroup)
from qgis.PyQt.QtCore import Qt, QDate, pyqtSlot, QEvent, QSize
from qgis.gui import QgsCheckableComboBox, QgsFileWidget, QgsDateEdit

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.gui.style import load_svg
from SAGisXPlanung.gui.widgets.inputs.base_input_element import BaseInputElement, XPlanungInputMeta
from SAGisXPlanung.utils import is_url
from SAGisXPlanung.XPlan.types import Angle, Length, Volume, Area, Scale, Sound

PYQT_DEFAULT_DATE = datetime.date(1752, 9, 14)


class LineEditMixin:

    def setInvalid(self, set_invalid):
        super(LineEditMixin, self).setInvalid(set_invalid)
        if set_invalid:
            self.textChanged.connect(self.onControlEdited)
        else:
            self.textChanged.disconnect(self.onControlEdited)

    @pyqtSlot(str)
    def onControlEdited(self, text):
        self.setInvalid(False)


class QStringInput(LineEditMixin, BaseInputElement, QLineEdit, metaclass=XPlanungInputMeta):

    def __init__(self, regex=None, validation_error=None, *args, **kwargs):
        super(QStringInput, self).__init__(*args, **kwargs)
        self.regex = regex
        self.validation_error = validation_error

    def value(self):
        return self.text() or None

    def setDefault(self, default):
        self.setText(default)

    def validate_widget(self, required):
        if required and not bool(self.text()):
            return False
        if self.regex and bool(self.text()) and not bool(re.match(self.regex, self.text())):
            self.error_message = self.validation_error
            return False
        return True


class QFloatInput(LineEditMixin, BaseInputElement, QLineEdit, metaclass=XPlanungInputMeta):

    def __init__(self, *args, **kwargs):
        super(QFloatInput, self).__init__(*args, **kwargs)

    def _normalized_text(self):
        text = self.text().strip()
        return text.replace(',', '.') if text else text

    def value(self):
        text = self._normalized_text()
        if not text:
            return None
        return float(text)

    def setDefault(self, default):
        self.setText('' if default is None else str(default))

    def validate_widget(self, required):
        text = self._normalized_text()
        if required and not text:
            return False
        if not text:
            return True

        try:
            float(text)
            return True
        except ValueError:
            self.error_message = 'Feld erwartet eine Zahl'
            return False


class QIntegerInput(LineEditMixin, BaseInputElement, QLineEdit, metaclass=XPlanungInputMeta):

    def __init__(self, *args, **kwargs):
        super(QIntegerInput, self).__init__(*args, **kwargs)

    def value(self):
        return int(self.text()) if self.text() else None

    def setDefault(self, default):
        self.setText('' if default is None else str(default))

    def validate_widget(self, required):
        text = self.text().strip()
        if required and not text:
            return False
        if not text:
            return True

        try:
            int(text)
            return True
        except ValueError:
            self.error_message = 'Feld erwartet einen ganzzahligen Wert'
            return False


class QBooleanInput(BaseInputElement, QWidget, metaclass=XPlanungInputMeta):

    def __init__(self, *args, **kwargs):
        super(QBooleanInput, self).__init__(*args, **kwargs)

        self.layout = QHBoxLayout()
        self.option_yes = QRadioButton('Ja')
        self.option_no = QRadioButton('Nein')
        self.option_yes.toggled.connect(self.onRadioButtonToggle)
        self.option_no.toggled.connect(self.onRadioButtonToggle)
        self.clear_button = QPushButton('Auswahl entfernen')
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.clicked.connect(self.clearSelection)
        self.clear_button.hide()
        self.clear_button.setStyleSheet('''
            QPushButton { 
                color: #64748b; 
                background: palette(window); 
                border: 0px; 
            } 
            QPushButton:hover {
                color: #334155;
            }''')

        self.layout.addWidget(self.option_yes)
        self.layout.addWidget(self.option_no)
        self.layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.layout.addWidget(self.clear_button)
        self.group = QButtonGroup()
        self.group.addButton(self.option_yes)
        self.group.addButton(self.option_no)

        self.setLayout(self.layout)

    @pyqtSlot(bool)
    def clearSelection(self, checked):
        self.clear_button.hide()
        # workaround for de-selecting radio buttons using QButtonGroup
        # https://stackoverflow.com/questions/8689909/uncheck-radiobutton-pyqt4
        self.group.setExclusive(False)
        self.option_yes.setChecked(False)
        self.option_no.setChecked(False)
        self.group.setExclusive(True)

    @pyqtSlot(bool)
    def onRadioButtonToggle(self, checked):
        if checked:
            self.clear_button.show()

    def value(self):
        if self.option_yes.isChecked():
            return True
        if self.option_no.isChecked():
            return False
        return None

    def setDefault(self, default):
        self.option_yes.setChecked(default)
        self.option_no.setChecked(not default)

    def validate_widget(self, required):
        if required and self.value() is None:
            return False
        return True


class QFileInput(BaseInputElement, QgsFileWidget, metaclass=XPlanungInputMeta):

    def __init__(self, *args, **kwargs):
        super(QFileInput, self).__init__(*args, **kwargs)

    def value(self):
        return self.filePath() or None

    def file(self):
        if not os.path.exists(self.filePath()):
            return
        with open(self.filePath(), "rb") as file:
            return file.read()

    def setDefault(self, default):
        self.setFilePath(default)

    def validate_widget(self, required):
        if is_url(self.value()):
            return True
        if os.path.exists(self.filePath()):
            # check for too large files
            file_size = Path(self.value()).stat().st_size
            if file_size/1000000 > 100:
                self.error_message = 'Datei darf nicht größer als 100MB sein'
                return False
            return True
        if not self.value() and not required:
            return True
        self.error_message = 'Feld erwartet eine URL oder einen gültigen Dateipfad'
        return False

    def setInvalid(self, set_invalid):
        super(QFileInput, self).setInvalid(set_invalid)
        if set_invalid:
            self.fileChanged.connect(self.onControlEdited)
        else:
            self.fileChanged.disconnect(self.onControlEdited)

    @pyqtSlot(str)
    def onControlEdited(self, text):
        self.setInvalid(False)
        self.lineEdit().setFocus()


class QTextInput(BaseInputElement, QTextEdit, metaclass=XPlanungInputMeta):

    def __init__(self, *args, **kwargs):
        super(QTextInput, self).__init__(*args, **kwargs)

    def value(self):
        return self.toPlainText() or None

    def setDefault(self, default):
        self.setText(default)

    def validate_widget(self, required):
        return True


class QMeasureTypeInput(LineEditMixin, BaseInputElement, QLineEdit, metaclass=XPlanungInputMeta):

    def __init__(self, measure_type, *args, **kwargs):
        super(QMeasureTypeInput, self).__init__(*args, **kwargs)
        self.measure_type = measure_type

    def value(self):
        if not self.text():
            return None
        if isinstance(self.measure_type, (Scale, Angle)):
            return int(self.text())
        if isinstance(self.measure_type, (Area, Volume, Length, Sound)):
            return float(self.text())

    def setDefault(self, default):
        self.setText('' if default is None else str(default))

    def error_message_text(self) -> str:
        if isinstance(self.measure_type, Angle):
            return 'Feld erwartet einen Winkel zwischen 0 und 360'
        if isinstance(self.measure_type, (Area, Volume, Length, Sound)):
            return f'Feld erwartet eine positive Zahl ({self.measure_type.UOM})'
        if isinstance(self.measure_type, Scale):
            return 'Feld erwartet eine Prozentwert zwischen 0 und 100'

    def validate_widget(self, required):
        try:
            if not self.value() and not required:
                return True
            if isinstance(self.measure_type, Angle) and 0 <= int(self.value()) <= 360:
                return True
            elif isinstance(self.measure_type, (Area, Volume, Length, Sound)) and 0 <= float(self.value()) <= sys.float_info.max:
                return True
            elif isinstance(self.measure_type, Scale) and 0 <= int(self.value()) <= 100:
                return True
            raise ValueError
        except (ValueError, TypeError):
            self.error_message = self.error_message_text()
            return False


class QMultiInputWidget(BaseInputElement, QWidget, metaclass=XPlanungInputMeta):
    def __init__(self, input_type='date', placeholder_text='', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.inputs = []
        self.input_type = input_type

        self.plus_icon_path = os.path.abspath(os.path.join(BASE_DIR, 'gui/resources/plus.svg'))
        self.minus_icon_path = os.path.abspath(os.path.join(BASE_DIR, 'gui/resources/minus.svg'))

        # First input field
        self.first_input = self.create_input_field(placeholder_text)

        # Add button
        self.add_button = self.create_button(self.plus_icon_path, "Add another field", self.add_input)

        # Initial layout
        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.first_input)
        hbox.addWidget(self.add_button)
        self.layout.addLayout(hbox)
        self.inputs.append(hbox)

        self.setLayout(self.layout)

    def create_input_field(self, placeholder_text):
        raise NotImplementedError()

    def create_button(self, icon_path, tooltip, callback):
        """Create a styled button."""
        button = QToolButton()
        button.setIcon(load_svg(icon_path))
        button.installEventFilter(self)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tooltip)
        button.clicked.connect(callback)
        button.setStyleSheet("QToolButton { background: palette(window); border: 0px; }")
        return button

    def add_input(self):
        """Add a new input field with a remove button."""
        el = self.create_input_field('')
        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(el)

        remove_button = self.create_button(self.minus_icon_path, "Feld entfernen", self.remove_input)
        hbox.addWidget(remove_button)

        self.inputs.append(hbox)
        self.layout.addLayout(hbox)
        return el

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.HoverEnter:
            obj.setIcon(load_svg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color='#1F2937'))
        elif event.type() == QEvent.Type.HoverLeave:
            obj.setIcon(load_svg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color='#6B7280'))
        return False

    def remove_input(self, checked):
        sender_button = self.sender()
        for layout in self.inputs:
            if sender_button in [layout.itemAt(i).widget() for i in range(layout.count())]:
                self.inputs.remove(layout)
                self.layout.removeItem(layout)
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                return

    def value(self):
        values = []
        for layout in self.inputs:
            widget = layout.itemAt(0).widget()
            v = widget.value()
            if v is None:
                continue
            values.append(v)

        return values or None

    def validate_widget(self, required):
        return True


class QDateListInput(QMultiInputWidget):
    def __init__(self, *args, **kwargs):
        super().__init__('date', *args, **kwargs)

    def create_input_field(self, placeholder_text):
        return QDateEditNoScroll(calendarPopup=True)

    def setDefault(self, default):
        if not default:
            return

        if isinstance(default, str):
            default = [datetime.datetime.strptime(date, "%d.%m.%Y").date() for date in default.split(', ')]
        self.first_input.setDate(default[0])
        for date in default[1:]:
            el = self.add_input()
            el.setDate(date)


class QTextListInput(QMultiInputWidget):
    def __init__(self, *args, **kwargs):
        super().__init__('text', *args, **kwargs)

    def create_input_field(self, placeholder_text):
        line_edit = QStringInput()
        line_edit.setPlaceholderText(placeholder_text)
        return line_edit

    def setDefault(self, default):
        if not default:
            return

        if isinstance(default, str):
            default = default.split(', ')
        self.first_input.setText(default[0])
        for text in default[1:]:
            el = self.add_input()
            el.setText(text)


class QIntegerListInput(QMultiInputWidget):
    def __init__(self, *args, **kwargs):
        super().__init__('integer', *args, **kwargs)

    def create_input_field(self, placeholder_text):
        line_edit = QIntegerInput()
        line_edit.setPlaceholderText(placeholder_text)
        return line_edit

    def setDefault(self, default):
        if not default:
            return

        if isinstance(default, str):
            default = [int(x.strip()) for x in default.split(',') if x.strip()]

        self.first_input.setText(str(default[0]))

        for number in default[1:]:
            el = self.add_input()
            el.setText(str(number))

    def validate_widget(self, required):
        has_value = False

        for layout in self.inputs:
            widget = layout.itemAt(0).widget()
            if not widget.validate_widget(False):
                self.error_message = widget.error_message
                return False

            if widget.value() is not None:
                has_value = True

        if required and not has_value:
            self.error_message = 'Mindestens ein ganzzahliger Wert erforderlich'
            return False

        return True


class QCheckableComboBoxInput(BaseInputElement, QgsCheckableComboBox, metaclass=XPlanungInputMeta):

    def __init__(self, items=None, enum_type=None, *args, **kwargs):
        super(QCheckableComboBoxInput, self).__init__(*args, **kwargs)
        self.enum_type = enum_type
        if items is not None:
            self.addItems(items)

    def value(self):
        if self.enum_type is not None:
            return [self.enum_type[enum_text] for enum_text in self.checkedItems()]
        return self.checkedItems()

    def setDefault(self, default):
        if isinstance(default, list):
            items = list(map(lambda enum: enum.name, default))
        else:
            items = str(default).split(", ")
        self.setCheckedItems(items)

    def validate_widget(self, required):
        if not required:
            return True
        return bool(self.checkedItems())

    def setInvalid(self, set_invalid):
        super(QCheckableComboBoxInput, self).setInvalid(set_invalid)
        if set_invalid:
            self.checkedItemsChanged.connect(self.onControlEdited)
        else:
            self.checkedItemsChanged.disconnect(self.onControlEdited)

    def onControlEdited(self, items):
        self.setInvalid(False)


class QComboBoxNoScroll(BaseInputElement, QComboBox, metaclass=XPlanungInputMeta):
    def __init__(self, scroll_widget=None, items=None, include_default=None, enum_type=None, *args, **kwargs):
        super(QComboBoxNoScroll, self).__init__(*args, **kwargs)
        self.scrollWidget = scroll_widget
        self.include_default = include_default
        self.enum_type = enum_type
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if self.include_default:
            self.addItem('')
            self.setCurrentIndex(0)

        if items is not None:
            self.addItems(items)

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus() or self.scrollWidget is None:
            return super(QComboBoxNoScroll, self).wheelEvent(*args, **kwargs)

        return self.scrollWidget.wheelEvent(*args, **kwargs)

    def value(self):
        if self.include_default and self.currentIndex() == 0:
            return None
        if self.enum_type:
            return self.enum_type[self.currentText()]
        return self.currentText()

    def setDefault(self, default):
        index = self.findText(str(default))
        if index >= 0:
            self.setCurrentIndex(index)

    def validate_widget(self, required):
        return True


class QDateEditNoScroll(BaseInputElement, QgsDateEdit, metaclass=XPlanungInputMeta):

    def __init__(self, scroll_widget=None, *args, **kwargs):
        super(QDateEditNoScroll, self).__init__(*args, **kwargs)
        self.scrollWidget = scroll_widget
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setAllowNull(True)
        self.setNullRepresentation('')
        self.clear()

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus() or self.scrollWidget is None:
            return super(QDateEditNoScroll, self).wheelEvent(*args, **kwargs)

        return self.scrollWidget.wheelEvent(*args, **kwargs)

    def mousePressEvent(self, event):
        self.setDate(QDate.currentDate())
        super(QDateEditNoScroll, self).mousePressEvent(event)

    def value(self):
        if self.isNull():
            return
        date = self.date().toPyDate()
        if date != PYQT_DEFAULT_DATE:
            return date

    def setDefault(self, default):
        self.setDate(default)

    def validate_widget(self, required):
        return True
