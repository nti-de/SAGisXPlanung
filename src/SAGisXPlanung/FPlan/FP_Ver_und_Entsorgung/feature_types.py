from typing import List

from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer)
from qgis.PyQt.QtGui import QColor

from sqlalchemy import Column, ForeignKey, Enum, ARRAY, String
from sqlalchemy.orm import declared_attr, relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty
from SAGisXPlanung.XPlan.renderer import fallback_renderer, icon_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungVerEntsorgung
from SAGisXPlanung.core.mixins.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType


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

    def layer_fields(self):
        return {
            'zweckbestimmung': ', '.join(str(z.value) for z in self.zweckbestimmung) if self.zweckbestimmung else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
        }

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
        if geom_type == QgsWkbTypes.PointGeometry:
            return icon_renderer('Versorgung', QgsSymbol.defaultSymbol(geom_type),
                                 'BP_Ver_und_Entsorgung', geometry_type=geom_type,
                                 symbol_size=30)
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')
