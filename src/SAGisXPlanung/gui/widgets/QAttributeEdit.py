import datetime
import inspect
import logging
import os
from collections import namedtuple

import qasync
from geoalchemy2 import WKBElement, WKTElement

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QAbstractTableModel, Qt, QSortFilterProxyModel, pyqtSlot, QModelIndex, QRegExp, pyqtSignal
from qgis.PyQt.QtWidgets import QHeaderView, QLineEdit
from qgis.PyQt.QtGui import QIcon, QRegExpValidator
from sqlalchemy import update

from SAGisXPlanung import BASE_DIR, Session, Base
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_AbstraktesPraesentationsobjekt
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Objekt
from SAGisXPlanung.XPlan.mixins import XPlanungEnumMixin, ElementOrderMixin
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import xplan_tooltip, export_version
from SAGisXPlanung.gui.XPEditAttributeDialog import XPEditAttributeDialog
from SAGisXPlanung.gui.commands import AttributeChangedCommand
from SAGisXPlanung.gui.widgets.QRelationDropdowns import QAddRelationDropdown

FORM_CLASS, CLS = uic.loadUiType(os.path.join(BASE_DIR, 'ui/attribute_edit.ui'))
logger = logging.getLogger(__name__)

ObjectRole = Qt.UserRole + 1


class QAttributeEdit(CLS, FORM_CLASS):
    nameChanged = pyqtSignal(str)

    ICON_DEFAULT_SIZE = 24
    TEXT_DEFAULT_SIZE = 6
    ATTRIBUTE_SIZE = 'skalierung'
    ATTRIBUTE_ANGLE = 'drehwinkel'

    @staticmethod
    def create(xplanung_item: XPlanungItem, data, parent):
        if issubclass(xplanung_item.xtype, XP_AbstraktesPraesentationsobjekt):
            from SAGisXPlanung.gui.widgets.QAttributeEditAnnotationItem import QAttributeEditAnnotationItem
            return QAttributeEditAnnotationItem(xplanung_item, data, parent)
        elif hasattr(xplanung_item.xtype, 'renderer') and isinstance(xplanung_item.xtype.renderer(xplanung_item.geom_type), RuleBasedSymbolRenderer):
            from SAGisXPlanung.gui.widgets.QAttributeEditSymbolRenderer import QAttributeEditSymbolRenderer
            return QAttributeEditSymbolRenderer(xplanung_item, data, parent)
        else:
            return QAttributeEdit(xplanung_item, data, parent)

    def __init__(self, xplanung_item: XPlanungItem, data, parent):
        super(QAttributeEdit, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self._xplanung_item = xplanung_item

        self.editSearch.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.LeadingPosition)
        reg_ex = QRegExp(r'\d{1,3}°?')
        self.angleEdit.setValidator(QRegExpValidator(reg_ex, self.angleEdit))

        # model setup
        edit_allowed = not issubclass(self._xplanung_item.xtype, XP_Objekt)
        self.model = AttributeTableModel(xplanung_item, data, edit=edit_allowed)
        self.proxyModel = QSortFilterProxyModel(self.tableView)
        self.proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxyModel.setSourceModel(self.model)
        self.tableView.setModel(self.proxyModel)

        # table header setup
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableView.verticalHeader().hide()

        self.styleGroup.setVisible(False)

        self.tableView.doubleClicked.connect(self.onDoubleClicked)
        self.editSearch.textChanged.connect(self.onFilterTextChanged)

    def set_form_values(self):
        with Session.begin() as session:
            plan_content = session.query(self._xplanung_item.xtype).get(self._xplanung_item.xid)
            scale = getattr(plan_content, self.ATTRIBUTE_SIZE)
            self.sizeSlider.setValue(scale * (99 - 1) + 1)
            angle = getattr(plan_content, self.ATTRIBUTE_ANGLE)
            self.angleEdit.setText(f'{angle}°')
            self.angleDial.setValue(angle)

    def initialize_listeners(self):
        self.sizeSlider.valueChanged.connect(self.onSliderValueChanged)
        self.sizeSlider.sliderReleased.connect(lambda a=self.ATTRIBUTE_SIZE: self.onSliderReleased(a))
        self.angleDial.valueChanged.connect(self.onDialValueChanged)
        self.angleDial.sliderReleased.connect(lambda a=self.ATTRIBUTE_ANGLE: self.onSliderReleased(a))
        self.angleEdit.editingFinished.connect(self.onAngleTextEdited)

    def model_index(self, attr: str):
        indices = self.model.match(self.model.index(0, 0), Qt.DisplayRole, attr, 1, Qt.MatchFixedString)
        if not indices:
            return QModelIndex()
        return indices[0].siblingAtColumn(1)

    @pyqtSlot()
    def onAngleTextEdited(self):
        text = self.angleEdit.text().replace('°', '')
        self.angleDial.setValue(int(text))
        self.onSliderReleased(self.ATTRIBUTE_ANGLE)

    @pyqtSlot(str)
    def onFilterTextChanged(self, text: str):
        self.proxyModel.setFilterFixedString(text)

    @pyqtSlot(QModelIndex)
    def onDoubleClicked(self, index: QModelIndex):
        if index.column() == 0:
            return
        index = self.proxyModel.mapToSource(index)
        attribute_name = index.siblingAtColumn(0).data()

        rel = next((r for r in self._xplanung_item.xtype.relationships() if r[0] == attribute_name), None)
        if rel is not None:
            dlg = XPEditAttributeDialog(attribute_name, None, index.data(), self._xplanung_item.xtype, parent=self)
            stub = namedtuple('stub', ['cls_type'])
            cb = QAddRelationDropdown(stub(cls_type=self._xplanung_item.xtype), rel)
            cb.setDefault(index.data(role=ObjectRole))

            dlg.control.hide()
            dlg.hl1.addWidget(cb)
            dlg.control = cb
        else:
            base_classes = [c for c in list(inspect.getmro(self._xplanung_item.xtype)) if issubclass(c, Base)]
            cls = next(c for c in base_classes if hasattr(c, attribute_name) and c.attr_fits_version(attribute_name, export_version()))
            field_type = getattr(cls, attribute_name).property.columns[0].type
            dlg = XPEditAttributeDialog(attribute_name, field_type, index.data(), self._xplanung_item.xtype, parent=self)

        dlg.attributeChanged.connect(lambda original, value, a=attribute_name, i=index:
                                     self.onAttributeChanged(i, a, value))
        dlg.attributeChanged.connect(lambda original, value, a=attribute_name, i=index:
                                     self.pushAttributeChangedCommand(original, value, a, i))
        dlg.fileChanged.connect(lambda value: self.onAttributeChanged(None, 'file', value))
        dlg.exec_()

    def pushAttributeChangedCommand(self, original_value, new_value, attr, index):
        command = AttributeChangedCommand(
            xplanung_item=self._xplanung_item,
            attribute=attr,
            previous_value=original_value,
            new_value=new_value,
            model_index=index
        )
        command.signal_proxy.changeApplied.connect(self.onChangeApplied)
        self.parent.undo_stack.push(command)

    @pyqtSlot(QModelIndex, str, object)
    def onChangeApplied(self, index, attr, value):
        if index is not None:
            self.model.setData(index, value)

        # send name changes to update other ui components
        if issubclass(self._xplanung_item.xtype, XP_Plan) and attr == 'name':
            self.nameChanged.emit(value)

    def onAttributeChanged(self, index, attr, value):
        with Session.begin() as session:
            session.expire_on_commit = False

            base_classes = [c for c in list(inspect.getmro(self._xplanung_item.xtype)) if issubclass(c, Base)]
            cls = next(c for c in reversed(base_classes) if hasattr(c, attr) and c.attr_fits_version(attr, export_version()))

            stmt = update(cls.__table__).where(
                cls.__table__.c.id == self._xplanung_item.xid
            ).values({attr: value})
            session.execute(stmt)

            self.onChangeApplied(index, attr, value)

    def onSliderReleased(self, attr):
        if attr == self.ATTRIBUTE_SIZE:
            slider_value = self.sizeSlider.value()
            scale = (slider_value - 1) / (99 - 1)
            value = f'{scale:.2f}'
        elif attr == self.ATTRIBUTE_ANGLE:
            value = self.angleDial.value()
        else:
            raise Exception('invalid attribute')

        with Session.begin() as session:
            plan_content = session.query(self._xplanung_item.xtype).get(self._xplanung_item.xid)
            setattr(plan_content, attr, value)


