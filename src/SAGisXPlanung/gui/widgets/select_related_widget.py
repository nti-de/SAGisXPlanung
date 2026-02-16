from dataclasses import dataclass

from qgis.PyQt.QtCore import Qt, QAbstractListModel, QModelIndex, QSortFilterProxyModel, QSize, QItemSelectionModel
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLineEdit,
                             QListView, QLabel, QStyledItemDelegate, QHBoxLayout)
from sqlalchemy import select

from SAGisXPlanung import Session
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.core.helper import find_true_class
from SAGisXPlanung.gui.style import ApplicationColor
from SAGisXPlanung.gui.widgets.QXPlanTabWidget import QXPlanTabWidget

style = """
QLabel[objectName="description_label"] {{
    color: {_label_color_mute};
}}

QTabBar::tab[objectName="styled_tab_bar"] {{
    border: none;
    border-radius: 5px;
    min-width: 20ex;
    background-color: palette(window);
    padding: 10px;
    cursor: pointer;
}}

QTabBar::tab:hover[objectName="styled_tab_bar"] {{
    background-color: #e5e7eb;
}}

QTabBar::tab:selected[objectName="styled_tab_bar"] {{
    border: 1px solid #d1d5db;
    background-color: palette(base);
}}

QListView {{
    border: none;
    background-color: palette(window);
    outline: none;
}}

QListView::item {{
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 12px;
    margin-top: 10px;
    background-color: white;
}}

QListView::item:hover {{
    background-color: #f9fafb;
    border-color: #d1d5db;
}}

QListView::item:selected {{
    background-color: #eff6ff;
    border-color: #3b82f6;
}}

QLineEdit[objectName="search_edit"] {{
    padding: 8px 8px 8px 8px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background-color: white;
    margin-right: 10px;
}}

QLineEdit:focus[objectName="search_edit"] {{
    border-color: #3b82f6;
}}

QLabel[objectName="selected_count"] {{
    background-color: palette(alternate-base);
    border-radius: 5px;
    padding: 8px;
    font-weight: bold;
}}
"""


@dataclass
class RelatedObjectItem:
    code: str
    title: str
    description: str
    xplan_item: XPlanungItem


class RelatedObjectModel(QAbstractListModel):
    """Model for displaying related objects in the list view"""

    CodeRole = Qt.ItemDataRole.UserRole + 1
    TitleRole = Qt.ItemDataRole.UserRole + 2
    DescriptionRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._items):
            return None

        item = self._items[index.row()]

        if role == self.CodeRole:
            return item.code
        elif role == self.TitleRole:
            return item.title
        elif role == self.DescriptionRole:
            return item.description

        return None

    def setItems(self, items):
        """Set the list of items to display"""
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def addItem(self, item):
        """Add a single item to the model"""
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self.endInsertRows()


class RelatedObjectDelegate(QStyledItemDelegate):
    """Custom delegate for rendering list items with code, title and description"""

    def paint(self, painter, option, index):
        # Let the default paint handle selection/hover states
        super().paint(painter, option, index)

        # Get data
        code = index.data(RelatedObjectModel.CodeRole)
        title = index.data(RelatedObjectModel.TitleRole)
        description = index.data(RelatedObjectModel.DescriptionRole)

        painter.save()

        # Define text areas
        rect = option.rect
        text_rect = rect.adjusted(12, 16, -12, -16)

        # Draw code (bold, black)
        painter.setPen(Qt.GlobalColor.black)
        code_font = painter.font()
        code_font.setBold(True)
        code_font.setPointSize(10)
        painter.setFont(code_font)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, code)

        # Calculate vertical offset for title
        code_height = painter.fontMetrics().height()
        title_rect = text_rect.adjusted(0, code_height + 2, 0, 0)

        # Draw title (brown/orange color)
        painter.setPen(Qt.GlobalColor.darkRed)
        title_font = painter.font()
        title_font.setBold(False)
        title_font.setPointSize(9)
        painter.setFont(title_font)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, title)

        # Calculate vertical offset for description
        title_height = painter.fontMetrics().height()
        desc_rect = title_rect.adjusted(0, title_height + 2, 0, 0)

        # Draw description (gray, wrapped)
        painter.setPen(Qt.GlobalColor.gray)
        desc_font = painter.font()
        desc_font.setPointSize(9)
        painter.setFont(desc_font)

        # Word wrap description
        fm = painter.fontMetrics()
        desc_rect_height = rect.bottom() - desc_rect.top() - 8
        elided_text = fm.elidedText(description, Qt.TextElideMode.ElideRight,
                                    desc_rect.width() * 2)  # Allow 2 lines approximately
        painter.drawText(desc_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                         elided_text)

        painter.restore()

    def sizeHint(self, option, index):
        # Set fixed height for items
        return QSize(option.rect.width(), 85)


