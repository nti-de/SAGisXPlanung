from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils,
                       QgsSimpleLineSymbolLayer, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize, Qt

from sqlalchemy import Column, ForeignKey, Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import xp_version, fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGewaesser
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry
from SAGisXPlanung.XPlan.types import GeometryType


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class FP_Gewaesser(PolygonGeometry, FP_Objekt):
    """ Darstellung einer Grünfläche nach § 5, Abs. 2, Nr. 5 BauGB """

    __tablename__ = 'fp_gewaesser'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_gewaesser',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(Enum(XP_ZweckbestimmungGewaesser))

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#71f8ff'))
        symbol.appendSymbolLayer(fill)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.5)
        line.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        line.setPenStyle(Qt.SolidLine)
        symbol.appendSymbolLayer(line)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(48, 48))
