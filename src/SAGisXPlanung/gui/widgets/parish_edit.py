import os
from typing import List

import qasync
from qgis.PyQt.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QToolButton, QSizePolicy, QFrame
from qgis.PyQt.QtCore import Qt, QPoint, QSize, pyqtSlot, QRect, QEvent, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter, QColor

from SAGisXPlanung import BASE_DIR, Session
from SAGisXPlanung.XPlan.data_types import XP_Gemeinde
from SAGisXPlanung.gui.widgets.QXPlanInputElement import QCheckableComboBoxInput


class QParishLabel(QWidget):
    IconSize = QSize(16, 16)
    HorizontalSpacing = 2

    parishEditRequested = pyqtSignal()

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.setMouseTracking(True)
        self.active = True

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.icon_button = QToolButton()
        self.icon_button.setIcon(QIcon(os.path.join(BASE_DIR, 'gui/resources/location_edit.svg')))
        self.icon_button.setStyleSheet('''
        QToolButton {
            background: palette(window); 
            border: 0px;
            border-radius: 3px;
        }
        ''')
        self.icon_button.clicked.connect(self.onLocationEdit)
        self.icon_button.setCursor(Qt.PointingHandCursor)
        self.icon_button.setVisible(False)
        self.installEventFilter(self)

        self.label = QLabel('<template-gemeinde>')
        layout.addWidget(self.label)
        layout.addWidget(self.icon_button)

    def setActive(self, active: bool):
        """ Whether the editing capabilities are activated """
        self.active = active

    def eventFilter(self, obj, event):
        # if editing is not active do nothing
        if not self.active:
            return False

        if event.type() == QEvent.Enter:
            self.icon_button.show()
        elif event.type() == QEvent.Leave:
            self.icon_button.hide()
        return False

    def setText(self, text):
        self.label.setText(text)

    @pyqtSlot(bool)
    def onLocationEdit(self, clicked):
        self.parishEditRequested.emit()


class QParishEdit(QWidget):

    parishChanged = pyqtSignal(dict)

    def __init__(self, parent=None):

        super(QParishEdit, self).__init__(parent)

        self.cb = QCheckableComboBoxInput()
        self.cb.checkedItemsChanged.connect(self.onControlEdited)

        self.group = QFrame()
        self.group.setFrameStyle(QFrame.StyledPanel)
        self.group.setLayout(QVBoxLayout())
        self.group.layout().addWidget(QLabel('Gemeinde auswählen:'))
        self.group.layout().addWidget(self.cb)

        self.close_button = QToolButton()
        self.close_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.close_button.setIcon(self.loadSvg(os.path.join(BASE_DIR, 'gui/resources/expand_less.svg')))
        self.close_button.installEventFilter(self)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setToolTip('Sektion schließen')
        self.close_button.setIconSize(QSize(24, 24))
        self.close_button.setStyleSheet('''
        QToolButton {
            background: palette(window);
            border: 0px;
            border-radius: 3px;
        }
        ''')
        self.close_button.clicked.connect(self.onExpandLessClicked)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.group)
        self.layout().addWidget(self.close_button, Qt.AlignCenter)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def setup(self, parish_objects: List[XP_Gemeinde]):
        self.cb.clear()
        if self.cb.invalid:
            self.cb.setInvalid(False)
        with Session.begin() as session:
            xp_gemeinde = session.query(XP_Gemeinde).all()
            for g in xp_gemeinde:
                match = bool(any(g == p for p in parish_objects))
                self.cb.addItemWithCheckState(str(g), Qt.Checked if match else Qt.Unchecked, str(g.id))

    @pyqtSlot(bool)
    def onExpandLessClicked(self, clicked):
        self.hide()

    @qasync.asyncSlot('QStringList')
    async def onControlEdited(self, checked_items):
        user_data = self.cb.checkedItemsData()
        parish = {}
        for i, item in enumerate(checked_items):
            parish[item] = user_data[i]

        if not self.cb.validate_widget(required=True):
            self.cb.setInvalid(True)
            return
        self.parishChanged.emit(parish)

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