from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtWidgets import (QLabel, QStyleOptionFrame, QStyle, QComboBox, QStyleOptionComboBox, QStylePainter)
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QPaintEvent, QPainter

from SAGisXPlanung.gui.style.styles import RemoveFrameFocusProxyStyle, FixComboStyleDelegate


class ElideLabel(QLabel):
    _elideMode = Qt.ElideMiddle

    def elideMode(self):
        return self._elideMode

    def setElideMode(self, mode):
        if self._elideMode != mode and mode != Qt.ElideNone:
            self._elideMode = mode
            self.updateGeometry()

    def minimumSizeHint(self):
        return self.sizeHint()

    def sizeHint(self):
        hint = self.fontMetrics().boundingRect(self.text()).size()
        l, t, r, b = self.getContentsMargins()
        margin = self.margin() * 2
        return QSize(
            min(100, hint.width()) + l + r + margin,
            min(self.fontMetrics().height(), hint.height()) + t + b + margin
        )

    def paintEvent(self, event):
        qp = QPainter(self)
        opt = QStyleOptionFrame()
        self.initStyleOption(opt)
        self.style().drawControl(QStyle.CE_ShapedFrame, opt, qp, self)
        l, t, r, b = self.getContentsMargins()
        margin = self.margin()
        try:
            # since Qt >= 5.11
            m = self.fontMetrics().horizontalAdvance('x') / 2 - margin
        except:
            m = self.fontMetrics().width('x') / 2 - margin
        r = self.contentsRect().adjusted(int(margin + m), margin, int(-(margin + m)), -margin)
        qp.drawText(r, self.alignment(), self.fontMetrics().elidedText(self.text(), self.elideMode(), r.width()))


class MultiSelectComboBox(QComboBox):
    def __init__(self, empty_text='Auswählen...', parent=None):
        super(MultiSelectComboBox, self).__init__(parent)
        self.setModel(QStandardItemModel(self))

        self.model().itemChanged.connect(self.on_item_changed)
        self.view().pressed.connect(self.on_item_pressed)

        self.setEditable(False)
        self.setItemDelegate(FixComboStyleDelegate())
        self.setStyleSheet("QListView::item { padding: 5px }")
        self._proxy_style = RemoveFrameFocusProxyStyle('Fusion')
        self._proxy_style.setParent(self)
        self.setStyle(self._proxy_style)

        self.empty_text = empty_text
        self.display_text = self.empty_text

    def add_item(self, text, data=None, check_state=Qt.Unchecked):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(data, Qt.UserRole)
        self.model().appendRow(item)

        item.setCheckState(check_state)

    def on_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

    def on_item_changed(self, item: QStandardItem):
        self.update_display_text()

    def checked_items(self, role=Qt.DisplayRole):
        checked_items = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.Checked:
                checked_items.append(item.data(role))
        return checked_items

    def update_display_text(self):
        checked_items = self.checked_items()
        self.display_text = ", ".join(checked_items) if checked_items else self.empty_text

    def paintEvent(self, event: QPaintEvent=None):
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        p = QStylePainter(self)
        p.drawComplexControl(QStyle.CC_ComboBox, opt)

        text_rect = self.style().subControlRect(QStyle.CC_ComboBox, opt, QStyle.SC_ComboBoxEditField)
        opt.currentText = p.fontMetrics().elidedText(self.display_text, Qt.ElideRight, text_rect.width())
        p.drawControl(QStyle.CE_ComboBoxLabel, opt)

    def sizeHint(self):
        hint = super().sizeHint()
        return QSize(
            min(100, hint.width()),
            hint.height()
        )


