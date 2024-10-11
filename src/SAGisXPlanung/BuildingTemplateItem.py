import abc
import logging
from enum import Enum
from operator import attrgetter
from typing import List

from PyQt5.QtCore import QMarginsF
from PyQt5.QtGui import QFont
from qgis._core import Qgis
from qgis.gui import QgsMapCanvasItem, QgsMapCanvas
from qgis.PyQt.QtWidgets import QGraphicsItem
from qgis.PyQt.QtGui import QPen, QBrush, QPainterPath, QColor, QTransform, QPainter
from qgis.PyQt.QtCore import QPointF, QRectF, QRect, pyqtSlot, QEvent, QObject, Qt, pyqtSignal
from qgis.core import (QgsPointXY, QgsRenderContext, QgsUnitTypes, QgsTextRenderer, QgsTextFormat)

from SAGisXPlanung.BPlan.BP_Bebauung.enums import BP_Bauweise, BP_BebauungsArt, BP_Dachform
from SAGisXPlanung.XPlan.enums import XP_AllgArtDerBaulNutzung, XP_BesondereArtDerBaulNutzung
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.ext.roman import to_roman

logger = logging.getLogger(__name__)


def stroke_circle(rect: QRectF, context: QgsRenderContext):
    painter: QPainter = context.painter()
    painter.save()

    inset = context.convertToPainterUnits(0.5, QgsUnitTypes.RenderMapUnits)
    pen_width = context.convertToPainterUnits(0.25, QgsUnitTypes.RenderMapUnits)
    radius = (rect.height() / 2) - inset
    path = QPainterPath()
    path.addEllipse(rect.center(), radius, radius)
    pen: QPen = painter.pen()
    pen.setWidthF(pen_width)
    painter.strokePath(path, pen)

    painter.restore()


def stroke_triangle(rect: QRectF, context: QgsRenderContext):
    painter: QPainter = context.painter()
    painter.save()

    pen_width = context.convertToPainterUnits(0.25, QgsUnitTypes.RenderMapUnits)

    path = QPainterPath()
    path.moveTo(rect.left() + (rect.width() / 2), rect.top())
    path.lineTo(rect.bottomLeft())
    path.lineTo(rect.bottomRight())
    path.lineTo(rect.left() + (rect.width() / 2), rect.top())

    pen: QPen = painter.pen()
    pen.setWidthF(pen_width)
    painter.strokePath(path, pen)
    painter.fillPath(path, QBrush(QColor("white")))

    painter.restore()


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


class TableCell(abc.ABC):
    # mysterious scaling parameter for drawing inside rect using QgsTextRenderer
    # no clue why that is even needed and why 0.1 works as a value
    FONT_SCALE = 0.1

    def __init__(self, attributes: dict, text: str = ''):
        self.text = text
        self.attributes = attributes

    @abc.abstractmethod
    def paint(self, rect: QRectF, context: QgsRenderContext):
        pass

    @property
    @abc.abstractmethod
    def name(self):
        pass


class ArtDerBaulNutzungCell(TableCell):
    name = 'Art d. baulichen Nutzung'
    affected_columns = ['allgArtDerBaulNutzung', 'besondereArtDerBaulNutzung', 'MaxZahlWohnungen']

    nutzungsArten = {
        XP_AllgArtDerBaulNutzung.WohnBauflaeche: 'W',
        XP_AllgArtDerBaulNutzung.GemischteBauflaeche: 'M',
        XP_AllgArtDerBaulNutzung.GewerblicheBauflaeche: 'G',
        XP_AllgArtDerBaulNutzung.SonderBauflaeche: 'S',
    }

    spezNutzungsArten = {
        XP_BesondereArtDerBaulNutzung.Kleinsiedlungsgebiet: 'S',
        XP_BesondereArtDerBaulNutzung.ReinesWohngebiet: 'R',
        XP_BesondereArtDerBaulNutzung.AllgWohngebiet: 'A',
        XP_BesondereArtDerBaulNutzung.BesonderesWohngebiet: 'B',
        XP_BesondereArtDerBaulNutzung.Dorfgebiet: 'D',
        XP_BesondereArtDerBaulNutzung.Mischgebiet: 'I',
        XP_BesondereArtDerBaulNutzung.UrbanesGebiet: 'U',
        XP_BesondereArtDerBaulNutzung.Kerngebiet: 'K',
        XP_BesondereArtDerBaulNutzung.Gewerbegebiet: 'E',
        XP_BesondereArtDerBaulNutzung.Industriegebiet: 'I',
        XP_BesondereArtDerBaulNutzung.Wochenendhausgebiet: 'O\r WOCH',
        XP_BesondereArtDerBaulNutzung.Sondergebiet: 'O',
        XP_BesondereArtDerBaulNutzung.SondergebietSonst: 'O',
        XP_BesondereArtDerBaulNutzung.SondergebietErholung: '0',
        XP_BesondereArtDerBaulNutzung.SonstigesGebiet: ''
    }

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.text = self.nutzungsArten[attributes['allgArtDerBaulNutzung']]
        self.MaxZahlWohnungen = ''
        if isinstance(attributes['besondereArtDerBaulNutzung'], XP_BesondereArtDerBaulNutzung):
            self.text += self.spezNutzungsArten[attributes['besondereArtDerBaulNutzung']]
        if a := attributes.get('MaxZahlWohnungen', ''):
            self.MaxZahlWohnungen = f'{a} Wo'

    def paint(self, rect: QRectF, context: QgsRenderContext):
        text_format = QgsTextFormat()
        text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)
        text_format.setSize(rect.height() * self.FONT_SCALE)
        QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter,
                                   [self.text, self.MaxZahlWohnungen] if self.MaxZahlWohnungen else [self.text],
                                   context, text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)


