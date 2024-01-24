import logging

from qgis.PyQt.QtCore import QModelIndex, QRect, Qt
from qgis.PyQt.QtGui import QPainter, QFontMetrics, QPen, QColor, QFont, QPalette, QBrush, QIcon
from qgis.PyQt.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QProxyStyle, QStyleOption, QStyle

logger = logging.getLogger(__name__)

FlagNewRole = Qt.UserRole + 1


class HighlightRowDelegate(QStyledItemDelegate):

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        option.palette.setBrush(QPalette.Highlight, QBrush(QColor('#CBD5E1')))
        option.palette.setBrush(QPalette.HighlightedText, QBrush(Qt.black))

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
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)

        fm_data = QFontMetrics(option.font)
        text_width = fm_data.horizontalAdvance(index.data())
        tag_rect = QRect(option.rect)
        tag_rect.setLeft(tag_rect.x() + text_width + self.margin_x)
        painter.setPen(QPen(QColor('#6B7280')))
        tag_font = QFont(option.font)
        tag_font.setPointSize(tag_font.pointSize() - 2)
        painter.setFont(tag_font)
        painter.drawText(tag_rect, option.displayAlignment | Qt.AlignVCenter, 'NEU')
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
        if element == QStyle.PE_PanelItemViewRow or element == QStyle.PE_PanelItemViewItem:
            opt = QStyleOptionViewItem(option)
            painter.save()

            if opt.state & QStyle.State_Selected:
                painter.fillRect(opt.rect, QColor('#CBD5E1'))
            elif opt.state & QStyle.State_MouseOver:
                painter.fillRect(opt.rect, QColor('#E2E8F0'))

            painter.restore()
            return
        elif element == QStyle.PE_FrameFocusRect:
            return
        super(HighlightRowProxyStyle, self).drawPrimitive(element, option, painter)


class ClearIconProxyStyle(QProxyStyle):
    """ Proxy style that can be applied to QLineEdit's
        to swap the default clear button with the QGIS variant"""
    def standardIcon(self, standard_icon, option=None, widget=None):
        logger.debug(f'called standardIcon {widget} with icon {standard_icon}')
        if standard_icon == QStyle.SP_LineEditClearButton:
            return QIcon(':/images/themes/default/mIconClearText.svg')
        return super().standardIcon(standard_icon, option, widget)