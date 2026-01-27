from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils,
                       QgsSimpleLineSymbolLayer, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize, Qt

from sqlalchemy import Column, ForeignKey, Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.FPlan.FP_Verkehr.enums import FP_ZweckbestimmungStrassenverkehr
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_Nutzungsform
from SAGisXPlanung.core.mixins.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class FP_Strassenverkehr(MixedGeometry, FP_Objekt):
    """ Darstellung einer Grünfläche nach § 5, Abs. 2, Nr. 5 BauGB """

    __tablename__ = 'fp_strassenverkehr'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_strassenverkehr',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(Enum(FP_ZweckbestimmungStrassenverkehr))
    nutzungsform = Column(XPEnum(XP_Nutzungsform, include_default=True))

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#fbdd19'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            point_symbol = QgsSymbol.defaultSymbol(geom_type)
            point_symbol.setColor(QColor('#fbdd19'))
            return QgsSingleSymbolRenderer(point_symbol)
        elif geom_type is not None:
            line_symbol = QgsSymbol.defaultSymbol(geom_type)
            line_symbol.setColor(QColor('#fbdd19'))
            return QgsSingleSymbolRenderer(line_symbol)
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(48, 48))
