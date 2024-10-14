import logging
from enum import Enum
from typing import List

from qgis.gui import QgsMapCanvasItem, QgsMapCanvas
from qgis.PyQt.QtWidgets import QGraphicsItem
from qgis.PyQt.QtGui import QBrush, QPainterPath, QColor, QPainter
from qgis.PyQt.QtCore import QPointF, QRectF, QEvent, QObject, Qt, pyqtSignal
from qgis.core import (QgsPointXY, QgsRenderContext, QgsUnitTypes)

from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.core.buildingtemplate.template_cells import ArtDerBaulNutzungCell, ZahlVollgeschosseCell, \
    BaumasseCell, GrundGeschossflaecheCell, GrundflaechenzahlCell, GeschossflaechenzahlCell, BebauungsArtCell, \
    BauweiseCell, DachformCell, DachneigungCell, BauHoeheCell, TableCell

logger = logging.getLogger(__name__)


class BuildingTemplateCellDataType(Enum):
    ArtDerBaulNutzung = ArtDerBaulNutzungCell
    ZahlVollgeschosse = ZahlVollgeschosseCell
    GRZ = GrundflaechenzahlCell
    GFZ = GeschossflaechenzahlCell
    BebauungsArt = BebauungsArtCell
    Bauweise = BauweiseCell
    Dachneigung = DachneigungCell
    Dachform = DachformCell
    BauHoehe = BauHoeheCell
    BauMasse = BaumasseCell
    GrundGeschossflaeche = GrundGeschossflaecheCell

    @classmethod
    def as_default(cls, rows=3):
        default = [cls.ArtDerBaulNutzung, cls.ZahlVollgeschosse, cls.GRZ, cls.GFZ, cls.BebauungsArt, cls.Bauweise]

        if rows == 4:
            default += [cls.Dachneigung, cls.Dachform]

        return default



class BuildingTemplateItem(QgsMapCanvasItem):
    """ Dekoriert Punkt mit Nutzungsschablone """

    xtype = 'XP_Nutzungsschablone'

    _path = None
    _color = QColor('black')
    _center = None

    def __init__(self, canvas: QgsMapCanvas, center: QgsPointXY, rows: int, data: List['TableCell'],
                 parent: XPlanungItem, scale=0.5, angle=0):
        super().__init__(canvas)
        self.canvas = canvas
        self.data = data
        self._center = center
        self._scale = scale
        self._angle = angle
        self.parent = parent

        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        settings = self.canvas.mapSettings()
        self.context = QgsRenderContext.fromMapSettings(settings)
        self.event_filter = CanvasEventFilter(self)

        self.columns = 2
        self.rows = rows
        self.cell_width = 10
        self.cell_height = 5
        self.width = self.cell_width * 2
        self.height = self.cell_height * self.rows

        self.updatePath()
        self.setCenter(center)
        self.setRotation(self._angle)
        self.setScale(self._scale)

        self.updateCanvas()

    def setItemData(self, data):
        self.data = data

    def paint(self, painter, option=None, widget=None):
        settings = self.canvas.mapSettings()
        self.context = QgsRenderContext.fromMapSettings(settings)
        self.context.setPainter(painter)

        painter.setRenderHint(QPainter.Antialiasing)

        brush = QBrush(self._color)
        painter.setBrush(brush)

        self.updatePath()
        painter.strokePath(self._path, painter.pen())

        self.paint_cell_content(painter)

    def paint_cell_content(self, painter: QPainter):
        height = self.context.convertToPainterUnits(self.height, QgsUnitTypes.RenderMapUnits)
        width = self.context.convertToPainterUnits(self.width, QgsUnitTypes.RenderMapUnits)
        cell_height = self.context.convertToPainterUnits(self.cell_height, QgsUnitTypes.RenderMapUnits)
        cell_width = self.context.convertToPainterUnits(self.cell_width, QgsUnitTypes.RenderMapUnits)

        for i in range(self.rows):
            for j in range(self.columns):
                rect = QRectF((j-1)*cell_width, -height / 2 + i*cell_height, cell_width, cell_height)

                data = self.cell_data(i, j)
                data.paint(rect, self.context)

    def cell_data(self, row: int, col: int) -> 'TableCell':
        index = row * self.columns + col % self.columns
        return self.data[index]

    def set_cell_data(self, cell_index: int, new_cell: TableCell):
        self.data[cell_index] = new_cell

    def beginMove(self):
        self.canvas.viewport().installEventFilter(self.event_filter)

    def endMove(self):
        self.canvas.viewport().removeEventFilter(self.event_filter)

    def setCenter(self, point: QgsPointXY):
        self._center = point
        pt = self.toCanvasCoordinates(self._center)
        self.setPos(pt)

    def setRowCount(self, row_count: int):
        self.rows = row_count
        self.height = self.cell_height * self.rows
        # updateCanvas() is not enough here, because the extent of the item changes
        # therefore do a expensive canvas refresh once
        self.canvas.refresh()

    def setAngle(self, angle: int):
        self._angle = angle
        self.setRotation(self._angle)

    def setScale(self, scale: float):
        super(BuildingTemplateItem, self).setScale(scale * 2.0)
        self._scale = scale

    def updatePath(self):
        self._path = QPainterPath()

        height = self.context.convertToPainterUnits(self.height, QgsUnitTypes.RenderMapUnits)
        width = self.context.convertToPainterUnits(self.width, QgsUnitTypes.RenderMapUnits)

        top_left = QPointF(-width/2, -height/2)

        for i in range(self.rows - 1):
            self._path.moveTo(QPointF(top_left.x(), top_left.y() + (i+1) * height/self.rows))
            self._path.lineTo(QPointF(top_left.x() + width, top_left.y() + (i+1) * height/self.rows))

        # vertical bar
        self._path.moveTo(QPointF(0, height/2))
        self._path.lineTo(QPointF(0, -height/2))

        # box
        self._path.addRect(top_left.x(), top_left.y(), width, height)

    def updatePosition(self):
        self.setCenter(self._center)

    def boundingRect(self):
        return self._path.boundingRect()

    def center(self) -> QgsPointXY:
        return self._center


class CanvasEventFilter(QObject):
    # add signal here, because QGraphicsItems dont inherit from QObject and therefore cant emit any signals themselves!
    positionUpdated = pyqtSignal(QgsPointXY)

    def __init__(self, canvas_item, parent=None):
        self.canvas_item = canvas_item
        super(CanvasEventFilter, self).__init__(parent)

    def eventFilter(self, obj, event):
        # on mouse move let canvas item follow mouse position
        if event.type() == QEvent.MouseMove:
            point = self.canvas_item.toMapCoordinates(event.pos())
            self.canvas_item.setCenter(point)
        # on click dont propagate the event and finish moving the canvas item
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                return False
            if event.button() == Qt.LeftButton:
                self.canvas_item.endMove()
                self.positionUpdated.emit(self.canvas_item.center())
            return True
        return False


class TableCellFactory:

    @staticmethod
    def create_cell(cell_datatype: 'BuildingTemplateCellDataType', xplan_objekt) -> 'TableCell':
        cell_type = cell_datatype.value

        attributes = {}

        for affected_col in cell_type.affected_columns:
            attr_name, value = xplan_objekt.get_attr(affected_col)
            attributes[attr_name] = value

        return cell_type(attributes)
