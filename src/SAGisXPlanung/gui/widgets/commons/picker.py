import math
import os
import re
from dataclasses import dataclass
from enum import auto, Enum
from typing import Any

from qgis.PyQt.QtCore import QAbstractListModel, QModelIndex, pyqtSignal, QSize, QRect, QPoint, QEvent, QRectF, \
    QSortFilterProxyModel, QSettings, QDateTime, Qt
from qgis.PyQt.QtGui import QPalette, QPainter, QColor, QIcon, QFontMetrics, QPen, QBrush, QFont, QPainterPath
from qgis.PyQt.QtWidgets import QVBoxLayout, QFrame, QLabel, QListView, QLineEdit, QProxyStyle, \
    QStyledItemDelegate, QStyleOptionViewItem, QHBoxLayout, QPushButton, QButtonGroup, QApplication, \
    QToolTip, QToolButton, QStylePainter, QStyleOptionComboBox, QStyle, QWidget, QComboBox

from SAGisXPlanung import PYQT5, BASE_DIR
from SAGisXPlanung.gui.style import load_svg, ApplicationColor, EmptyStateFilter
from SAGisXPlanung.gui.style.styles import ModernScrollBarStyle


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


@dataclass
class PickerItem:
    id: str
    text: str
    category: str | None = None
    is_favorite: bool = False
    data: Any = None
    search_terms: tuple[str, ...] = ()
    _search_stack: str = ""

    def __post_init__(self):
        self._recompute_search_stack()

    def _recompute_search_stack(self):
        parts = (self.text, *self.search_terms)
        self._search_stack = " ".join(p for p in parts if p).casefold()

    def update_text(self, text: str):
        self.text = text
        self._recompute_search_stack()

    def update_search_terms(self, search_terms: tuple[str, ...]):
        self.search_terms = tuple(search_terms)
        self._recompute_search_stack()


@dataclass
class Category:
    id: str
    label: str
    checked: bool = False


class PickerSortMode(Enum):
    NAME = auto()
    LAST_USED = auto()


class ItemMetadataStore:
    def __init__(self, settings_key='plugins/xplanung/picker/item_metadata'):
        self._settings = QSettings()
        self._settings_key = settings_key

    def _data(self) -> dict:
        data = self._settings.value(self._settings_key, {})
        return data if isinstance(data, dict) else {}

    def _save(self, data: dict):
        self._settings.setValue(self._settings_key, data)

    def get(self, item_id: str, field: str, default=None):
        return self._data().get(item_id, {}).get(field, default)

    def set(self, item_id: str, field: str, value):
        data = self._data()
        data.setdefault(item_id, {})[field] = value
        self._save(data)

    def unset(self, item_id: str, field: str):
        data = self._data()
        entry = data.get(item_id)
        if entry and field in entry:
            del entry[field]
            if not entry:
                del data[item_id]
            self._save(data)

    def forget_item(self, item_id: str):
        """Drop all metadata for an item, e.g. when it's removed from the picker."""
        data = self._data()
        if item_id in data:
            del data[item_id]
            self._save(data)

    def prune(self, valid_ids: set):
        """Drop metadata for any item id not in valid_ids (call after set_items)."""
        data = self._data()
        stale = [item_id for item_id in data if item_id not in valid_ids]
        if not stale:
            return
        for item_id in stale:
            del data[item_id]
        self._save(data)

    def clear(self):
        self._settings.remove(self._settings_key)

    def is_favorite(self, item_id: str) -> bool:
        return bool(self.get(item_id, 'favorite', False))

    def set_favorite(self, item_id: str, favorite: bool):
        if favorite:
            self.set(item_id, 'favorite', True)
        else:
            self.unset(item_id, 'favorite')

    def last_used(self, item_id: str) -> int | None:
        return self.get(item_id, 'last_used')

    def mark_used(self, item_id: str):
        self.set(item_id, 'last_used', QDateTime.currentDateTimeUtc().toSecsSinceEpoch())


