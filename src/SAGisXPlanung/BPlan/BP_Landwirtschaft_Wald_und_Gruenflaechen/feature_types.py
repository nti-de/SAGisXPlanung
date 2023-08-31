import logging
from typing import List

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils, QgsSimpleFillSymbolLayer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize

from lxml import etree
from sqlalchemy import Integer, Column, ForeignKey, Float, Enum, String
from sqlalchemy.orm import relationship, declared_attr

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty
from SAGisXPlanung.XPlan.enums import XP_Nutzungsform, XP_ZweckbestimmungLandwirtschaft, XP_ZweckbestimmungWald, \
    XP_EigentumsartWald, XP_WaldbetretungTyp, XP_ZweckbestimmungGruen
from SAGisXPlanung.XPlan.mixins import PolygonGeometry, FlaechenschlussObjekt
from SAGisXPlanung.XPlan.types import Area, Length, Volume, GeometryType, XPEnum


logger = logging.getLogger(__name__)


class BP_GruenFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Festsetzungen von öffentlichen und privaten Grünflächen (§ 9, Abs. 1, Nr. 15 BauGB)."""

    __tablename__ = 'bp_gruenflaeche'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_gruenflaeche',
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
        return XPCol(Enum(XP_ZweckbestimmungGruen), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestGruen", back_populates="gruenflaeche",
                                       cascade="all, delete", passive_deletes=True)

    nutzungsform = Column(XPEnum(XP_Nutzungsform, include_default=True))
    zugunstenVon = Column(String)

    __icon_map__ = [
        ('Parkanlage', '"zweckbestimmung" LIKE \'10%\'', 'Parkanlage.svg'),
        ('Dauerkleingärten', '"zweckbestimmung" LIKE \'12%\'', 'Dauerkleingärten.svg'),
        ('Sportanlage', '"zweckbestimmung" LIKE \'14%\'', 'Sportplatz.svg'),
        ('Spielplatz', '"zweckbestimmung" LIKE \'16%\'', 'Spielplatz.svg'),
        ('Zeltplatz', '"zweckbestimmung" LIKE \'18%\'', 'Zeltplatz.svg'),
        ('Badeplatz', '"zweckbestimmung" LIKE \'20%\'', 'Badeplatz.svg'),
        ('Friedhof', '"zweckbestimmung" LIKE \'26%\'', 'Friedhof.svg'),
        ('Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ]

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
    def attributes(cls):
        return ['zweckbestimmung', 'skalierung', 'drehwinkel']

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#8fe898'))
        symbol.appendSymbolLayer(fill)

        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        renderer = RuleBasedSymbolRenderer(cls.__icon_map__, cls.symbol(), 'BP_Landwirtschaft_Wald_und_Gruenflaechen')
        return renderer

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_LandwirtschaftsFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Festsetzungen für die Landwirtschaft (§ 9, Abs. 1, Nr. 18a BauGB) """

    __tablename__ = 'bp_landwirtschaft'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_landwirtschaft',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(Enum(XP_ZweckbestimmungLandwirtschaft), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestLandwirtschaft", back_populates="landwirtschaft",
                                       cascade="all, delete", passive_deletes=True)

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

        fill = QgsSimpleFillSymbolLayer(QColor('#befe9d'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_WaldFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Festsetzung von Waldflächen (§ 9, Abs. 1, Nr. 18b BauGB). """

    __tablename__ = 'bp_wald'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_wald',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(Enum(XP_ZweckbestimmungWald), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestWald", back_populates="waldflaeche",
                                       cascade="all, delete", passive_deletes=True)

    eigentumsart = Column(Enum(XP_EigentumsartWald))
    betreten = Column(Enum(XP_WaldbetretungTyp))

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

        fill = QgsSimpleFillSymbolLayer(QColor('#17a8a5'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))
