import logging

from qgis.PyQt import sip
from qgis.PyQt.QtCore import pyqtSignal, QModelIndex, Qt, QRectF, QRect, QObject, QEvent, QVariant, QPointF
from qgis.PyQt.QtGui import QPainter, QFontMetrics, QPen, QColor, QFont, QPalette, QBrush, QIcon
from qgis.PyQt.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QProxyStyle, QStyleOption, QStyle, QAbstractItemView
from qgis.PyQt.QtSvg import QSvgRenderer

logger = logging.getLogger(__name__)

FlagNewRole = Qt.ItemDataRole.UserRole + 1


class DateTimeDisplayDelegate(QStyledItemDelegate):
    """
    Delegate to format a datetime object as readable string.
    """
    def displayText(self, value: QVariant, locale):
        return value.toString('dd.MM.yyyy HH:mm')


class FixComboStyleDelegate(QStyledItemDelegate):
    """
    Weird workaround for showing checkboxes in the dropdown view of a combobox
    Without this delegate the checkboxes are either not shown at all, or they are displayed way too large???
    """
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        option.showDecorationSelected = False
        super(FixComboStyleDelegate, self).paint(painter, option, index)


class HighlightRowDelegate(QStyledItemDelegate):

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        option.palette.setBrush(QPalette.ColorRole.Highlight, QBrush(QColor('#CBD5E1')))
        option.palette.setBrush(QPalette.ColorRole.HighlightedText, QBrush(Qt.GlobalColor.black))

        super(HighlightRowDelegate, self).paint(painter, option, index)


