import logging
from enum import Enum
from typing import List

logger = logging.getLogger(__name__)


class ApplicationColor(str, Enum):
    Primary = '#000000'
    Secondary = '#4b5563'
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
    logger.debug(stylesheet)
    logger.debug(widget.styleSheet() + stylesheet)
    widget.setStyleSheet(widget.styleSheet() + stylesheet)


def apply_color(widget, color: ApplicationColor):
    # TODO: remove any previously set color from properties
    widget.setProperty(str(color), True)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