class CategoryChipModel(QAbstractListModel):
    IdRole = Qt.ItemDataRole.UserRole + 1
    LabelRole = Qt.ItemDataRole.UserRole + 2
    CheckedRole = Qt.ItemDataRole.UserRole + 3

    categoriesChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._categories: list[Category] = []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._categories)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        category = self._categories[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return category.label

        if role == self.IdRole:
            return category.id

        if role == self.LabelRole:
            return category.label

        if role == self.CheckedRole:
            return category.checked

        return None

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.DisplayRole):
        if role == self.CheckedRole:
            category = self._categories[index.row()]
            category.checked = value
            self.dataChanged.emit(index, index, [self.CheckedRole])
            self.categoriesChanged.emit()

    def addCategory(self, category: Category):
        if self.contains(category.id):
            return

        row = len(self._categories)

        self.beginInsertRows(QModelIndex(), row, row)
        self._categories.append(category)
        self.endInsertRows()

        self.categoriesChanged.emit()

    def removeCategory(self, category_id: str):
        row = self.indexOf(category_id)

        if row < 0:
            return

        self.beginRemoveRows(QModelIndex(), row, row)
        self._categories.pop(row)
        self.endRemoveRows()

        self.categoriesChanged.emit()

    def setCategories(self, categories: list[Category]):
        self.beginResetModel()
        self._categories = list(categories)
        self.endResetModel()

        self.categoriesChanged.emit()

    def clear(self):
        if not self._categories:
            return

        self.beginResetModel()
        self._categories.clear()
        self.endResetModel()

        self.categoriesChanged.emit()

    def contains(self, category_id: str) -> bool:
        return self.indexOf(category_id) >= 0

    def indexOf(self, category_id: str) -> int:
        for row, category in enumerate(self._categories):
            if category.id == category_id:
                return row

        return -1

    def categories(self) -> list[Category]:
        return list(self._categories)

    def ids(self) -> list[str]:
        return [category.id for category in self._categories]


class CategoryChipDelegate(QStyledItemDelegate):
    HORIZONTAL_PADDING = 10
    CLOSE_WIDTH = 12
    CLOSE_GAP = 5
    CHIP_HEIGHT = 20

    # Unselected
    BG_COLOR = QColor(ApplicationColor.SurfaceStrong)
    BORDER_COLOR = QColor(ApplicationColor.Border)
    TEXT_COLOR = QColor(ApplicationColor.PrimaryText)

    # Selected
    SELECTED_BG_COLOR = QColor(ApplicationColor.PrimaryLight)
    SELECTED_BORDER_COLOR = QColor(ApplicationColor.Primary)
    SELECTED_TEXT_COLOR = QColor(ApplicationColor.OnPrimary)

    # Hover
    HOVER_BG_COLOR = QColor(ApplicationColor.SurfaceSelected)
    SELECTED_HOVER_BG_COLOR = QColor(ApplicationColor.Primary)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.close_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/close.svg'), color=self.SELECTED_TEXT_COLOR)

    def sizeHint(self, option, index):
        label = index.data(CategoryChipModel.LabelRole) or ""
        checked = index.data(CategoryChipModel.CheckedRole)

        self.initStyleOption(option, index)
        option.font.setPointSize(8)
        fm = QFontMetrics(option.font)

        width = self.HORIZONTAL_PADDING * 2 + fm.horizontalAdvance(label)

        if checked:
            width += self.CLOSE_GAP + self.CLOSE_WIDTH

        return QSize(width, self.CHIP_HEIGHT)

    def paint(self, painter: QPainter, option, index):
        painter.save()

        self.initStyleOption(option, index)

        label = index.data(CategoryChipModel.LabelRole) or ""
        checked = index.data(CategoryChipModel.CheckedRole)

        if checked:
            background = self.SELECTED_BG_COLOR
            border = self.SELECTED_BORDER_COLOR
            text_color = self.SELECTED_TEXT_COLOR

            if option.state & QStyle.StateFlag.State_MouseOver:
                background = self.SELECTED_HOVER_BG_COLOR
        else:
            background = self.BG_COLOR
            border = self.BORDER_COLOR
            text_color = self.TEXT_COLOR

            if option.state & QStyle.StateFlag.State_MouseOver:
                background = self.HOVER_BG_COLOR

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect

        painter.setPen(QPen(border, 1))
        painter.setBrush(QBrush(background))

        painter.drawRoundedRect(rect,rect.height() / 2, rect.height() / 2)

        option.font.setPointSize(8)
        painter.setFont(option.font)
        painter.setPen(text_color)
        fm = QFontMetrics(option.font)

        text_left = rect.left() + self.HORIZONTAL_PADDING
        text_rect = QRect(text_left, rect.top(), fm.horizontalAdvance(label), rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label)

        if checked and not self.close_icon.isNull():
            close_rect = self.closeRect(option, index)

            self.close_icon.paint(painter, close_rect, Qt.AlignmentFlag.AlignCenter, QIcon.Mode.Normal)

        painter.restore()

    def closeRect(self, option, index):
        if not index.data(CategoryChipModel.CheckedRole):
            return QRect()

        rect = option.rect.adjusted(1, 1, -1, -1)

        return QRect(
            rect.right() - self.HORIZONTAL_PADDING - self.CLOSE_WIDTH,
            rect.top(),
            self.CLOSE_WIDTH,
            rect.height(),
        )

