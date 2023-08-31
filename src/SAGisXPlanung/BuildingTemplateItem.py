from enum import Enum

from qgis.gui import QgsMapCanvasItem, QgsMapCanvas
from qgis.PyQt.QtWidgets import QGraphicsItem
from qgis.PyQt.QtGui import QPen, QBrush, QPainterPath, QColor, QTransform, QPainter
from qgis.PyQt.QtCore import QPointF, QRectF, QRect, pyqtSlot, QEvent, QObject, Qt, pyqtSignal
from qgis.core import (QgsPointXY, QgsRenderContext, QgsUnitTypes, QgsTextRenderer, QgsTextFormat)

from SAGisXPlanung.BPlan.BP_Bebauung.enums import BP_Bauweise, BP_BebauungsArt, BP_Dachform
from SAGisXPlanung.XPlan.enums import XP_AllgArtDerBaulNutzung, XP_BesondereArtDerBaulNutzung
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.ext.roman import to_roman


class BuildingTemplateItem(QgsMapCanvasItem):
    """ Dekoriert Punkt mit Nutzungsschablone """

    xtype = 'XP_Nutzungsschablone'

    _path = None
    _color = QColor('black')
    _center = None

    def __init__(self, canvas: QgsMapCanvas, center: QgsPointXY, rows: int, data, parent: XPlanungItem,
                 scale=0.5, angle=0):
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
        self.cell_width = 30
        self.cell_height = 16
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

        pen = QPen(self._color)
        pen.setWidth(1)
        brush = QBrush(self._color)
        painter.setBrush(brush)

        self.updatePath()
        painter.strokePath(self._path, painter.pen())

        self.paintTextCells()

    def paintTextCells(self):
        width = self.context.convertFromMapUnits(self.width, QgsUnitTypes.RenderMillimeters)
        height = self.context.convertFromMapUnits(self.height, QgsUnitTypes.RenderMillimeters)
        cell_width = self.context.convertFromMapUnits(self.cell_width, QgsUnitTypes.RenderMillimeters)
        cell_height = self.context.convertFromMapUnits(self.cell_height, QgsUnitTypes.RenderMillimeters)

        for i in range(self.rows):
            for j in range(self.columns):
                rect = QRectF((j-1)*cell_width, -height / 2 + i*cell_height, cell_width, cell_height)

                index = i * self.columns + j % self.columns
                data = self.data[index]
                data.text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)
                data.text_format.setSize(cell_height * 0.15)
                QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter, [data.text], self.context,
                                           data.text_format, True, QgsTextRenderer.AlignVCenter)

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

        height = self.context.convertFromMapUnits(self.height, QgsUnitTypes.RenderMillimeters)
        width = self.context.convertFromMapUnits(self.width, QgsUnitTypes.RenderMillimeters)

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


class BuildingTemplateCellFormat(Enum):
    Text = 1
    Symbol = 2


class BuildingTemplateCellDataType(Enum):
    ArtDerBaulNutzung = 'Art d. baulichen Nutzung'
    ZahlVollgeschosse = 'Anzahl der Vollgeschosse'
    GRZ = 'Grundflächenzahl'
    GFZ = 'Geschossflächenzahl'
    BebauungsArt = 'Art der Bebauung'
    Bauweise = 'Bauweise'
    Dachneigung = 'Dachneigung'
    Dachform = 'zulässige Dachform'

    @classmethod
    def as_default(cls, rows=3):
        default = [cls.ArtDerBaulNutzung, cls.ZahlVollgeschosse, cls.GRZ, cls.GFZ, cls.BebauungsArt, cls.Bauweise]

        if rows == 4:
            default += [cls.Dachneigung, cls.Dachform]

        return default


