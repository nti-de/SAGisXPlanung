
from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter, QColor, QFocusEvent, QKeyEvent
from qgis.PyQt.QtWidgets import QLineEdit, QToolButton, QProxyStyle, QStyle, QApplication
from qgis.PyQt.QtCore import QEvent, QSize, Qt, pyqtSlot

from SAGisXPlanung import PYQT5
from SAGisXPlanung.gui.style import ClearIconProxyStyle


class QCollapsibleSearch(QLineEdit):

    def __init__(self, parent=None):
        super(QCollapsibleSearch, self).__init__(parent)

        self.search_icon_action = self.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.ActionPosition.LeadingPosition)
        self.search_icon_action.triggered.connect(self.onSearchActionTriggered)
        if PYQT5:
            self.search_widget = [w for w in self.search_icon_action.associatedWidgets() if isinstance(w, QToolButton)][0]
        else:
            self.search_widget = [w for w in self.search_icon_action.associatedObjects() if isinstance(w, QToolButton)][0]
        self.search_widget.setObjectName('search-icon')
        self.search_widget.installEventFilter(self)
        self.search_widget.setCursor(Qt.CursorShape.PointingHandCursor)

        self.proxy_style = ClearIconProxyStyle('Fusion')
        self.proxy_style.setParent(self)
        self.setStyle(self.proxy_style)

        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setMaximumWidth(30)
        self.setProperty('expanded', False)

        self.setStyleSheet('''
        * [expanded=false] {
            border: none;
            background-color: palette(window);
        }
        ''')

    @pyqtSlot(bool)
    def onSearchActionTriggered(self, checked: bool):
        if self.property('expanded'):
            return
        self.setMaximumWidth(200)
        self.setProperty('expanded', True)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setFocus()
        self.search_widget.removeEventFilter(self)

    def focusInEvent(self, evt: QFocusEvent):
        super(QCollapsibleSearch, self).focusInEvent(evt)

        if not self.property('expanded'):
            self.clearFocus()

    def focusOutEvent(self, evt: QFocusEvent):
        super(QCollapsibleSearch, self).focusOutEvent(evt)

        if not self.property('expanded') or self.text():
            return
        self.setMaximumWidth(30)
        self.setProperty('expanded', False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.search_widget.installEventFilter(self)
        self.search_widget.setIcon(self.loadSvg(
            self.search_widget.icon().pixmap(self.search_widget.icon().actualSize(QSize(32, 32))), color='#6B7280'))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.HoverEnter:
            obj.setIcon(self.loadSvg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color='#1F2937'))
        elif event.type() == QEvent.Type.HoverLeave:
            obj.setIcon(self.loadSvg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color='#6B7280'))
        return False

    def loadSvg(self, svg, color=None):
        img = QPixmap(svg)
        if color:
            qp = QPainter(img)
            qp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            qp.fillRect(img.rect(), QColor(color))
            qp.end()
        return QIcon(img)
