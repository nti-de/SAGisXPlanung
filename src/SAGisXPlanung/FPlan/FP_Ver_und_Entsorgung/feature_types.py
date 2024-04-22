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
    XP_Traegerschaft, XP_ZweckbestimmungVerEntsorgung
from SAGisXPlanung.XPlan.mixins import PolygonGeometry, MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


class FP_VerEntsorgung(MixedGeometry, FP_Objekt):
    """ Flächen für Versorgungsanlagen, für die Abfallentsorgung und Abwasserbeseitigung sowie für Ablagerungen
    (§5, Abs. 2, Nr. 4 BauGB) """

    __tablename__ = 'fp_versorgung'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_versorgung',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(ARRAY(Enum(XP_ZweckbestimmungVerEntsorgung)), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("FP_KomplexeZweckbestVerEntsorgung", back_populates="versorgung",
                                       cascade="all, delete", passive_deletes=True)

    textlicheErgaenzung = XPCol(String, version=XPlanVersion.FIVE_THREE)
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

        fill = QgsSimpleFillSymbolLayer(QColor('#f7ff5a'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')