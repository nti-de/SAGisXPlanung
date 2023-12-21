from typing import List

from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils,
                       QgsSimpleLineSymbolLayer, QgsMarkerLineSymbolLayer, QgsCentroidFillSymbolLayer,
                       QgsSvgMarkerSymbolLayer, QgsMarkerSymbol, QgsUnitTypes, QgsMapUnitScale, QgsRuleBasedRenderer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize, Qt

from sqlalchemy import Column, ForeignKey, Enum, ARRAY, String
from sqlalchemy.orm import declared_attr, relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty, fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGemeinbedarf, XP_ZweckbestimmungSpielSportanlage, \
    XP_Traegerschaft
from SAGisXPlanung.XPlan.mixins import PolygonGeometry, MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


class FP_Gemeinbedarf(MixedGeometry, FP_Objekt):
    """ Darstellung von Flächen für den Gemeinbedarf nach § 5, Abs. 2, Nr. 2 BauGB """

    __tablename__ = 'fp_gemeinbedarf'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_gemeinbedarf',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(ARRAY(Enum(XP_ZweckbestimmungGemeinbedarf)))

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(ARRAY(Enum(XP_ZweckbestimmungGemeinbedarf)), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("FP_KomplexeZweckbestGemeinbedarf", back_populates="gemeinbedarf",
                                       cascade="all, delete", passive_deletes=True)

    traeger = Column(XPEnum(XP_Traegerschaft, include_default=True))
    zugunstenVon = Column(String)

    @classmethod
    def import_zweckbestimmung_attr(cls, version):
        if version == XPlanVersion.FIVE_THREE:
            return 'zweckbestimmung'
        else:
            return 'rel_zweckbestimmung'

    @classmethod
    def xp_relationship_properties(cls) -> List[XPRelationshipProperty]:
        return [
            XPRelationshipProperty(rel_name='rel_zweckbestimmung', xplan_attribute='zweckbestimmung',
                                   allowed_version=XPlanVersion.SIX)
        ]

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#febae1'))
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
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(48, 48))


class FP_SpielSportanlage(MixedGeometry, FP_Objekt):
    """ Darstellung von Flächen für Spiel- und Sportanlagen nach §5, Abs. 2, Nr. 2 BauGB """

    __tablename__ = 'fp_spiel_sportanlage'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_spiel_sportanlage',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(Enum(XP_ZweckbestimmungSpielSportanlage))

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(Enum(XP_ZweckbestimmungSpielSportanlage), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("FP_KomplexeZweckbestSpielSportanlage", back_populates="sportanlage",
                                       cascade="all, delete", passive_deletes=True)

    zugunstenVon = Column(String)

    @classmethod
    def import_zweckbestimmung_attr(cls, version):
        if version == XPlanVersion.FIVE_THREE:
            return 'zweckbestimmung'
        else:
            return 'rel_zweckbestimmung'

    @classmethod
    def xp_relationship_properties(cls) -> List[XPRelationshipProperty]:
        return [
            XPRelationshipProperty(rel_name='rel_zweckbestimmung', xplan_attribute='zweckbestimmung',
                                   allowed_version=XPlanVersion.SIX)
        ]

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.5)
        line.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        line.setPenStyle(Qt.SolidLine)

        dotted_line_inner = QgsMarkerLineSymbolLayer()
        dotted_line_inner.setColor(QColor(0, 0, 0))
        dotted_line_inner.setWidth(0.8)
        dotted_line_inner.setOffset(2)
        dotted_line_inner.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        dotted_line_outer = dotted_line_inner.clone()
        dotted_line_outer.setOffset(1)
        dotted_line_outer.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        symbol.appendSymbolLayer(fill)
        symbol.appendSymbolLayer(line)
        symbol.appendSymbolLayer(dotted_line_inner)
        symbol.appendSymbolLayer(dotted_line_outer)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(48, 48))
