from typing import List

from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils,
                       QgsSimpleLineSymbolLayer, QgsMarkerLineSymbolLayer, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize, Qt

from sqlalchemy import Column, ForeignKey, Enum, ARRAY, String
from sqlalchemy.orm import declared_attr, relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Gemeinbedarf.codelists import FP_DetailZweckbestGemeinbedarfCodelistAssoc
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.renderer import fallback_renderer, icon_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGemeinbedarf, XP_ZweckbestimmungSpielSportanlage, \
    XP_Traegerschaft
from SAGisXPlanung.core.mixins.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


class FP_Gemeinbedarf(MixedGeometry, FP_Objekt):
    """ Darstellung von Flächen für den Gemeinbedarf nach § 5, Abs. 2, Nr. 2 BauGB """

    __tablename__ = 'fp_gemeinbedarf'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_gemeinbedarf',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(ARRAY(Enum(XP_ZweckbestimmungGemeinbedarf)), info={'xplan_version': XPlanVersion.FIVE_THREE})

    detaillierteZweckbestimmung = relationship('FP_DetailZweckbestGemeinbedarf', back_populates='codelist_user',
                                               secondary=FP_DetailZweckbestGemeinbedarfCodelistAssoc,
                                               info={
                                                   'xplan_version': XPlanVersion.FIVE_THREE,
                                                   'form-type': 'inline'
                                               })

    rel_zweckbestimmung = relationship("FP_KomplexeZweckbestGemeinbedarf", back_populates="gemeinbedarf",
                                       cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'zweckbestimmung'
                                       })

    traeger = Column(XPEnum(XP_Traegerschaft, include_default=True), info={'xplan_version': XPlanVersion.SIX})
    zugunstenVon = Column(String, info={'xplan_version': XPlanVersion.SIX})

    def layer_fields(self):
        return {
            'zweckbestimmung': ', '.join(str(z.value) for z in self.zweckbestimmung) if self.zweckbestimmung else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
        }

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#febae1'))
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
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('Gemeinbedarf', QgsSymbol.defaultSymbol(geom_type),
                                 'BP_Gemeinbedarf_Spiel_und_Sportanlagen', geometry_type=geom_type,
                                 symbol_size=30)
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

    zweckbestimmung = Column(Enum(XP_ZweckbestimmungSpielSportanlage), info={'xplan_version': XPlanVersion.FIVE_THREE})

    rel_zweckbestimmung = relationship("FP_KomplexeZweckbestSpielSportanlage", back_populates="sportanlage",
                                       cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'zweckbestimmung'
                                       })

    zugunstenVon = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.5)
        line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        line.setPenStyle(Qt.PenStyle.SolidLine)

        dotted_line_inner = QgsMarkerLineSymbolLayer()
        dotted_line_inner.setColor(QColor(0, 0, 0))
        dotted_line_inner.setWidth(0.8)
        dotted_line_inner.setOffset(2)
        dotted_line_inner.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        dotted_line_outer = dotted_line_inner.clone()
        dotted_line_outer.setOffset(1)
        dotted_line_outer.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        symbol.appendSymbolLayer(fill)
        symbol.appendSymbolLayer(line)
        symbol.appendSymbolLayer(dotted_line_inner)
        symbol.appendSymbolLayer(dotted_line_outer)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('SpielSportanlage', QgsSymbol.defaultSymbol(geom_type),
                                 'BP_Gemeinbedarf_Spiel_und_Sportanlagen', geometry_type=geom_type,
                                 scale_factor=5)
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(48, 48))
