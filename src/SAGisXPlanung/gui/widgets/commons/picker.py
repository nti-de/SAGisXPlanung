import math
import os
from dataclasses import dataclass
from enum import auto, Enum
from typing import Any

from PyQt5.QtCore import QAbstractListModel, QModelIndex, pyqtSignal, QSize, QRect, QPoint, QEvent, QRectF
from PyQt5.QtGui import QPainter, QColor, QIcon, QFontMetrics, QPen, QBrush, QFont, QPainterPath
from qgis.PyQt.QtGui import QPalette
from PyQt5.QtWidgets import QVBoxLayout, QFrame, QLabel, QListView, QLineEdit, QGraphicsDropShadowEffect, QProxyStyle, \
    QStyledItemDelegate, QSizePolicy, QStyleOptionViewItem
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QStylePainter, QStyleOptionComboBox, QStyle
from qgis.PyQt.QtWidgets import QWidget, QDialog, QComboBox
from qgis.utils import iface
from sqlalchemy.orm import load_only

from SAGisXPlanung import PYQT5, BASE_DIR, Session
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.gui.style import load_svg, ApplicationColor


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

        rows = 1
        current_width = 0

        for row in range(self.model().rowCount()):
            index = self.model().index(row, 0)
            item_width = delegate.sizeHint(option, index).width()

            if current_width > 0 and current_width + 2 * self.spacing() + item_width > width:
                rows += 1
                current_width = item_width + 2 * self.spacing()
            else:
                current_width += 2 * self.spacing()
                current_width += item_width

        print(QSize(width, rows * item_height + (self.spacing() * rows * 2)))
        return QSize(width, rows * item_height + (self.spacing() * rows * 2))

    def minimumSizeHint(self):
        return self.sizeHint()

    
class SearchEditStyle(QProxyStyle):

    def __init__(self, base_style=None):
        super().__init__(base_style)

        self.radius = 7
        self.border_width = 1

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

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
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

        item.is_favorite = not item.is_favorite


class PickerListDelegate(QStyledItemDelegate):
    ROW_HEIGHT = 32
    SECTION_HEIGHT = 28

    CHIP_HEIGHT = 20
    PADDING = 12
    GAP = 12

    STAR_SIZE = 16

    TEXT_COLOR = QColor("#202020")
    SECTION_COLOR = QColor("#707070")
    HOVER_COLOR = QColor("#F4F4F4")
    SELECTED_COLOR = QColor("#EDEDED")

    DOT_COLOR = QColor("#00B887")
    STAR_COLOR = QColor("#707070")

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
        painter.drawText(rect.adjusted(self.GAP, 0, -self.GAP, 0), Qt.AlignmentFlag.AlignVCenter, title)

    def _paint_item(self, painter, option, index, item):
        self._paint_background(painter, option)

        rect = option.rect
        center_y = rect.top() + rect.height() / 2

        star_rect = self._star_rect(rect)

        chip_width = self._chip_width(painter, item.category, option.font)
        chip_rect = QRectF(
            star_rect.left() - self.GAP - chip_width,
            center_y - self.CHIP_HEIGHT / 2,
            chip_width,
            self.CHIP_HEIGHT,
        )

        text_rect = QRectF(
            rect.left() + self.GAP,
            rect.top(),
            chip_rect.left() - 2 * self.GAP,
            rect.height(),
        )

        self._paint_text(painter, text_rect, item.text, option.font)

        if item.category:
            self._paint_chip(painter, chip_rect, item.category, option.font)

        if option.state & QStyle.StateFlag.State_Selected or option.state & QStyle.StateFlag.State_MouseOver:
            self._paint_star(painter, star_rect, item.is_favorite)

    def _paint_background(self, painter, option):
        if option.state & QStyle.StateFlag.State_Selected:
            color = self.SELECTED_COLOR
        elif option.state & QStyle.StateFlag.State_MouseOver:
            color = self.HOVER_COLOR
        else:
            return

        rect = option.rect.adjusted(6, 2, -6, -2)

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

    def _chip_width(self, painter, category, font):
        if not category:
            return 0

        font = QFont(font)
        font.setPointSize(9)

        return QFontMetrics(font).horizontalAdvance(category) + self.PADDING * 2

    def _paint_chip(self, painter, rect, category, font):
        background, foreground = self.CATEGORY_COLORS.get(
            category, (QColor("#EAEAEA"), QColor("#555555"))
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        font = QFont(font)
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(foreground)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, category)

    def _star_rect(self, rect):
        center_y = rect.top() + rect.height() / 2
        return QRectF(
            rect.right() - self.GAP - self.STAR_SIZE,
            center_y - self.STAR_SIZE / 2,
            self.STAR_SIZE,
            self.STAR_SIZE,
        )

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

        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                if self._star_rect(option.rect).contains(event.pos()):
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
    

class PickerPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText('Suchen...')
        self.search_bar.addAction(QIcon(':/images/themes/default/search.svg'), QLineEdit.ActionPosition.LeadingPosition)
        self.search_bar.setStyle(SearchEditStyle(self.search_bar.style()))

        self.category_model = CategoryChipModel(self)

        self.category_list_view = CategoryChipView()
        self.category_list_view.setModel(self.category_model)
        # self.category_model.categoriesChanged.connect(self._categoriesChanged)
        # self.category_list_view.removeRequested.connect( self.removeCategory)

        self.item_list_view = PickerListView()
        self.picker_model = PickerModel(self)
        self.item_list_view.setModel(self.picker_model)

        layout.addWidget(self.search_bar)
        layout.addWidget(self.category_list_view)
        layout.addWidget(self.item_list_view)

        self.setLayout(layout)
        
    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(self.palette().color(QPalette.Mid))
        painter.setBrush(self.palette().color(QPalette.Base))
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 10, 10)

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

        self._popup = PickerPopup(self)
        self._popup.hide()

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

    def showPopup(self):
        print('showPopup')
        position = self.mapToGlobal(self.rect().bottomLeft())
        print(position)
        self._popup.move(position)
        self._popup.search_bar.setFocus()
        self._popup.show()

    def add_category(self, category_id: str, label: str, checked: bool = False):
        self._popup.add_category(category_id, label, checked)

    def set_picker_items(self, items: list[PickerItem]):
        self._popup.set_picker_items(items)


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
        picker_item = PickerItem(id=str(plan.id), text=plan.name, category='BP_Plan')
        picker_items.append(picker_item)
    p.set_picker_items(picker_items)

d = QDialog(iface.mainWindow())
d.setLayout(QVBoxLayout())
d.layout().addWidget(p)
d.show()