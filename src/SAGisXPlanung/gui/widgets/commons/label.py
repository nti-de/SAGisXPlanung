from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPainter, QFontMetrics
from qgis.PyQt.QtWidgets import QLabel


class ElideLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._elide_mode = Qt.TextElideMode.ElideRight
        self._cached_text = ""
        self._cached_elided_text = ""

    def setElideMode(self, mode: Qt.TextElideMode):
        self._elide_mode = mode
        self._cached_text = ""
        self.update()

    def elideMode(self):
        return self._elide_mode

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._cached_text = ""

    def paintEvent(self, event):
        if self._elide_mode == Qt.TextElideMode.ElideNone:
            super().paintEvent(event)
            return

        self._update_cached_texts()

        painter = QPainter(self)
        painter.setFont(self.font())
        rect = self.contentsRect()

        painter.drawText(rect,int(self.alignment()), self._cached_elided_text)

    def _update_cached_texts(self):
        txt = super().text()
        if self._cached_text == txt:
            return

        self._cached_text = txt
        fm = QFontMetrics(self.font())

        self._cached_elided_text = fm.elidedText(txt, self._elide_mode,self.width(), Qt.TextFlag.TextShowMnemonic)

        # ensure first character always visible
        if txt:
            show_first = txt[0] + "..."
            self.setMinimumWidth(fm.horizontalAdvance(show_first) + 1)