class TagStyledDelegate(HighlightRowDelegate):

    margin_x = 10
    padding = 2

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):

        super(TagStyledDelegate, self).paint(painter, option, index)

        if not index.data(role=FlagNewRole):
            return

        self.initStyleOption(option, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        fm_data = QFontMetrics(option.font)
        text_width = fm_data.horizontalAdvance(index.data())
        tag_rect = QRect(option.rect)
        tag_rect.setLeft(tag_rect.x() + text_width + self.margin_x)
        painter.setPen(QPen(QColor('#6B7280')))
        tag_font = QFont(option.font)
        tag_font.setPointSize(tag_font.pointSize() - 2)
        painter.setFont(tag_font)
        painter.drawText(tag_rect, option.displayAlignment | Qt.AlignmentFlag.AlignVCenter, 'NEU')
        fm_tag = QFontMetrics(tag_font)
        border_rect = QRect(tag_rect)
        border_rect.setLeft(border_rect.left() - self.padding)
        border_rect.setTop(border_rect.top() + round(0.5*self.padding))
        border_rect.setBottom(border_rect.bottom() - round(0.5*self.padding))
        border_rect.setRight(border_rect.left() + fm_tag.horizontalAdvance('NEU') + 2*self.padding)
        painter.setPen(QPen(QColor('#16A34A')))
        painter.drawRoundedRect(border_rect, 5, 5)

        painter.restore()


class HighlightRowProxyStyle(QProxyStyle):

    def drawPrimitive(self, element, option: QStyleOption, painter: QPainter, widget=None):
        if element == QStyle.PrimitiveElement.PE_PanelItemViewRow or element == QStyle.PrimitiveElement.PE_PanelItemViewItem:
            opt = QStyleOptionViewItem(option)
            painter.save()

            if opt.state & QStyle.StateFlag.State_Selected:
                painter.fillRect(opt.rect, QColor('#CBD5E1'))
            elif opt.state & QStyle.StateFlag.State_MouseOver:
                painter.fillRect(opt.rect, QColor('#E2E8F0'))

            painter.restore()
            return
        elif element == QStyle.PrimitiveElement.PE_FrameFocusRect:
            return
        super(HighlightRowProxyStyle, self).drawPrimitive(element, option, painter)


class ClearIconProxyStyle(QProxyStyle):
    """ Proxy style that can be applied to QLineEdit's
        to swap the default clear button with the QGIS variant"""
    def standardIcon(self, standard_icon, option=None, widget=None):
        if standard_icon == QStyle.StandardPixmap.SP_LineEditClearButton:
            return QIcon(':/images/themes/default/mIconClearText.svg')
        return super().standardIcon(standard_icon, option, widget)


class RemoveFrameFocusProxyStyle(QProxyStyle):
    def drawPrimitive(self, element, option: QStyleOption, painter: QPainter, widget=None):
        if element == QStyle.PrimitiveElement.PE_FrameFocusRect:
            return
        super(RemoveFrameFocusProxyStyle, self).drawPrimitive(element, option, painter)


class EmptyStateFilter(QObject):
    """
    An event filter that automatically paints empty states for views.
    Installs itself on the view's viewport to intercept paint events.
    """

    def __init__(self, view: QAbstractItemView, parent=None):
        super().__init__(parent or view)
        self._view = view

        # Default settings
        self._icon_path = None
        self._icon_size = 48
        self._icon_color = QColor(100, 100, 100)
        self._title = "No items to display"
        self._subtitle = None
        self._title_color = QColor(100, 100, 100)
        self._subtitle_color = QColor(150, 150, 150)
        self._spacing = 10
        self._subtitle_spacing = 8
        self._title_font = None
        self._subtitle_font = None

        self._active = True

        # Install event filter to intercept paint events
        self._view.viewport().installEventFilter(self)

    def set_active(self, active: bool):
        self._active = active
        return self

    def set_icon(self, icon_path: str):
        """Set the path to the SVG icon."""
        self._icon_path = icon_path
        return self

    def set_icon_size(self, size: int):
        """Set the icon size in pixels."""
        self._icon_size = size
        return self

    def set_title(self, text: str):
        """Set the title text."""
        self._title = text
        return self

    def set_subtitle(self, text: str):
        """Set the optional subtitle text."""
        self._subtitle = text
        return self

    def set_title_color(self, color: QColor):
        """Set the title text color."""
        self._title_color = color
        self._icon_color = color
        return self

    def set_subtitle_color(self, color: QColor):
        """Set the subtitle text color."""
        self._subtitle_color = color
        return self

    def set_spacing(self, spacing: int):
        """Set the spacing between icon and text."""
        self._spacing = spacing
        return self

    def set_subtitle_spacing(self, spacing: int):
        """Set the spacing between title and subtitle."""
        self._subtitle_spacing = spacing
        return self

    def set_title_font(self, font: QFont):
        """Set a custom font for the title."""
        self._title_font = font
        return self

    def set_subtitle_font(self, font: QFont):
        """Set a custom font for the subtitle."""
        self._subtitle_font = font
        return self

    def eventFilter(self, obj, event):
        if sip.isdeleted(self._view) or sip.isdeleted(self._view.viewport()) or not self._active:
            return super().eventFilter(obj, event)

        if obj == self._view.viewport() and event.type() == QEvent.Type.Paint:
            model = self._view.model()
            if model and model.rowCount() == 0:
                result = super().eventFilter(obj, event)

                painter = QPainter(self._view.viewport())
                self._draw_empty_state(painter, self._view.viewport().rect())
                painter.end()

                return True

        return super().eventFilter(obj, event)

    def _draw_empty_state(self, painter: QPainter, viewport_rect: QRect):
        """Draw the empty state in the center of the viewport."""
        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # painter.setBrush(Qt.NoBrush)

        # Calculate total height needed
        total_height = 0

        # Icon height
        if self._icon_path:
            total_height += self._icon_size + self._spacing

        # Title height
        title_font = self._title_font if self._title_font else painter.font()
        painter.setFont(title_font)
        title_metrics = painter.fontMetrics()
        title_height = title_metrics.height()
        total_height += title_height

        # Subtitle height
        subtitle_height = 0
        if self._subtitle:
            total_height += self._subtitle_spacing
            subtitle_font = self._subtitle_font if self._subtitle_font else painter.font()
            painter.setFont(subtitle_font)
            subtitle_metrics = painter.fontMetrics()
            subtitle_height = subtitle_metrics.height()
            total_height += subtitle_height

        # Starting Y position (centered vertically)
        current_y = viewport_rect.center().y() - (total_height / 2)

        # Draw icon
        if self._icon_path:
            painter.setPen(self._icon_color)
            painter.setBrush(self._icon_color)
            renderer = QSvgRenderer(self._icon_path)
            icon_rect = QRectF(0, 0, self._icon_size, self._icon_size)
            icon_rect.moveCenter(QPointF(viewport_rect.center()))
            icon_rect.moveTop(current_y)
            renderer.render(painter, icon_rect)
            current_y += self._icon_size + self._spacing

        # Draw title
        painter.setFont(title_font)
        painter.setPen(self._title_color)
        title_rect = title_metrics.boundingRect(self._title)
        title_rect.moveCenter(viewport_rect.center())
        title_rect.moveTop(int(current_y))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self._title)
        current_y += title_height

        # Draw subtitle
        if self._subtitle:
            current_y += self._subtitle_spacing
            subtitle_font = self._subtitle_font if self._subtitle_font else painter.font()
            painter.setFont(subtitle_font)
            painter.setPen(self._subtitle_color)
            subtitle_rect = subtitle_metrics.boundingRect(self._subtitle)
            subtitle_rect.moveCenter(viewport_rect.center())
            subtitle_rect.moveTop(int(current_y))
            painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, self._subtitle)

        painter.restore()



