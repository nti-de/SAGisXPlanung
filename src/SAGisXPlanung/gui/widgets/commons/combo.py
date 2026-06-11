from pathlib import Path

from qgis.PyQt.QtCore import QSize, Qt, QSortFilterProxyModel
from qgis.PyQt.QtWidgets import (QStyle, QComboBox, QStyleOptionComboBox, QStylePainter,
                                 QCompleter, QAbstractItemView, QStyledItemDelegate, QListView)
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QPaintEvent

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.gui.style import RemoveFrameFocusProxyStyle, FixComboStyleDelegate


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

    def add_item(self, text, data=None, check_state=Qt.CheckState.Unchecked):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setData(data, Qt.ItemDataRole.UserRole)
        self.model().appendRow(item)

        item.setCheckState(check_state)

    def on_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)

    def on_item_changed(self, item: QStandardItem):
        self.update_display_text()

    def checked_items(self, role=Qt.ItemDataRole.DisplayRole):
        checked_items = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_items.append(item.data(role))
        return checked_items

    def update_display_text(self):
        checked_items = self.checked_items()
        self.display_text = ", ".join(checked_items) if checked_items else self.empty_text

    def paintEvent(self, event: QPaintEvent=None):
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        p = QStylePainter(self)
        p.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt)

        text_rect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxEditField)
        opt.currentText = p.fontMetrics().elidedText(self.display_text, Qt.TextElideMode.ElideRight, text_rect.width())
        p.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opt)

    def sizeHint(self):
        hint = super().sizeHint()
        return QSize(
            min(100, hint.width()),
            hint.height()
        )


class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super(SearchableComboBox, self).__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setEditable(True)

        # prevent insertions into combobox
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # filter model for matching items
        self.filter_model = QSortFilterProxyModel(self)
        self.filter_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter_model.setSourceModel(self.model())

        # completer that uses filter model
        self.completer = QCompleter(self.filter_model, self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

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
        self.completer_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
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

        self.setMinimumContentsLength(15)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)

        # connect signals
        self.lineEdit().textEdited[str].connect(self.on_text_edited)
        self.completer.activated.connect(self.on_completer_activated)

    def on_completer_activated(self, text):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            self.activated[str].emit(self.itemText(index))

    def on_text_edited(self, text):
        self.filter_model.setFilterFixedString(text)

        selected_text = self.itemText(self.currentIndex())
        if self.currentIndex() > 0 and text != selected_text:
            self.setCurrentIndex(-1)

    def setModel(self, model):
        super(SearchableComboBox, self).setModel(model)
        self.filter_model.setSourceModel(model)
        self.completer.setModel(self.filter_model)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.filter_model.setFilterKeyColumn(column)
        super(SearchableComboBox, self).setModelColumn(column)