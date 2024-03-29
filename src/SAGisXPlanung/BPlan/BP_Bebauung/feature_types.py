import logging
import os
import uuid
from typing import List

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsPointXY, QgsGeometry, QgsSingleSymbolRenderer,
                       QgsSimpleLineSymbolLayer, QgsLimitedRandomColorRamp, QgsRuleBasedRenderer, QgsSymbolLayerUtils,
                       QgsSimpleFillSymbolLayer)
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtCore import Qt, QSize, pyqtSlot
from qgis.utils import iface

from geoalchemy2 import WKBElement
from sqlalchemy import Integer, Column, ForeignKey, Float, Enum, String, Boolean, event
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, load_only, joinedload, declared_attr

from SAGisXPlanung import Session, XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.BPlan.BP_Bebauung.data_types import BP_Dachgestaltung
from SAGisXPlanung.BPlan.BP_Bebauung.enums import BP_Zulaessigkeit, BP_Bauweise, BP_BebauungsArt, BP_GrenzBebauung
from SAGisXPlanung.BuildingTemplateItem import BuildingTemplateData, BuildingTemplateCellDataType, BuildingTemplateItem
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_Nutzungsschablone
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty, fallback_renderer
from SAGisXPlanung.XPlan.enums import (XP_AllgArtDerBaulNutzung, XP_BesondereArtDerBaulNutzung, XP_AbweichungBauNVOTypen,
                                       XP_Sondernutzungen)
from SAGisXPlanung.XPlan.mixins import LineGeometry, PolygonGeometry, FlaechenschlussObjekt
from SAGisXPlanung.XPlan.types import Angle, Area, Length, Volume, Scale, ConformityException, GeometryType, XPEnum
from SAGisXPlanung.XPlanungItem import XPlanungItem

logger = logging.getLogger(__name__)


