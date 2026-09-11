import logging
from enum import Enum

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QSize, QModelIndex, Qt, QRectF, QRect, QObject, QEvent, QVariant, QPointF
from qgis.PyQt.QtGui import QPainter, QFontMetrics, QPen, QColor, QFont, QPalette, QBrush, QIcon, QPainterPath, QPixmap
from qgis.PyQt.QtWidgets import (QStyledItemDelegate, QStyleOptionViewItem, QProxyStyle, QStyleOption, QStyle,
                                 QAbstractItemView, QWidget, QAbstractButton, QStyleOptionButton)
from qgis.PyQt.QtSvg import QSvgRenderer

from .palette import ApplicationColor

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
        option.palette.setBrush(QPalette.ColorRole.Highlight, QBrush(QColor(ApplicationColor.SurfaceHighlighted)))
        option.palette.setBrush(QPalette.ColorRole.HighlightedText, QBrush(QColor(ApplicationColor.PrimaryText)))

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
                painter.fillRect(opt.rect, QColor(ApplicationColor.SurfaceHighlighted))
            elif opt.state & QStyle.StateFlag.State_MouseOver:
                painter.fillRect(opt.rect, QColor(ApplicationColor.SurfaceStrong))

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
        self._icon_color = QColor(ApplicationColor.IconMuted)
        self._title = "No items to display"
        self._subtitle = None
        self._title_color = QColor(ApplicationColor.PrimaryText)
        self._subtitle_color = QColor(ApplicationColor.MutedText)
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
                print('paint')
                self._draw_empty_state(painter, self._view.viewport().rect())
                painter.end()

                return True

        return super().eventFilter(obj, event)

    def _draw_empty_state(self, painter: QPainter, viewport_rect: QRect):
        """Draw the empty state in the center of the viewport."""
        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

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
        if self._subtitle:
            total_height += self._subtitle_spacing
            subtitle_font = self._subtitle_font if self._subtitle_font else painter.font()
            painter.setFont(subtitle_font)
            subtitle_metrics = painter.fontMetrics()

            # Limit subtitle to the available width so it can wrap
            subtitle_rect = subtitle_metrics.boundingRect(
                viewport_rect,
                Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter,
                self._subtitle,
            )
            subtitle_height = subtitle_rect.height()
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
            painter.setFont(subtitle_font)
            painter.setPen(self._subtitle_color)

            subtitle_draw_rect = QRect(
                viewport_rect.left(),
                int(current_y),
                viewport_rect.width(),
                subtitle_height,
            )

            painter.drawText(
                subtitle_draw_rect,
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self._subtitle,
            )

        painter.restore()


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


class ButtonVariant(str, Enum):
    DEFAULT = "default"
    PRIMARY = "primary"
    SECONDARY = "secondary"


_VARIANT_PROPERTY = "buttonVariant"


def set_button_variant(button: QAbstractButton, variant: ButtonVariant | str) -> None:
    """Tag a QToolButton with a visual variant, consumed by ModernToolButtonStyle."""
    value = variant.value if isinstance(variant, ButtonVariant) else variant
    button.setProperty(_VARIANT_PROPERTY, value)
    # force a re-polish so the new variant is picked up immediately
    button.style().unpolish(button)
    button.style().polish(button)
    button.update()


def _lighter(color: QColor, factor: int = 115) -> QColor:
    return QColor(color).lighter(factor)


def _darker(color: QColor, factor: int = 115) -> QColor:
    return QColor(color).darker(factor)


