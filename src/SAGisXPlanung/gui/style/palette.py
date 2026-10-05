import logging
import sys
from typing import List

from qgis.PyQt.QtCore import Qt

from SAGisXPlanung import PYQT5

logger = logging.getLogger(__name__)

if sys.version_info >= (3, 11):
    from enum import StrEnum as StrEnumCompat
else:
    from enum import Enum

    class StrEnumCompat(str, Enum):
        pass


def is_dark_mode() -> bool:
    if PYQT5:
        return False
    else:
        from qgis.PyQt.QtGui import QGuiApplication

        style_hints = QGuiApplication.styleHints()
        color_mode = style_hints.colorScheme()

        return color_mode == Qt.ColorScheme.Dark


class ApplicationColor(StrEnumCompat):
    PrimaryText = '#ffffff' if is_dark_mode() else '#000000'
    SecondaryText = '#93c5fd' if is_dark_mode() else '#1e40af'
    MutedText = '#cbd5e1' if is_dark_mode() else '#4b5563'

    Primary = '#1D4ED8'
    PrimaryLight = '#3B82F6'
    PrimaryLightest = '#162456' if is_dark_mode() else '#EFF6FF'
    PrimaryDark = '#1E3A8A'
    Secondary = '#bedbff' if is_dark_mode() else '#111827'

    Background = '#2d2d2d' if is_dark_mode() else '#FFFFFF'
    BackgroundHover = '#383838' if is_dark_mode() else '#F3F4F6'

    Error = '#be123c'
    ErrorBackground = '#FECACA'
    Success = '#15803d'
    SuccessBackground = '#BBF7D0'
    WarningText = '#D97706'
    WarningBackground = '#FEF3C7'

    OnPrimary = '#ffffff'

    Grey100 = '#f3f4f6'
    Grey200 = '#e5e7eb'
    Grey300 = '#d1d5db'
    Grey400 = '#9ca3af'
    Grey500 = '#6a7282'
    Grey600 = '#4b5563'

    Surface = '#3a3a3a' if is_dark_mode() else Grey100          # subtle panel/section tints
    SurfaceStrong = '#454545' if is_dark_mode() else Grey200    # actionable items, chips, rows, buttons
    SurfaceHighlighted = '#565656' if is_dark_mode() else Grey300  # selected rows, items
    Border = '#565656' if is_dark_mode() else Grey300           # dividers, outlines, borders
    IconMuted = Grey300 if is_dark_mode() else Grey500        # secondary icons
    TextStrong = Grey300 if is_dark_mode() else Grey600       # highest-contrast neutral text


def with_color_palette(widget, colors: List[ApplicationColor], class_=''):
    stylesheet = ''
    for color in colors:
        stylesheet += f'''
        {class_}[{color.name}=true] {{
                color: {color.value};
            }}
        '''

    widget.setStyleSheet(widget.styleSheet() + stylesheet)


def apply_color(widget, color: ApplicationColor):
    # remove any previous color props
    properties = widget.dynamicPropertyNames()
    for prop in properties:
        for enum in ApplicationColor:
            if enum.name == prop.data().decode('utf-8'):
                widget.setProperty(prop, None)

    widget.setProperty(color.name, True)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