class BuildingTemplateData:

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

    bauweise = {
        BP_Bauweise.OffeneBauweise: 'o',
        BP_Bauweise.GeschlosseneBauweise: 'g',
        BP_Bauweise.AbweichendeBauweise: 'a',
        BP_Bauweise.KeineAngabe: '',
    }

    bebauungsart = {
        BP_BebauungsArt.Einzelhaeuser: 'E',
        BP_BebauungsArt.EinzelDoppelhaeuser: 'E, D',
        BP_BebauungsArt.EinzelhaeuserHausgruppen: 'E, G',
        BP_BebauungsArt.Doppelhaeuser: 'D',
        BP_BebauungsArt.DoppelhaeuserHausgruppen: 'D, G',
        BP_BebauungsArt.Hausgruppen: 'G',
        BP_BebauungsArt.Reihenhaeuser: 'R',
        BP_BebauungsArt.EinzelhaeuserDoppelhaeuserHausgruppen: 'E, D, G'
    }

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

    def __init__(self, cell_type: BuildingTemplateCellFormat, text: str = '',
                 text_format: QgsTextFormat = QgsTextFormat()):
        self.cell_type = cell_type
        self.text = text
        self.text_format = text_format

    @staticmethod
    def fromAttribute(item, cell_type, item2=None):
        if not item:
            return BuildingTemplateData(BuildingTemplateCellFormat.Text)

        if cell_type == BuildingTemplateCellDataType.ArtDerBaulNutzung:
            text = BuildingTemplateData.nutzungsArten[item]
            if isinstance(item2, XP_BesondereArtDerBaulNutzung):
                text += BuildingTemplateData.spezNutzungsArten[item2]
            return BuildingTemplateData(BuildingTemplateCellFormat.Text, text)

        if cell_type == BuildingTemplateCellDataType.ZahlVollgeschosse:
            text = to_roman(int(item))
            return BuildingTemplateData(BuildingTemplateCellFormat.Text, text)

        if cell_type == BuildingTemplateCellDataType.GRZ:
            return BuildingTemplateData(BuildingTemplateCellFormat.Text, str(item))

        if cell_type == BuildingTemplateCellDataType.GFZ:
            text = str(item)
            text_format = QgsTextFormat()
            # background = QgsTextBackgroundSettings()
            # background.setEnabled(True)
            # background.setType(QgsTextBackgroundSettings.ShapeCircle)
            #
            # # fill_symbol = background.fillSymbol()
            # fill_symbol = QgsFillSymbol()
            # print(fill_symbol.dump())
            # fill_symbol.deleteSymbolLayer(0)
            # line = QgsSimpleLineSymbolLayer(QColor(0, 0, 0), 0.1)
            # fill_symbol.appendSymbolLayer(line)
            # print(fill_symbol.dump())
            # background.setFillSymbol(fill_symbol)
            #
            # text_format.setBackground(background)
            return BuildingTemplateData(BuildingTemplateCellFormat.Text, text, text_format)

        if cell_type == BuildingTemplateCellDataType.BebauungsArt:
            text = BuildingTemplateData.bebauungsart[item]
            return BuildingTemplateData(BuildingTemplateCellFormat.Text, text)

        if cell_type == BuildingTemplateCellDataType.Bauweise:
            text = BuildingTemplateData.bauweise[item]
            return BuildingTemplateData(BuildingTemplateCellFormat.Text, text)

        if cell_type == BuildingTemplateCellDataType.Dachneigung:
            if item is not None:
                return BuildingTemplateData(BuildingTemplateCellFormat.Text, f'{item}°')
            elif isinstance(item2, tuple) and item2[0] is not None and item2[1] is not None:
                return BuildingTemplateData(BuildingTemplateCellFormat.Text, f'{item2[0]}-{item2[1]}°')
            else:
                return BuildingTemplateData(BuildingTemplateCellFormat.Text, '')

        if cell_type == BuildingTemplateCellDataType.Dachform:
            text = BuildingTemplateData.dachform[item]
            return BuildingTemplateData(BuildingTemplateCellFormat.Text, text)