class CategoryChipView(QListView):
    removeRequested = pyqtSignal(str)
    chipClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(4)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QListView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMouseTracking(True)

        self.setItemDelegate(CategoryChipDelegate(self))

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        index: QModelIndex = self.indexAt(event.pos())

        if not index.isValid():
            return

        option = self.view_options()
        option.rect = self.visualRect(index)

        category_id = index.data(CategoryChipModel.IdRole)

        if category_id:
            self.chipClicked.emit(category_id)
            checked = index.data(CategoryChipModel.CheckedRole)
            self.model().setData(index, not checked, CategoryChipModel.CheckedRole)
            self.updateGeometry()

        event.accept()

    def view_options(self):
        if PYQT5:
            option = self.viewOptions()
        else:
            option = QStyleOptionViewItem()
            self.initViewItemOption(option)

        return option

    def sizeHint(self):
        size = super().sizeHint()
        width = size.width()

        if width <= 0 or not self.model() or self.model().rowCount() == 0:
            return QSize(0, 0)

        delegate = self.itemDelegate()
        option = self.view_options()

        item_height = delegate.sizeHint(option, self.model().index(0, 0)).height()
        row_count = self.model().rowCount()

        rows = 1
        current_width = 0

        for row in range(row_count):
            index = self.model().index(row, 0)
            item_width = delegate.sizeHint(option, index).width()
            if current_width > 0 and current_width + self.spacing() + item_width > width:
                rows += 1
                current_width = item_width + self.spacing()
            else:
                current_width += item_width + self.spacing()

        return QSize(width, rows * item_height + (self.spacing() * rows * 2))

    def minimumSizeHint(self):
        return self.sizeHint()

    
class SearchEditStyle(QProxyStyle):

    def __init__(self, base_style=None):
        super().__init__(base_style)

    def drawPrimitive(self,element,option, painter, widget=None):
        if element == QStyle.PrimitiveElement.PE_FrameLineEdit and isinstance(widget, QLineEdit):
            return
        
        super().drawPrimitive(element, option, painter, widget)


class PickerModel(QAbstractListModel):
    def __init__(self, items: list[PickerItem] | None = None, metadata_store: ItemMetadataStore | None = None, parent=None):
        super().__init__(parent)

        self._metadata_store = metadata_store or ItemMetadataStore()
        self._items: list[PickerItem] = items or []
        self._search_text = ""

    def _favorite_items(self) -> list[PickerItem]:
        return [item for item in self._items if item.is_favorite]

    def _has_favorites(self) -> bool:
        return bool(self._favorite_items())

    def _is_section(self, row: int) -> bool:
        favorites = self._favorite_items()
        if favorites:
            if row == 0:
                return True

            all_header = len(favorites) + 1
            if row == all_header:
                return True
        else:
            if row == 0:
                return True

        return False

    def _section_title(self, row: int) -> str:
        favorites = self._favorite_items()

        if favorites:
            if row == 0:
                return "Favoriten"
            if row == len(favorites) + 1:
                return "Alle Pläne"

        return "Alle Pläne"

    def _item_at_row(self, row: int) -> PickerItem | None:
        favorites = self._favorite_items()
        if favorites:
            if 1 <= row <= len(favorites):
                return favorites[row - 1]
            all_start = len(favorites) + 2
        else:
            all_start = 1

        all_index = row - all_start
        if 0 <= all_index < len(self._items):
            return self._items[all_index]

        return None

    def _find_item(self, item_id: str) -> PickerItem | None:
        for item in self._items:
            if item.id == item_id:
                return item

        return None

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid() or not self._items:
            return 0

        favorites_count = sum(item.is_favorite for item in self._items)
        if favorites_count > 0:
            return len(self._items) + favorites_count + 2  # two section headers (favorites and all)
        else:
            return len(self._items) + 1  # no favorites -> only one section header

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()

        if self._is_section(row):
            if role == Qt.ItemDataRole.DisplayRole:
                return self._section_title(row)
            return None

        item = self._item_at_row(row)
        if item is not None and role == Qt.ItemDataRole.DisplayRole:
            return item.text
        if item is not None and role == Qt.ItemDataRole.ToolTipRole:
            return item.text

        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        if self._is_section(index.row()):
            return Qt.ItemFlag.ItemIsEnabled

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def _apply_stored_favorites(self):
        for item in self._items:
            item.is_favorite = self._metadata_store.is_favorite(item.id)

    def set_items(self, items: list[PickerItem]):
        self.beginResetModel()
        self._items = items
        self._apply_stored_favorites()
        self.endResetModel()

        self._metadata_store.prune({item.id for item in self._items})

    def toggle_favorite(self, item_id: str):
        item = self._find_item(item_id)

        if item is None:
            return

        self.beginResetModel()
        item.is_favorite = not item.is_favorite
        self._metadata_store.set_favorite(item_id, item.is_favorite)
        self.endResetModel()

    def remove_item(self, item_id: str) -> bool:
        item = self._find_item(item_id)

        if item is None:
            return False

        self.beginResetModel()
        self._items.remove(item)
        self.endResetModel()

        self._metadata_store.forget_item(item_id)
        return True

    def update_item(self, item_id: str, text: str | None = None, search_terms: tuple[str, ...] | None = None) -> bool:
        item = self._find_item(item_id)

        if item is None:
            return False

        self.beginResetModel()
        if text is not None:
            item.update_text(text)
        if search_terms is not None:
            item.update_search_terms(search_terms)
        self.endResetModel()

        return True


