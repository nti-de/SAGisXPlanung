import logging
import os
import uuid
from typing import List

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsUnitTypes,
                       QgsSimpleLineSymbolLayer, QgsLimitedRandomColorRamp, QgsRuleBasedRenderer, QgsSymbolLayerUtils,
                       QgsSimpleFillSymbolLayer, QgsFillSymbol, QgsLinePatternFillSymbolLayer)
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtCore import Qt, QSize

from sqlalchemy import Integer, Column, ForeignKey, Float, Enum, String, Boolean, event, Table
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.BPlan.BP_Bebauung.codelists import BP_DetailZweckbestGemeinschaftsanlagenCodelistAssoc
from SAGisXPlanung.BPlan.BP_Bebauung.enums import (BP_Zulaessigkeit, BP_Bauweise, BP_BebauungsArt, BP_GrenzBebauung,
                                                    BP_ZweckbestimmungNebenanlagen, BP_NebenanlagenAusschlussTyp,
                                                    BP_TypWohngebaeudeFlaeche,
                                                    BP_ZweckbestimmungGemeinschaftsanlagen,
                                                    BP_GebaeudeStellungTypen, BP_SpezielleBauweiseTypen)
from SAGisXPlanung.XPlan.core import xp_version, LayerPriorityType
from SAGisXPlanung.core.buildingtemplate.template_item import BuildingTemplateCellDataType, TableCellFactory
from SAGisXPlanung.core.buildingtemplate.template_cells import TableCell
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.enums import (XP_AllgArtDerBaulNutzung, XP_BesondereArtDerBaulNutzung, XP_AbweichungBauNVOTypen,
                                       XP_Sondernutzungen)
from SAGisXPlanung.core.mixins.mixins import LineGeometry, PolygonGeometry, FlaechenschlussObjekt, UeberlagerungsObjekt
from SAGisXPlanung.XPlan.types import Angle, Area, Length, Volume, Scale, ConformityException, GeometryType, XPEnum
from SAGisXPlanung.XPlanungItem import XPlanungItem

logger = logging.getLogger(__name__)

