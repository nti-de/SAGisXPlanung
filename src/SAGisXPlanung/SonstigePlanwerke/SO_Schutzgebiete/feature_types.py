from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsSymbol, QgsSimpleFillSymbolLayer, QgsSimpleLineSymbolLayer, QgsUnitTypes, QgsWkbTypes,
                       QgsSingleSymbolRenderer, QgsSymbolLayerUtils, QgsMarkerLineSymbolLayer, QgsMarkerSymbol,
                       QgsSimpleMarkerSymbolLayer, QgsSimpleMarkerSymbolLayerBase)

from sqlalchemy import Column, ForeignKey, Enum, String, Boolean

from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Objekt
from SAGisXPlanung.SonstigePlanwerke.SO_Schutzgebiete import SO_KlassifizSchutzgebietWasserrecht, SO_SchutzzonenWasserrecht
from SAGisXPlanung.XPlan.core import fallback_renderer
from SAGisXPlanung.XPlan.mixins import PolygonGeometry
from SAGisXPlanung.XPlan.types import GeometryType


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