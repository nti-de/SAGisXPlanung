import os
import re
import sys
import datetime
from abc import ABC, abstractmethod
from pathlib import Path

from geoalchemy2 import Geometry
from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter, QColor
from qgis.PyQt.QtWidgets import (QLineEdit, QComboBox, QRadioButton, QTextEdit, QToolButton, QWidget,
                                 QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QPushButton, QButtonGroup, QLabel)
from qgis.PyQt.QtCore import Qt, QDate, QObject, pyqtSlot, QEvent, QSize, QVersionNumber, qVersion
from qgis.gui import QgsCheckableComboBox, QgsFileWidget, QgsDateEdit
from sqlalchemy import ARRAY

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.config import export_version
from SAGisXPlanung.utils import is_url
from SAGisXPlanung.XPlan.types import LargeString, RefURL, Angle, Length, Volume, Area, Scale, XPlanungMeasureType, \
    RegExString, XPEnum

PYQT_DEFAULT_DATE = datetime.date(1752, 9, 14)


class QXPlanInputElement(ABC):
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
            self.background_widget.setStyleSheet(
                'QWidget#back {background-color: #ffb0b0; border: 1px solid red; border-radius: 3px;}')
            self.invalid = True
        else:
            self.remove_background_widget()
            self.background_widget.setStyleSheet('')
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

    def remove_background_widget(self):
        if not self.invalid:
            return

        layout = self.parentWidget().parentWidget().layout()
        layout.replaceWidget(self.background_widget, self)
        self.background_widget.deleteLater()
        self.error_message = None
        self.setFocus()

    @staticmethod
    def create(field_type, parent=None):
        if field_type is None:
            return QStringInput()
        if isinstance(field_type, ARRAY) and hasattr(field_type.item_type, 'enums'):
            version = export_version()
            if hasattr(field_type.item_type.enum_class, 'version'):
                enum_values = [e for e in field_type.item_type.enums if field_type.item_type.enum_class[e].version in [None, version]]
            else:
                enum_values = field_type.item_type.enums
            return QCheckableComboBoxInput(enum_values)
        if hasattr(field_type, 'enums'):
            should_include_default = isinstance(field_type, XPEnum) and field_type.include_default
            version = export_version()
            if hasattr(field_type.enum_class, 'version'):
                enum_values = [e for e in field_type.enums if field_type.enum_class[e].version in [None, version]]
            else:
                enum_values = field_type.enums
            return QComboBoxNoScroll(parent, items=enum_values, include_default=should_include_default)
        if isinstance(field_type, RefURL):
            return QFileInput()
        if isinstance(field_type, LargeString):
            return QTextInput()
        if isinstance(field_type, Geometry):
            from SAGisXPlanung.gui.widgets.QFeatureIdentify import QFeatureIdentify
            return QFeatureIdentify()
        if isinstance(field_type, XPlanungMeasureType):
            return QMeasureTypeInput(field_type)
        if isinstance(field_type, RegExString):
            return QStringInput(field_type.expression, field_type.error_msg)

        if field_type.python_type == datetime.date:
            return QDateEditNoScroll(parent, calendarPopup=True)
        if field_type.python_type == bool:
            return QBooleanInput()
        if field_type.python_type == list and field_type.item_type.python_type == datetime.date:
            return QDateListInput()
        if field_type.python_type == int:
            return QIntegerInput()
        if field_type.python_type == float:
            return QFloatInput()

        return QStringInput()


# workaround for mixin in abstract base class together with QObject
# https://stackoverflow.com/questions/28720217/multiple-inheritance-metaclass-conflict
class XPlanungInputMeta(type(QObject), type(QXPlanInputElement)):
    pass


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


class QStringInput(LineEditMixin, QXPlanInputElement, QLineEdit, metaclass=XPlanungInputMeta):

    def __init__(self, regex=None, validation_error=None):
        super(QStringInput, self).__init__()
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


class QFloatInput(LineEditMixin, QXPlanInputElement, QLineEdit, metaclass=XPlanungInputMeta):

    def value(self):
        return float(self.text()) if self.text() else None

    def setDefault(self, default):
        self.setText('' if default is None else str(default))

    def validate_widget(self, required):
        try:
            if not self.value() and required:
                return False
            return True
        except ValueError:
            self.error_message = 'Feld erwartet eine Zahl'
            return False