BP_GemeinschaftsanlagenFlaecheEigentuemerAssoc = Table('assoc_gemeinschaftsanlage_eigentuemer', BP_Objekt.metadata,
    Column('gemeinschaftsanlage_id', UUID(as_uuid=True), ForeignKey('bp_gemeinschaftsanlage.id', ondelete='CASCADE')),
    Column('baugebiet_id', UUID(as_uuid=True), ForeignKey('bp_baugebiet.id', ondelete='CASCADE'))
)


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

    # BP_TextAbschnitt [0..*] (v5.3)
    abweichungText_v5 = relationship("BP_TextAbschnitt", back_populates="bp_baugebiet",
                                     cascade="all, delete", passive_deletes=True,
                                     foreign_keys="BP_TextAbschnitt.bp_baugebiet_id",
                                     info={'xplan_version': XPlanVersion.FIVE_THREE,
                                           'xplan_attribute': 'abweichungText'})

    # XP_TextAbschnitt [0..*] (v6)
    abweichungText_v6 = relationship("XP_TextAbschnitt", back_populates="bp_baugebiet",
                                     cascade="all, delete", passive_deletes=True,
                                     foreign_keys="XP_TextAbschnitt.bp_baugebiet_id",
                                     info={'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'abweichungText'})

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

    sondernutzung = Column(ARRAY(Enum(XP_Sondernutzungen)), info={'xplan_version': XPlanVersion.FIVE_THREE})

    rel_sondernutzung = relationship("BP_KomplexeSondernutzung", back_populates="baugebiet",
                                     cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'sondernutzung'
                                       })

    detaillierteArtDerBaulNutzung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detaillierteArtDerBaulNutzung = relationship("BP_DetailArtDerBaulNutzung", back_populates="bp_baugebiet",
                                                 foreign_keys=[detaillierteArtDerBaulNutzung_id], info={
                                                     'form-type': 'inline'
                                                 })

    nutzungText = Column(String, info={'xplan_version': XPlanVersion.FIVE_THREE})
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
    def symbol(cls):
        return QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        color_map = [
            (
                'Wohnbaufläche',
                "(\"besondereArtDerBaulNutzung\" IN ('Kleinsiedlungsgebiet', 'ReinesWohngebiet', 'AllgWohngebiet', 'BesonderesWohngebiet') OR \"allgArtDerBaulNutzung\" = 'WohnBauflaeche') AND (\"flaechenschluss\" = 'True' OR \"flaechenschluss\" IS NULL)",
                QColor('#f4c3b4')),
            (
                'Gemischte Baufläche',
                "(\"besondereArtDerBaulNutzung\" IN ('Dorfgebiet', 'DoerflichesWohngebiet', 'Mischgebiet', 'UrbanesGebiet', 'Kerngebiet') OR \"allgArtDerBaulNutzung\" = 'GemischteBauflaeche') AND (\"flaechenschluss\" = 'True' OR \"flaechenschluss\" IS NULL)",
                QColor('#d5a744')),
            (
                'Gewerbliche Baufläche',
                "(\"besondereArtDerBaulNutzung\" IN ('Gewerbegebiet', 'Industriegebiet') OR \"allgArtDerBaulNutzung\" = 'GewerblicheBauflaeche') AND (\"flaechenschluss\" = 'True' OR \"flaechenschluss\" IS NULL)",
                QColor('#a6a596')),
            (
                'Sonderbaufläche',
                "(\"besondereArtDerBaulNutzung\" IN ('SondergebietErholung', 'SondergebietSonst', 'Wochenendhausgebiet', 'Sondergebiet') OR \"allgArtDerBaulNutzung\" = 'SonderBauflaeche') AND (\"flaechenschluss\" = 'True' OR \"flaechenschluss\" IS NULL)",
                QColor('#fbad03')),
            ('keine Nutzungsangabe', '"allgArtDerBaulNutzung" LIKE \'\'', QgsLimitedRandomColorRamp.randomColors(1)[0])
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

    def template_cell_data(self, cells: List[BuildingTemplateCellDataType] = None) -> List[TableCell]:
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


class BP_AbstandsFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Festsetzung eines abweichenden Masses der Tiefe der Abstandsflaeche. """

    __tablename__ = 'bp_abstand'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_abstand',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    tiefe = Column(Length)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))
        fill.setStrokeColor(QColor('#005b96'))
        fill.setStrokeWidth(0.5)
        fill.setBrushStyle(Qt.BrushStyle.FDiagPattern)
        symbol.appendSymbolLayer(fill)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_AbweichungVonBaugrenze(LineGeometry, BP_Objekt):
    """ Linienhafte Festlegung des Umfangs der Abweichung von der Baugrenze. """

    __tablename__ = 'bp_abweichung_baugrenze'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type or QgsWkbTypes.GeometryType.LineGeometry))


@xp_version(versions=[XPlanVersion.SIX])
class BP_AbweichungVonUeberbaubarerGrundstuecksFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Flaechenhafte Festlegung des Umfangs der Abweichung von der ueberbaubaren Grundstuecksflaeche. """

    __tablename__ = 'bp_abweichung_ueberbaubare_grundstuecksflaeche'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type or QgsWkbTypes.GeometryType.PolygonGeometry))


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class BP_AbweichungVonUeberbaubererGrundstuecksFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Flaechenhafte Festlegung des Umfangs der Abweichung von der ueberbaubaren Grundstuecksflaeche. """

    __table__ = BP_AbweichungVonUeberbaubarerGrundstuecksFlaeche.__table__

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type or QgsWkbTypes.GeometryType.PolygonGeometry))


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
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        symbol.setOpacity(0.4)

        fill = QgsSimpleFillSymbolLayer(QColor('#beb297'))
        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())


class BP_GebaeudeFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Grundrissflaeche eines existierenden Gebaeudes. """

    __tablename__ = 'bp_gebaeude_flaeche'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            props = {
                'color': '#dcdcdc',  # Transparent fill
                'outline_width': '0.1',  # Width
            }
            fill_layer = QgsSimpleFillSymbolLayer.create(props)
            symbol = QgsFillSymbol()
            symbol.changeSymbolLayer(0, fill_layer)
            symbol.setOpacity(0.75)
            renderer = QgsSingleSymbolRenderer(symbol)

            return renderer
        else:
            raise ValueError('Renderer of BP_GebaeudeFlaeche should only be called with polygon geometry')