class BP_BaugebietsTeilFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Teil eines Baugebiets mit einheitlicher Art der baulichen Nutzung. """

    def __init__(self):
        super(BP_BaugebietsTeilFlaeche, self).__init__()

        self.id = uuid.uuid4()
        template = XP_Nutzungsschablone()
        template.dientZurDarstellungVon_id = self.id
        self.wirdDargestelltDurch.append(template)

        self.xplan_item = XPlanungItem(xid=str(self.id), xtype=BP_BaugebietsTeilFlaeche)

    __tablename__ = 'bp_baugebiet'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_baugebiet',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    dachgestaltung = relationship("BP_Dachgestaltung", back_populates="baugebiet", cascade="all, delete",
                                  passive_deletes=True)

    FR = Column(Angle)
    # abweichungText [BP_TextAbschnitt]
    MaxZahlWohnungen = Column(Integer)
    MinGRWohneinheit = Column(Area)
    Fmin = Column(Area)
    Fmax = Column(Area)
    Bmin = Column(Length)
    Bmax = Column(Length)
    Tmin = Column(Length)
    Tmax = Column(Length)
    GFZmin = Column(Float)
    GFZmax = Column(Float)
    GFZ = Column(Float)
    GFZ_Ausn = Column(Float)
    GFmin = Column(Area)
    GFmax = Column(Area)
    GF = Column(Area)
    GF_Ausn = Column(Area)
    BMZ = Column(Float)
    BMZ_Ausn = Column(Float)
    BM = Column(Volume)
    BM_Ausn = Column(Volume)
    GRZmin = Column(Float)
    GRZmax = Column(Float)
    GRZ = Column(Float)
    GRZ_Ausn = Column(Float)
    GRmin = Column(Area)
    GRmax = Column(Area)
    GR = Column(Area)
    GR_Ausn = Column(Area)
    Zmin = Column(Integer)
    Zmax = Column(Integer)
    Zzwingend = Column(Integer)
    Z = Column(Integer)
    Z_Ausn = Column(Integer)
    Z_Staffel = Column(Integer)
    Z_Dach = Column(Integer)
    ZUmin = Column(Integer)
    ZUmax = Column(Integer)
    ZUzwingend = Column(Integer)
    ZU = Column(Integer)
    ZU_Ausn = Column(Integer)
    wohnnutzungEGStrasse = Column(XPEnum(BP_Zulaessigkeit, include_default=True))
    ZWohn = Column(Integer)
    GFAntWohnen = Column(Scale)
    GFWohnen = Column(Area)
    GFAntGewerbe = Column(Scale)
    GFGewerbe = Column(Area)
    VF = Column(Area)
    allgArtDerBaulNutzung = Column(Enum(XP_AllgArtDerBaulNutzung))
    besondereArtDerBaulNutzung = Column(Enum(XP_BesondereArtDerBaulNutzung))

    @declared_attr
    def sondernutzung(cls):
        return XPCol(ARRAY(Enum(XP_Sondernutzungen)), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_sondernutzung_attr)

    rel_sondernutzung = relationship("BP_KomplexeSondernutzung", back_populates="baugebiet",
                                     cascade="all, delete", passive_deletes=True)

    nutzungText = XPCol(String, version=XPlanVersion.FIVE_THREE)
    abweichungBauNVO = Column(Enum(XP_AbweichungBauNVOTypen))
    bauweise = Column(XPEnum(BP_Bauweise, include_default=True))
    vertikaleDifferenzierung = Column(Boolean)
    bebauungsArt = Column(XPEnum(BP_BebauungsArt, include_default=True))
    bebauungVordereGrenze = Column(Enum(BP_GrenzBebauung))
    bebauungRueckwaertigeGrenze = Column(Enum(BP_GrenzBebauung))
    bebauungSeitlicheGrenze = Column(Enum(BP_GrenzBebauung))
    refGebaeudequerschnitt = relationship("XP_ExterneReferenz", back_populates="baugebiet", cascade="all, delete",
                                          passive_deletes=True)
    zugunstenVon = Column(String)

    @classmethod
    def import_sondernutzung_attr(cls, version):
        if version == XPlanVersion.FIVE_THREE:
            return 'sondernutzung'
        else:
            return 'rel_sondernutzung'

    @classmethod
    def xp_relationship_properties(cls) -> List[XPRelationshipProperty]:
        return [
            XPRelationshipProperty(rel_name='rel_sondernutzung', xplan_attribute='sondernutzung',
                                   allowed_version=XPlanVersion.SIX)
        ]

    @classmethod
    def symbol(cls):
        return QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        color_map = [
            ('Wohngebiet', '"allgArtDerBaulNutzung" LIKE \'WohnBauflaeche\'', QColor('#f4c3b4')),
            ('Gemischtes Gebiet', '"allgArtDerBaulNutzung" LIKE \'GemischteBauflaeche\'', QColor('#ddc885')),
            ('Gewerbliches Gebiet', '"allgArtDerBaulNutzung" LIKE \'GewerblicheBauflaeche\'', QColor('#aeb5ad')),
            ('Sondergebiet', '"allgArtDerBaulNutzung" LIKE \'SonderBauflaeche\'', QColor('#fbad03')),
            ('keine Nutzung', '"allgArtDerBaulNutzung" LIKE \'\'', QgsLimitedRandomColorRamp.randomColors(1)[0])
        ]

        renderer = QgsRuleBasedRenderer(cls.symbol())
        root_rule = renderer.rootRule()

        for label, expression, color_name in color_map:
            rule = root_rule.children()[0].clone()
            rule.setLabel(label)
            rule.setFilterExpression(expression)
            rule.symbol().setColor(color_name)
            root_rule.appendChild(rule)

        root_rule.removeChildAt(0)
        return renderer

    @classmethod
    def previewIcon(cls):
        return QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  '../../symbole/BP_Bebauung/BP_BaugebietsTeilFlaeche.svg')))

    @classmethod
    def attributes(cls):
        return ['allgArtDerBaulNutzung']

    def toCanvas(self, layer_group, plan_xid=None):
        self.xplan_item.plan_xid = str(plan_xid)
        super(BP_BaugebietsTeilFlaeche, self).toCanvas(layer_group, plan_xid)

    def asFeature(self, fields=None):
        feat = super(BP_BaugebietsTeilFlaeche, self).asFeature(fields)

        # return early when `XP_Nutzungsschablone` should not be shown
        template = self.template()
        if template.hidden:
            return feat

        if not template.position:
            geom = feat.geometry().centroid()
            point = geom.asPoint()
            template.position = WKBElement(geom.asWkb(), srid=self.position.srid)
        else:
            point = template.geometry().asPoint()

        cells = template.data_attributes
        rows = template.zeilenAnz
        scale = template.skalierung
        angle = template.drehwinkel
        table = BuildingTemplateItem(iface.mapCanvas(), point, rows, self.usageTemplateData(cells),
                                     parent=self.xplan_item, scale=scale, angle=angle)
        # connect to signal on event filter, because QGraphicsItems can't emit signals
        table.event_filter.positionUpdated.connect(lambda p: self.onTemplatePositionUpdated(p))
        MapLayerRegistry().addCanvasItem(table, str(self.id))

        return feat

    def onTemplatePositionUpdated(self, pos: QgsPointXY):
        with Session.begin() as session:
            _self = session.query(self.xplan_item.xtype).options(
                load_only('position'),
                joinedload('wirdDargestelltDurch')
            ).get(self.xplan_item.xid)
            geom = QgsGeometry.fromPointXY(pos)
            _self.template().position = WKBElement(geom.asWkb(), srid=_self.position.srid)

    def template(self):
        return next((x for x in self.wirdDargestelltDurch if isinstance(x, XP_Nutzungsschablone)), None)

    def usageTemplateData(self, cells=None):

        def f(cell_type, item, additional_data=None):
            return BuildingTemplateData.fromAttribute(item, cell_type, additional_data)

        cell_mapping = {
            BuildingTemplateCellDataType.ArtDerBaulNutzung: (self.allgArtDerBaulNutzung, self.besondereArtDerBaulNutzung),
            BuildingTemplateCellDataType.ZahlVollgeschosse: (self.Z,),
            BuildingTemplateCellDataType.GRZ: (self.GRZ,),
            BuildingTemplateCellDataType.GFZ: (self.GFZ,),
            BuildingTemplateCellDataType.BebauungsArt: (self.bebauungsArt,),
            BuildingTemplateCellDataType.Bauweise: (self.bauweise,),
            BuildingTemplateCellDataType.Dachneigung:
                ('',) if not self.dachgestaltung else (self.dachgestaltung[0].DN,
                                                    (self.dachgestaltung[0].DNmin, self.dachgestaltung[0].DNmax)),
            BuildingTemplateCellDataType.Dachform:
                ('',) if not self.dachgestaltung else (self.dachgestaltung[0].dachform, )
        }

        if cells is None:
            cells = BuildingTemplateCellDataType.as_default()

        return [f(cell_type, *cell_mapping[cell_type]) for cell_type in cells]

    def layer_fields(self):
        return {
            'allgArtDerBaulNutzung': self.allgArtDerBaulNutzung.name if self.allgArtDerBaulNutzung else ''
        }

    def validate(self):
        if (self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Kleinsiedlungsgebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.ReinesWohngebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.AllgWohngebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.BesonderesWohngebiet.name) and (
                self.allgArtDerBaulNutzung != XP_AllgArtDerBaulNutzung.WohnBauflaeche.name):
            raise ConformityException(f'Wenn <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{self.besondereArtDerBaulNutzung}</b> hat, '
                                      f'muss <code>allgArtDerBaulNutzung</code> den Wert <b>'
                                      f'{XP_AllgArtDerBaulNutzung(1000)}</b> haben',
                                      '4.5.1.2', self.__class__.__name__)

        if (self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Dorfgebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Mischgebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.UrbanesGebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Kerngebiet.name) and (
                self.allgArtDerBaulNutzung != XP_AllgArtDerBaulNutzung.GemischteBauflaeche.name):
            raise ConformityException(f'Wenn <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{self.besondereArtDerBaulNutzung}</b> hat, '
                                      f'muss <code>allgArtDerBaulNutzung</code> den Wert <b>'
                                      f'{XP_AllgArtDerBaulNutzung(2000)}</b> haben',
                                      '4.5.1.2', self.__class__.__name__)

        if (self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Gewerbegebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Industriegebiet.name) and (
                self.allgArtDerBaulNutzung != XP_AllgArtDerBaulNutzung.GewerblicheBauflaeche.name):
            raise ConformityException(f'Wenn <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{self.besondereArtDerBaulNutzung}</b> hat, '
                                      f'muss <code>allgArtDerBaulNutzung</code> den Wert <b>'
                                      f'{XP_AllgArtDerBaulNutzung(3000)}</b> haben',
                                      '4.5.1.2', self.__class__.__name__)

        if (self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Sondergebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.SondergebietErholung.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.SondergebietSonst.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Wochenendhausgebiet.name) and (
                self.allgArtDerBaulNutzung != XP_AllgArtDerBaulNutzung.SonderBauflaeche.name):
            raise ConformityException(f'Wenn <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{self.besondereArtDerBaulNutzung}</b> hat, '
                                      f'muss <code>allgArtDerBaulNutzung</code> den Wert <b>'
                                      f'{XP_AllgArtDerBaulNutzung(4000)}</b> haben',
                                      '4.5.1.2', self.__class__.__name__)

        erholung_sondernutzungen = [XP_Sondernutzungen.Wochendhausgebiet.name, XP_Sondernutzungen.Ferienhausgebiet.name,
                                    XP_Sondernutzungen.Campingplatzgebiet.name, XP_Sondernutzungen.Kurgebiet.name,
                                    XP_Sondernutzungen.SonstSondergebietErholung.name]
        if (self.sondernutzung and not set(self.sondernutzung).isdisjoint(set(erholung_sondernutzungen))) and \
                self.besondereArtDerBaulNutzung != XP_BesondereArtDerBaulNutzung.SondergebietErholung.name:
            raise ConformityException(f'Wenn <code>sonderNutzung</code> den Wert <b>{self.sondernutzung}</b> hat, '
                                      f'muss <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{XP_BesondereArtDerBaulNutzung(2000)}</b> haben',
                                      '4.5.1.2', self.__class__.__name__)
        if (self.sondernutzung and set(self.sondernutzung).isdisjoint(set(erholung_sondernutzungen))) and \
                self.besondereArtDerBaulNutzung != XP_BesondereArtDerBaulNutzung.SondergebietSonst.name:
            raise ConformityException(f'Wenn <code>sonderNutzung</code> den Wert <b>{self.sondernutzung}</b> hat, '
                                      f'muss <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{XP_BesondereArtDerBaulNutzung(2100)}</b> haben',
                                      '4.5.1.2', self.__class__.__name__)


@event.listens_for(BP_BaugebietsTeilFlaeche, 'load')
def receive_load(target, context):
    target.xplan_item = XPlanungItem(xid=str(target.id), xtype=BP_BaugebietsTeilFlaeche)


class BP_BauGrenze(LineGeometry, BP_Objekt):
    """ Festsetzung einer Baugrenze (§9 Abs. 1 Nr. 2 BauGB, §22 und 23 BauNVO). """

    __tablename__ = 'bp_baugrenze'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_baugrenze',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    bautiefe = Column(Length)
    geschossMin = Column(Integer)
    geschossMax = Column(Integer)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
        symbol.deleteSymbolLayer(0)

        colored_strip = QgsSimpleLineSymbolLayer.create({})
        colored_strip.setColor(QColor('#1e8ebe'))
        colored_strip.setWidth(0.8)
        colored_strip.setOffset(0.3)

        border = QgsSimpleLineSymbolLayer.create({})
        border.setColor(QColor(0, 0, 0))
        border.setWidth(0.3)
        border.setPenStyle(Qt.DashDotLine)

        symbol.appendSymbolLayer(colored_strip)
        symbol.appendSymbolLayer(border)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_BauLinie(LineGeometry, BP_Objekt):
    """ Festsetzung einer Baulinie (§9 Abs. 1 Nr. 2 BauGB, §22 und 23 BauNVO). """

    __tablename__ = 'bp_baulinie'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_baulinie',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    bautiefe = Column(Length)
    geschossMin = Column(Integer)
    geschossMax = Column(Integer)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
        symbol.deleteSymbolLayer(0)

        colored_strip = QgsSimpleLineSymbolLayer.create({})
        colored_strip.setColor(QColor('#e95c4a'))
        colored_strip.setWidth(0.8)
        colored_strip.setOffset(0.3)

        border = QgsSimpleLineSymbolLayer.create({})
        border.setColor(QColor(0, 0, 0))
        border.setWidth(0.3)
        border.setPenStyle(Qt.DashDotDotLine)

        symbol.appendSymbolLayer(colored_strip)
        symbol.appendSymbolLayer(border)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_BesondererNutzungszweckFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Festsetzung einer Fläche mit besonderem Nutzungszweck, der durch besondere städtebauliche Gründe erfordert
        wird (§9 Abs. 1 Nr. 9 BauGB.). """

    __tablename__ = 'bp_besondere_nutzung'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_besondere_nutzung',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    dachgestaltung = relationship("BP_Dachgestaltung", back_populates="besondere_nutzung", cascade="all, delete",
                                  passive_deletes=True)

    FR = Column(Angle)
    MaxZahlWohnungen = Column(Integer)
    MinGRWohneinheit = Column(Area)
    Fmin = Column(Area)
    Fmax = Column(Area)
    Bmin = Column(Length)
    Bmax = Column(Length)
    Tmin = Column(Length)
    Tmax = Column(Length)
    GFZmin = Column(Float)
    GFZmax = Column(Float)
    GFZ = Column(Float)
    GFZ_Ausn = Column(Float)
    GFmin = Column(Area)
    GFmax = Column(Area)
    GF = Column(Area)
    GF_Ausn = Column(Area)
    BMZ = Column(Float)
    BMZ_Ausn = Column(Float)
    BM = Column(Volume)
    BM_Ausn = Column(Volume)
    GRZmin = Column(Float)
    GRZmax = Column(Float)
    GRZ = Column(Float)
    GRZ_Ausn = Column(Float)
    GRmin = Column(Area)
    GRmax = Column(Area)
    GR = Column(Area)
    GR_Ausn = Column(Area)
    Zmin = Column(Integer)
    Zmax = Column(Integer)
    Zzwingend = Column(Integer)
    Z = Column(Integer)
    Z_Ausn = Column(Integer)
    Z_Staffel = Column(Integer)
    Z_Dach = Column(Integer)
    ZUmin = Column(Integer)
    ZUmax = Column(Integer)
    ZUzwingend = Column(Integer)
    ZU = Column(Integer)
    ZU_Ausn = Column(Integer)
    zweckbestimmung = Column(String)
    bauweise = Column(XPEnum(BP_Bauweise, include_default=True))
    bebauungsArt = Column(XPEnum(BP_BebauungsArt, include_default=True))

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.3)

        fill = QgsSimpleFillSymbolLayer.create({})
        fill.setFillColor(QColor('white'))

        symbol.appendSymbolLayer(line)
        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))

