from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QPainter
from qgis.PyQt.QtWidgets import QStyle, QStyleOptionFrame, QLabel


class ElideLabel(QLabel):
    _elideMode = Qt.TextElideMode.ElideMiddle

    def elideMode(self):
        return self._elideMode

    def setElideMode(self, mode):
        if self._elideMode != mode and mode != Qt.TextElideMode.ElideNone:
            self._elideMode = mode
            self.updateGeometry()

    def minimumSizeHint(self):
        return self.sizeHint()

    def sizeHint(self):
        hint = self.fontMetrics().boundingRect(self.text()).size()
        l, t, r, b = self.layout().getContentsMargins()
        margin = self.margin() * 2
        return QSize(
            min(100, hint.width()) + l + r + margin,
            min(self.fontMetrics().height(), hint.height()) + t + b + margin
        )

    def paintEvent(self, event):
        qp = QPainter(self)
        opt = QStyleOptionFrame()
        self.initStyleOption(opt)
        self.style().drawControl(QStyle.ControlElement.CE_ShapedFrame, opt, qp, self)
        margin = self.margin()
        try:
            # since Qt >= 5.11
            m = self.fontMetrics().horizontalAdvance('x') / 2 - margin
        except:
            m = self.fontMetrics().width('x') / 2 - margin
        r = self.contentsRect().adjusted(int(margin + m), margin, int(-(margin + m)), -margin)
        qp.drawText(r, self.alignment(), self.fontMetrics().elidedText(self.text(), self.elideMode(), r.width()))