class QIntegerInput(LineEditMixin, QXPlanInputElement, QLineEdit, metaclass=XPlanungInputMeta):

    def value(self):
        return int(self.text()) if self.text() else None

    def setDefault(self, default):
        self.setText('' if default is None else str(default))

    def validate_widget(self, required):
        try:
            if not self.value() and required:
                return False
            return True
        except ValueError:
            self.error_message = 'Feld erwartet einen ganzzahligen Wert'
            return False


class QBooleanInput(QXPlanInputElement, QWidget, metaclass=XPlanungInputMeta):

    def __init__(self):
        super(QBooleanInput, self).__init__()
        self.layout = QHBoxLayout()
        self.option_yes = QRadioButton('Ja')
        self.option_no = QRadioButton('Nein')
        self.option_yes.toggled.connect(self.onRadioButtonToggle)
        self.option_no.toggled.connect(self.onRadioButtonToggle)
        self.clear_button = QPushButton('Auswahl entfernen')
        self.clear_button.setCursor(Qt.PointingHandCursor)
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
        self.layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
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


class QFileInput(QXPlanInputElement, QgsFileWidget, metaclass=XPlanungInputMeta):

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


class QTextInput(QXPlanInputElement, QTextEdit, metaclass=XPlanungInputMeta):

    def value(self):
        return self.toPlainText() or None

    def setDefault(self, default):
        self.setText(default)

    def validate_widget(self, required):
        return True


class QMeasureTypeInput(LineEditMixin, QXPlanInputElement, QLineEdit, metaclass=XPlanungInputMeta):

    def __init__(self, measure_type):
        super(QMeasureTypeInput, self).__init__()
        self.measure_type = measure_type

    def value(self):
        if not self.text():
            return None
        if isinstance(self.measure_type, (Scale, Angle)):
            return int(self.text())
        if isinstance(self.measure_type, (Area, Volume, Length)):
            return float(self.text())

    def setDefault(self, default):
        self.setText('' if default is None else str(default))

    def error_message_text(self) -> str:
        if isinstance(self.measure_type, Angle):
            return 'Feld erwartet einen Winkel zwischen 0 und 360'
        if isinstance(self.measure_type, (Area, Volume, Length)):
            return 'Feld erwartet eine positive Zahl'
        if isinstance(self.measure_type, Scale):
            return 'Feld erwartet eine Prozentwert zwischen 0 und 100'

    def validate_widget(self, required):
        try:
            if not self.value() and not required:
                return True
            if isinstance(self.measure_type, Angle) and 0 <= int(self.value()) <= 360:
                return True
            elif isinstance(self.measure_type, (Area, Volume, Length)) and 0 <= float(self.value()) <= sys.float_info.max:
                return True
            elif isinstance(self.measure_type, Scale) and 0 <= int(self.value()) <= 100:
                return True
            raise ValueError
        except (ValueError, TypeError):
            self.error_message = self.error_message_text()
            return False


