from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsSymbol, QgsSimpleLineSymbolLayer, QgsUnitTypes, QgsWkbTypes,
                       QgsSingleSymbolRenderer, QgsSymbolLayerUtils)

from sqlalchemy import Column, ForeignKey, Enum, String

from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Objekt
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete import SO_KlassifizSchutzgebietWasserrecht, SO_SchutzzonenWasserrecht
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete.enums import SO_SchutzzonenNaturschutzrecht
from SAGisXPlanung.XPlan.enums import XP_KlassifizSchutzgebietNaturschutzrecht
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry, MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


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
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        border = QgsSimpleLineSymbolLayer(QColor('black'))
        border.setWidth(0.5)
        border.setOffset(0.25)
        border.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        symbol.appendSymbolLayer(border)

        outline_strip = QgsSimpleLineSymbolLayer(QColor('#0df919'))
        outline_strip.setWidth(8)
        outline_strip.setOffset(4.25)
        outline_strip.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        outline_strip.setPenJoinStyle(Qt.MiterJoin)
        symbol.appendSymbolLayer(outline_strip)
        symbol.setOpacity(0.75)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
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

    artDerFestlegung = Column(Enum(SO_KlassifizSchutzgebietWasserrecht))
    zone = Column(Enum(SO_SchutzzonenWasserrecht))
    name = Column(String)
    nummer = Column(String)

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        symbol.setOpacity(0.7)

        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer(color=QColor('#00ffff'), width=25)
        line.setOutputUnit(QgsUnitTypes.RenderMapUnits)
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