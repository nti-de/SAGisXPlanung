import logging
import sys
from typing import List

logger = logging.getLogger(__name__)

if sys.version_info >= (3, 11):
    from enum import StrEnum as StrEnumCompat
else:
    from enum import Enum

    class StrEnumCompat(str, Enum):
        pass


class ApplicationColor(StrEnumCompat):
    PrimaryText = '#000000'
    MutedText = '#4b5563'

    Primary = '#1D4ED8'
    PrimaryLight = '#3B82F6'
    PrimaryLightest = '#EFF6FF'
    PrimaryDark = '#1E3A8A'
    Secondary = '#111827'

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
    Grey600 = '#4b5563'


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
