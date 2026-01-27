import logging

from qgis.PyQt.QtGui import QColor
from qgis._core import QgsFillSymbol, QgsLinePatternFillSymbolLayer, QgsUnitTypes, QgsSimpleLineSymbolLayer
from sqlalchemy import Column, ForeignKey, ARRAY, Enum, Boolean, String

from qgis.core import QgsWkbTypes, QgsSymbol, QgsSingleSymbolRenderer

from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.FPlan.FP_Sonstiges.enums import FP_ZweckbestimmungPrivilegiertesVorhaben
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.XPlan.renderer import fallback_renderer, generic_objects_renderer, icon_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungKennzeichnung
from SAGisXPlanung.core.mixins.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum

logger = logging.getLogger(__name__)


class FP_GenerischesObjekt(MixedGeometry, FP_Objekt):
    """ Klasse zur Modellierung aller Inhalte des Bebauungsplans,die durch keine andere spezifische XPlanung Klasse
        repräsentiert werden können """

    __tablename__ = 'fp_generisches_objekt'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_generisches_objekt',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return generic_objects_renderer(geom_type)


class FP_Kennzeichnung(MixedGeometry, FP_Objekt):
    """ Kennzeichnung gemäß §5 Abs. 3 BauGB """

    __tablename__ = 'fp_kennzeichnung'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_kennzeichnung',
    }
    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(ARRAY(Enum(XP_ZweckbestimmungKennzeichnung)))
    istVerdachtsflaeche = Column(Boolean)
    nummer = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('Kennzeichnung', QgsSymbol.defaultSymbol(geom_type),
                                 'Sonstiges', geometry_type=geom_type,
                                 scale_factor=5)
        return generic_objects_renderer(geom_type)


class FP_PrivilegiertesVorhaben(MixedGeometry, FP_Objekt):
    """ Standorte für privilegierte Außenbereichsvorhaben und für sonstige Anlagen in Außenbereichen gem. § 35 Abs. 1
        und 2 BauGB """

    __tablename__ = 'fp_privilegiertes_vorhaben'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(XPEnum(FP_ZweckbestimmungPrivilegiertesVorhaben, include_default=True))
    vorhaben = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        line_pattern = QgsLinePatternFillSymbolLayer()
        line_pattern.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        line_pattern.setLineAngle(45)
        line_pattern.setDistance(30)
        line_pattern.setLineWidth(1)
        line_pattern.setColor(QColor(0, 0, 0))

        symbol = QgsFillSymbol()
        symbol.changeSymbolLayer(0, line_pattern)

        line = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        line.setWidth(0.5)
        line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        symbol.appendSymbolLayer(line)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')