class BP_PersGruppenBestimmteFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Flaeche fuer Wohngebaeude fuer Personengruppen mit besonderem Wohnbedarf. """

    __tablename__ = 'bp_persgruppen_bestimmte_flaeche'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type or QgsWkbTypes.GeometryType.PolygonGeometry))


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
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.LineGeometry)
        symbol.deleteSymbolLayer(0)

        colored_strip = QgsSimpleLineSymbolLayer.create({})
        colored_strip.setColor(QColor('#1e8ebe'))
        colored_strip.setWidth(0.8)
        colored_strip.setOffset(-0.4)
        colored_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        colored_strip.setPenJoinStyle(Qt.PenJoinStyle.MiterJoin)
        colored_strip.setPenCapStyle(Qt.PenCapStyle.FlatCap)

        border = QgsSimpleLineSymbolLayer.create({})
        border.setColor(QColor(0, 0, 0))
        border.setWidth(0.3)
        border.setPenStyle(Qt.PenStyle.DashDotLine)

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
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.LineGeometry)
        symbol.deleteSymbolLayer(0)

        colored_strip = QgsSimpleLineSymbolLayer.create({})
        colored_strip.setColor(QColor('#e95c4a'))
        colored_strip.setWidth(0.8)
        colored_strip.setOffset(-0.4)
        colored_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        colored_strip.setPenJoinStyle(Qt.PenJoinStyle.MiterJoin)
        colored_strip.setPenCapStyle(Qt.PenCapStyle.FlatCap)

        border = QgsSimpleLineSymbolLayer.create({})
        border.setColor(QColor(0, 0, 0))
        border.setWidth(0.3)
        border.setPenStyle(Qt.PenStyle.DashDotLine)

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
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
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


class BP_NebenanlagenAusschlussFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Festsetzung einer Fläche für die Einschränkung oder den Ausschluss von Nebenanlagen nach §14 Absatz 1 Satz
        3 BauNVO. """

    __tablename__ = 'bp_nebenanlagen_ausschluss_flaeche'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    typ = Column(XPEnum(BP_NebenanlagenAusschlussTyp, include_default=True))

    # BP_TextAbschnitt [0..*] (v5.3)
    abweichungText_v5 = relationship("BP_TextAbschnitt", back_populates="bp_nebenanlagen_ausschluss_flaeche",
                                     cascade="all, delete", passive_deletes=True, uselist=False,
                                     foreign_keys="BP_TextAbschnitt.bp_nebenanlagen_ausschluss_flaeche_id",
                                     info={'xplan_version': XPlanVersion.FIVE_THREE,
                                           'xplan_attribute': 'abweichungText'})

    # XP_TextAbschnitt [0..*] (v6)
    abweichungText_v6 = relationship("XP_TextAbschnitt", back_populates="bp_nebenanlagen_ausschluss_flaeche",
                                     cascade="all, delete", passive_deletes=True, uselist=False,
                                     foreign_keys="XP_TextAbschnitt.bp_nebenanlagen_ausschluss_flaeche_id",
                                     info={'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'abweichungText'})

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            symbol = QgsSymbol.defaultSymbol(geom_type)
            symbol.setColor(QColor('black'))
            symbol.deleteSymbolLayer(0)

            hatch_layer = QgsLinePatternFillSymbolLayer()
            hatch_layer.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
            hatch_layer.setDistance(4.0)
            hatch_layer.setLineAngle(135.0)

            line_symbol = hatch_layer.subSymbol()
            line_layer = line_symbol.symbolLayer(0)
            line_layer.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
            line_layer.setWidth(0.3)
            line_layer.setColor(QColor(0, 0, 0))
            line_layer.setPenStyle(Qt.PenStyle.DashLine)

            symbol.appendSymbolLayer(hatch_layer)

            return QgsSingleSymbolRenderer(symbol)
        else:
            raise ValueError('Renderer of BP_NebenanlagenAusschlussFlaeche should only be called with polygon geometry')


class BP_RegelungVergnuegungsstaetten(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Festsetzung zur Zulaessigkeit von Vergnuegungsstaetten gemaess BauGB. """

    __tablename__ = 'bp_regelung_vergnuegungsstaetten'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }
    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zulaessigkeit = Column(XPEnum(BP_Zulaessigkeit, include_default=True))

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        colored_strip = QgsSimpleLineSymbolLayer(QColor('#cb199e'))
        colored_strip.setWidth(0.3)
        colored_strip.setOffset(0.15)
        colored_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        colored_strip.setPenJoinStyle(Qt.PenJoinStyle.MiterJoin)
        symbol.appendSymbolLayer(colored_strip)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            raise ValueError('Renderer of BP_RegelungVergnuegungsstaetten should only be called with polygon geometry')


class BP_SpezielleBauweise(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Festsetzung der speziellen Bauweise oder baulichen Besonderheit. """

    __tablename__ = 'bp_spezielle_bauweise'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    typ = Column(XPEnum(BP_SpezielleBauweiseTypen, include_default=True))

    sonstTyp_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    sonstTyp = relationship('BP_SpezielleBauweiseSonstTypen', back_populates='bp_spezielle_bauweise',
                            foreign_keys=[sonstTyp_id], info={
                                'form-type': 'inline'
                            })

    Bmin = Column(Length)
    Bmax = Column(Length)
    Tmin = Column(Length)
    Tmax = Column(Length)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type or QgsWkbTypes.GeometryType.PolygonGeometry))


class BP_NebenanlagenFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Fläche für Nebenanlagen, die auf Grund anderer Vorschriften für die Nutzung von Grundstücken erforderlich sind,
    wie Spiel-, Freizeit- und Erholungsflächen sowie die Fläche für Stellplätze und Garagen mit ihren Einfahrten
    (§9 Abs. 1 Nr. 4 BauGB) """

    __tablename__ = 'bp_nebenanlage'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_nebenanlage',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(ARRAY(Enum(BP_ZweckbestimmungNebenanlagen)), info={'xplan_version': XPlanVersion.FIVE_THREE})

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestNebenanlagen", back_populates="nebenanlage",
                                       cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'zweckbestimmung'
                                       })

    Zmax = Column(Integer)

    def layer_fields(self):
        return {
            'zweckbestimmung': ', '.join(str(z.value) for z in self.zweckbestimmung) if self.zweckbestimmung else '',
        }

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        red_outline = QgsSimpleLineSymbolLayer(QColor('red'))
        red_outline.setWidth(0.3)
        red_outline.setOffset(0.15)
        red_outline.setPenStyle(Qt.PenStyle.DashLine)
        red_outline.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        symbol.appendSymbolLayer(red_outline)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_GemeinschaftsanlagenFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Fläche für Gemeinschaftsanlagen (§ 9 Abs. 1 Nr. 22 BauGB). """

    __tablename__ = 'bp_gemeinschaftsanlage'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_gemeinschaftsanlage',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(ARRAY(Enum(BP_ZweckbestimmungGemeinschaftsanlagen)),
                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    detaillierteZweckbestimmung = relationship(
        'BP_DetailZweckbestGemeinschaftsanlagen',
        back_populates='codelist_user',
        secondary=BP_DetailZweckbestGemeinschaftsanlagenCodelistAssoc,
        info={
            'xplan_version': XPlanVersion.FIVE_THREE,
            'form-type': 'inline'
        }
    )

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestGemeinschaftsanlagen",
                                       back_populates="gemeinschaftsanlage",
                                       cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'zweckbestimmung'
                                       })

    eigentuemer = relationship('BP_BaugebietsTeilFlaeche', secondary=BP_GemeinschaftsanlagenFlaecheEigentuemerAssoc,
                               info={'link': 'xlink-only'})

    Zmax = Column(Integer)

    def layer_fields(self):
        return {
            'zweckbestimmung': ', '.join(str(z.value) for z in self.zweckbestimmung) if self.zweckbestimmung else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
        }

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        red_outline = QgsSimpleLineSymbolLayer(QColor('red'))
        red_outline.setWidth(0.3)
        red_outline.setOffset(0.15)
        red_outline.setPenStyle(Qt.PenStyle.DashLine)
        red_outline.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        symbol.appendSymbolLayer(red_outline)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_NichtUeberbaubareGrundstuecksflaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Festlegung der nicht-ueberbaubaren Grundstuecksflaeche. """

    __tablename__ = 'bp_nicht_ueberbaubare_grundstuecksflaeche'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    nutzung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    nutzung = relationship('BP_NutzungNichtUeberbaubGrundstFlaeche',
                           back_populates='bp_nicht_ueberbaubare_grundstuecksflaechen',
                           foreign_keys=[nutzung_id], info={
                               'form-type': 'inline'
                           })

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))
        fill.setStrokeColor(QColor('#3d3d3d'))
        fill.setStrokeWidth(0.4)
        fill.setBrushStyle(Qt.BrushStyle.BDiagPattern)
        symbol.appendSymbolLayer(fill)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


@xp_version(versions=[XPlanVersion.SIX])
class BP_GebaeudeStellung(LineGeometry, BP_Objekt):
    """ Gestaltungs-Festsetzung der Firstrichtung bzw. Dach-Ausrichtung. """

    __tablename__ = 'bp_gebaeude_stellung'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    typ = Column(XPEnum(BP_GebaeudeStellungTypen), nullable=False)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.LineGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor('#1f1f1f'))
        line.setWidth(0.7)
        line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        symbol.appendSymbolLayer(line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


@xp_version(versions=[XPlanVersion.SIX])
class BP_WohngebaeudeFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Fläche für die Errichtung von Wohngebäuden in einem Bebauungsplan zur Wohnraumversorgung gemäß §9 Absatz 2d
        BauGB. """

    __tablename__ = 'bp_wohngebaeude_flaeche'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    dachgestaltung = relationship("BP_Dachgestaltung", back_populates="bp_wohngebaeude_flaeche", cascade="all, delete",
                                  passive_deletes=True)

    FR = Column(Angle)

    # XP_TextAbschnitt [0..*]
    abweichungText = relationship("XP_TextAbschnitt", back_populates="bp_baugebiet",
                                     cascade="all, delete", passive_deletes=True, uselist=False)

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

    # BP_TypWohngebaeudeFlaeche [1]
    typ = Column(XPEnum(BP_TypWohngebaeudeFlaeche), nullable=False)

    abweichungBauNVO = Column(Enum(XP_AbweichungBauNVOTypen))
    bauweise = Column(XPEnum(BP_Bauweise, include_default=True))
    vertikaleDifferenzierung = Column(Boolean)
    bebauungsArt = Column(XPEnum(BP_BebauungsArt, include_default=True))
    bebauungVordereGrenze = Column(Enum(BP_GrenzBebauung))
    bebauungRueckwaertigeGrenze = Column(Enum(BP_GrenzBebauung))
    bebauungSeitlicheGrenze = Column(Enum(BP_GrenzBebauung))
    refGebaeudequerschnitt = relationship("XP_ExterneReferenz", back_populates="bp_wohngebaeude_flaeche",
                                          cascade="all, delete", passive_deletes=True)
    zugunstenVon = Column(String)

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