class PickerFilterProxyModel(QSortFilterProxyModel):
    sortChanged = pyqtSignal(PickerSortMode, Qt.SortOrder)

    def __init__(self, metadata_store: ItemMetadataStore | None = None, parent=None):
        super().__init__(parent)

        self._search_text = ""
        self._categories: set[str] = set()
        self._sort_mode = PickerSortMode.NAME
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._metadata_store = metadata_store or ItemMetadataStore()

        self.setDynamicSortFilter(False)
        self.sort(0, self._sort_order)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def set_sort_mode(self, mode: PickerSortMode):
        if mode == self._sort_mode:
            self._sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._sort_mode = mode
            self._sort_order = Qt.SortOrder.AscendingOrder

        self.sortChanged.emit(self._sort_mode, self._sort_order)
        self.sort(0, self._sort_order)

    def set_search_text(self, text: str):
        text = (text or "").strip()

        if text == self._search_text:
            return

        self._search_text = text
        self.invalidate()

    def set_categories(self, categories: set[str]):
        categories = set(categories)

        if categories == self._categories:
            return

        self._categories = categories
        self.invalidate()

    def _source_index(self, proxy_row: int) -> QModelIndex:
        return self.mapToSource(self.index(proxy_row, 0))

    def _is_section(self, row: int) -> bool:
        source_index = self._source_index(row)

        if not source_index.isValid():
            return False

        return self.sourceModel()._is_section(source_index.row())

    def _item_at_row(self, row: int) -> PickerItem | None:
        source_index = self._source_index(row)

        if not source_index.isValid():
            return None

        return self.sourceModel()._item_at_row(source_index.row())

    def toggle_favorite(self, item_id: str):
        self.sourceModel().toggle_favorite(item_id)

    def remove_item(self, item_id: str) -> bool:
        return self.sourceModel().remove_item(item_id)

    def update_item(self, item_id: str, text: str | None = None, search_terms: tuple[str, ...] | None = None) -> bool:
        return self.sourceModel().update_item(item_id, text=text, search_terms=search_terms)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        source = self.sourceModel()

        if source is None or source_parent.isValid():
            return False

        if source._is_section(source_row):
            return self._section_has_matching_items(source_row)

        item = source._item_at_row(source_row)
        if item is None:
            return False

        return self._item_matches(item)

    def _item_matches(self, item: PickerItem) -> bool:
        if self._categories:
            if item.category not in self._categories:
                return False

        search = self._search_text.casefold()
        if search and search not in item._search_stack:
            return False

        return True

    def _section_has_matching_items(self, section_row: int) -> bool:
        source = self.sourceModel()

        row = section_row + 1
        while row < source.rowCount():
            # Stop when we reach the next section.
            if source._is_section(row):
                break

            item = source._item_at_row(row)
            if item is not None and self._item_matches(item):
                return True

            row += 1

        return False

    def _row_group(self, row: int) -> int:
        """0 = Favoriten section (header + favorite items), 1 = Alle Pläne section."""
        favorites = self.sourceModel()._favorite_items()
        if favorites and row <= len(favorites):
            return 0
        return 1

    def lessThan(self, source_left, source_right):
        left_row, right_row = source_left.row(), source_right.row()

        # Qt calls lessThan with arguments swapped when sortOrder() is
        # Descending (it sorts using lessThan(right, left) internally, so it
        # gets a reversed order "for free" from a single comparator). That's
        # exactly what we want for item-vs-item comparisons below, but
        # structural placement (headers first, favorites group first) must
        # stay pinned to the top regardless of direction, so we detect the
        # swap here and cancel it out only for the structural checks.
        descending = self.sortOrder() == Qt.SortOrder.DescendingOrder

        left_group = self._row_group(left_row)
        right_group = self._row_group(right_row)
        if left_group != right_group:
            result = left_group < right_group
            return not result if descending else result

        source = self.sourceModel()
        left_is_header = source._is_section(left_row)
        right_is_header = source._is_section(right_row)
        if left_is_header or right_is_header:
            result = left_is_header and not right_is_header
            return not result if descending else result

        left_item = source._item_at_row(left_row)
        right_item = source._item_at_row(right_row)
        if left_item is None or right_item is None:
            return False

        if self._sort_mode == PickerSortMode.LAST_USED:
            return self._less_than_last_used(left_item, right_item)
        return natural_sort_key(left_item.text) < natural_sort_key(right_item.text)

    def _less_than_last_used(self, left, right):
        left_used = self._metadata_store.last_used(left.id)
        right_used = self._metadata_store.last_used(right.id)

        # Never-used items go last.
        if left_used is None and right_used is None:
            return natural_sort_key(left.text) < natural_sort_key(right.text)

        if left_used is None:
            return False

        if right_used is None:
            return True

        # Most recently used first.
        if left_used != right_used:
            return left_used > right_used

        # Stable deterministic tie-breaker.
        return natural_sort_key(left.text) < natural_sort_key(right.text)


