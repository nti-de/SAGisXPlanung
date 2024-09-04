from typing import List

from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils,
                       QgsSimpleLineSymbolLayer, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize, Qt

from sqlalchemy import Column, ForeignKey, Enum, ARRAY
from sqlalchemy.orm import declared_attr, relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty, fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGruen, XP_Nutzungsform, XP_ZweckbestimmungLandwirtschaft, \
    XP_ZweckbestimmungWald, XP_EigentumsartWald, XP_WaldbetretungTyp
from SAGisXPlanung.core.mixins.mixins import FlaechenschlussObjekt, MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


class FP_Gruen(MixedGeometry, FP_Objekt):
    """ Darstellung einer Grünfläche nach § 5, Abs. 2, Nr. 5 BauGB """

    __tablename__ = 'fp_gruen'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_gruen',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(Enum(XP_ZweckbestimmungGruen), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("FP_KomplexeZweckbestGruen", back_populates="gruenflaeche",
                                       cascade="all, delete", passive_deletes=True)

    nutzungsform = Column(XPEnum(XP_Nutzungsform, include_default=True))

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

        fill = QgsSimpleFillSymbolLayer(QColor('#7ec400'))
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


class FP_Landwirtschaft(MixedGeometry, FP_Objekt):
    """ Darstellung von Flächen für Spiel- und Sportanlagen nach §5, Abs. 2, Nr. 2 BauGB """

    __tablename__ = 'fp_landwirtschaft'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_landwirtschaft',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(Enum(XP_ZweckbestimmungLandwirtschaft), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("FP_KomplexeZweckbestLandwirtschaft", back_populates="landwirtschaft",
                                       cascade="all, delete", passive_deletes=True)

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

        fill = QgsSimpleFillSymbolLayer(QColor('#fff394'))
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


class FP_WaldFlaeche(MixedGeometry, FlaechenschlussObjekt, FP_Objekt):
    """ Darstellung von Waldflächen nach §5, Abs. 2, Nr. 9b, """

    __tablename__ = 'fp_wald'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_wald',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(Enum(XP_ZweckbestimmungWald), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("FP_KomplexeZweckbestWald", back_populates="waldflaeche",
                                       cascade="all, delete", passive_deletes=True)

    eigentumsart = Column(XPEnum(XP_EigentumsartWald, include_default=True))
    betreten = Column(ARRAY(Enum(XP_WaldbetretungTyp)))

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

        fill = QgsSimpleFillSymbolLayer(QColor('#00cb4d'))
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
