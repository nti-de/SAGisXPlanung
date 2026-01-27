import copy
import os
import sys
from typing import List, Optional

from qgis.PyQt.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QDialog, QFormLayout, QComboBox, QGroupBox, QFrame, QScrollArea,
    QTextEdit, QMessageBox, QSpacerItem, QSizePolicy, QGridLayout, QListView, QStyledItemDelegate, QStyle,
    QStyleOptionViewItem
)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QTimer, QRect, QAbstractListModel, QModelIndex, QVariant
from qgis.PyQt.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush, QIcon, QMouseEvent, QFontDatabase, QFontMetrics
import json
import uuid

from sqlalchemy.orm import load_only

from SAGisXPlanung import BASE_DIR, Session
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.core.helper.xpath import XPathExpression, PathSegment
from SAGisXPlanung.gui.style import HighlightRowProxyStyle, HighlightRowDelegate, ApplicationColor, load_svg
from SAGisXPlanung.gui.widgets.inputs.base_input_element import BaseInputElement, XPlanungInputMeta
from SAGisXPlanung.utils import full_version_required_warning


class XPathListWidget(BaseInputElement, QWidget, metaclass=XPlanungInputMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = XPathModel(self)
        self.setup_ui()

        self.xplan_item = self.get_context_value('xplan_item')

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("XPath-Ausdrücke"))
        header_layout.addStretch()

        add_btn = QPushButton("XPath hinzufügen")
        add_btn.clicked.connect(self.add_xpath)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Custom list view
        self.list_view = XPathListView()
        self.list_view.setModel(self.model)

        # Connect signals from the custom list view
        self.list_view.delegate.copyRequested.connect(self.copy_xpath_at_index)
        self.list_view.delegate.editRequested.connect(self.edit_xpath_at_index)
        self.list_view.delegate.deleteRequested.connect(self.delete_xpath_at_index)

        layout.addWidget(self.list_view)

    def add_xpath(self):
        full_version_required_warning()

    def copy_xpath_at_index(self, index):
        expression = self.model.getExpression(index)
        if expression:
            clipboard = QApplication.clipboard()
            clipboard.setText(expression.xpath)
            QMessageBox.information(self, "Kopiert", "XPath Ausdruck in Zwischenablage kopiert")

    def edit_xpath_at_index(self, index):
        full_version_required_warning()

    def delete_xpath_at_index(self, index):
        expression = self.model.getExpression(index)
        if expression:
            reply = QMessageBox.question(
                self, "Ausdruck löschen",
                f"Diesen XPath-Ausdruck löschen?\n\n{expression.xpath}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.model.removeRow(index)

    def value(self):
        return [expr.xpath for expr in self.model.expressions]

    def setDefault(self, default: List[str]):
        expressions = [XPathExpression.from_xpath(xpath) for xpath in default]
        self.model.setExpressions(expressions)

    def validate_widget(self, required):
        return True


class XPathListView(QListView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._empty_message = "Kein XPath-Ausdruck konfiguriert.\nKlicken Sie auf \"XPath hinzufügen\" um zu starten."

        self.setMouseTracking(True)
        self.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.setStyleSheet("QListView::item { padding: 5px;}")

        self.delegate = XPathItemDelegate(self)
        self.setItemDelegate(self.delegate)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.model() and self.model().is_empty():
            self._paint_empty_message(event)

    def _paint_empty_message(self, event):
        """Paint the empty state message."""
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set up font and color
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor(ApplicationColor.Grey400))

        # Calculate text rect
        rect = self.viewport().rect()
        text_rect = QRect(
            rect.x() + 20,
            rect.y() + 20,
            rect.width() - 40,
            rect.height() - 40
        )

        # Draw the message
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self._empty_message
        )

    def leaveEvent(self, event):
        self.delegate.hovered_button = {}
        self.viewport().update()
        QApplication.restoreOverrideCursor()
        super().leaveEvent(event)

class XPathModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._expressions = []

        self.font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)

    def rowCount(self, parent=QModelIndex()):
        return len(self._expressions)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._expressions):
            return NULL

        expression = self._expressions[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return expression.xpath
        elif role == Qt.ItemDataRole.UserRole:
            return expression
        elif role == Qt.ItemDataRole.FontRole:
            return self.font

        return NULL

    def insertRow(self, row, parent=QModelIndex()):
        return self.insertRows(row, 1, parent)

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            self._expressions.insert(row + i, XPathExpression())
        self.endInsertRows()
        return True

    def removeRow(self, row, parent=QModelIndex()):
        return self.removeRows(row, 1, parent)

    def removeRows(self, row, count, parent=QModelIndex()):
        if row < 0 or row + count > len(self._expressions):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        for i in range(count):
            del self._expressions[row]
        self.endRemoveRows()
        return True

    def addExpression(self, expression):
        row = len(self._expressions)
        self.beginInsertRows(QModelIndex(), row, row)
        self._expressions.append(expression)
        self.endInsertRows()

    def removeExpression(self, expression):
        try:
            row = self._expressions.index(expression)
            self.removeRow(row)
            return True
        except ValueError:
            return False

    def getExpression(self, index) -> Optional[XPathExpression]:
        if 0 <= index < len(self._expressions):
            return self._expressions[index]
        return None

    def updateExpression(self, index, new_expression):
        if 0 <= index < len(self._expressions):
            model_index = self.createIndex(index, 0)
            self._expressions[index] = new_expression
            self.dataChanged.emit(model_index, model_index)

    def setExpressions(self, expressions):
        self.beginResetModel()
        self._expressions = expressions[:]
        self.endResetModel()

    @property
    def expressions(self):
        return self._expressions[:]

    def is_empty(self):
        return len(self._expressions) == 0


class XPathItemDelegate(HighlightRowDelegate):
    copyRequested = pyqtSignal(int)
    editRequested = pyqtSignal(int)
    deleteRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.button_rects = {}  # button rectangles for hit testing
        self.hovered_button = {}  # {row: 'copy' | 'edit' | 'delete' | None}

        self.copy_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/copy.svg'),
                                        color=ApplicationColor.Tertiary))
        self.edit_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/edit.svg'),
                                        color=ApplicationColor.Tertiary))
        self.delete_icon = QIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/delete.svg'),
                                          color=ApplicationColor.Tertiary))

    def paint(self, painter, option, index):
        expression = index.data(Qt.ItemDataRole.UserRole)
        if not expression:
            return

        icon_area_width = 90
        text_rect = QRect(
            option.rect.left() + 5,
            option.rect.top(),
            option.rect.width() - icon_area_width - 15,
            option.rect.height()
        )
        painter.setFont(index.data(Qt.ItemDataRole.FontRole))
        metrics = QFontMetrics(painter.font())
        elided_text = metrics.elidedText(expression.xpath, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_text)

        # Button area
        button_y = option.rect.top() + (option.rect.height() - 30) // 2
        button_spacing = 30

        row = index.row()
        self.button_rects[row] = {}

        copy_rect = QRect(option.rect.right() - 90, button_y, 30, 30)
        edit_rect = QRect(option.rect.right() - 60, button_y, 30, 30)
        delete_rect = QRect(option.rect.right() - 30, button_y, 30, 30)

        self.button_rects[row] = {
            'copy': copy_rect,
            'edit': edit_rect,
            'delete': delete_rect
        }

        hovered = self.hovered_button.get(row, None)
        self._draw_button(painter, copy_rect, self.copy_icon, hovered == 'copy')
        self._draw_button(painter, edit_rect, self.edit_icon, hovered == 'edit')
        self._draw_button(painter, delete_rect, self.delete_icon, hovered == 'delete')

    def _draw_button(self, painter, rect, icon: QIcon, hovered=False):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if hovered:
            painter.setBrush(QBrush(QColor(ApplicationColor.Grey200)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 3, 3)

        icon_size = 16
        icon_rect = QRect(
            rect.x() + (rect.width() - icon_size) // 2,
            rect.y() + (rect.height() - icon_size) // 2,
            icon_size,
            icon_size
        )
        icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)
        painter.restore()


    def sizeHint(self, option, index):
        return QRect(0, 0, 0, 40).size()

    def editorEvent(self, event, model, option, index):
        row = index.row()

        if event.type() == QMouseEvent.Type.MouseMove:
            pos = event.pos()
            hovered = None

            for key, rect in self.button_rects.get(row, {}).items():
                if rect.contains(pos):
                    hovered = key
                    break

            if self.hovered_button.get(row) != hovered:
                self.hovered_button = {row: hovered}
                option.widget.viewport().update()

            if hovered:
                option.widget.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                option.widget.setCursor(Qt.CursorShape.ArrowCursor)

            return False

        elif event.type() == QMouseEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            option.widget.setCursor(Qt.CursorShape.ArrowCursor)
            for key, rect in self.button_rects.get(row, {}).items():
                if rect.contains(pos):
                    if key == 'copy':
                        self.copyRequested.emit(row)
                    elif key == 'edit':
                        self.editRequested.emit(row)
                    elif key == 'delete':
                        self.deleteRequested.emit(row)
                    return True

        return super().editorEvent(event, model, option, index)