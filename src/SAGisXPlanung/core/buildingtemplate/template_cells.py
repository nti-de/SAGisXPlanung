import abc

from qgis.PyQt.QtCore import QRectF, QMarginsF
from qgis.PyQt.QtGui import QPainter, QPainterPath, QPen, QBrush, QColor
from qgis.core import QgsRenderContext, QgsUnitTypes, QgsTextFormat, QgsTextRenderer, Qgis

from SAGisXPlanung.BPlan.BP_Bebauung.enums import BP_BebauungsArt, BP_Bauweise, BP_Dachform
from SAGisXPlanung.XPlan.enums import XP_AllgArtDerBaulNutzung, XP_BesondereArtDerBaulNutzung, XP_ArtHoehenbezug
from SAGisXPlanung.ext.roman import to_roman


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


class TableCell(abc.ABC):
    # mysterious scaling parameter for drawing inside rect using QgsTextRenderer
    # no clue why that is even needed and why 0.1 works as a value
    FONT_SCALE = 0.1

    def __init__(self, attributes: dict, text: str = ''):
        self.text = text
        self.attributes = attributes

        self.text_format = QgsTextFormat()
        self.text_format.setSizeUnit(QgsUnitTypes.RenderMillimeters)

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


class BaumasseCell(TableCell):
    name = 'Baumasse / Baumassenzahl'
    affected_columns = ['BM', 'BMZ', 'BM_Ausn', 'BMZ_Ausn']

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.BMZ = attributes.get('BMZ')
        self.BM = attributes.get('BM')
        self.text = [
            f'BM {self.BM:.0f} m\N{SUPERSCRIPT THREE}' if self.BM else None,
            f'BMZ {self.BMZ:.2f}' if self.BMZ else None,
        ]
        self.text = list(filter(None, self.text))
        print(self.text)

    def paint(self, rect: QRectF, context: QgsRenderContext):
        self.text_format.setSize(rect.height() * (self.FONT_SCALE / len(self.text)))
        QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter, self.text, context,
                                   self.text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)


class GrundGeschossflaecheCell(TableCell):
    name = 'Grundfläche / Geschossfläche'
    affected_columns = ['GF', 'GFmin', 'GFmax', 'GR', 'GR_Ausn']

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.GR = attributes.get('GR')
        self.GF = attributes.get('GF')
        self.GFmin = attributes.get('GFmin')
        self.GFmax = attributes.get('GFmax')
        gf_text = (
            f'GF {self._num_format(self.GFmin)}-{self._num_format(self.GFmax)} m\N{SUPERSCRIPT TWO}'
            if self.GFmin is not None and self.GFmax is not None
            else f'GF {self._num_format(self.GF)} m\N{SUPERSCRIPT TWO}' if self.GF else None
        )
        self.text = [
            f'GR {self._num_format(self.GR)} m\N{SUPERSCRIPT TWO}' if self.GR else None,
            gf_text
        ]
        self.text = list(filter(None, self.text))

    def _num_format(self, val):
        return f'{val:.2f}' if val % 1 else f'{int(val)}'

    def paint(self, rect: QRectF, context: QgsRenderContext):
        self.text_format.setSize(rect.height() * (self.FONT_SCALE / len(self.text)))
        QgsTextRenderer().drawText(rect, 0, QgsTextRenderer.AlignCenter, self.text, context,
                                   self.text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)


class GrundflaechenzahlCell(TableCell):
    name = 'Grundflächenzahl'
    affected_columns = ['GRZ', 'GRZmin', 'GRZmax', 'GRZ_Ausn']

    def __init__(self, attributes: dict):
        super().__init__(attributes)

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


class BauHoeheCell(TableCell):
    name = 'Höhe baulicher Anlagen'
    affected_columns = [
        'hoehenangabe.hoehenbezug',
        'hoehenangabe.bezugspunkt',
        'hoehenangabe.hMin',
        'hoehenangabe.hMax',
        'hoehenangabe.hZwingend',
        'hoehenangabe.h'
    ]

    hoehenbezug_map = {
        XP_ArtHoehenbezug.absolutNHN: 'NHN',
        XP_ArtHoehenbezug.absolutNN: 'NN',
        XP_ArtHoehenbezug.absolutDHHN: 'DHHN',
        XP_ArtHoehenbezug.relativGelaendeoberkante: 'GOK',
        XP_ArtHoehenbezug.relativGehwegOberkante: 'Gehweg',
        XP_ArtHoehenbezug.relativBezugshoehe: '',
        XP_ArtHoehenbezug.relativStrasse: 'Straße',
        XP_ArtHoehenbezug.relativEFH: 'EFH'
    }

    def __init__(self, attributes: dict):
        super().__init__(attributes)

        self.text = []
        self.bezugspunkt = attributes.get('bezugspunkt')
        self.hoehenbezug = attributes.get('hoehenbezug')
        items_dict = {}
        if (hMin := attributes.get('hMin')) and (hMax := attributes.get('hMax')):
            for i, (bezug, low, high) in enumerate(zip(self.bezugspunkt, hMin, hMax)):
                if low and high:
                    items_dict[i] = f'{bezug.name or ""} {low}m - {high}m'
        if h := attributes.get('h'):
            for i, dn in enumerate(h):
                if dn:
                    items_dict[i] = f'{self.bezugspunkt[i].name or ""} {dn}m'

        for i in items_dict.keys():
            items_dict[i] += f' ü. {self.hoehenbezug_map[self.hoehenbezug[i]]}'

        self.text = [items_dict[key] for key in sorted(items_dict.keys())]
        self.text = list(filter(None, self.text))

    def paint(self, rect: QRectF, context: QgsRenderContext):
        if not self.text:
            return

        self.text_format.setSize(rect.height() * (self.FONT_SCALE / len(self.text)))

        inset = context.convertToPainterUnits(0.5, QgsUnitTypes.RenderMapUnits)
        rect = rect.marginsRemoved(QMarginsF(inset, inset, inset, inset))
        QgsTextRenderer().drawText(rect, 0, Qgis.TextHorizontalAlignment.Left, self.text, context,
                                   self.text_format, True, QgsTextRenderer.AlignVCenter,
                                   Qgis.TextRendererFlags(Qgis.TextRendererFlag.WrapLines),
                                   Qgis.TextLayoutMode.Rectangle)
