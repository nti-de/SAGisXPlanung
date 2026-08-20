import math
import os
from dataclasses import dataclass
from enum import auto, Enum
from typing import Any

from PyQt5.QtCore import QAbstractListModel, QModelIndex, pyqtSignal, QSize, QRect, QPoint, QEvent, QRectF
from PyQt5.QtGui import QPainter, QColor, QIcon, QFontMetrics, QPen, QBrush, QFont, QPainterPath
from plotly.validators.treemap.marker.pattern import _bgcolor
from qgis.PyQt.QtGui import QPalette
from PyQt5.QtWidgets import QVBoxLayout, QFrame, QLabel, QListView, QLineEdit, QGraphicsDropShadowEffect, QProxyStyle, \
    QStyledItemDelegate, QSizePolicy, QStyleOptionViewItem, QHBoxLayout, QPushButton, QButtonGroup
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QStylePainter, QStyleOptionComboBox, QStyle
from qgis.PyQt.QtWidgets import QWidget, QDialog, QComboBox
from qgis.utils import iface
from sqlalchemy.orm import load_only

from SAGisXPlanung import PYQT5, BASE_DIR, Session
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.gui.style import load_svg, ApplicationColor, EmptyStateFilter


@dataclass
class PickerItem:
    id: str
    text: str
    category: str | None = None
    is_favorite: bool = False
    data: Any = None


class RowType(Enum):
    SECTION = auto()
    ITEM = auto()


@dataclass
class PickerRow:
    type: RowType
    item: PickerItem | None = None
    title: str | None = None


@dataclass
class Category:
    id: str
    label: str
    checked: bool = False


