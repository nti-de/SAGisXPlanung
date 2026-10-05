import logging
from enum import Enum

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QSize, QModelIndex, Qt, QRectF, QRect, QObject, QEvent, QVariant, QPoint
from qgis.PyQt.QtGui import QPainter, QFontMetrics, QPen, QColor, QFont, QPalette, QBrush, QIcon, QPainterPath, QPixmap
from qgis.PyQt.QtWidgets import (QStyledItemDelegate, QStyleOptionViewItem, QProxyStyle, QStyleOption, QStyle,
                                 QAbstractItemView, QWidget, QAbstractButton, QStyleOptionButton, QStyleOptionTab,
                                 QLineEdit, QTabBar)

from .svg import load_svg
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
        super(RemoveFrameFocusProxyStyle, self).drawPrimitive(element, option, painter, widget)


class ModernLineEditStyle(QProxyStyle):

    RADIUS = 5
    PADDING = 8
    MIN_CONTENT_HEIGHT = 16
    BORDER_WIDTH = 1

    def __init__(self, base_style: QStyle | str | None = None, radius: int = 5, padding: int = 8,
                 background=None, border=None, focus_border=None):
        super().__init__(base_style)
        self._radius = radius
        self._padding = padding
        self._background = QColor(background) if background is not None else QColor(ApplicationColor.Background)
        self._border = QColor(border) if border is not None else QColor(ApplicationColor.Border)
        self._focus_border = QColor(focus_border) if focus_border is not None else QColor(ApplicationColor.PrimaryLight)

    def drawPrimitive(self, element, option: QStyleOption, painter: QPainter, widget: QWidget | None = None):
        if element == QStyle.PrimitiveElement.PE_FrameFocusRect and isinstance(widget, QLineEdit):
            return
        if element in (QStyle.PrimitiveElement.PE_PanelLineEdit,
                       QStyle.PrimitiveElement.PE_FrameLineEdit) and isinstance(widget, QLineEdit):
            if widget.hasFrame():
                self._draw_frame(option, painter, widget)
                return
        super().drawPrimitive(element, option, painter, widget)

    def _draw_frame(self, option: QStyleOption, painter: QPainter, widget: QLineEdit) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(option.rect).adjusted(0.5, 0.5, -0.5, -0.5)
        has_focus = bool(option.state & QStyle.StateFlag.State_HasFocus) or widget.hasFocus()
        is_enabled = bool(option.state & QStyle.StateFlag.State_Enabled)

        if not is_enabled:
            border_color = self._border
            background = QColor(ApplicationColor.SurfaceStrong)
        elif has_focus and not widget.isReadOnly():
            border_color = self._focus_border
            background = self._background
        else:
            border_color = self._border
            background = self._background

        pen = painter.pen()
        pen.setColor(border_color)
        pen.setWidthF(self.BORDER_WIDTH)
        painter.setPen(pen)
        painter.setBrush(background)
        painter.drawRoundedRect(rect, self._radius, self._radius)
        painter.restore()

    def subElementRect(self, element, option, widget: QWidget | None = None):
        rect = super().subElementRect(element, option, widget)
        if element == QStyle.SubElement.SE_LineEditContents and isinstance(widget, QLineEdit):
            # emulate horizontal `padding: 8px`; vertical padding is realized
            # via sizeFromContents/minimum height plus vertical centering
            return rect.adjusted(self._padding, 0, -self._padding, 0)
        return rect

    def sizeFromContents(self, contents_type, option, contents_size, widget: QWidget | None = None):
        size = super().sizeFromContents(contents_type, option, contents_size, widget)
        if contents_type == QStyle.ContentsType.CT_LineEdit and isinstance(widget, QLineEdit):
            min_height = self.MIN_CONTENT_HEIGHT + 2 * self._padding + 2 * self.BORDER_WIDTH
            size.setWidth(size.width() + 2 * self._padding)
            size.setHeight(max(size.height() + self._padding, min_height))
        return size

    def standardIcon(self, standard_icon, option=None, widget=None):
        if standard_icon == QStyle.StandardPixmap.SP_LineEditClearButton:
            return QIcon(':/images/themes/default/mIconClearText.svg')
        return super().standardIcon(standard_icon, option, widget)


