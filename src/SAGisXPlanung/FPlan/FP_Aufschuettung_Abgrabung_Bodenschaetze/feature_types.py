from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsUnitTypes, Qgis, QgsMarkerSymbolLayer,
                       QgsSimpleMarkerSymbolLayerBase, QgsMarkerLineSymbolLayer, QgsMarkerSymbol,
                       QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer, QgsSimpleFillSymbolLayer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

from sqlalchemy import Column, ForeignKey, String

from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import fallback_renderer
from SAGisXPlanung.core.mixins.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType


class FP_Abgrabung(MixedGeometry, FP_Objekt):
    """ Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§5, Abs. 2, Nr. 8 BauGB). Hier:
        Flächen für Abgrabungen und die Gewinnung von Bodenschätzen"""

    __tablename__ = 'fp_abgrabung'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_abgrabung',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    abbaugut = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.5)
        border.setOffset(0.25)
        border.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        border.setPenJoinStyle(Qt.MiterJoin)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.Triangle
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.Triangle

        triangle_symbol = QgsSimpleMarkerSymbolLayer(
            shape=shape,
            color=QColor('#000000'),
            strokeColor=QColor('#000000'),
            size=20
        )
        triangle_symbol.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)

        marker_line = QgsMarkerLineSymbolLayer(interval=30)
        marker_line.setAverageAngleLength(0)
        marker_line.setOffset(10)
        marker_line.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(triangle_symbol)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(fill)
        symbol.appendSymbolLayer(border)
        symbol.appendSymbolLayer(marker_line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


class FP_Aufschuettung(MixedGeometry, FP_Objekt):
    """ Flächen für Aufschüttungen, Abgrabungen oder für die Gewinnung von Bodenschätzen (§5, Abs. 2, Nr. 8 BauGB).
        Hier: Flächen für Aufschüttungen"""

    __tablename__ = 'fp_aufschuettung'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_aufschuettung',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    aufschuettungsmaterial = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.5)
        border.setOffset(0.25)
        border.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        border.setPenJoinStyle(Qt.MiterJoin)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.Triangle
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.Triangle

        triangle_symbol = QgsSimpleMarkerSymbolLayer(
            shape=shape,
            color=QColor('#000000'),
            strokeColor=QColor('#000000'),
            size=20
        )
        triangle_symbol.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
        triangle_symbol.setAngle(180)
        triangle_symbol.setVerticalAnchorPoint(QgsMarkerSymbolLayer.Bottom)

        marker_line = QgsMarkerLineSymbolLayer(interval=30)
        marker_line.setAverageAngleLength(0)
        marker_line.setOffset(20)
        marker_line.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(triangle_symbol)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(fill)
        symbol.appendSymbolLayer(border)
        symbol.appendSymbolLayer(marker_line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
