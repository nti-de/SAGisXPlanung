import logging
import os
from dataclasses import dataclass

from qgis.PyQt.QtCore import Qt, QAbstractListModel, QModelIndex, QSortFilterProxyModel, QSize, QItemSelectionModel, QRect
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLineEdit, QStyleOptionButton, QStyle, QApplication,
                             QListView, QLabel, QStyledItemDelegate, QHBoxLayout, QStyleOptionViewItem, QCheckBox)
from sqlalchemy import select, inspect

from SAGisXPlanung import Session, BASE_DIR
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.core.helper import find_true_class
from SAGisXPlanung.core.mixins.mixins import PlanLinkedMixin
from SAGisXPlanung.gui.style import ApplicationColor, load_svg, EmptyStateFilter
from SAGisXPlanung.gui.widgets.QXPlanTabWidget import QXPlanTabWidget

logger = logging.getLogger(__name__)

EMPTY_STATE_FILTER_HINT = "Suchbegriff oder Filter entfernen um alle Objekte zu finden..."

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


class RelatedObjectProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plan_xid = None
        self.filter_current_plan = False

    def setPlanFilter(self, plan_xid: str | None, enabled: bool):
        self.plan_xid = plan_xid
        self.filter_current_plan = enabled
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)

        code = model.data(index, RelatedObjectModel.CodeRole) or ""
        title = model.data(index, RelatedObjectModel.TitleRole) or ""
        desc = model.data(index, RelatedObjectModel.DescriptionRole) or ""

        # Text filter
        search = self.filterRegularExpression().pattern().lower()
        if search:
            combined = f"{code} {title} {desc}".lower()
            if search not in combined:
                return False

        # Plan filter
        if self.filter_current_plan and self.plan_xid:
            item = model._items[source_row]
            if self.plan_xid not in item.xplan_item.plan_xids:
                return False

        return True


class RelatedObjectDelegate(QStyledItemDelegate):
    """Debug version: paints all layout rects with bright red outlines"""

    CHECKBOX_SIZE = 18
    LEFT_MARGIN = 12
    CHECKBOX_TEXT_SPACING = 12

    def paint(self, painter, option, index):
        rect = option.rect.adjusted(0, 5, 0, -5)
        option_copy = QStyleOptionViewItem(option)
        option_copy.rect = rect

        option.widget.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_PanelItemViewItem,
            option_copy,
            painter,
            option.widget
        )

        code = index.data(RelatedObjectModel.CodeRole)
        title = index.data(RelatedObjectModel.TitleRole)
        description = index.data(RelatedObjectModel.DescriptionRole)

        painter.save()

        rect = option_copy.rect
        # -------------------------
        # Checkbox
        # -------------------------
        indicator_width = QApplication.style().pixelMetric(
            QStyle.PixelMetric.PM_IndicatorWidth
        )
        indicator_height = QApplication.style().pixelMetric(
            QStyle.PixelMetric.PM_IndicatorHeight
        )

        checkbox_rect = QRect(
            rect.left() + self.LEFT_MARGIN,
            rect.top() + (rect.height() - indicator_height) // 2,
            indicator_width,
            indicator_height
        )

        checkbox_option = QStyleOptionButton()
        checkbox_option.rect = checkbox_rect
        checkbox_option.state |= QStyle.StateFlag.State_Enabled

        if option.state & QStyle.StateFlag.State_Selected:
            checkbox_option.state |= QStyle.StateFlag.State_On
        else:
            checkbox_option.state |= QStyle.StateFlag.State_Off

        QApplication.style().drawControl(
            QStyle.ControlElement.CE_CheckBox,
            checkbox_option,
            painter
        )

        # -------------------------
        # Text content area
        # -------------------------
        padding = 12

        text_left = checkbox_rect.right() + self.CHECKBOX_TEXT_SPACING
        text_rect = QRect(
            text_left,
            rect.top() + padding,
            rect.width() - (text_left - rect.left()) - padding,
            rect.height() - (2 * padding)
        )

        # -------------------------
        # Code (Bold Title)
        # -------------------------
        painter.setPen(Qt.GlobalColor.black)
        code_font = painter.font()
        code_font.setBold(True)
        code_font.setPointSize(10)
        painter.setFont(code_font)

        code_height = painter.fontMetrics().height()
        code_rect = QRect(
            text_rect.left(),
            text_rect.top(),
            text_rect.width(),
            code_height
        )
        fm = painter.fontMetrics()
        elided_code_text = fm.elidedText(code,  Qt.TextElideMode.ElideRight, code_rect.width())

        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(code_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, elided_code_text)
        # -------------------------
        # Title (is subtitle)
        # -------------------------
        title_font = painter.font()
        title_font.setBold(False)
        title_font.setPointSize(9)
        painter.setFont(title_font)

        title_height = painter.fontMetrics().height()

        title_rect = QRect(
            text_rect.left(),
            code_rect.bottom() + 3,
            text_rect.width(),
            title_height
        )

        painter.setPen(Qt.GlobalColor.darkRed)
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            title
        )

        # -------------------------
        # Description
        # -------------------------
        desc_font = painter.font()
        desc_font.setPointSize(9)
        painter.setFont(desc_font)

        desc_rect = QRect(
            text_rect.left(),
            title_rect.bottom() + 3,
            text_rect.width(),
            text_rect.bottom() - (title_rect.bottom() + 3)
        )

        fm = painter.fontMetrics()
        elided_text = fm.elidedText(description, Qt.TextElideMode.ElideRight, desc_rect.width())

        painter.setPen(Qt.GlobalColor.gray)
        painter.drawText(
            desc_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            elided_text
        )

        painter.restore()

    def sizeHint(self, option, index):
        # Set fixed height for items
        return QSize(option.rect.width(), 92)


