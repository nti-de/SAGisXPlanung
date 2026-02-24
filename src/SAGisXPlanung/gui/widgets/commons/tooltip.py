
from qgis.PyQt.QtCore import QEvent, QObject, QPoint, QTimer, Qt, QPropertyAnimation, QModelIndex, QRect
from qgis.PyQt.QtGui import QColor, QHelpEvent
from qgis.PyQt.QtWidgets import (QApplication, QFrame, QGraphicsDropShadowEffect,
                             QHBoxLayout, QLabel, QWidget, QAbstractItemView, QStyleOptionViewItem,
                             QTableView)

class ToolTip(QFrame):
    def __init__(self, text='', parent=None):
        super().__init__(parent=parent)
        self._text = text
        self._duration = 1000

        self.container = self._createContainer()
        self.timer = QTimer(self)

        self.setLayout(QHBoxLayout())
        self.containerLayout = QHBoxLayout(self.container)
        self.label = QLabel(text, self)

        # set layout
        self.layout().setContentsMargins(12, 8, 12, 12)
        self.layout().addWidget(self.container)
        self.containerLayout.addWidget(self.label)
        self.containerLayout.setContentsMargins(8, 6, 8, 6)

        # add opacity effect
        self.opacityAni = QPropertyAnimation(self, b'windowOpacity', self)
        self.opacityAni.setDuration(150)

        # add shadow
        self.shadowEffect = QGraphicsDropShadowEffect(self)
        self.shadowEffect.setBlurRadius(25)
        self.shadowEffect.setColor(QColor(0, 0, 0, 50))
        self.shadowEffect.setOffset(0, 5)
        self.container.setGraphicsEffect(self.shadowEffect)

        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

        # set style
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self._set_style()

    def text(self):
        return self._text

    def setText(self, text):
        """ set text on tooltip """
        self._text = text
        self.label.setText(text)
        self.container.adjustSize()
        self.adjustSize()

    def duration(self):
        return self._duration

    def setDuration(self, duration: int):
        """ set tooltip duration in milliseconds

        Parameters
        ----------
        duration: int
            display duration in milliseconds, if `duration <= 0`, tooltip won't disappear automatically
        """
        self._duration = duration

    def _set_style(self):
        """ set style sheet """
        self.container.setObjectName("container")
        self.label.setObjectName("contentLabel")

        self.setStyleSheet("""
            ToolTip {
                border-radius: 4px;
            }
            
            ToolTip>#container {
                border: 1px solid rgba(0, 0, 0, 0.06);
                background-color: rgb(249, 249, 249);
                border-radius: 4px;
            }
            
            ToolTip>#container[transparent=true] {
                background-color: transparent;
            }
            
            
            QLabel {
                background-color: transparent;
                font: 12px --FontFamilies;
                border: none;
                color: black;
            }"""
        )

        self.label.adjustSize()
        self.adjustSize()

    def _createContainer(self):
        return QFrame(self)

    def showEvent(self, e):
        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.start()

        self.timer.stop()
        if self.duration() > 0:
            self.timer.start(self._duration + self.opacityAni.duration())

        super().showEvent(e)

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)

    def adjust_pos(self, widget, model_index=None):
        if isinstance(widget, QAbstractItemView):
            if model_index:
                rect = widget.visualRect(model_index)
            else:
                rect = QRect()
            pos = widget.mapToGlobal(rect.bottomLeft())
            x = pos.x()
            y = pos.y() - self.height() + 10
        else:
            pos = widget.mapToGlobal(QPoint())
            x = pos.x() + widget.width() // 2 - self.width() // 2
            y = pos.y() - self.height()

            screen = widget.window().windowHandle().screen()
            rect = screen.geometry()
            x = max(rect.left(), min(x, rect.right() - self.width() - 4))
            y = max(rect.top(), min(y, rect.bottom() - self.height() - 4))

        self.move(QPoint(x, y))

