from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from qgis.core import (QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbol, QgsPointPatternFillSymbolLayer, QgsMarkerSymbol,
                       QgsSimpleMarkerSymbolLayer, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor

from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Objekt
from SAGisXPlanung.SonstigePlanwerke.SO_Sonstiges.enums import SO_KlassifizGelaendemorphologie
from SAGisXPlanung.XPlan.enums import XP_GrenzeTypen
from SAGisXPlanung.XPlan.renderer import fallback_renderer, generic_objects_renderer
from SAGisXPlanung.core.mixins.mixins import MixedGeometry, LineGeometry
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
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        marker_pattern = QgsPointPatternFillSymbolLayer()
        marker_pattern.setDistanceX(5.0)
        marker_pattern.setDistanceY(5.0)
        marker_pattern_symbol: QgsMarkerSymbol = QgsMarkerSymbol.createSimple({})
        marker_pattern_symbol.deleteSymbolLayer(0)
        marker_pattern_layer = QgsSimpleMarkerSymbolLayer()
        marker_pattern_layer.setColor(QColor('black'))
        marker_pattern_layer.setSize(0.5)
        marker_pattern_layer.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        marker_pattern_symbol.appendSymbolLayer(marker_pattern_layer)
        marker_pattern.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        marker_pattern.setSubSymbol(marker_pattern_symbol)
        symbol.appendSymbolLayer(marker_pattern)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            return generic_objects_renderer(geom_type)


class SO_Grenze(LineGeometry, SO_Objekt):
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
