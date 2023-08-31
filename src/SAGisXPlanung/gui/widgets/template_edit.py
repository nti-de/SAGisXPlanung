import os

from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QComboBox, QGroupBox, QHBoxLayout, QToolButton,
                                 QSizePolicy, QSpacerItem, QButtonGroup, QLabel)
from qgis.PyQt.QtCore import pyqtSlot, pyqtSignal, Qt
from qgis.PyQt.QtGui import QIcon, QMouseEvent

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.BuildingTemplateItem import BuildingTemplateCellDataType
from .po_styling_options import QCommonStylingOptions


class QBuildingTemplateEdit(QWidget):

    cellDataChanged = pyqtSignal(BuildingTemplateCellDataType, int)
    rowCountChanged = pyqtSignal(int, list)  # row count, cell types
    styleChanged = pyqtSignal(str, object)  # style attribute, value

    def __init__(self, cells, rows, scale=0.5, angle=0, parent=None):
        super(QBuildingTemplateEdit, self).__init__(parent)

        self.cells = cells
        self.columns = 2
        self.rows = rows

        self._layout = QVBoxLayout()
        self.template_form = SelectTemplateFormWidget(default_rows=self.rows)
        self.template_form.rowCountChanged.connect(self.onRowCountChanged)

        self._layout.addWidget(self.template_form)

        self.template_grid_container = QGroupBox('Zellwerte der Nutzungschablone')
        self.template_grid = QGridLayout()
        self.buildTemplateGrid()
        self._layout.addWidget(self.template_grid_container)

        self.common_style_container = QGroupBox('Allgemeine Darstellungsoptionen')
        self.common_style_container.setLayout(QVBoxLayout())
        self.common_styling_opt = QCommonStylingOptions()
        self.common_styling_opt.setSize(scale)
        self.common_styling_opt.setAngle(angle)
        self.common_styling_opt.styleChanged.connect(lambda k, v: self.styleChanged.emit(k, v))
        self.common_style_container.layout().addWidget(self.common_styling_opt)

        self._layout.addItem((QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Expanding)))
        self._layout.addWidget(self.common_style_container)

        self.setLayout(self._layout)

    def buildTemplateGrid(self):
        # hackish solution to clear layout, transfer to new widget which will be destroyed automatically
        # when out it goes of scope: https://stackoverflow.com/a/7082920/12690772
        QWidget().setLayout(self.template_grid)

        self.template_grid = QGridLayout()
        for i in range(self.rows):
            for j in range(self.columns):
                index = i * self.columns + j % self.columns

                cb = QComboBox()
                cb.setProperty('template-index', index)
                for x in BuildingTemplateCellDataType:
                    cb.addItem(x.value, x.name)
                index = cb.findData(self.cells[index].name)
                if index >= 0:
                    cb.setCurrentIndex(index)

                cb.currentIndexChanged.connect(self.onComboBoxIndexChanged)

                self.template_grid.addWidget(cb, i, j)

        self.template_grid_container.setLayout(self.template_grid)

    @pyqtSlot(int)
    def onComboBoxIndexChanged(self, index: int):
        cell_index = self.sender().property('template-index')
        item_value = self.sender().itemData(index)
        item = BuildingTemplateCellDataType[item_value]
        self.cellDataChanged.emit(item, cell_index)

    @pyqtSlot(int)
    def onRowCountChanged(self, row_count: int):
        row_difference = self.rows - row_count
        if row_difference > 0:
            del self.cells[-1*abs(row_difference)*self.columns:]
        elif row_difference < 0:
            all_cell_types = set([x for x in BuildingTemplateCellDataType])
            unused_cell_types = [x for x in all_cell_types if x not in self.cells]
            for i in range(abs(row_difference)*self.columns):
                self.cells.append(unused_cell_types[i])
        self.rows = row_count
        self.rowCountChanged.emit(self.rows, self.cells)

        self.buildTemplateGrid()


class SelectTemplateFormWidget(QGroupBox):

    rowCountChanged = pyqtSignal(int)

    def __init__(self, default_rows=None, parent=None):

        super(SelectTemplateFormWidget, self).__init__('Form der Nutzungschablone')

        self._layout = QHBoxLayout()

        self.button_small = LabeledButton(QIcon(os.path.join(BASE_DIR, 'gui/resources/grid2x2.svg')), '2 x 2', 2)
        self.button_medium = LabeledButton(QIcon(os.path.join(BASE_DIR, 'gui/resources/grid2x3.svg')), '2 x 3', 3)
        self.button_large = LabeledButton(QIcon(os.path.join(BASE_DIR, 'gui/resources/grid2x4.svg')), '2 x 4', 4)
        self.button_small.buttonToggled.connect(self.onButtonToggled)
        self.button_medium.buttonToggled.connect(self.onButtonToggled)
        self.button_large.buttonToggled.connect(self.onButtonToggled)

        self._buttons = [self.button_small, self.button_medium, self.button_large]

        if default_rows == 2:
            self.button_small.toggleButton(True)
        elif default_rows == 3:
            self.button_medium.toggleButton(True)
        elif default_rows == 4:
            self.button_large.toggleButton(True)

        self._layout.addWidget(self.button_small)
        self._layout.addWidget(self.button_medium)
        self._layout.addWidget(self.button_large)
        self._layout.setSpacing(25)
        self.setLayout(self._layout)

        self.setStyleSheet('''
        QToolButton {
            border: 0px;
        }
        ''')

    @pyqtSlot(bool, int)
    def onButtonToggled(self, checked: bool, row_count: int):
        if not checked:
            return

        self.rowCountChanged.emit(row_count)

        for b in self._buttons:
            if b == self.sender():
                continue
            b.toggleButton(False)


class LabeledButton(QWidget):

    buttonToggled = pyqtSignal(bool, int)  # checked, row count

    def __init__(self, icon, label_text, row_count):
        super(LabeledButton, self).__init__()
        self.row_count = row_count

        self.setLayout(QVBoxLayout())
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName('back')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.layout().setContentsMargins(5, 5, 5, 5)

        self._button = QToolButton()
        self._button.setIcon(icon)
        self._button.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.layout().addWidget(self._button, 0, Qt.AlignCenter)
        self.layout().addWidget(QLabel(label_text), 0, Qt.AlignCenter)

        self.setStyleSheet('''
        #back:hover {
            background-color: #E5E7EB;
            border: none; 
            border-radius: 3px;
        }
        #back[checked=true] {
            border: 1px solid #1D4ED8;
            border-radius: 3px;
        }
        ''')

    def toggleButton(self, checked: bool):
        self.setProperty('checked', checked)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        self.buttonToggled.emit(checked, self.row_count)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and not self.property('checked'):
            self.toggleButton(True)
        super(LabeledButton, self).mousePressEvent(event)

    def button(self):
        return self._button