class ZahlVollgeschosseCell(TableCell):
    name = 'Anzahl der Vollgeschosse'
    affected_columns = ['Z', 'Zzwingend', 'Zmin', 'Zmax', 'Z_Ausn', 'Z_Staffel', 'Z_Dach']

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.text_format = QgsTextFormat()
        self.text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

        self.text = ""
        self.zwingend = False
        if (Zmin := attributes.get('Zmin')) and (Zmax := attributes.get('Zmax')):
            self.text = f"{to_roman(Zmin)}-{to_roman(Zmax)}"
        elif Zzwingend := attributes.get('Zzwingend'):
            self.text = f"{to_roman(Zzwingend)}"
            self.zwingend = True
        elif Z := attributes.get('Z'):
            self.text = f"{to_roman(Z)}"

    def paint(self, rect: QRectF, context: QgsRenderContext):
        self.text_format.setSize(rect.height() * self.FONT_SCALE)
        QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter, [self.text], context,
                                   self.text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)

        if self.zwingend:
            stroke_circle(rect, context)


class GrundflaechenzahlCell(TableCell):
    name = 'Grundflächenzahl'
    affected_columns = ['GRZ', 'GRZmin', 'GRZmax', 'GRZ_Ausn']

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.text_format = QgsTextFormat()
        self.text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

        self.text = ""
        self.zwingend = False
        if (GRZmin := attributes.get('GRZmin')) and (GRZmax := attributes.get('GRZmax')):
            self.text = f"{GRZmin} - {GRZmax}"
        elif GRZ := attributes.get('GRZ'):
            self.text = f"{GRZ}"

    def paint(self, rect: QRectF, context: QgsRenderContext):
        self.text_format.setSize(rect.height() * self.FONT_SCALE)
        QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter, [self.text], context,
                                   self.text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)


class GeschossflaechenzahlCell(TableCell):
    name = 'Geschossflächenzahl'
    affected_columns = ['GFZ', 'GFZmin', 'GFZmax', 'GFZ_Ausn']

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.text_format = QgsTextFormat()
        self.text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

        self.text = ""
        self.range = False
        if (GFZmin := attributes.get('GFZmin')) and (GFZmax := attributes.get('GFZmax')):
            self.text = [f"{GFZmin}", f"{GFZmax}"]
            self.range = True
        elif GFZ := attributes.get('GFZ'):
            self.text = f"{GFZ}"

    def paint(self, rect: QRectF, context: QgsRenderContext):
        if not self.text:
            return

        self.text_format.setSize(rect.height() * self.FONT_SCALE)

        if not self.range:
            QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter, [self.text], context,
                                       self.text_format, True, QgsTextRenderer.AlignVCenter,
                                       Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                       Qgis.TextLayoutMode.Rectangle)

            stroke_circle(rect, context)
        else:
            rect_left = QRectF(rect.left(), rect.top(), rect.height(), rect.height())
            stroke_circle(rect_left, context)
            QgsTextRenderer().drawText(rect_left, 0, QgsTextRenderer.AlignCenter, [self.text[0]], context,
                                       self.text_format, True, QgsTextRenderer.AlignVCenter,
                                       Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                       Qgis.TextLayoutMode.Rectangle)

            rect_right = QRectF(rect.right()-rect.height(), rect.top(), rect.height(), rect.height())
            stroke_circle(rect_right, context)
            QgsTextRenderer().drawText(rect_right, 0, QgsTextRenderer.AlignCenter, [self.text[1]], context,
                                       self.text_format, True, QgsTextRenderer.AlignVCenter,
                                       Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                       Qgis.TextLayoutMode.Rectangle)


class BebauungsArtCell(TableCell):
    name = 'Art der Bebauung'
    affected_columns = ['bebauungsArt']

    bebauungsart = {
        BP_BebauungsArt.Einzelhaeuser: 'E',
        BP_BebauungsArt.EinzelDoppelhaeuser: 'ED',
        BP_BebauungsArt.EinzelhaeuserHausgruppen: 'EG',
        BP_BebauungsArt.Doppelhaeuser: 'D',
        BP_BebauungsArt.DoppelhaeuserHausgruppen: 'DG',
        BP_BebauungsArt.Hausgruppen: 'G',
        BP_BebauungsArt.Reihenhaeuser: 'R',
        BP_BebauungsArt.EinzelhaeuserDoppelhaeuserHausgruppen: 'EDG'
    }

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.text_format = QgsTextFormat()
        self.text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

        self.text = ""
        if a := attributes.get('bebauungsArt'):
            self.text = self.bebauungsart[a]

    def paint(self, rect: QRectF, context: QgsRenderContext):
        if not self.text:
            return

        self.text_format.setSize(rect.height() * self.FONT_SCALE)

        inset = context.convertToPainterUnits(0.5, QgsUnitTypes.RenderMapUnits)
        width_offset = rect.width() / 6
        triangle_rect = rect.marginsRemoved(QMarginsF(inset + width_offset, inset, inset + width_offset, inset))
        stroke_triangle(triangle_rect, context)

        QgsTextRenderer().drawText(triangle_rect, 0, QgsTextRenderer.AlignCenter, ['', self.text], context,
                                   self.text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)


