from qgis.PyQt.QtGui import QPixmap, QPainter, QColor, QIcon
from qgis.PyQt.QtCore import QObject, QEvent, QSize


def load_svg(svg, color=None):
    img = QPixmap(svg)
    if color:
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect(img.rect(), QColor(color))
        qp.end()
    return QIcon(img)


class SVGButtonEventFilter(QObject):
    """ Eventfilter to style common toolbutton widgets that use a svg icon"""

    def __init__(self, color='#6B7280', hover_color='#1F2937'):
        super().__init__()
        self.color = color
        self.hover_color = hover_color

    def eventFilter(self, obj, event):
        if event.type() == QEvent.HoverEnter:
            obj.setIcon(load_svg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color=self.hover_color))
        elif event.type() == QEvent.HoverLeave:
            obj.setIcon(load_svg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color=self.color))
        return False


