from typing import List

from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSymbolLayerUtils,
                       QgsSimpleLineSymbolLayer, QgsMarkerLineSymbolLayer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize

from sqlalchemy import Column, ForeignKey, String, Integer, Float, Enum
from sqlalchemy.orm import relationship, declared_attr

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.BPlan.BP_Bebauung.enums import BP_BebauungsArt, BP_Bauweise
from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty
from SAGisXPlanung.XPlan.renderer import fallback_renderer, icon_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungSpielSportanlage, XP_ZweckbestimmungGemeinbedarf, \
    XP_Traegerschaft
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry, FlaechenschlussObjekt
from SAGisXPlanung.XPlan.types import Area, Volume, Length, Angle, GeometryType, XPEnum


class BP_GemeinbedarfsFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Einrichtungen und Anlagen zur Versorgung mit Gütern und Dienstleistungen des öffentlichen und privaten
        Bereichs, hier Flächen für den Gemeindebedarf (§9, Abs. 1, Nr.5 und Abs. 6 BauGB)."""

    __tablename__ = 'bp_gemeinbedarf'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_gemeinbedarf',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    dachgestaltung = relationship("BP_Dachgestaltung", back_populates="gemeinbedarf", cascade="all, delete",
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

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(Enum(XP_ZweckbestimmungGemeinbedarf), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestGemeinbedarf", back_populates="gemeinbedarf",
                                       cascade="all, delete", passive_deletes=True)

    bauweise = Column(XPEnum(BP_Bauweise, include_default=True))
    bebauungsArt = Column(XPEnum(BP_BebauungsArt, include_default=True))
    traeger = XPCol(XPEnum(XP_Traegerschaft, include_default=True), version=XPlanVersion.SIX)
    zugunstenVon = Column(String)

    def layer_fields(self):
        return {
            'zweckbestimmung': self.zweckbestimmung.value if self.zweckbestimmung else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
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
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#febae1'))
        symbol.appendSymbolLayer(fill)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        renderer = icon_renderer('Gemeinbedarf', cls.symbol(),
                                 'BP_Gemeinbedarf_Spiel_und_Sportanlagen', geometry_type=geom_type)
        return renderer

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_SpielSportanlagenFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Einrichtungen und Anlagen zur Versorgung mit Gütern und Dienstleistungen des öffentlichen und privaten
        Bereichs, hier Flächen für Sport- und Spielanlagen (§9, Abs. 1, Nr. 5 und Abs. 6 BauGB). """

    __tablename__ = 'bp_spiel_sportanlage'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_spiel_sportanlage',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

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

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(Enum(XP_ZweckbestimmungSpielSportanlage), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestSpielSportanlage", back_populates="spiel_sportanlage",
                                       cascade="all, delete", passive_deletes=True)
    zugunstenVon = Column(String)

    __icon_map__ = [
        ('Sportanlage', '"zweckbestimmung" LIKE \'Sportanlage\'', 'Anlage_Sportanlage.svg'),
        ('Spielanlage', '"zweckbestimmung" LIKE \'Spielanlage\'', 'Anlage_Spielanlage.svg'),
        ('Gemischt/Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ]

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
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        border = QgsSimpleLineSymbolLayer()
        border.setColor(QColor(0, 0, 0))
        border.setWidth(0.3)

        dotted_line_inner = QgsMarkerLineSymbolLayer()
        dotted_line_inner.setColor(QColor(0, 0, 0))
        dotted_line_inner.setWidth(0.5)
        dotted_line_inner.setOffset(1.5)

        dotted_line_outer = dotted_line_inner.clone()
        dotted_line_outer.setOffset(0.8)

        symbol.appendSymbolLayer(border)
        symbol.appendSymbolLayer(dotted_line_inner)
        symbol.appendSymbolLayer(dotted_line_outer)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        renderer = RuleBasedSymbolRenderer(cls.__icon_map__, cls.symbol(), 'BP_Gemeinbedarf_Spiel_und_Sportanlagen')
        return renderer

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))
