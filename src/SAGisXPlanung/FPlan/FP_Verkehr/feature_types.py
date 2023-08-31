from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils,
                       QgsSimpleLineSymbolLayer, QgsMarkerLineSymbolLayer, QgsCentroidFillSymbolLayer,
                       QgsSvgMarkerSymbolLayer, QgsMarkerSymbol, QgsUnitTypes, QgsMapUnitScale, QgsRuleBasedRenderer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize, Qt

from sqlalchemy import Column, ForeignKey, Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.FPlan.FP_Verkehr.enums import FP_ZweckbestimmungStrassenverkehr
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.enums import XP_Nutzungsform
from SAGisXPlanung.XPlan.mixins import PolygonGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class FP_Strassenverkehr(PolygonGeometry, FP_Objekt):
    """ Darstellung einer Grünfläche nach § 5, Abs. 2, Nr. 5 BauGB """

    __tablename__ = 'fp_strassenverkehr'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_strassenverkehr',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(Enum(FP_ZweckbestimmungStrassenverkehr))
    nutzungsform = Column(XPEnum(XP_Nutzungsform, include_default=True))

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffb300'))
        symbol.appendSymbolLayer(fill)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.5)
        line.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        line.setPenStyle(Qt.SolidLine)
        symbol.appendSymbolLayer(line)

        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(48, 48))
