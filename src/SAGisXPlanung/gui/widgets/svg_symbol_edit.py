import os
from pathlib import Path

import qasync
from qgis.PyQt.QtGui import QIcon, QMouseEvent
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import (QGroupBox, QHBoxLayout, QVBoxLayout, QLabel, QWidget, QToolButton, QSizePolicy,
                                 QDialog, QDialogButtonBox)
from qgis.core import QgsApplication

from qgis.gui import QgsSvgSelectorWidget

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.config import SVG_CONFIG


class SVGSymbolDisplayWidget(QGroupBox):

    svg_selection_saved = pyqtSignal(str)  # path

    def __init__(self, svg_path, parent=None):

        super(SVGSymbolDisplayWidget, self).__init__('Symbol')

        self._layout = QHBoxLayout()
        self.label_layout = QVBoxLayout()

        self.svg_widget = SymbolEditButton(QIcon(svg_path))
        self.svg_widget.svg_selected.connect(self.onSvgSelected)
        self.svg_widget.svg_selection_saved.connect(self.onSvgSelectionSaved)
        self.svg_widget.svg_selection_rejected.connect(self.onSvgSelectionRejected)

        file_name = Path(svg_path).name
        symbol_node = SVG_CONFIG.get(file_name, "")
        self.current_name = symbol_node['name'] if symbol_node else 'Fehlerhaftes Symbol'
        self.current_category = symbol_node['category'] if symbol_node else ''
        self.label_name = QLabel(self.current_name)
        self.label_name.setObjectName('name')
        self.category_name = QLabel(self.current_category)
        self.category_name.setObjectName('category')

        self.label_layout.addWidget(self.category_name)
        self.label_layout.addWidget(self.label_name)

        self._layout.addWidget(self.svg_widget)
        self._layout.addItem(self.label_layout)
        self._layout.setSpacing(25)
        self.setLayout(self._layout)

        self.setStyleSheet('''
        QToolButton {
            border: 0px;
        }
        #category {
            text-transform: uppercase;
            font-weight: 400;
            color: #374151;
        }
        #name {
            font-size: 1.125rem;
            font-weight: 500;
            color: #1c1917;
        }
        ''')

    @qasync.asyncSlot()
    async def onSvgSelectionRejected(self):
        self.svg_widget.button().setIcon(self.svg_widget.icon)
        self.category_name.setText(self.current_category)
        self.label_name.setText(self.current_name)

    @qasync.asyncSlot(str)
    async def onSvgSelectionSaved(self, path):
        file_name = Path(path).name
        symbol_node = SVG_CONFIG.get(file_name, "")
        if not symbol_node:
            return
        self.current_name = symbol_node['name']
        self.current_category = symbol_node['category']
        self.svg_selection_saved.emit(path)

    @qasync.asyncSlot(str)
    async def onSvgSelected(self, path: str):
        file_name = Path(path).name
        symbol_node = SVG_CONFIG.get(file_name, "")
        if not symbol_node:
            return

        icon = QIcon(path)
        self.svg_widget.button().setIcon(icon)

        self.category_name.setText(symbol_node['category'])
        self.label_name.setText(symbol_node['name'])


class SymbolEditButton(QWidget):

    svg_selected = pyqtSignal(str)  # path
    svg_selection_saved = pyqtSignal(str)  # path
    svg_selection_rejected = pyqtSignal()

    def __init__(self, icon):
        super(SymbolEditButton, self).__init__()
        self.icon = icon

        self.setLayout(QVBoxLayout())
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName('back')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.layout().setContentsMargins(5, 5, 5, 5)

        self._button = QToolButton()
        self._button.setIcon(self.icon)
        self._button.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._button.setMinimumHeight(20)
        self.setMinimumHeight(20)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        self.layout().addWidget(self._button, 0, Qt.AlignCenter)

        self.setStyleSheet('''
        #back:hover {
            background-color: #bfdbfe;
            border: none; 
            border-radius: 3px;
        }
        ''')

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            svg_dialog = QSymbolSelectionDialog(self)
            svg_dialog.svg_selected.connect(self.svg_selected.emit)
            svg_dialog.svg_selection_saved.connect(self.onSvgSelectionSaved)
            svg_dialog.rejected.connect(self.svg_selection_rejected.emit)
            svg_dialog.show()
        super(SymbolEditButton, self).mouseReleaseEvent(event)

    @qasync.asyncSlot(str)
    async def onSvgSelectionSaved(self, path):
        self.icon = QIcon(os.path.join(BASE_DIR, path))
        self.svg_selection_saved.emit(path)

    def button(self):
        return self._button


class QSymbolSelectionDialog(QDialog):

    svg_selected = pyqtSignal(str)  # path
    svg_selection_saved = pyqtSignal(str)  # path

    def __init__(self, parent):

        super(QSymbolSelectionDialog, self).__init__(parent)

        self.setWindowTitle('Symbol wählen')

        self._layout = QVBoxLayout()

        self.previous_svg_path = QgsApplication.svgPaths()
        QgsApplication.setSvgPaths([os.path.join(BASE_DIR, 'symbole')])
        QgsApplication.setDefaultSvgPaths([os.path.join(BASE_DIR, 'symbole')])

        self.svg_widget = QgsSvgSelectorWidget()
        self.svg_widget.sourceLineEdit().setVisible(False)
        self.svg_widget.setSvgPath(os.path.join(BASE_DIR, 'symbole'))
        self.svg_widget.svgSelected.connect(self.onSvgSelected)
        self._layout.addWidget(self.svg_widget)

        self.nav_layout = QHBoxLayout()
        self.nav_layout.setSpacing(10)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.error_label = QLabel('')
        self.error_label.setObjectName('error-label')
        self.nav_layout.addWidget(self.error_label)
        self.nav_layout.addWidget(self.buttons)
        self._layout.addItem(self.nav_layout)

        self.setLayout(self._layout)

        self.setStyleSheet('''
        #error-label {
            font-weight: bold; 
            font-size: 7pt; 
            color: #991B1B;
        }
        ''')

    def closeEvent(self, e):
        QgsApplication.setDefaultSvgPaths(self.previous_svg_path)
        QgsApplication.setSvgPaths(self.previous_svg_path)

    @qasync.asyncSlot(str)
    async def onSvgSelected(self, path: str):
        file_name = Path(path).name
        symbol_node = SVG_CONFIG.get(file_name, "")
        if not symbol_node:
            self.error_label.setText('Dieses Symbol gehört nicht zum Symbolkatalog von SAGis XPlanung!')
            self.buttons.button(QDialogButtonBox.Save).setEnabled(False)
            return

        self.buttons.button(QDialogButtonBox.Save).setEnabled(True)
        self.error_label.clear()
        self.svg_selected.emit(path)

    def accept(self):
        file_name = Path(self.svg_widget.currentSvgPath()).name
        symbol_node = SVG_CONFIG[file_name]

        self.svg_selection_saved.emit(os.path.join('symbole', symbol_node['category'], file_name))

        super(QSymbolSelectionDialog, self).accept()

    def closeEvent(self, event):
        super(QSymbolSelectionDialog, self).closeEvent(event)