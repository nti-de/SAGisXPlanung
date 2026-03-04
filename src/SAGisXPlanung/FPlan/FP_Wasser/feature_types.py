from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils,
                       QgsSimpleLineSymbolLayer, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize, Qt

from sqlalchemy import Column, ForeignKey, Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import xp_version, LayerPriorityType
from SAGisXPlanung.XPlan.renderer import fallback_renderer, icon_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGewaesser, XP_ZweckbestimmungWasserwirtschaft
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry, MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class FP_Gewaesser(PolygonGeometry, FP_Objekt):
    """ Darstellung von Wasserflächen nach §5, Abs. 2, Nr. 7 BauGB """

    __tablename__ = 'fp_gewaesser'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_gewaesser',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(Enum(XP_ZweckbestimmungGewaesser))

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#71f8ff'))
        symbol.appendSymbolLayer(fill)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.5)
        line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        line.setPenStyle(Qt.PenStyle.SolidLine)
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
class FP_Wasserwirtschaft(MixedGeometry, FP_Objekt):
    """ Die für die Wasserwirtschaft vorgesehenen Flächen sowie Flächen, die im Interesse des Hochwasserschutzes
        und der Regelung des Wasserabflusses freizuhalten sind (§5 Abs. 2 Nr. 7 BauGB). """

    __tablename__ = 'fp_wasserwirtschaft'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_wasserwirtschaft',
    }

    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(XPEnum(XP_ZweckbestimmungWasserwirtschaft, include_default=True))

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        colored_strip = QgsSimpleLineSymbolLayer(QColor('#71f8ff'))
        colored_strip.setWidth(3)
        colored_strip.setOffset(1.5)
        colored_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        colored_strip.setPenJoinStyle(Qt.PenJoinStyle.MiterJoin)
        symbol.appendSymbolLayer(colored_strip)

        border = QgsSimpleLineSymbolLayer(QColor('black'))
        border.setWidth(0.5)
        border.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        symbol.appendSymbolLayer(border)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('Wasserwirtschaft', QgsSymbol.defaultSymbol(geom_type),
                                 'BP_Wasser', geometry_type=geom_type,
                                 scale_factor=4)
        else:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