class PickerListDelegate(QStyledItemDelegate):
    ROW_HEIGHT = 32
    SECTION_HEIGHT = 28

    CHIP_HEIGHT = 20
    PADDING = 12
    GAP = 12

    STAR_SIZE = 14

    TEXT_COLOR = QColor(ApplicationColor.PrimaryText)
    SECTION_COLOR = QColor(ApplicationColor.MutedText)
    HOVER_COLOR = QColor(ApplicationColor.BackgroundHover)
    SELECTED_COLOR = QColor(ApplicationColor.SurfaceSelected)

    STAR_COLOR = QColor(ApplicationColor.MutedText)
    CHIP_FG, CHIP_BG = QColor(ApplicationColor.PrimaryText), QColor(ApplicationColor.SurfaceStrong)

    def sizeHint(self, option, index):
        if index.model().sourceModel()._is_section(index.row()):
            return QSize(0, self.SECTION_HEIGHT)
        return QSize(0, self.ROW_HEIGHT)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        model = index.model().sourceModel()
        source_index = index.model().mapToSource(index)
        row = source_index.row()

        if model._is_section(row):
            self._paint_section(painter, option, model._section_title(row))
        else:
            item = model._item_at_row(row)
            if item is not None:
                self._paint_item(painter, option, index, item)

        painter.restore()

    def _paint_section(self, painter, option, title):
        rect = option.rect

        font = QFont(option.font)
        font.setPointSize(9)
        font.setWeight(QFont.Weight.Medium)

        painter.setFont(font)
        painter.setPen(self.SECTION_COLOR)
        painter.drawText(rect.adjusted(self.GAP // 2, 0, -self.GAP // 2, 0), Qt.AlignmentFlag.AlignVCenter, title)

    def _paint_item(self, painter, option, index, item):
        text_rect, chip_rect, star_rect = self._item_geometry(option, item)

        self._paint_background(painter, option)
        self._paint_text(painter, text_rect, item.text, option.font)

        if item.category:
            self._paint_chip(painter, chip_rect, item.category, option.font)

        if (
            option.state & QStyle.StateFlag.State_Selected or
            option.state & QStyle.StateFlag.State_MouseOver or
            item.is_favorite
        ):
            self._paint_star(painter, star_rect, item.is_favorite)

    def _paint_background(self, painter, option):
        if option.state & QStyle.StateFlag.State_Selected:
            color = self.SELECTED_COLOR
        elif option.state & QStyle.StateFlag.State_MouseOver:
            color = self.HOVER_COLOR
        else:
            return

        rect = option.rect.adjusted(2, 2, -2, -2)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(rect, 8, 8)

    def _paint_text(self, painter, rect, text, font):
        font = QFont(font)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(self.TEXT_COLOR)

        text = QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, int(rect.width()))
        painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter, text)

    def _chip_width(self, category, font):
        if not category:
            return 0

        font = QFont(font)
        font.setPointSize(8)

        return QFontMetrics(font).horizontalAdvance(category) + self.PADDING * 2

    def _paint_chip(self, painter, rect, category, font):
        background, foreground = self.CHIP_BG, self.CHIP_FG

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        font = QFont(font)
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(foreground)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, category)

    def _item_geometry(self, option, item):
        rect = option.rect
        center_y = rect.top() + rect.height() / 2

        chip_width = self._chip_width(item.category, option.font)

        star_rect = QRectF(
            rect.right() - self.GAP - self.STAR_SIZE,
            center_y - self.STAR_SIZE / 2,
            self.STAR_SIZE,
            self.STAR_SIZE,
        )

        chip_rect = QRectF(
            star_rect.left() - self.GAP - chip_width,
            center_y - self.CHIP_HEIGHT / 2,
            chip_width,
            self.CHIP_HEIGHT,
        )

        text_left = rect.left() + self.GAP
        text_right = chip_rect.left() - self.GAP
        text_rect = QRectF(text_left, rect.top(), text_right - text_left, rect.height())

        return text_rect, chip_rect, star_rect

    def _paint_star(self, painter, rect, favorite):
        painter.save()

        painter.setPen(QPen(self.STAR_COLOR, 1.5))
        painter.setBrush(self.STAR_COLOR if favorite else Qt.BrushStyle.NoBrush)
        painter.drawPath(self._star_path(rect))

        painter.restore()

    def _star_path(self, rect):
        cx = rect.center().x()
        cy = rect.center().y()
        outer = min(rect.width(), rect.height()) / 2
        inner = outer * 0.42

        path = QPainterPath()

        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            radius = outer if i % 2 == 0 else inner
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius

            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        path.closeSubpath()
        return path

    def editorEvent(self, event, model, option, index):
        if not index.isValid() or model._is_section(index.row()):
            return False

        item = model._item_at_row(index.row())
        if item is None:
            return False

        _, _, star_rect = self._item_geometry(option, item)
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                if PYQT5:
                    mouse_position = event.pos()
                else:
                    mouse_position = event.position()
                if star_rect.contains(mouse_position):
                    model.toggle_favorite(item.id)
                    return True

        return super().editorEvent(event, model, option, index)

    def helpEvent(self, event, view, option, index):
        if not index.isValid():
            return False

        if event.type() == QEvent.Type.ToolTip:
            item = view.model()._item_at_row(index.row())
            if item is None:
                return False

            text_rect, _, _ = self._item_geometry(option, item)
            tooltip_text = view.model().data(index, Qt.ItemDataRole.ToolTipRole)
            elided = option.fontMetrics.elidedText(item.text, Qt.TextElideMode.ElideRight, int(text_rect.width()))

            is_elided = elided != item.text
            if is_elided:
                QToolTip.showText(event.globalPos(), tooltip_text, view, view.visualRect(index))
            else:
                QToolTip.hideText()
            return True

        return super().helpEvent(event, view, option, index)