class SeparatorDelegate(QStyledItemDelegate):
    """Custom delegate that draws separators between rows"""

    link_clicked = pyqtSignal(QModelIndex)  # index

    def __init__(self, link_icon: QIcon, parent=None):
        super().__init__(parent)
        self.separator_color = QColor(200, 200, 200)  # Light gray
        self.separator_thickness = 1

        self.link_icon = link_icon

        # Badge styling
        self.badge_bg_color = QColor(220, 220, 220)  # Light gray background
        self.badge_text_color = QColor(80, 80, 80)   # Dark gray text
        self.badge_padding = 6
        self.badge_height = 20
        self.badge_radius = 10

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        if not index.isValid():
            return super().paint(painter, option, index)

        option.palette.setBrush(QPalette.ColorRole.HighlightedText, QBrush(Qt.GlobalColor.black))
        option.palette.setBrush(QPalette.ColorRole.Highlight, QColor('#CBD5E1'))

        is_last_column = index.column() == index.model().columnCount(index.parent()) - 1
        node = index.data(Qt.ItemDataRole.UserRole + 2)
        index_text = index.data(Qt.ItemDataRole.DisplayRole)

        if is_last_column and node.node_type == "section" and node.value:
            # Custom rendering for section badges
            painter.save()

            # Draw the selection/hover background if needed
            if option.state & QStyle.StateFlag.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            # Calculate badge dimensions
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.horizontalAdvance(index_text)
            badge_width = text_width + 2 * self.badge_padding

            # Center the badge vertically in the cell
            badge_rect = option.rect.adjusted(
                self.badge_padding,
                (option.rect.height() - self.badge_height) // 2,
                -option.rect.width() + badge_width + self.badge_padding,
                -(option.rect.height() - self.badge_height) // 2
            )

            # Draw badge background (rounded rectangle)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(self.badge_bg_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge_rect, self.badge_radius, self.badge_radius)

            # Draw badge text
            painter.setPen(self.badge_text_color)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, index_text)

            painter.restore()

        elif is_last_column and node and node.node_type == "relation" and node.value:
            # Custom rendering for relation links with chevron
            painter.save()
            option.palette.setBrush(QPalette.ColorRole.HighlightedText, QColor(100, 150, 255))
            if option.state & QStyle.StateFlag.State_MouseOver:
                font = option.font
                font.setUnderline(True)
                painter.setFont(font)
            super().paint(painter, option, index)

            if self.link_icon:
                icon_size = 12
                # Position icon at the right side of the text
                font_metrics = painter.fontMetrics()
                text_width = font_metrics.horizontalAdvance(index_text)

                icon_x = option.rect.left() + text_width + 8
                icon_y = option.rect.top() + (option.rect.height() - icon_size) // 2

                icon_rect = option.rect.adjusted(
                    icon_x - option.rect.left(),
                    icon_y - option.rect.top(),
                    -(option.rect.width() - icon_size - (icon_x - option.rect.left())),
                    -(option.rect.bottom() - icon_y - icon_size)
                )

                self.link_icon.paint(painter, icon_rect)

            painter.restore()
        else:
            # Standard rendering for other items
            super().paint(painter, option, index)

        # Only draw the separator in the last column to avoid multiple overlapping lines
        if is_last_column:
            painter.save()
            pen = QPen(self.separator_color, self.separator_thickness)
            painter.setPen(pen)

            # Get the view to calculate full row width
            view = self.parent()
            y = option.rect.bottom()
            viewport_rect = view.viewport().rect()
            painter.drawLine(0, y, viewport_rect.right(), y)

            painter.restore()

    def editorEvent(self, event, model, option, index):
        node = index.data(Qt.ItemDataRole.UserRole + 2)
        is_relation = node and node.node_type == "relation" and index.column() == 1

        if is_relation and node.value:
            if event.type() == QEvent.Type.MouseButtonRelease:
                self.link_clicked.emit(index)
                return True

        return False


