import logging
from enum import Enum
from typing import List

from qgis.core import QgsRendererAbstractMetadata
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtGui import QBrush, QPainterPath, QColor, QPainter
from qgis.PyQt.QtCore import QPointF, QRectF
from qgis.core import (QgsPointXY, QgsRenderContext, QgsUnitTypes, QgsFeatureRenderer,  Qgis)
from qgis.utils import iface

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



class BuildingTemplateRenderer(QgsFeatureRenderer):

    def __init__(self, _type: str):
        super().__init__(_type)

    def usedAttributes(self, context):
        return ["id", "skalierung", "drehwinkel", "rows", "cell_content"]

    def symbolForFeature(self, feature, context):
        return None

    def willRenderFeature(self, feature, context):
        return True

    def renderFeature(self, feature, context, layer=-1, selected=False, drawVertexMarker=False):
        painter = context.painter()
        if not painter:
            return False

        if not feature.hasGeometry() or feature.geometry().type() != Qgis.GeometryType.Point:
            return False

        attr_map = dict(feature.attributeMap())
        table = BuildingTemplateItem(
            attr_map.get('id'),
            iface.mapCanvas(),
            feature.geometry().asPoint(),
            int(attr_map.get('zeilenAnz', 3)),
            TableCell.deserialize_cells(str(attr_map.get('cell_content', ''))),
            scale=float(attr_map.get('skalierung', 0)),
            angle=int(float((attr_map.get('drehwinkel', 0))))
        )

        painter.save()

        try:
            # Check if table position is within current extent
            if not context.extent().contains(table.position):
                return False

            table.paint(painter, context)

            return True
        finally:
            painter.restore()

    def clone(self):
        r = BuildingTemplateRenderer(self.type())
        return r

    def save(self, doc, context):
        elem = doc.createElement('renderer-v2')
        elem.setAttribute('type', self.type())
        return elem

    def load(self, symbology_elem, context):
        r_type = symbology_elem.attribute('type')
        r = BuildingTemplateRenderer(r_type)
        return r


class BuildingTemplateRendererMetadata(QgsRendererAbstractMetadata):
    def __init__(self):
        super().__init__('sagisxplanung.buildingtemplate', 'SAGis XPlanung: Nutzungsschablone')

    def createRenderer(self, element, context):
        r_type = element.attribute('type')
        return BuildingTemplateRenderer(r_type)


class BuildingTemplateItem:
    """ Dekoriert Punkt mit Nutzungsschablone """

    xtype = 'XP_Nutzungsschablone'

    _path = None
    _color = QColor('black')
    _center = None
    _pen_width_map_units = 0.1

    def __init__(self, ppo_id, canvas: QgsMapCanvas, center: QgsPointXY, rows: int, data: List['TableCell'],
                 scale=1, angle=0):
        self.id = ppo_id
        self.canvas = canvas
        self.data = data
        self.position = center

        self._scale = scale
        self._angle = angle

        settings = self.canvas.mapSettings()
        self.context = QgsRenderContext.fromMapSettings(settings)

        map_to_pixel = self.context.mapToPixel()
        self._center = map_to_pixel.transform(self.position).toQPointF()

        self.columns = 2
        self.rows = rows
        self.cell_width = 8
        self.cell_height = 4
        self.width = self.cell_width * 2
        self.height = self.cell_height * self.rows

        self.updatePath()

    def setItemData(self, data):
        self.data = data

    def paint(self, painter, context):
        self.context = context
        painter.setRenderHint(QPainter.Antialiasing)

        brush = QBrush(self._color)
        painter.setBrush(brush)

        map_to_pixel = self.context.mapToPixel()
        self._center = map_to_pixel.transform(self.position).toQPointF()

        painter.save()
        painter.translate(self._center)
        painter.rotate(self._angle)
        painter.scale(self._scale, self._scale)

        self.updatePath()
        pen = painter.pen()
        pen.setWidthF(
            self.context.convertToPainterUnits(
                self._pen_width_map_units, # * self._scale,
                QgsUnitTypes.RenderMapUnits
            )
        )
        painter.strokePath(self._path, pen)

        self.paint_cell_content(painter)

        painter.restore()

    def paint_cell_content(self, painter: QPainter):
        height = self.context.convertToPainterUnits(self.height, QgsUnitTypes.RenderMapUnits)
        width = self.context.convertToPainterUnits(self.width, QgsUnitTypes.RenderMapUnits)
        cell_height = self.context.convertToPainterUnits(self.cell_height, QgsUnitTypes.RenderMapUnits)
        cell_width = self.context.convertToPainterUnits(self.cell_width, QgsUnitTypes.RenderMapUnits)

        for i in range(self.rows):
            for j in range(self.columns):
                rect = QRectF(
                    (j - 1) * cell_width,
                    (-height / 2 + i * cell_height),
                    cell_width,
                    cell_height
                )

                data = self.cell_data(i, j)
                data.paint(rect, self.context)

    def cell_data(self, row: int, col: int) -> 'TableCell':
        index = row * self.columns + col % self.columns
        return self.data[index]

    def set_cell_data(self, cell_index: int, new_cell: TableCell):
        self.data[cell_index] = new_cell

    def replace_cells_of_type(self, new_cell: TableCell):
        for i, cell in enumerate(self.data):
            if type(cell) is type(new_cell):
                self.data[i] = new_cell

    def setCenter(self, point: QgsPointXY):
        self.position = point
        map_to_pixel = self.context.mapToPixel()
        self._center = map_to_pixel.transform(self.position).toQPointF()

    def setRowCount(self, row_count: int):
        self.rows = row_count
        self.height = self.cell_height * self.rows
        # updateCanvas() is not enough here, because the extent of the item changes
        # therefore do a expensive canvas refresh once
        self.canvas.refresh()

    def setAngle(self, angle: int):
        self._angle = angle

    def setScale(self, scale: float):
        self._scale = scale

    def updatePath(self):
        self._path = QPainterPath(self._center)

        height = self.context.convertToPainterUnits(self.height, QgsUnitTypes.RenderMapUnits)
        width = self.context.convertToPainterUnits(self.width, QgsUnitTypes.RenderMapUnits)

        top_left = QPointF(-width/2, -height/2)

        for i in range(self.rows - 1):
            y_pos = top_left.y() + (i + 1) * height / self.rows
            self._path.moveTo(QPointF(top_left.x(), y_pos))
            self._path.lineTo(QPointF(top_left.x() + width, y_pos))

        # vertical bar
        self._path.moveTo(QPointF(0, -height / 2))
        self._path.lineTo(QPointF(0, height / 2))

        # box
        self._path.addRect(top_left.x(), top_left.y(), width, height)

    def boundingRect(self):
        return self._path.boundingRect()

    def center(self) -> QgsPointXY:
        return self._center


class TableCellFactory:

    @staticmethod
    def create_cell(cell_datatype: 'BuildingTemplateCellDataType', xplan_objekt) -> 'TableCell':
        cell_type = cell_datatype.value

        attributes = {}

        for affected_col in cell_type.affected_columns:
            attr_name, value = xplan_objekt.get_attr(affected_col)
            attributes[attr_name] = value

        return cell_type(attributes)