class PickerListView(QListView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(2)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMouseTracking(True)

        self.setItemDelegate(PickerListDelegate(self))
        self.setStyle(ModernScrollBarStyle('Fusion'))
    

class PickerPopup(QWidget):
    itemSelected = pyqtSignal(PickerItem)
    EMPTY_STATE_FILTER_HINT = "Suchbegriff oder Filter entfernen um alle Objekte zu finden..."

    def __init__(self, empty_state_title="Keine Inhalte gefunden", parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.metadata_store = ItemMetadataStore()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText('Suchen...')
        self.search_bar.setClearButtonEnabled(True)
        close_icon = load_svg(os.path.join(BASE_DIR, 'gui/resources/close.svg'), color=ApplicationColor.PrimaryText)
        self.search_bar.findChild(QToolButton).setIcon(close_icon)
        self.search_bar.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.ActionPosition.LeadingPosition)
        self.search_bar.setStyle(SearchEditStyle('Fusion'))

        self.category_model = CategoryChipModel(self)

        self.category_list_view = CategoryChipView()
        self.category_list_view.setModel(self.category_model)

        self.sort_widget = QWidget(self)
        self.sort_widget.setObjectName('sort_widget')
        self.sort_button_group = QButtonGroup(self.sort_widget)
        self.sort_widget.setLayout(QHBoxLayout())
        self.sort_widget.layout().setContentsMargins(8, 5, 8, 5)
        self.sort_widget.layout().addWidget(QLabel('Sortieren nach'), stretch=1)
        self.button_sort_name = QPushButton('Name')
        self.button_sort_name.setCheckable(True)
        self.button_sort_name.setChecked(True)
        self.icon_sort_name_ascending = load_svg(os.path.join(BASE_DIR, 'gui/resources/arrow-down-a-z.svg'))
        self.icon_sort_name_descending = load_svg(os.path.join(BASE_DIR, 'gui/resources/arrow-up-z-a.svg'))
        self.icon_sort_last_used_ascending = load_svg(os.path.join(BASE_DIR, 'gui/resources/clock-arrow-down.svg'))
        self.icon_sort_last_used_descending = load_svg(os.path.join(BASE_DIR, 'gui/resources/clock-arrow-up.svg'))
        self.button_sort_name.setIcon(self.icon_sort_name_ascending)
        self.button_sort_last_used = QPushButton('Letzte')
        self.button_sort_last_used.setCheckable(True)
        self.button_sort_last_used.setIcon(self.icon_sort_last_used_ascending)
        self.sort_button_group.addButton(self.button_sort_name)
        self.sort_button_group.addButton(self.button_sort_last_used)
        self.sort_widget.layout().addWidget(self.button_sort_name)
        self.sort_widget.layout().addWidget(self.button_sort_last_used)
        sort_widget_style = """
            QWidget[objectName="sort_widget"] {{
                border-top: 1px solid {_border_color};
                border-bottom: 1px solid {_border_color};
            }}
            QPushButton {{
                border: none;
                padding: 5px;
            }}
            QPushButton:checked {{
                border: 1px solid {_border_color};
                border-radius: 5px;
                padding: 5px;
                background-color: {_bg_color_checked};
            }}
        """
        self.sort_widget.setStyleSheet(sort_widget_style.format(
            _bg_color_checked=ApplicationColor.SurfaceStrong,
            _border_color=ApplicationColor.SurfaceSelected
        ))

        self.item_list_view = PickerListView()
        self.picker_model = PickerModel(metadata_store=self.metadata_store, parent=self)
        self.picker_proxy_model = PickerFilterProxyModel(metadata_store=self.metadata_store, parent=self)
        self.picker_proxy_model.setSourceModel(self.picker_model)
        self.picker_proxy_model.sortChanged.connect(self._on_sort_changed)
        self.item_list_view.setModel(self.picker_proxy_model)
        self.item_list_view.clicked.connect(self._on_clicked)
        self.item_list_empty_state = EmptyStateFilter(self.item_list_view)
        self.item_list_empty_state.set_icon(':/images/themes/default/search.svg') \
            .set_icon_size(24) \
            .set_title(empty_state_title) \
            .set_subtitle(self.EMPTY_STATE_FILTER_HINT)

        layout.addWidget(self.search_bar)
        layout.addWidget(self.category_list_view)
        layout.addWidget(self.sort_widget)
        layout.addWidget(self.item_list_view, stretch=1)

        self.setLayout(layout)

        self.button_sort_name.clicked.connect(
            lambda: self.picker_proxy_model.set_sort_mode(PickerSortMode.NAME)
        )
        self.button_sort_last_used.clicked.connect(
            lambda: self.picker_proxy_model.set_sort_mode(PickerSortMode.LAST_USED)
        )
        self.search_bar.textChanged.connect(self.picker_proxy_model.set_search_text)
        self.category_model.categoriesChanged.connect(self._categories_changed)
        
    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(self.palette().color(QPalette.ColorRole.Mid))
        painter.setBrush(self.palette().color(QPalette.ColorRole.Base))
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 10, 10)

    def _on_sort_changed(self, sort_mode: PickerSortMode, sort_order: Qt.SortOrder):
        if sort_mode == PickerSortMode.NAME:
            if sort_order == Qt.SortOrder.AscendingOrder:
                sort_icon = self.icon_sort_name_ascending
            else:
                sort_icon = self.icon_sort_name_descending
            self.button_sort_name.setIcon(sort_icon)
        else:
            if sort_order == Qt.SortOrder.AscendingOrder:
                sort_icon = self.icon_sort_last_used_ascending
            else:
                sort_icon = self.icon_sort_last_used_descending
            self.button_sort_last_used.setIcon(sort_icon)

    def _on_clicked(self, index):
        row = index.row()

        if self.picker_proxy_model._is_section(row):
            return

        item = self.picker_proxy_model._item_at_row(row)
        if item is None:
            return

        self.itemSelected.emit(item)

        self.picker_proxy_model.sort(0, self.picker_proxy_model.sortOrder())

    def _categories_changed(self):
        categories = {
            category.id
            for category in self.category_model.categories()
            if category.checked
        }

        self.picker_proxy_model.set_categories(categories)

    def mark_used(self, item_id: str):
        self.metadata_store.mark_used(item_id)

    def add_category(self, category_id: str, label: str, checked: bool = False):
        self.category_model.addCategory(
            Category(
                id=category_id,
                label=label,
                checked=checked,
            )
        )

    def set_picker_items(self, items: list[PickerItem]):
        self.picker_model.set_items(items)

    def remove_item(self, item_id: str) -> bool:
        return self.picker_proxy_model.remove_item(item_id)

    def update_item(self, item_id: str, text: str | None = None, search_terms: tuple[str, ...] | None = None) -> bool:
        return self.picker_proxy_model.update_item(item_id, text=text, search_terms=search_terms)


