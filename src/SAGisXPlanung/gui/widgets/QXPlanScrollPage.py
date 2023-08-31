import datetime
import logging
import os
from collections import namedtuple
from inspect import getmro
from pathlib import Path
from typing import List

import yaml
from qgis.PyQt import QtCore, QtWidgets, QtGui
from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtWidgets import QFrame, QSpacerItem, QSizePolicy, QGridLayout, QGroupBox

from sqlalchemy import inspect, null
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.exc import UnmappedClassError

from SAGisXPlanung import Session, BASE_DIR, Base
from SAGisXPlanung.XPlan.feature_types import XP_Objekt
from SAGisXPlanung.XPlan.types import InvalidFormException
from SAGisXPlanung.config import xplan_tooltip, export_version
from SAGisXPlanung.gui.widgets.QRelationDropdowns import QAddRelationDropdown
from SAGisXPlanung.gui.widgets.QXPlanInputElement import QXPlanInputElement, QFileInput

PYQT_DEFAULT_DATE = datetime.date(1752, 9, 14)
logger = logging.getLogger(__name__)


class QXPlanScrollPage(QtWidgets.QScrollArea):

    addRelationRequested = QtCore.pyqtSignal(object, bool, str)
    parentLinkClicked = QtCore.pyqtSignal()
    requestPageToTop = QtCore.pyqtSignal()

    def __init__(self, cls_type, parent_class, parent_attribute=None, existing_xid=None, *args, **kwargs):
        super(QXPlanScrollPage, self).__init__(*args, **kwargs)
        self.cls_type = cls_type
        self.parent_class = parent_class
        self.parent_attribute = parent_attribute
        self.existing_xid = existing_xid
        self.child_pages = []
        self.fields = {}
        self.required_inputs = []
        self.hidden_inputs = []

        s = QSettings()
        self.ATTRIBUTE_CONFIG = yaml.safe_load(s.value(f"plugins/xplanung/attribute_config", '')) or {}

        if hasattr(cls_type, 'hidden_inputs'):
            self.hidden_inputs = cls_type.hidden_inputs()

        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalScrollBar().setEnabled(False)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.content_widget = QtWidgets.QWidget()
        self.setWidget(self.content_widget)
        self.vBox = QtWidgets.QVBoxLayout()
        self.vBox.setSpacing(20)
        self.content_widget.setLayout(self.vBox)

        if self.parent_class is not None:
            self.createHeader()
        self.createLayout()

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.vBox.addWidget(spacer)

    def sizeHint(self):
        size = super(QXPlanScrollPage, self).sizeHint()
        size.setWidth(size.width() + 5 * self.verticalScrollBar().sizeHint().width())
        return size

    def addChildPage(self, page):
        self.child_pages.append(page)

    def removeChildPage(self, page):
        self.child_pages.remove(page)

    def createHeader(self):
        widget = QtWidgets.QWidget(self)
        widget.setStyleSheet("""
            QLabel#lParentAttribute {
                color: #64748b;
            }
            QPushButton#lParentClass{
                color: #1e293b;
                background: palette(window);
                border: 0px;
            }
            QPushButton#lParentClass:hover {
                color: #0ea5e9;
            }
        """)
        h_layout = QtWidgets.QHBoxLayout(widget)
        h_layout.setContentsMargins(0, 10, 0, 10)
        l1 = QtWidgets.QLabel('Objekt gehört zu:')
        l2 = QtWidgets.QPushButton(self.parent_class.__name__, objectName='lParentClass')
        l1.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        l2.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        h_layout.addWidget(l1)
        h_layout.addWidget(l2)
        if self.parent_attribute:
            l3 = QtWidgets.QLabel(f'(Attribut: {self.parent_attribute})', objectName='lParentAttribute')
            l2.setCursor(Qt.PointingHandCursor)
            l2.clicked.connect(lambda checked: self.parentLinkClicked.emit())
            h_layout.addWidget(l3)
        else:
            l2.setDisabled(True)
            h_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.vBox.addWidget(widget)

    def createLayout(self):
        column_resizer = ColumnResizer()

        for cls in self.cls_type.mro():
            # catches base classes which are no sqlalchemy models
            if not is_mapped(cls):
                continue

            group_box = QGroupBox(cls.__name__)
            grid = QtWidgets.QGridLayout(group_box)

            rel_offset = 0
            for rel in inspect(cls).relationships.items():
                class_type = rel[1].mapper.class_

                # don't show if relationship property does not fit export version
                if not cls.relation_fits_version(rel[0], export_version()):
                    continue

                # don't show, if relationship is treated as column
                if hasattr(cls, f'{rel[0]}_id') and cls.attr_is_treated_as_column(f'{rel[0]}_id', consider_suffix=False):
                    continue

                # disallow specifically declared relations
                if hasattr(cls, '__avoidRelation__') and rel[0] in cls.__avoidRelation__:
                    continue

                # disallow inherited relationships
                if rel[1].parent.class_ != cls:
                    continue

                # avoid referencing of circular dependencies
                if class_type == self.parent_class or \
                        (self.parent_class is not None and issubclass(self.parent_class, class_type)):
                    continue

                # avoid references to XP_Objekt's. They are set via the 'Planinhalt konfigurieren' Dialog.
                if class_type == XP_Objekt:
                    continue


                label_name, tooltip = cls.relation_prop_display(rel)
                label = QtWidgets.QLabel(label_name)
                if tooltip:
                    label.setToolTip(tooltip)

                label.setObjectName(rel[0])
                required_rel = bool(hasattr(cls, '__requiredRelationships__') and label.objectName() in cls.__requiredRelationships__)
                if required_rel:
                    label.setStyleSheet("font-weight: bold")
                    self.required_inputs.append(label.objectName())
                grid.addWidget(label, rel_offset, 0)

                # complex many-to-many or many-to-one relation
                if next(iter(rel[1].remote_side)).primary_key or rel[1].secondary is not None:
                    widget = QAddRelationDropdown(self, rel)

                # one-to-many relation, one-to-one relation (defined by `uselist=False`)
                else:
                    widget = QtWidgets.QPushButton("Hinzufügen")
                    try:
                        if rel[0] in self.cls_type.__requiredRelationships__:
                            self.addRelationRequested.emit(class_type)
                    except AttributeError:
                        pass
                    widget.clicked.connect(lambda state, c=class_type, u=rel[1].uselist, a=rel[0]:
                                           self.onRelationButtonClicked(c, u, a))

                self.fields[rel[0]] = widget
                grid.addWidget(widget, rel_offset, 1)
                rel_offset += 1

            col_skip = 0
            for i, key in enumerate(cls.element_order(include_base=False, only_columns=True, export=False,
                                                      version=export_version())):
                if key in self.hidden_inputs:
                    col_skip += 1
                    continue
                # don't show attributes that are disabled in settings
                if key in self.ATTRIBUTE_CONFIG.get(cls.__name__, []):
                    col_skip += 1
                    continue

                label, control = self.createInput(key, cls)
                control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                grid.addWidget(label, i + rel_offset - col_skip, 0)
                grid.addWidget(control, i + rel_offset - col_skip, 1)

                self.fields[key] = control

            # don't add group boxes that are empty
            if grid.count() == 0:
                continue

            column_resizer.form_widgets.append(grid)
            self.vBox.addWidget(group_box)

        column_resizer.applyResize()

    def onRelationButtonClicked(self, class_type, uselist, parent_attribute):
        if not uselist:
            button = self.fields[parent_attribute]
            button.setDisabled(True)
        self.addRelationRequested.emit(class_type, uselist, parent_attribute)

    def createInput(self, label_name: str, cls: type):
        # if column is a relationship-column, configure relation dropdown instead of normal input element
        if (rel := next((r for r in cls.relationships() if r[0] == label_name), None)) is not None:
            stub = namedtuple('stub', ['cls_type'])
            control = QAddRelationDropdown(stub(cls_type=self.cls_type), rel)

            label = QtWidgets.QLabel(label_name)
            tooltip = xplan_tooltip(self.cls_type, label_name)
            label.setToolTip(tooltip)

            return label, control

        base_classes = [c for c in list(getmro(cls)) if issubclass(c, Base)]
        cls = next(c for c in base_classes if
                   hasattr(c, label_name) and c.attr_fits_version(label_name, export_version()))
        column = getattr(cls, label_name).property.columns[0]
        field_type = column.type
        nullable = column.nullable

        control = QXPlanInputElement.create(field_type, self)

        if column.doc:
            label = QtWidgets.QLabel(column.doc)
            label.setToolTip(f'XPlanung-Attribut: {label_name}')
        else:
            label = QtWidgets.QLabel(label_name)
            tooltip = xplan_tooltip(self.cls_type, label_name)
            label.setToolTip(tooltip)

        label.setObjectName(label_name)

        if not nullable:
            font = QtGui.QFont()
            font.setBold(True)
            label.setFont(font)
            self.required_inputs.append(label_name)

        return label, control

    def getObjectFromInputs(self, validate_forms=True):
        if validate_forms and not self.validateForms():
            raise InvalidFormException()

        obj = self.cls_type()
        if self.existing_xid:
            obj.id = self.existing_xid

        for column, input_field in self.fields.items():
            if isinstance(input_field, QAddRelationDropdown):
                class_type = getattr(obj.__class__, column).property.mapper.class_
                if input_field.relation[1].secondary is None:
                    selected_object = input_field.value()
                    if not selected_object:  # no relation selected
                        setattr(obj, f'{column}_id', null())
                        continue
                    with Session.begin() as session:
                        obj_from_db = session.merge(selected_object)
                        setattr(obj, f'{column}_id', obj_from_db.id)
                    setattr(obj, column, obj_from_db)
                else:
                    selected_objects = input_field.value()
                    with Session.begin() as session:
                        obj_list = []
                        for selected_item in input_field.value():
                            obj_list.append(session.merge(selected_item))
                    setattr(obj, column, obj_list)
                continue

            if not isinstance(input_field, QXPlanInputElement):
                continue

            setattr(obj, column, input_field.value())

            if isinstance(input_field, QFileInput):
                setattr(obj, 'file', input_field.file())

        return obj

    def validateForms(self):
        is_valid = True
        invalid_attributes = []
        for attribute, control in self.fields.items():
            if not isinstance(control, QXPlanInputElement):
                continue

            required_input = bool(attribute in self.required_inputs)
            if not control.validate_widget(required_input):
                is_valid = False
                control.setInvalid(True)
                invalid_attributes.append(attribute)

        if not is_valid:
            label = self.findChild(QtWidgets.QLabel, invalid_attributes[0])
            self.ensureWidgetVisible(label)
            self.requestPageToTop.emit()

        return is_valid


def is_mapped(obj):
    try:
        class_mapper(obj)
    except UnmappedClassError:
        return False
    return True

# ****************************************************************


class ColumnResizer:
    """
    Helper-Klasse zum Anpassen des Layouts der Eingabeformulare.
    Gleicht die Breite der Spalten mehrerer voneinander unabhängiger GridLayouts an.

    Inspiriert durch https://github.com/agateau/columnresizer
    """

    def __init__(self):
        self.form_widgets: List[QGridLayout] = []

    def applyResize(self):
        largest_size = 0

        # find largest label size
        for widget in self.form_widgets:
            # prevent empty layouts
            if widget.rowCount() < 1:
                continue
            for i in range(widget.rowCount()):
                label = widget.itemAtPosition(i, 0).widget()
                size = label.minimumSizeHint().width()
                largest_size = max(largest_size, size)

        # apply resizing: set all labels to minimum width
        for widget in self.form_widgets:
            if widget.rowCount() < 1:
                continue
            for i in range(widget.rowCount()):
                label = widget.itemAtPosition(i, 0).widget()
                label.setMinimumWidth(largest_size)
