import logging
from typing import List

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils, QgsSimpleFillSymbolLayer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize

from sqlalchemy import Integer, Column, ForeignKey, Float, Enum, String
from sqlalchemy.orm import relationship, declared_attr

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.XPlan.renderer import fallback_renderer, icon_renderer
from SAGisXPlanung.XPlan.enums import XP_Nutzungsform, XP_ZweckbestimmungLandwirtschaft, XP_ZweckbestimmungWald, \
    XP_EigentumsartWald, XP_WaldbetretungTyp, XP_ZweckbestimmungGruen
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry, FlaechenschlussObjekt
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

    zweckbestimmung = Column(Enum(XP_ZweckbestimmungGruen), info={'xplan_version': XPlanVersion.FIVE_THREE})

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestGruen", back_populates="gruenflaeche",
                                       cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'zweckbestimmung'
                                       })

    nutzungsform = Column(XPEnum(XP_Nutzungsform, include_default=True))
    zugunstenVon = Column(String)

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#8fe898'))
        symbol.appendSymbolLayer(fill)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return icon_renderer('Gruen', cls.symbol(),
                             'BP_Landwirtschaft_Wald_und_Gruenflaechen', geometry_type=geom_type)

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_KleintierhaltungFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Flaeche fuer Anlagen der Kleintierhaltung. """

    __tablename__ = 'bp_kleintierhaltung'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type or QgsWkbTypes.GeometryType.PolygonGeometry))


class BP_LandwirtschaftsFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Festsetzungen für die Landwirtschaft (§ 9, Abs. 1, Nr. 18a BauGB) """

    __tablename__ = 'bp_landwirtschaft'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_landwirtschaft',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(Enum(XP_ZweckbestimmungLandwirtschaft), info={'xplan_version': XPlanVersion.FIVE_THREE})

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestLandwirtschaft", back_populates="landwirtschaft",
                                       cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'zweckbestimmung'
                                       })

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#befe9d'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
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

    zweckbestimmung = Column(Enum(XP_ZweckbestimmungWald), info={'xplan_version': XPlanVersion.FIVE_THREE})

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestWald", back_populates="waldflaeche",
                                       cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'zweckbestimmung'
                                       })

    eigentumsart = Column(Enum(XP_EigentumsartWald))
    betreten = Column(Enum(XP_WaldbetretungTyp))

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#17a8a5'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))
