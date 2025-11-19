from dataclasses import dataclass

from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QSortFilterProxyModel, QSize, QItemSelectionModel
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLineEdit,
                             QListView, QLabel, QStyledItemDelegate, QStyleOptionViewItem)
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

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
}}

QLineEdit:focus[objectName="search_edit"] {{
    border-color: #3b82f6;
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

    CodeRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    DescriptionRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index, role=Qt.DisplayRole):
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
        painter.setPen(Qt.black)
        code_font = painter.font()
        code_font.setBold(True)
        code_font.setPointSize(10)
        painter.setFont(code_font)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, code)

        # Calculate vertical offset for title
        code_height = painter.fontMetrics().height()
        title_rect = text_rect.adjusted(0, code_height + 2, 0, 0)

        # Draw title (brown/orange color)
        painter.setPen(Qt.darkRed)
        title_font = painter.font()
        title_font.setBold(False)
        title_font.setPointSize(9)
        painter.setFont(title_font)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop, title)

        # Calculate vertical offset for description
        title_height = painter.fontMetrics().height()
        desc_rect = title_rect.adjusted(0, title_height + 2, 0, 0)

        # Draw description (gray, wrapped)
        painter.setPen(Qt.gray)
        desc_font = painter.font()
        desc_font.setPointSize(9)
        painter.setFont(desc_font)

        # Word wrap description
        fm = painter.fontMetrics()
        desc_rect_height = rect.bottom() - desc_rect.top() - 8
        elided_text = fm.elidedText(description, Qt.ElideRight,
                                    desc_rect.width() * 2)  # Allow 2 lines approximately
        painter.drawText(desc_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
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

        # Search field
        self.search_edit = QLineEdit(self)
        self.search_edit.setObjectName("search_edit")
        self.search_edit.addAction(QIcon(':/images/themes/default/search.svg'),
                                   QLineEdit.LeadingPosition)
        self.search_edit.setPlaceholderText('Suchen...')
        self.search_edit.textChanged.connect(self.on_search_filter_changed)
        search_layout.addWidget(self.search_edit)

        # List view with model
        self.list_view = QListView(self)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setSelectionMode(QListView.MultiSelection)
        self.list_view.setEditTriggers(QListView.NoEditTriggers)
        self.list_view.setWordWrap(True)

        # Setup model
        self.model = RelatedObjectModel(self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterRole(RelatedObjectModel.CodeRole)

        self.list_view.setModel(self.proxy_model)

        # Setup custom delegate
        self.delegate = RelatedObjectDelegate(self)
        self.list_view.setItemDelegate(self.delegate)

        search_layout.addWidget(self.list_view)

        self.tab_widget.insertTab(1, search_existing_widget, "Vorhandene durchsuchen")

        main_layout.addWidget(self.tab_widget)

        # Apply styles
        qss = style.format(_label_color_mute=ApplicationColor.Grey600)
        self.setStyleSheet(qss)

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
            selected_orm_ids = [o.id for o in selected_orm_objects] if selected_orm_objects else []
            for i, o in enumerate(orm_objects):
                xplan_item = XPlanungItem(xid=str(o.id), xtype=self.create_type)
                items.append(RelatedObjectItem(o.schluessel, o.gesetzlicheGrundlage, o.text, xplan_item))

            self.model.setItems(items)

            if selected_orm_ids:
                for src_row, o in enumerate(orm_objects):
                    if o.id in selected_orm_ids:
                        source_index = self.model.index(src_row, 0)
                        proxy_index = self.proxy_model.mapFromSource(source_index)
                        if proxy_index.isValid():
                            self.list_view.selectionModel().select(proxy_index, QItemSelectionModel.Select)

    def on_search_filter_changed(self, filter_text: str):
        """Filter the list based on search text"""
        self.proxy_model.setFilterFixedString(filter_text)

    def is_create_new(self):
        return self.tab_widget.currentIndex() == 0

    def get_selected_ids(self):
        """
        Return the list of selected ORM ids (native type).
        We stored xid as string in XPlanungItem; convert back to original id type if needed.
        """
        selected = []
        sel_model = self.list_view.selectionModel()
        if not sel_model:
            return selected

        for proxy_index in sel_model.selectedIndexes():
            # map to source index to access the model._items list
            source_index = self.proxy_model.mapToSource(proxy_index)
            if not source_index.isValid():
                continue
            row = source_index.row()
            try:
                item: RelatedObjectItem = self.model._items[row]
            except (IndexError, AttributeError):
                continue
            selected.append(item.xplan_item.xid)
        return selected
