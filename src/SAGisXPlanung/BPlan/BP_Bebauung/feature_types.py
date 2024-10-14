import logging
import os
import uuid
from typing import List

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsPointXY, QgsGeometry, QgsSingleSymbolRenderer, QgsUnitTypes,
                       QgsSimpleLineSymbolLayer, QgsLimitedRandomColorRamp, QgsRuleBasedRenderer, QgsSymbolLayerUtils,
                       QgsSimpleFillSymbolLayer)
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtCore import Qt, QSize
from qgis.utils import iface

from geoalchemy2 import WKBElement
from sqlalchemy import Integer, Column, ForeignKey, Float, Enum, String, Boolean, event
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, load_only, joinedload, declared_attr

from SAGisXPlanung import Session, XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.BPlan.BP_Bebauung.enums import (BP_Zulaessigkeit, BP_Bauweise, BP_BebauungsArt, BP_GrenzBebauung,
                                                   BP_ZweckbestimmungNebenanlagen)
from SAGisXPlanung.core.buildingtemplate.template_item import BuildingTemplateCellDataType, BuildingTemplateItem, \
    TableCellFactory
from SAGisXPlanung.core.buildingtemplate.template_cells import TableCell
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_Nutzungsschablone
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.enums import (XP_AllgArtDerBaulNutzung, XP_BesondereArtDerBaulNutzung, XP_AbweichungBauNVOTypen,
                                       XP_Sondernutzungen)
from SAGisXPlanung.core.mixins.mixins import LineGeometry, PolygonGeometry, FlaechenschlussObjekt, UeberlagerungsObjekt
from SAGisXPlanung.XPlan.types import Angle, Area, Length, Volume, Scale, ConformityException, GeometryType, XPEnum
from SAGisXPlanung.XPlanungItem import XPlanungItem

logger = logging.getLogger(__name__)


class BP_BaugebietsTeilFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Teil eines Baugebiets mit einheitlicher Art der baulichen Nutzung. """

    def __init__(self):
        super(BP_BaugebietsTeilFlaeche, self).__init__()

        self.id = uuid.uuid4()
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
    besondereArtDerBaulNutzung = Column(XPEnum(XP_BesondereArtDerBaulNutzung, include_default=True))

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

        cell_data = self.usage_cell_data(template.data_attributes)
        rows = template.zeilenAnz
        scale = template.skalierung
        angle = template.drehwinkel
        table = BuildingTemplateItem(iface.mapCanvas(), point, rows, cell_data,
                                     parent=self.xplan_item, scale=scale, angle=angle)
        # connect to signal on event filter, because QGraphicsItems can't emit signals
        table.event_filter.positionUpdated.connect(lambda p: self.onTemplatePositionUpdated(p))
        MapLayerRegistry().add_canvas_item(table, str(self.id), self.xplan_item.plan_xid)

        return feat

    def onTemplatePositionUpdated(self, pos: QgsPointXY):
        with Session.begin() as session:
            _self = session.query(self.xplan_item.xtype).options(
                load_only('position'),
                joinedload('wirdDargestelltDurch')
            ).get(self.xplan_item.xid)
            geom = QgsGeometry.fromPointXY(pos)
            _self.template().position = WKBElement(geom.asWkb(), srid=_self.position.srid)

    def template(self) -> XP_Nutzungsschablone:
        template = next((x for x in self.wirdDargestelltDurch if isinstance(x, XP_Nutzungsschablone)), None)
        if template is None:
            template = XP_Nutzungsschablone()
            template.dientZurDarstellungVon_id = self.id
            self.wirdDargestelltDurch.append(template)

        return template

    def usage_cell_data(self, cells: List[BuildingTemplateCellDataType] = None) -> List[TableCell]:
        if cells is None:
            cells = BuildingTemplateCellDataType.as_default()

        cell_data = [TableCellFactory.create_cell(cell_type, self) for cell_type in cells]
        return cell_data

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


class BP_UeberbaubareGrundstuecksFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Festsetzung der überbaubaren Grundstücksfläche (§9, Abs. 1, Nr. 2 BauGB). """

    __tablename__ = 'bp_grundstueck_ueberbaubar'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_grundstueck_ueberbaubar',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    dachgestaltung = relationship("BP_Dachgestaltung", back_populates="grundstueck_ueberbaubar", cascade="all, delete",
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
    bauweise = Column(XPEnum(BP_Bauweise, include_default=True))
    # BP_AbweichendeBauweise[0..1]
    vertikaleDifferenzierung = Column(Boolean)
    bebauungsArt = Column(XPEnum(BP_BebauungsArt, include_default=True))
    bebauungVordereGrenze = Column(XPEnum(BP_GrenzBebauung, include_default=True))
    bebauungRueckwaertigeGrenze = Column(XPEnum(BP_GrenzBebauung, include_default=True))
    bebauungSeitlicheGrenze = Column(XPEnum(BP_GrenzBebauung, include_default=True))
    refGebaeudequerschnitt = relationship("XP_ExterneReferenz", back_populates="grundstueck_ueberbaubar",
                                          cascade="all, delete", passive_deletes=True)
    geschossMin = Column(Integer)
    geschossMax = Column(Integer)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        symbol.setOpacity(0.4)

        fill = QgsSimpleFillSymbolLayer(QColor('#beb297'))
        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())


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


class BP_NebenanlagenFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Fläche für Nebenanlagen, die auf Grund anderer Vorschriften für die Nutzung von Grundstücken erforderlich sind,
    wie Spiel-, Freizeit- und Erholungsflächen sowie die Fläche für Stellplätze und Garagen mit ihren Einfahrten
    (§9 Abs. 1 Nr. 4 BauGB) """

    __tablename__ = 'bp_nebenanlage'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_nebenanlage',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(ARRAY(Enum(BP_ZweckbestimmungNebenanlagen)), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestNebenanlagen", back_populates="nebenanlage",
                                       cascade="all, delete", passive_deletes=True)

    Zmax = Column(Integer)

    def layer_fields(self):
        return {
            'zweckbestimmung': ', '.join(str(z.value) for z in self.zweckbestimmung) if self.zweckbestimmung else '',
        }

    @classmethod
    def import_zweckbestimmung_attr(cls, version):
        if version == XPlanVersion.FIVE_THREE:
            return 'zweckbestimmung'
        else:
            return 'rel_zweckbestimmung'

    @classmethod
    def xp_relationship_properties(cls) -> List[XPRelationshipProperty]:
        return [
            XPRelationshipProperty(rel_name='rel_zweckbestimmung', xplan_attribute='zweckbestimmung',
                                   allowed_version=XPlanVersion.SIX)
        ]

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        red_outline = QgsSimpleLineSymbolLayer(QColor('red'))
        red_outline.setWidth(0.3)
        red_outline.setPenStyle(Qt.DashLine)
        red_outline.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        symbol.appendSymbolLayer(red_outline)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))