class QDateListInput(LineEditMixin, QXPlanInputElement, QWidget, metaclass=XPlanungInputMeta):

    def __init__(self):
        super(QDateListInput, self).__init__()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.inputs = []
        self.plus_icon_path = os.path.abspath(os.path.join(BASE_DIR, 'gui/resources/plus.svg'))
        self.minus_icon_path = os.path.abspath(os.path.join(BASE_DIR, 'gui/resources/minus.svg'))

        self.first_input = QDateEditNoScroll(self, calendarPopup=True)

        self.add_button = QToolButton()
        self.add_button.setIcon(self.loadSvg(self.plus_icon_path))
        self.add_button.installEventFilter(self)
        self.add_button.setCursor(Qt.PointingHandCursor)
        self.add_button.setToolTip('Weiteres Feld hinzufügen')
        self.add_button.clicked.connect(self.addInput)
        self.add_button.setStyleSheet('''
            QToolButton {
                background: palette(window); 
                border: 0px; 
            }
            ''')

        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.first_input)
        hbox.addWidget(self.add_button)
        self.layout.addItem(hbox)
        self.inputs.append(hbox)

        self.setLayout(self.layout)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.HoverEnter:
            obj.setIcon(self.loadSvg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color='#1F2937'))
        elif event.type() == QEvent.HoverLeave:
            obj.setIcon(self.loadSvg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color='#6B7280'))
        return False

    def loadSvg(self, svg, color=None):
        img = QPixmap(svg)
        if color:
            qp = QPainter(img)
            qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
            qp.fillRect(img.rect(), QColor(color))
            qp.end()
        return QIcon(img)

    def addInput(self, checked):
        el = QDateEditNoScroll(self, calendarPopup=True)
        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(el)
        remove_button = QToolButton()
        remove_button.setIcon(self.loadSvg(self.minus_icon_path))
        remove_button.installEventFilter(self)
        remove_button.setCursor(Qt.PointingHandCursor)
        remove_button.setToolTip('Eingabefeld entfernen')
        remove_button.clicked.connect(self.removeInput)
        remove_button.setStyleSheet('''
            QToolButton {
                background: palette(window); 
                border: 0px; 
            }
            ''')
        hbox.addWidget(remove_button)
        self.inputs.append(hbox)
        self.layout.addLayout(hbox)
        return el

    def removeInput(self, checked):
        for layout in self.inputs:
            for i in range(layout.count()):
                if self.sender() == layout.itemAt(i).widget():
                    self.inputs.remove(layout)
                    self.layout.removeItem(layout)
                    layout.deleteLater()

    def value(self):
        input_fields = [layout.itemAt(0).widget() for layout in self.inputs]
        dates = []
        for edit in input_fields:
            if not edit.value():
                continue
            dates.append(edit.value())

        return dates

    def setDefault(self, default):
        if not default:
            return
        dates = [datetime.datetime.strptime(date, "%d.%m.%Y") for date in str(default).split(', ')]
        if not dates:
            return
        self.first_input.setDefault(dates[0])
        for date in dates[1:]:
            el = self.addInput(None)
            el.setDefault(date)

    def validate_widget(self, required):
        return True


class QCheckableComboBoxInput(QXPlanInputElement, QgsCheckableComboBox, metaclass=XPlanungInputMeta):

    def __init__(self, items=None):
        super(QCheckableComboBoxInput, self).__init__()
        if items is not None:
            self.addItems(items)

    def value(self):
        return self.checkedItems()

    def setDefault(self, default):
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


class QComboBoxNoScroll(QXPlanInputElement, QComboBox, metaclass=XPlanungInputMeta):
    def __init__(self, scroll_widget=None, items=None, include_default=None, *args, **kwargs):
        super(QComboBoxNoScroll, self).__init__(*args, **kwargs)
        self.scrollWidget = scroll_widget
        self.include_default = include_default
        self.setFocusPolicy(Qt.StrongFocus)

        if items is not None:
            self.addItems(items)

        if self.include_default:
            # TODO: `setPlaceHolderText` is not working from Qt 5.15.2 upwards. (and was only introduced with 5.15.0)
            #  verify that it does work when QGIS moves to higher Qt version 5.15.9 or 6.0.1?
            #  https://bugreports.qt.io/browse/QTBUG-90595
            if QVersionNumber.fromString(qVersion()) > QVersionNumber.fromString('5.15.0'):
                self.setPlaceholderText('-- Keine Auswahl --')
            self.setCurrentIndex(-1)

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus() or self.scrollWidget is None:
            return super(QComboBoxNoScroll, self).wheelEvent(*args, **kwargs)

        return self.scrollWidget.wheelEvent(*args, **kwargs)

    def value(self):
        if self.currentIndex() == -1:
            return None
        return self.currentText()

    def setDefault(self, default):
        index = self.findText(str(default))
        if index >= 0:
            self.setCurrentIndex(index)

    def validate_widget(self, required):
        return True


class QDateEditNoScroll(QXPlanInputElement, QgsDateEdit, metaclass=XPlanungInputMeta):

    def __init__(self, scroll_widget=None, *args, **kwargs):
        super(QDateEditNoScroll, self).__init__(*args, **kwargs)
        self.scrollWidget = scroll_widget
        self.setFocusPolicy(Qt.StrongFocus)

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
