import os
from pathlib import Path

from PyQt5.QtCore import QSortFilterProxyModel, QPoint
from PyQt5.QtGui import QColor, QPen, QPolygon, QBrush
from PyQt5.QtWidgets import QCompleter, QTreeView, QAbstractItemView, QStyledItemDelegate, QListView, QProxyStyle
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtWidgets import (QLabel, QStyleOptionFrame, QStyle, QComboBox, QStyleOptionComboBox, QStylePainter)
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QPaintEvent, QPainter

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.gui.style.styles import RemoveFrameFocusProxyStyle, FixComboStyleDelegate, HighlightRowDelegate, \
    HighlightRowProxyStyle


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


class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super(SearchableComboBox, self).__init__(parent)

        self.setFocusPolicy(Qt.ClickFocus)
        self.setEditable(True)

        # prevent insertions into combobox
        self.setInsertPolicy(QComboBox.NoInsert)

        # filter model for matching items
        self.filter_model = QSortFilterProxyModel(self)
        self.filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.filter_model.setSourceModel(self.model())

        # completer that uses filter model
        self.completer = QCompleter(self.filter_model, self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        icon_path = Path(BASE_DIR, 'gui', 'resources', 'arrow_drop_down.svg').as_posix()
        self.setStyleSheet(f"""
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;      
                border: none;        
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: url({icon_path});
                width: 24px; 
                height: 24px;
            }}
        """)

        view_sheet_style = """      
            QAbstractItemView { 
                background-color: white;
                selection-background-color: #d1d5db;
                selection-color: black;
            }    
            QAbstractItemView::item { 
                border: none;
                padding: 5px; 
            }
            
            QAbstractItemView QScrollBar:vertical {
                background: #f9fafb;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            
            QAbstractItemView QScrollBar::handle:vertical {
                background: #d1d5db;
                border-radius: 4px;
                min-height: 20px;
            }
            
            QAbstractItemView QScrollBar::handle:vertical:hover {
                background: #9ca3af;
            }
            
            QAbstractItemView QScrollBar::add-line:vertical,
            QAbstractItemView QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        self.view().setStyleSheet(view_sheet_style)
        self._proxy_style = RemoveFrameFocusProxyStyle('Fusion')
        self._proxy_style.setParent(self)
        self.view().setStyle(self._proxy_style)

        self.completer_view = QListView(self)
        self.completer_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.completer_view.setMouseTracking(True)
        self.completer_view.setStyleSheet(view_sheet_style)
        self.completer_view.setStyle(self._proxy_style)
        self.completer.setPopup(self.completer_view)

        # QT-BUG: completer is the parent of the popup view (not the combobox itself)
        # QCompleter is a QObject subclass and cant be styled however
        # For stylesheets to take effect, set a custom styled item delegate which can paint the qss
        self.completer.popup().setItemDelegate(QStyledItemDelegate())

        # QT-BUG: reset item delegate, otherwise stylesheets are not taking effect
        # similar issue as directly above
        # https://stackoverflow.com/questions/13308341/qcombobox-abstractitemviewitem
        self.setItemDelegate(QStyledItemDelegate())

        # connect signals
        self.lineEdit().textEdited[str].connect(self.filter_model.setFilterFixedString)
        self.completer.activated.connect(self.on_completer_activated)

    def on_completer_activated(self, text):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            self.activated[str].emit(self.itemText(index))

    def setModel(self, model):
        super(SearchableComboBox, self).setModel(model)
        self.filter_model.setSourceModel(model)
        self.completer.setModel(self.filter_model)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.filter_model.setFilterKeyColumn(column)
        super(SearchableComboBox, self).setModelColumn(column)