class ModernListViewStyle(QProxyStyle):

    RADIUS = 6

    def __init__(self, base_style: QStyle | str | None = None, radius: int = 6,
                 background=None, border=None,
                 hover_background=None, hover_border=None,
                 selected_background=None, selected_border=None):
        super().__init__(base_style)
        self._radius = radius
        self._background = QColor(background) if background is not None else QColor(ApplicationColor.Background)
        self._border = QColor(border) if border is not None else QColor(ApplicationColor.SurfaceStrong)
        self._hover_background = QColor(hover_background) if hover_background is not None \
            else QColor(ApplicationColor.BackgroundHover)
        self._hover_border = QColor(hover_border) if hover_border is not None \
            else QColor(ApplicationColor.Border)
        self._selected_background = QColor(selected_background) if selected_background is not None \
            else QColor(ApplicationColor.PrimaryLightest)
        self._selected_border = QColor(selected_border) if selected_border is not None \
            else QColor(ApplicationColor.PrimaryLight)

    def drawPrimitive(self, element, option: QStyleOption, painter: QPainter, widget: QWidget | None = None):
        if element == QStyle.PrimitiveElement.PE_FrameFocusRect:
            return
        if element in (QStyle.PrimitiveElement.PE_PanelItemViewItem,
                       QStyle.PrimitiveElement.PE_PanelItemViewRow):
            self._draw_item(option, painter)
            return
        super().drawPrimitive(element, option, painter, widget)

    def drawControl(self, element, option, painter: QPainter, widget: QWidget | None = None):
        if element == QStyle.ControlElement.CE_ShapedFrame and isinstance(widget, QAbstractItemView):
            # QListView { border: none; }
            return
        super().drawControl(element, option, painter, widget)

    def _draw_item(self, option: QStyleOption, painter: QPainter) -> None:
        state = option.state
        if state & QStyle.StateFlag.State_Selected:
            background = self._selected_background
            border_color = self._selected_border
        elif state & QStyle.StateFlag.State_MouseOver:
            background = self._hover_background
            border_color = self._hover_border
        else:
            background = self._background
            border_color = self._border

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(option.rect).adjusted(0.5, 0.5, -0.5, -0.5)
        pen = painter.pen()
        pen.setColor(border_color)
        pen.setWidthF(1)
        painter.setPen(pen)
        painter.setBrush(background)
        painter.drawRoundedRect(rect, self._radius, self._radius)
        painter.restore()

    def polish(self, widget):
        super().polish(widget)
        if isinstance(widget, QAbstractItemView):
            # QStyleSheetStyle enabled hover tracking automatically for
            # ::item:hover; without QSS we have to do it ourselves.
            widget.setMouseTracking(True)
            widget.viewport().setMouseTracking(True)
            # QListView { background-color: palette(window); }
            palette = widget.palette()
            palette.setColor(QPalette.ColorRole.Base, palette.color(QPalette.ColorRole.Window))
            widget.setPalette(palette)


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
        self._icon = None
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
        self._load_icon()
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

    def _load_icon(self):
        self._icon = load_svg(self._icon_path, color=self._icon_color)

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
        if self._icon:
            icon_rect = QRect(0, 0, self._icon_size, self._icon_size)
            icon_rect.moveCenter(QPoint(viewport_rect.center()))
            icon_rect.moveTop(int(current_y))

            self._icon.paint(painter, icon_rect)
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
    SIMPLE = "simple"


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

    def __init__(self, base_style: QStyle | str | None = None):
        super().__init__(base_style)
        self._padding_horizontal = 0
        self._padding_vertical = 0

    def set_padding(self, padding: int | tuple[int, int]):
        if isinstance(padding, int):
            self._padding_horizontal = padding
            self._padding_vertical = padding
        else:
            self._padding_horizontal = padding[0]
            self._padding_vertical = padding[1]

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

        if variant == ButtonVariant.SIMPLE.value:
            bg = QColor(ApplicationColor.Surface)
            return {
                "bg": bg,
                "bg_hover": QColor(ApplicationColor.SurfaceStrong),
                "bg_pressed": _darker(QColor(ApplicationColor.SurfaceStrong), 110),
                "bg_checked": QColor(ApplicationColor.SurfaceHighlighted),
                "bg_checked_hover": _lighter(QColor(ApplicationColor.SurfaceHighlighted), 112),
                "text": QColor(ApplicationColor.PrimaryText),
                "border": QColor(ApplicationColor.Border),
                "border_checked": QColor(ApplicationColor.Border),
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

    def sizeFromContents(self, contents_type, option, contents_size, widget: QWidget | None = None):
        is_button = contents_type == QStyle.ContentsType.CT_ToolButton or contents_type == QStyle.ContentsType.CT_PushButton
        if is_button:
            size = super().sizeFromContents(contents_type, option, contents_size,widget)
            if widget.property(_VARIANT_PROPERTY) == ButtonVariant.SIMPLE.value:
                size += QSize(8, 4)
            elif self._padding_horizontal > 0 or self._padding_vertical > 0:
                size += QSize(self._padding_horizontal, self._padding_vertical)

            return size

        return super().sizeFromContents(contents_type, option, contents_size,widget)


class TabBarStyle(QProxyStyle):
    BORDER_RADIUS = 5
    HORIZONTAL_PADDING = 10
    VERTICAL_PADDING = 5
    MIN_WIDTH_EX = 20

    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PrimitiveElement.PE_FrameTabBarBase:
            # QTabBar paints this square fill behind the tabs (drawBase is on
            # by default). With rounded tabs its color shines through the
            # corners, so leave the background transparent and let the dialog
            # show through instead.
            return
        super().drawPrimitive(element, option, painter, widget)

    def polish(self, widget):
        super().polish(widget)
        if isinstance(widget, QTabBar):
            # QTabBar derives State_MouseOver from its internal hoverRect,
            # which is only maintained from HoverMove/HoverEnter events. Those
            # are only delivered with WA_Hover (stylesheets enable it
            # automatically for :hover rules, proxy styles must do it here).
            # Mouse tracking alone is not enough.
            widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            widget.setMouseTracking(True)

    def drawControl(self, element, option, painter, widget=None):
        if element != QStyle.ControlElement.CE_TabBarTab:
            return super().drawControl(element, option, painter, widget)

        if not isinstance(option, QStyleOptionTab):
            return super().drawControl(element, option, painter, widget)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        palette = option.palette
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        if selected:
            background = QColor(ApplicationColor.Background)
        elif hovered:
            background = QColor(ApplicationColor.BackgroundHover)
        else:
            background = palette.color(QPalette.ColorRole.Window)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(option.rect, self.BORDER_RADIUS, self.BORDER_RADIUS)

        if selected:
            painter.setPen(QColor(ApplicationColor.Border))
            painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.drawRoundedRect(option.rect, self.BORDER_RADIUS, self.BORDER_RADIUS)

        painter.restore()
        self.baseStyle().drawControl(QStyle.ControlElement.CE_TabBarTabLabel, option, painter, widget)

    def sizeFromContents(self, contents_type, option, contents_size, widget=None):
        if contents_type == QStyle.ContentsType.CT_TabBarTab and isinstance(option, QStyleOptionTab):
            # Start with whatever the platform style considers necessary
            # for the label/icon.
            size = self.baseStyle().sizeFromContents(contents_type, option, contents_size, widget)
            size += QSize(self.HORIZONTAL_PADDING * 2, self.VERTICAL_PADDING * 2)

            font_metrics = option.fontMetrics
            min_width = font_metrics.horizontalAdvance("x") * self.MIN_WIDTH_EX
            size.setWidth(max(size.width(), min_width))

            return size

        return super().sizeFromContents(contents_type, option, contents_size, widget)