class ModernScrollBarStyle(QProxyStyle):
    SCROLLBAR_WIDTH = 8
    HANDLE_MARGIN = 2
    HANDLE_MIN_HEIGHT = 30

    TRACK_COLOR = QColor(0, 0, 0, 0)
    HANDLE_COLOR = QColor("#C4C4C4")
    HANDLE_HOVER_COLOR = QColor("#A8A8A8")

    def pixelMetric(self, metric, option=None, widget=None):
        if metric in (
            QStyle.PixelMetric.PM_ScrollBarExtent,
            QStyle.PixelMetric.PM_ScrollBarSliderMin,
        ):
            if metric == QStyle.PixelMetric.PM_ScrollBarExtent:
                return self.SCROLLBAR_WIDTH
            return self.HANDLE_MIN_HEIGHT

        return super().pixelMetric(metric, option, widget)

    def subControlRect(self, control, option, sub_control, widget=None):
        if control == QStyle.ComplexControl.CC_ScrollBar:
            if sub_control == QStyle.SubControl.SC_ScrollBarAddLine:
                return QRect()

            if sub_control == QStyle.SubControl.SC_ScrollBarSubLine:
                return QRect()

            if sub_control == QStyle.SubControl.SC_ScrollBarAddPage:
                return QRect()

            if sub_control == QStyle.SubControl.SC_ScrollBarSubPage:
                return QRect()

            if sub_control == QStyle.SubControl.SC_ScrollBarGroove:
                return option.rect

            if sub_control == QStyle.SubControl.SC_ScrollBarSlider:
                return self._slider_rect(option)

        return super().subControlRect(control, option, sub_control, widget)

    def drawComplexControl(self, control, option, painter, widget=None):
        if control != QStyle.ComplexControl.CC_ScrollBar:
            return super().drawComplexControl(control, option, painter, widget)

        scrollbar = option
        rect = scrollbar.rect

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track
        painter.fillRect(rect, self.TRACK_COLOR)

        # Handle
        handle = self._slider_rect(scrollbar)

        if scrollbar.state & QStyle.StateFlag.State_MouseOver:
            color = self.HANDLE_HOVER_COLOR
        else:
            color = self.HANDLE_COLOR

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)

        radius = handle.width() / 2
        painter.drawRoundedRect(handle, radius, radius)

        painter.restore()

    def _slider_rect(self, option):
        rect = option.rect

        if option.orientation == Qt.Orientation.Vertical:
            margin = self.HANDLE_MARGIN

            available = rect.height() - 2 * margin

            minimum = option.minimum
            maximum = option.maximum
            page_step = option.pageStep

            if maximum <= minimum:
                height = available
                y = margin
            else:
                total = maximum - minimum + page_step
                height = max(
                    self.HANDLE_MIN_HEIGHT,
                    int(available * page_step / total),
                )

                height = min(height, available)

                span = available - height
                value_range = maximum - minimum

                if value_range:
                    y = margin + int(
                        span * (option.sliderPosition - minimum)
                        / value_range
                    )
                else:
                    y = margin

            return QRect(
                rect.left() + margin,
                rect.top() + y,
                rect.width() - 2 * margin,
                height,
            )

        else:
            margin = self.HANDLE_MARGIN

            available = rect.width() - 2 * margin

            minimum = option.minimum
            maximum = option.maximum
            page_step = option.pageStep

            if maximum <= minimum:
                width = available
                x = margin
            else:
                total = maximum - minimum + page_step
                width = max(
                    self.HANDLE_MIN_HEIGHT,
                    int(available * page_step / total),
                )

                width = min(width, available)

                span = available - width
                value_range = maximum - minimum

                if value_range:
                    x = margin + int(
                        span * (option.sliderPosition - minimum)
                        / value_range
                    )
                else:
                    x = margin

            return QRect(
                rect.left() + x,
                rect.top() + margin,
                width,
                rect.height() - 2 * margin,
            )


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
            self.dataChanged.emit(index, index)

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
    BG_COLOR = QColor(ApplicationColor.Grey200)
    BORDER_COLOR = QColor(ApplicationColor.Grey300)
    TEXT_COLOR = QColor(ApplicationColor.PrimaryText)

    # Selected
    SELECTED_BG_COLOR = QColor(ApplicationColor.PrimaryLight)
    SELECTED_BORDER_COLOR = QColor(ApplicationColor.Primary)
    SELECTED_TEXT_COLOR = QColor(ApplicationColor.OnPrimary)

    # Hover
    HOVER_BG_COLOR = QColor(ApplicationColor.Grey300)
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
        text_rect = QRect(text_left, rect.top(), fm.horizontalAdvance(label) ,rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, label)

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
        option = self.viewOptions()

        item_height = delegate.sizeHint(option, self.model().index(0, 0)).height()
        row_count = self.model().rowCount()

        rows = 1
        current_width = 0

        for row in range(row_count):
            index = self.model().index(row, 0)
            item_width = delegate.sizeHint(option, index).width()
            # print(width, current_width, item_width, 'rows', rows)
            if current_width > 0 and current_width + self.spacing() + item_width > width:
                rows += 1
                current_width = item_width + self.spacing()
            else:
                current_width += item_width + self.spacing()

        print(QSize(width, rows * item_height + (self.spacing() * rows * 2)), 'rows', rows)
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
    def __init__(self, items: list[PickerItem] | None = None, parent=None):
        super().__init__(parent)

        self._items: list[PickerItem] = items or []
        self._rows: list[PickerRow] = []

        self._search_text = ""
        self._categories: set[str] = set()

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

        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        if self._is_section(index.row()):
            return Qt.ItemFlag.ItemIsEnabled

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def set_items(self, items: list[PickerItem]):
        self.beginResetModel()
        self._items = items
        self.endResetModel()

    def set_search_text(self, text: str):
        self._search_text = text

    def set_categories(self, categories: set[str]):
        self._categories = categories

    def toggle_favorite(self, item_id: str):
        item = self._find_item(item_id)

        if item is None:
            return

        self.beginResetModel()
        item.is_favorite = not item.is_favorite
        self.endResetModel()