class SelectRelatedWidget(QWidget):
    def __init__(self, create_type: type, parent_item: XPlanungItem, orm_attribute: str, parent=None):
        super().__init__(parent)
        self.create_type = create_type
        self.parent_item = parent_item
        self.orm_attribute = orm_attribute

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Description
        description_label = QLabel(
            f"Erstellen Sie ein neues {create_type.__name__} oder wählen Sie ein bestehendes aus."
        )
        description_label.setWordWrap(True)
        description_label.setObjectName("description_label")
        main_layout.addWidget(description_label)

        # Tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.tabBar().setObjectName("styled_tab_bar")
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabBar().setExpanding(True)

        # Tab 1: Create new
        create_new_widget = QWidget(self)
        create_new_widget.setLayout(QVBoxLayout())
        create_new_widget.layout().setContentsMargins(0, 10, 0, 10)
        self.data_input_widget = QXPlanTabWidget(create_type)
        create_new_widget.layout().addWidget(self.data_input_widget)
        self.tab_widget.insertTab(0, create_new_widget, "Neu erstellen")

        # Tab 2: Search existing
        search_existing_widget = QWidget(self)
        search_layout = QVBoxLayout(search_existing_widget)
        search_layout.setContentsMargins(0, 10, 0, 10)

        # header with search field and selection count
        header_layout = QHBoxLayout()
        self.search_edit = QLineEdit(self)
        self.search_edit.setObjectName("search_edit")
        self.search_edit.addAction(QIcon(':/images/themes/default/search.svg'),
                                   QLineEdit.ActionPosition.LeadingPosition)
        self.search_edit.setPlaceholderText('Suchen...')
        self.search_edit.textChanged.connect(self.on_search_filter_changed)
        header_layout.addWidget(self.search_edit)
        header_layout.addWidget(QLabel("Ausgewählt:"))
        self.selected_count = QLabel("0")
        self.selected_count.setObjectName("selected_count")
        header_layout.addWidget(self.selected_count)
        search_layout.addLayout(header_layout)

        # List view with model
        self.list_view = QListView(self)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setSelectionMode(QListView.SelectionMode.MultiSelection)
        self.list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.list_view.setWordWrap(True)

        # Setup model
        self.model = RelatedObjectModel(self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterRole(RelatedObjectModel.CodeRole)

        self.list_view.setModel(self.proxy_model)
        self.list_view.selectionModel().selectionChanged.connect(self.on_view_selection_changed)

        # Setup custom delegate
        self.delegate = RelatedObjectDelegate(self)
        self.list_view.setItemDelegate(self.delegate)

        search_layout.addWidget(self.list_view)

        self.tab_widget.insertTab(1, search_existing_widget, "Vorhandene durchsuchen")

        main_layout.addWidget(self.tab_widget)

        # Apply styles
        qss = style.format(_label_color_mute=ApplicationColor.Grey600)
        self.setStyleSheet(qss)

        self._selected_ids: set[str] = set()
        self._syncing_selection = False
        self._load_data()

    def _load_data(self):
        items = []
        with Session() as session:
            orm_objects = session.query(self.create_type).all()
            true_class = find_true_class(self.parent_item.xtype, self.orm_attribute)
            stmt = select(true_class).filter_by(id=self.parent_item.xid)
            result = session.execute(stmt)
            parent_obj = result.scalar_one()
            selected_orm_objects = getattr(parent_obj, self.orm_attribute)
            for i, o in enumerate(orm_objects):
                xplan_item = XPlanungItem(xid=str(o.id), xtype=self.create_type)
                items.append(RelatedObjectItem(o.schluessel, o.gesetzlicheGrundlage, o.text, xplan_item))

            self.model.setItems(items)

            self._selected_ids = {str(o.id) for o in selected_orm_objects}
            self.restore_view_selection()
            self.update_selected_count()

    def on_view_selection_changed(self, selected, deselected):
        if self._syncing_selection:
            return

        for index in selected.indexes():
            src = self.proxy_model.mapToSource(index)
            if src.isValid():
                item = self.model._items[src.row()]
                self._selected_ids.add(item.xplan_item.xid)

        for index in deselected.indexes():
            src = self.proxy_model.mapToSource(index)
            if src.isValid():
                item = self.model._items[src.row()]
                self._selected_ids.discard(item.xplan_item.xid)

        self.update_selected_count()

    def restore_view_selection(self):
        sel_model = self.list_view.selectionModel()
        sel_model.blockSignals(True)
        sel_model.clearSelection()
        for row in range(self.proxy_model.rowCount()):
            proxy_index = self.proxy_model.index(row, 0)
            source_index = self.proxy_model.mapToSource(proxy_index)
            if not source_index.isValid():
                continue

            item = self.model._items[source_index.row()]
            if item.xplan_item.xid in self._selected_ids:
                sel_model.select(proxy_index, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)

        sel_model.blockSignals(False)

    def update_selected_count(self):
        self.selected_count.setText(str(len(self._selected_ids)))

    def on_search_filter_changed(self, filter_text: str):
        self._syncing_selection = True
        self.proxy_model.setFilterFixedString(filter_text)
        self.restore_view_selection()
        self._syncing_selection = False

        self.update_selected_count()

    def is_create_new(self):
        return self.tab_widget.currentIndex() == 0

    def get_selected_ids(self):
        return list(self._selected_ids)