class BauweiseCell(TableCell):
    name = 'Bauweise'
    affected_columns = ['bauweise']

    bauweise = {
        BP_Bauweise.OffeneBauweise: 'o',
        BP_Bauweise.GeschlosseneBauweise: 'g',
        BP_Bauweise.AbweichendeBauweise: 'a',
        BP_Bauweise.KeineAngabe: '',
    }

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.text_format = QgsTextFormat()
        self.text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

        self.text = ""
        if a := attributes.get('bauweise'):
            self.text = self.bauweise[a]

    def paint(self, rect: QRectF, context: QgsRenderContext):
        if not self.text:
            return

        self.text_format.setSize(rect.height() * self.FONT_SCALE)

        QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter, [self.text], context,
                                   self.text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)


class DachformCell(TableCell):
    name = 'Dachform'
    affected_columns = ['dachgestaltung.dachform']

    dachform = {
        BP_Dachform.Flachdach: 'FD',
        BP_Dachform.Pultdach: 'PD',
        BP_Dachform.VersetztesPultdach: 'VPD',
        BP_Dachform.GeneigtesDach: 'GD',
        BP_Dachform.Satteldach: 'SD',
        BP_Dachform.Walmdach: 'WD',
        BP_Dachform.KrueppelWalmdach: 'KWD',
        BP_Dachform.Mansarddach: 'MD',
        BP_Dachform.Zeltdach: 'ZD',
        BP_Dachform.Kegeldach: 'KeD',
        BP_Dachform.Kuppeldach: 'KuD',
        BP_Dachform.Sheddach: 'ShD',
        BP_Dachform.Bogendach: 'BD',
        BP_Dachform.Turmdach: 'TuD',
        BP_Dachform.Tonnendach: 'ToD',
        BP_Dachform.Mischform: 'GDF',
        BP_Dachform.Sonstiges: 'SDF',
    }

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.text_format = QgsTextFormat()
        self.text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

        self.text = []
        if dachform := attributes.get('dachform'):
            all_items = [self.dachform[df] for df in dachform]
            midpoint = len(all_items) // 2
            self.text = [' '.join(all_items[:midpoint]), ' '.join(all_items[midpoint:])]

    def paint(self, rect: QRectF, context: QgsRenderContext):
        if not self.text:
            return

        self.text_format.setSize(rect.height() * self.FONT_SCALE)

        QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter, filter(None, self.text), context,
                                   self.text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)


class DachneigungCell(TableCell):
    name = 'Dachneigung'
    affected_columns = ['dachgestaltung.DN', 'dachgestaltung.DNmin', 'dachgestaltung.DNmax', 'dachgestaltung.DNZwingend']

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.text_format = QgsTextFormat()
        self.text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

        self.text = []
        items_dict = {}
        if (DNmin := attributes.get('DNmin')) and (DNmax := attributes.get('DNmax')):
            for i, (low, high) in enumerate(zip(DNmin, DNmax)):
                if low and high:
                    items_dict[i] = f'{low}° - {high}°'
        if DN := attributes.get('DN'):
            for i, dn in enumerate(DN):
                if dn:
                    items_dict[i] = f'{dn}°'

        item_list = [items_dict[key] for key in sorted(items_dict.keys())]
        midpoint = len(item_list) // 2
        self.text = [' '.join(item_list[:midpoint]), ' '.join(item_list[midpoint:])]

    def paint(self, rect: QRectF, context: QgsRenderContext):
        if not self.text:
            return

        self.text_format.setSize(rect.height() * self.FONT_SCALE)

        QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter, filter(None, self.text), context,
                                   self.text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)


class BuildingTemplateCellDataType(Enum):
    ArtDerBaulNutzung = ArtDerBaulNutzungCell
    ZahlVollgeschosse = ZahlVollgeschosseCell
    GRZ = GrundflaechenzahlCell
    GFZ = GeschossflaechenzahlCell
    BebauungsArt = BebauungsArtCell
    Bauweise = BauweiseCell
    Dachneigung = DachneigungCell
    Dachform = DachformCell

    @classmethod
    def as_default(cls, rows=3):
        default = [cls.ArtDerBaulNutzung, cls.ZahlVollgeschosse, cls.GRZ, cls.GFZ, cls.BebauungsArt, cls.Bauweise]

        if rows == 4:
            default += [cls.Dachneigung, cls.Dachform]

        return default