class PickerListDelegate(QStyledItemDelegate):
    ROW_HEIGHT = 32
    SECTION_HEIGHT = 28

    CHIP_HEIGHT = 20
    PADDING = 12
    GAP = 12

    STAR_SIZE = 14

    TEXT_COLOR = QColor(ApplicationColor.PrimaryText)
    SECTION_COLOR = QColor(ApplicationColor.MutedText)
    HOVER_COLOR = QColor(ApplicationColor.Grey200)
    SELECTED_COLOR = QColor(ApplicationColor.Grey300)

    STAR_COLOR = QColor(ApplicationColor.MutedText)
    CHIP_FG, CHIP_BG = QColor(ApplicationColor.PrimaryText), QColor(ApplicationColor.Grey200)

    CATEGORY_COLORS = {
        "BP_PLAN": (QColor("#D7F3EB"), QColor("#008F70")),
        "RP_PLAN": (QColor("#DCE9FF"), QColor("#2455D6")),
        "LP_PLAN": (QColor("#FFF0D8"), QColor("#C75A00")),
        "FP_PLAN": (QColor("#EEDCFF"), QColor("#8A12D6")),
    }

    def sizeHint(self, option, index):
        if index.model()._is_section(index.row()):
            return QSize(0, self.SECTION_HEIGHT)
        return QSize(0, self.ROW_HEIGHT)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        model = index.model()
        row = index.row()
        # painter.drawRect(option.rect)
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
        font.setPointSize(9)

        return QFontMetrics(font).horizontalAdvance(category) + self.PADDING * 2

    def _paint_chip(self, painter, rect, category, font):
        background, foreground = self.CATEGORY_COLORS.get(
            category, (self.CHIP_BG, self.CHIP_FG)
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        font = QFont(font)
        font.setPointSize(9)
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
                if star_rect.contains(event.pos()):
                    model.toggle_favorite(item.id)
                    return True

        return super().editorEvent(event, model, option, index)


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

        layout = QVBoxLayout(self)

        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText('Suchen...')
        self.search_bar.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.ActionPosition.LeadingPosition)
        self.search_bar.setStyle(SearchEditStyle('Fusion'))

        self.category_model = CategoryChipModel(self)

        self.category_list_view = CategoryChipView()
        self.category_list_view.setModel(self.category_model)
        # self.category_model.categoriesChanged.connect(self._categoriesChanged)
        # self.category_list_view.removeRequested.connect( self.removeCategory)

        self.sort_widget = QWidget(self)
        self.sort_widget.setObjectName('sort_widget')
        self.sort_button_group = QButtonGroup(self.sort_widget)
        self.sort_widget.setLayout(QHBoxLayout())
        self.sort_widget.layout().setContentsMargins(8, 5, 8, 5)
        self.sort_widget.layout().addWidget(QLabel('Sortieren nach'), stretch=1)
        self.button_sort_name = QPushButton('Name')
        self.button_sort_name.setCheckable(True)
        self.button_sort_name.setChecked(True)
        self.button_sort_name.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/arrow-down-a-z.svg')))
        self.button_sort_last_used = QPushButton('Letzte')
        self.button_sort_last_used.setCheckable(True)
        self.button_sort_last_used.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/clock-arrow-down.svg')))
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
            _bg_color_checked=ApplicationColor.Grey200,
            _border_color=ApplicationColor.Grey300
        ))

        self.item_list_view = PickerListView()
        self.picker_model = PickerModel(parent=self)
        self.item_list_view.setModel(self.picker_model)
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
        
    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(self.palette().color(QPalette.Mid))
        painter.setBrush(self.palette().color(QPalette.Base))
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 10, 10)

    def _on_clicked(self, index):
        row = index.row()

        if self.picker_model._is_section(row):
            return

        item = self.picker_model._item_at_row(row)
        if item is None:
            return

        self.itemSelected.emit(item)

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


class GenericPicker(QComboBox):
    def __init__(self, parent=None):
        print('init')
        super().__init__(parent)

        self._popup = PickerPopup(parent=self)
        self._popup.hide()

        self._popup.itemSelected.connect(self._on_popup_item_selected)

    def paintEvent(self, event):
        print('paintEvent')
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)

        painter = QStylePainter(self)
        painter.setPen(self.palette().color(QPalette.Text))
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt)

        text_rect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxEditField)
        opt.currentText = painter.fontMetrics().elidedText(self.currentText(), Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opt)

    def _on_popup_item_selected(self, item: PickerItem):
        self.setCurrentText(item.text)
        self.hidePopup()

    def showPopup(self):
        print('showPopup')
        position = self.mapToGlobal(self.rect().bottomLeft())

        self._popup.resize(288, 426)
        self._popup.move(position)
        self._popup.search_bar.setFocus()
        self._popup.show()
        self._popup.update()

    def hidePopup(self):
        self._popup.hide()

    def add_category(self, category_id: str, label: str, checked: bool = False):
        self._popup.add_category(category_id, label, checked)

    def set_picker_items(self, items: list[PickerItem]):
        self._popup.set_picker_items(items)
        for item in items:
            self.addItem(item.text, item.id)


p = GenericPicker()
p.add_category("bp", "BP_Plan")
p.add_category("fp", "FP_Plan")
p.add_category("lp", "LP_Plan")
p.add_category("rp", "RP_Plan")

with Session.begin() as session:
    plans = session.query(XP_Plan).options(
        load_only(XP_Plan.id, XP_Plan.name, XP_Plan.type)
    ).all()
    picker_items = []
    for plan in plans:
        picker_item = PickerItem(id=str(plan.id), text=plan.name, category=plan.__class__.__name__)
        picker_items.append(picker_item)
    p.set_picker_items(picker_items)

d = QDialog(iface.mainWindow())
d.setLayout(QVBoxLayout())
d.layout().addWidget(p)
d.show()