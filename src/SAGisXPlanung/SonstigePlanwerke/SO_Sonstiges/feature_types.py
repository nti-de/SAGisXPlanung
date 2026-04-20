from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from qgis.core import QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbol

from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Objekt
from SAGisXPlanung.SonstigePlanwerke.SO_Sonstiges.enums import SO_KlassifizGelaendemorphologie
from SAGisXPlanung.XPlan.enums import XP_GrenzeTypen
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.core.mixins.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


class SO_Gelaendemorphologie(MixedGeometry, SO_Objekt):
    """ Das Landschaftsbild praegende Gelaendestruktur. """

    __tablename__ = 'so_gelaendemorphologie'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizGelaendemorphologie, include_default=True))

    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizGelaendemorphologie",
                                          back_populates="so_gelaendemorphologie",
                                          foreign_keys=[detailArtDerFestlegung_id], info={
                                              'form-type': 'inline'
                                          })

    name = Column(String)
    nummer = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type or QgsWkbTypes.GeometryType.PolygonGeometry))


class SO_Grenze(MixedGeometry, SO_Objekt):
    """ Grenze einer Verwaltungseinheit oder sonstige Grenze in raumbezogenen Plaenen. """

    __tablename__ = 'so_grenze'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    typ = Column(XPEnum(XP_GrenzeTypen, include_default=True))

    sonstTyp_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    sonstTyp = relationship("SO_SonstGrenzeTypen", back_populates="so_grenze",
                            foreign_keys=[sonstTyp_id], info={
                                'form-type': 'inline'
                            })

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type or QgsWkbTypes.GeometryType.LineGeometry))
