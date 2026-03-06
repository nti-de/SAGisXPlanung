from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils,
                       QgsSimpleLineSymbolLayer, QgsUnitTypes, QgsGeometryGeneratorSymbolLayer, Qgis)
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

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))
        symbol.appendSymbolLayer(fill)

        blue_strip = QgsGeometryGeneratorSymbolLayer.create({})
        blue_strip.setSymbolType(Qgis.SymbolType.Fill)
        blue_strip.setColor(QColor('#45a1d0'))
        blue_strip.setStrokeColor(QColor('#45a1d0'))
        blue_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        blue_strip.setGeometryExpression("difference($geometry, buffer(wave($geometry, 20, 1.5), -4))")
        sub_symbol = blue_strip.subSymbol()
        fill_layer = sub_symbol.symbolLayer(0)
        fill_layer.setStrokeColor(QColor('#45a1d0'))
        fill_layer.setStrokeWidth(0)
        symbol.appendSymbolLayer(blue_strip)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('Wasserwirtschaft', QgsSymbol.defaultSymbol(geom_type),
                                 'BP_Wasser', geometry_type=geom_type, scale_factor=4)
        else:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
