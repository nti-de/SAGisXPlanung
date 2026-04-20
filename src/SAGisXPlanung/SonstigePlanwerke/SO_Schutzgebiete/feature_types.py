from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsSymbol, QgsSimpleLineSymbolLayer, QgsUnitTypes, QgsWkbTypes,
                       QgsSingleSymbolRenderer, QgsSymbolLayerUtils)

from sqlalchemy import Column, ForeignKey, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Objekt
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete import SO_KlassifizSchutzgebietWasserrecht, SO_SchutzzonenWasserrecht
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete.codelists import SO_DetailKlassifizSchutzgebietSonstRecht
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete.enums import SO_SchutzzonenNaturschutzrecht
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.enums import XP_KlassifizSchutzgebietNaturschutzrecht
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete.enums import SO_KlassifizSchutzgebietSonstRecht
from SAGisXPlanung.XPlan.renderer import fallback_renderer, icon_renderer
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry, MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class SO_SchutzgebietNaturschutzrecht(MixedGeometry, SO_Objekt):
    """ Schutzgebiet nach Naturschutzrecht """

    __tablename__ = 'so_naturschutz'
    __mapper_args__ = {
        'polymorphic_identity': 'so_naturschutz',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(XP_KlassifizSchutzgebietNaturschutzrecht, include_default=True))
    zone = Column(XPEnum(SO_SchutzzonenNaturschutzrecht, include_default=True))
    name = Column(String)
    nummer = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        border = QgsSimpleLineSymbolLayer(QColor('black'))
        border.setWidth(0.5)
        border.setOffset(0.25)
        border.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        symbol.appendSymbolLayer(border)

        outline_strip = QgsSimpleLineSymbolLayer(QColor('#0df919'))
        outline_strip.setWidth(8)
        outline_strip.setOffset(4.25)
        outline_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        outline_strip.setPenJoinStyle(Qt.PenJoinStyle.MiterJoin)
        symbol.appendSymbolLayer(outline_strip)
        symbol.setOpacity(0.75)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('Naturschutz', QgsSymbol.defaultSymbol(geom_type),
                                 'BP_Naturschutz_Landschaftsbild_Naturhaushalt', geometry_type=geom_type,
                                 scale_factor=4)
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')


class SO_SchutzgebietWasserrecht(PolygonGeometry, SO_Objekt):
    """ Schutzgebiet nach WasserSchutzGesetz (WSG) bzw. HeilQuellenSchutzGesetz (HQSG). """

    __tablename__ = 'so_wasserschutz'
    __mapper_args__ = {
        'polymorphic_identity': 'so_wasserschutz',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizSchutzgebietWasserrecht, include_default=True))
    zone = Column(XPEnum(SO_SchutzzonenWasserrecht, include_default=True))
    name = Column(String)
    nummer = Column(String)

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        symbol.setOpacity(0.7)

        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer(color=QColor('#00ffff'), width=25)
        line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        line.setDrawInsidePolygon(True)
        symbol.appendSymbolLayer(line)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(48, 48))


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class SO_SchutzgebietSonstigesRecht(MixedGeometry, SO_Objekt):
    """ Schutzgebiet nach sonstigem Recht (nur XPlanung 5.3). """

    __tablename__ = 'so_schutzgebiet_sonstiges_recht'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizSchutzgebietSonstRecht, include_default=True))
    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizSchutzgebietSonstRecht",
                                          back_populates="so_schutzgebiet_sonstiges_recht",
                                          foreign_keys=[detailArtDerFestlegung_id], info={
                                              'form-type': 'inline'
                                          })
    name = Column(String)
    nummer = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
