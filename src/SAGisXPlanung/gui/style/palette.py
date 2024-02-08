import logging
from enum import Enum
from typing import List

logger = logging.getLogger(__name__)


class ApplicationColor(str, Enum):
    Primary = '#000000'
    Secondary = '#111827'
    Error = '#be123c'
    Success = '#15803d'

    OnPrimary = '#ffffff'

    Grey400 = '#9ca3af'
    Grey600 = '#4b5563'

    def __str__(self):
        return str(self.name)


def with_color_palette(widget, colors: List[ApplicationColor], class_=''):
    stylesheet = ''
    for color in colors:
        stylesheet += f'''
        {class_}[{color}=true] {{
                color: {color.value};
            }}
        '''

    widget.setStyleSheet(widget.styleSheet() + stylesheet)


def apply_color(widget, color: ApplicationColor):
    # remove any previous color props
    properties = widget.dynamicPropertyNames()
    for prop in properties:
        for enum_color in ApplicationColor:
            if str(enum_color) in prop.data().decode('utf-8'):
                widget.setProperty(prop, None)

    widget.setProperty(str(color), True)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