class SelectRelatedWidget(QWidget):
    def __init__(self, create_type: type, parent_item: XPlanungItem, orm_attribute: str, plan_xid: str = None, parent=None):
        super().__init__(parent)
        self.create_type = create_type
        self.parent_item = parent_item
        self.orm_attribute = orm_attribute
        self.plan_xid = plan_xid

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

        sub_header_layout = QHBoxLayout()
        self.select_filter_current_plan = QCheckBox("Nur Objekte des Plans")
        self.select_filter_current_plan.setChecked(True)
        self.select_filter_current_plan.stateChanged.connect(self.on_filter_current_plan_changed)
        sub_header_layout.addWidget(self.select_filter_current_plan)
        search_layout.addLayout(sub_header_layout)

        # List view with model
        self.list_view = QListView(self)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setSelectionMode(QListView.SelectionMode.MultiSelection)
        self.list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.list_view.setWordWrap(True)
        # self.list_view.setSpacing(10)
        self.list_view.setContentsMargins(0, 0, 0, 0)

        # Setup model
        self.model = RelatedObjectModel(self)
        self.proxy_model = RelatedObjectProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setPlanFilter(self.plan_xid, True)

        self.list_view.setModel(self.proxy_model)
        self.list_view.selectionModel().selectionChanged.connect(self.on_view_selection_changed)

        # Setup custom delegate and event filters
        self.delegate = RelatedObjectDelegate(self)
        self.list_view.setItemDelegate(self.delegate)
        self.list_empty_state = EmptyStateFilter(self.list_view)
        self.list_empty_state.set_icon(os.path.join(BASE_DIR, 'gui/resources/warning.svg')) \
            .set_icon_size(16) \
            .set_title("Keine Objekte gefunden") \
            .set_subtitle(EMPTY_STATE_FILTER_HINT)


        search_layout.addWidget(self.list_view)

        self.tab_widget.insertTab(0, create_new_widget, "Neu erstellen")
        self.tab_widget.insertTab(1, search_existing_widget, "Vorhandene durchsuchen")
        add_circle_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/add_circle.svg'), color=ApplicationColor.Tertiary)
        manage_search_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/manage_search.svg'), color=ApplicationColor.Tertiary)
        self.tab_widget.tabBar().setTabIcon(0, add_circle_icon)
        self.tab_widget.tabBar().setTabIcon(1, manage_search_icon)

        main_layout.addWidget(self.tab_widget)

        # Apply styles
        qss = style.format(_label_color_mute=ApplicationColor.Grey600)
        self.setStyleSheet(qss)

        self._selected_ids: set[str] = set()
        self._syncing_selection = False
        self._load_data()

    def _load_data(self):
        self._all_items = []
        with Session() as session:
            orm_objects = session.query(self.create_type).all()
            true_class = find_true_class(self.parent_item.xtype, self.orm_attribute)
            stmt = select(true_class).filter_by(id=self.parent_item.xid)
            result = session.execute(stmt)
            parent_obj = result.scalar_one()
            selected_orm_objects = getattr(parent_obj, self.orm_attribute)

            for i, o in enumerate(orm_objects):
                item_plan_xids = self._get_plan_xids(o)
                xplan_item = XPlanungItem(
                    xid=str(o.id),
                    xtype=self.create_type,
                )
                xplan_item.plan_xids = set(str(pid) for pid in item_plan_xids) if item_plan_xids else set()
                related_item = RelatedObjectItem(o.schluessel, o.gesetzlicheGrundlage, o.text, xplan_item)
                self._all_items.append(related_item)

            self._selected_ids = {str(o.id) for o in selected_orm_objects}
            self.model.setItems(self._all_items)

            self.restore_view_selection()
            self.update_selected_count()

    def _get_plan_xids(self, orm_object) -> list[str | None] | None:
        if orm_object is None:
            return []

        orm_cls = type(orm_object)

        if not issubclass(orm_cls, PlanLinkedMixin):
            logger.warning(f"{orm_cls.__name__} "f"does not implement PlanLinkedMixin")
            return []

        session = inspect(orm_object).session
        if session is None:
            raise ValueError("Object is not attached to a session.")

        object_id = inspect(orm_object).identity[0]

        try:
            plan_ids = orm_cls.get_plan_xids(session, object_id)
            return plan_ids

        except Exception as e:
            logger.error(f"{orm_cls.__name__} ({object_id}): {e}")
            return []

    def on_filter_current_plan_changed(self, state):
        current_plan_filter_is_checked = self.select_filter_current_plan.isChecked()
        self._syncing_selection = True

        self.proxy_model.setPlanFilter(self.plan_xid, current_plan_filter_is_checked)
        self.proxy_model.invalidateFilter()
        self.restore_view_selection()
        self._syncing_selection = False

        if current_plan_filter_is_checked:
            self.list_empty_state.set_subtitle(EMPTY_STATE_FILTER_HINT)
        else:
            self.list_empty_state.set_subtitle("")

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
        self.proxy_model.setFilterRegularExpression(filter_text)
        self.restore_view_selection()
        self._syncing_selection = False

        if filter_text:
            self.list_empty_state.set_subtitle(EMPTY_STATE_FILTER_HINT)
        else:
            self.list_empty_state.set_subtitle("")

    def is_create_new(self):
        return self.tab_widget.currentIndex() == 0

    def get_selected_ids(self):
        return list(self._selected_ids)