class AttributeTableModel(QAbstractTableModel):
    def __init__(self, xplanung_item: XPlanungItem, data, edit=True):
        super(AttributeTableModel, self).__init__()
        self.edit_allowed = edit
        self._xplanung_item = xplanung_item
        self._data = data
        self._horizontal_header = ['XPlanung-Attribut', 'Wert']

    @staticmethod
    def parser(value):
        if isinstance(value, datetime.date):
            return value.strftime("%d.%m.%Y")
        return str(value)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            if isinstance(value, (WKBElement, WKTElement)):
                return geometry_from_spatial_element(value).asWkt()
            if isinstance(value, (XPlanungEnumMixin, ElementOrderMixin)):
                return str(value)
            if isinstance(value, datetime.date):
                return value.strftime("%d.%m.%Y")
            if isinstance(value, list):
                return ", ".join(map(AttributeTableModel.parser, value))
            return value
        if role == ObjectRole:
            value = self._data[index.row()][index.column()]
            return value
        if role == Qt.ToolTipRole:
            if not self.edit_allowed:
                return "Editieren von Attributen nur in der Vollversion möglich"
            # show tooltips for first column, which are the xplanung attributes
            if index.column() != 0:
                return
            return xplan_tooltip(self._xplanung_item.xtype, self._data[index.row()][index.column()])

    def setData(self, index: QModelIndex, value, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._horizontal_header[col]

    def flags(self, index):
        current_flags = super(AttributeTableModel, self).flags(index)
        if not self.edit_allowed:
            return current_flags & ~Qt.ItemIsEnabled

        attribute_name = self._data[index.row()][0]
        xtype = self._xplanung_item.xtype
        if hasattr(xtype, '__readonly_columns__') and attribute_name in xtype.__readonly_columns__:
            return current_flags & ~Qt.ItemIsEnabled
        if index.column() == 0:
            return current_flags & ~Qt.ItemIsSelectable
        return current_flags

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return 2