class ModernToolButtonStyle(QProxyStyle):
    """A flat, rounded, stylesheet-free look for QAbstractButton."""

    RADIUS = 5
    PADDING = 5

    def __init__(self, base_style: QStyle | str | None = None):
        super().__init__(base_style)

    def _palette_for(self, widget: QWidget | None) -> dict:
        variant = widget.property(_VARIANT_PROPERTY) if widget else None

        if variant == ButtonVariant.PRIMARY.value:
            return {
                "bg": None,
                "bg_hover": QColor(ApplicationColor.SurfaceStrong),
                "bg_pressed": _darker(QColor(ApplicationColor.SurfaceStrong), 110),
                "bg_checked": QColor(ApplicationColor.SurfaceHighlighted),
                "bg_checked_hover": _lighter(QColor(ApplicationColor.SurfaceHighlighted), 106),
                "text": QColor(ApplicationColor.Primary),
                "border": None,
                "border_checked": QColor(ApplicationColor.Border),
                "border_width": 1,
            }

        if variant == ButtonVariant.SECONDARY.value:
            bg = QColor(ApplicationColor.Background)
            bg_pressed = _darker(bg, 110)
            return {
                "bg": None,
                "bg_hover": QColor(ApplicationColor.SurfaceStrong),
                "bg_pressed": _darker(QColor(ApplicationColor.SurfaceStrong), 110),
                "bg_checked": QColor(ApplicationColor.SurfaceHighlighted),
                "bg_checked_hover": _lighter(bg_pressed, 112),
                "text": QColor(ApplicationColor.OnPrimary),
                "border": QColor(ApplicationColor.Border),
                "border_width": 1,
            }

        return {
            "bg": None,
            "bg_hover": QColor(ApplicationColor.SurfaceStrong),
            "bg_pressed": _darker(QColor(ApplicationColor.SurfaceStrong), 110),
            "bg_checked": QColor(ApplicationColor.Background),
            "bg_checked_hover": _lighter(QColor(ApplicationColor.Background), 106),
            "text": None,
            "border": None,
            "border_checked": QColor(ApplicationColor.Border),
            "border_width": 1,
        }

    def drawPrimitive(self, element, option, painter: QPainter, widget: QWidget | None = None) -> None:
        if isinstance(widget, QAbstractButton):
            if element in (
                    QStyle.PrimitiveElement.PE_PanelButtonTool,
                    QStyle.PrimitiveElement.PE_PanelButtonCommand,
            ):
                self._draw_panel(option, painter, widget)
                return

            if element in (
                    QStyle.PrimitiveElement.PE_FrameButtonTool,
                    QStyle.PrimitiveElement.PE_FrameDefaultButton,
            ):
                # Some base styles (platform-dependent) draw their own frame
                # here regardless of what PE_PanelButtonTool did above. We
                # own borders entirely via the "border" key in _palette_for,
                # so swallow this and draw nothing.
                return

        super().drawPrimitive(element, option, painter, widget)

    def _draw_panel(self, option, painter: QPainter, widget: QWidget | None) -> None:
        colors = self._palette_for(widget)
        state = option.state

        is_enabled = bool(state & QStyle.StateFlag.State_Enabled)
        is_pressed = bool(state & QStyle.StateFlag.State_Sunken)
        is_checked = bool(state & QStyle.StateFlag.State_On)
        is_hover = bool(state & QStyle.StateFlag.State_MouseOver)

        border_color = colors.get("border_checked") if is_checked else colors["border"]
        if not is_enabled:
            if colors["bg"] is not None:
                painter.save()
                painter.setOpacity(0.4)
                self._fill(painter, option.rect, colors["bg"], border_color, colors["border_width"])
                painter.restore()
            return

        if is_pressed:
            color = colors["bg_pressed"]
        elif is_checked and is_hover:
            color = colors["bg_checked_hover"]
        elif is_checked:
            color = colors["bg_checked"]
        elif is_hover:
            color = colors["bg_hover"]
        else:
            color = colors["bg"]

        self._fill(painter, option.rect, color, border_color, colors["border_width"])

    def _fill(self, painter: QPainter, rect, color: QColor, border: QColor | None = None,
              border_width: int = 1) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), self.RADIUS, self.RADIUS)

        painter.setBrush(color) if color else painter.setBrush(Qt.BrushStyle.NoBrush)
        if border is not None:
            pen = painter.pen()
            pen.setColor(border)
            pen.setWidthF(border_width)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        painter.drawPath(path)
        painter.restore()

    def drawControl(self, element, option, painter: QPainter, widget: QWidget | None = None) -> None:
        is_tool_label = element == QStyle.ControlElement.CE_ToolButtonLabel and isinstance(widget, QAbstractButton)
        is_push_label = element == QStyle.ControlElement.CE_PushButtonLabel and isinstance(widget, QAbstractButton)

        if is_tool_label or is_push_label:
            colors = self._palette_for(widget)
            text_color = colors.get("text")

            if text_color is not None and (option.state & QStyle.StateFlag.State_Enabled):
                opt = QStyleOptionButton(option)
                for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
                    opt.palette.setColor(group, QPalette.ColorRole.ButtonText, text_color)
                    opt.palette.setColor(group, QPalette.ColorRole.WindowText, text_color)
                super().drawControl(element, opt, painter, widget)
                return

        super().drawControl(element, option, painter, widget)

    def pixelMetric(self, metric, option=None, widget: QWidget | None = None) -> int:
        if metric == QStyle.PixelMetric.PM_ButtonMargin and isinstance(widget, QAbstractButton):
            return self.PADDING
        return super().pixelMetric(metric, option, widget)