class GenericPicker(QComboBox):
    def __init__(self, parent=None, *, default_size=(288, 426)):
        super().__init__(parent)

        self.default_size = default_size
        self._suppress_usage_tracking = False

        self._popup = PickerPopup(parent=self)
        self._popup.hide()

        self._popup.itemSelected.connect(self._on_popup_item_selected)
        self.currentIndexChanged.connect(self._on_current_index_changed)

        self.setMinimumContentsLength(20)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)

    def paintEvent(self, event):
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        painter = QStylePainter(self)
        painter.setPen(self.palette().color(QPalette.ColorRole.Text))
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt)

        if self.count() == 0:
            text = self.placeholderText()
            painter.setPen(self.palette().color(QPalette.ColorRole.PlaceholderText))
        else:
            text = self.currentText()

        text_rect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxEditField)
        opt.currentText = painter.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opt)

    def _on_popup_item_selected(self, item: PickerItem):
        self.setCurrentText(item.text)
        self._popup.search_bar.clear()
        self.hidePopup()

    def _on_current_index_changed(self, index: int):
        if self._suppress_usage_tracking or index < 0:
            return

        item_id = self.itemData(index)
        if item_id:
            self._popup.mark_used(item_id)

    def showPopup(self):
        self._position_popup()
        self._popup.search_bar.setFocus()
        self._popup.show()
        self._popup.update()

    def _position_popup(self):
        desired_width = max(self.default_size[0], self.width())
        desired_height = self.default_size[1]

        combo_rect = QRect(self.mapToGlobal(QPoint(0, 0)), self.size())

        screen = QApplication.screenAt(combo_rect.center())
        if screen is None:
            screen = QApplication.primaryScreen()

        available = screen.availableGeometry()
        space_below = available.bottom() - combo_rect.bottom()
        space_above = combo_rect.top() - available.top()

        # Prefer below unless there is substantially more room above.
        if space_below >= desired_height or space_below >= space_above:
            direction = "below"
            available_height = space_below
        else:
            direction = "above"
            available_height = space_above

        height = min(desired_height, available_height)
        width = min(desired_width, available.width())

        if direction == "below":
            y = combo_rect.bottom()
        else:
            y = combo_rect.top() - height

        x = combo_rect.left()

        # Keep horizontally inside the available screen.
        x = max(available.left(), min(x, available.right() - width))

        self._popup.setFixedSize(width, height)
        self._popup.move(x, y)

    def hidePopup(self):
        self._popup.hide()

    def add_category(self, category_id: str, label: str, checked: bool = False):
        self._popup.add_category(category_id, label, checked)

    def set_picker_items(self, items: list[PickerItem]):
        self._suppress_usage_tracking = True
        try:
            self.clear()
            self._popup.set_picker_items(items)
            for item in items:
                self.addItem(item.text, item.id)
        finally:
            self._suppress_usage_tracking = False

    def remove_item(self, item_id: str) -> bool:
        removed = self._popup.remove_item(item_id)

        index = self.findData(item_id)
        if index >= 0:
            was_current = self.currentData() == item_id
            self._suppress_usage_tracking = True
            try:
                self.removeItem(index)
                if was_current:
                    self.setCurrentIndex(-1)
            finally:
                self._suppress_usage_tracking = False

        return removed

    def update_item(self, item_id: str, text: str | None = None, search_terms: tuple[str, ...] | None = None) -> bool:
        updated = self._popup.update_item(item_id, text=text, search_terms=search_terms)

        index = self.findData(item_id)
        if index >= 0:
            was_current = self.currentIndex() == index
            self.setItemText(index, text)
            if was_current:
                self.update()

        return updated
