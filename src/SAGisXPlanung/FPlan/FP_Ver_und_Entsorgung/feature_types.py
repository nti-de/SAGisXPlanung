from qgis.core import (QgsSimpleFillSymbolLayer, QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer,
                       QgsSimpleLineSymbolLayer, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

from sqlalchemy import Column, ForeignKey, Enum, ARRAY, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.XPlan.renderer import fallback_renderer, icon_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungVerEntsorgung
from SAGisXPlanung.core.mixins.mixins import MixedGeometry, PolygonGeometry, UeberlagerungsObjekt
from SAGisXPlanung.XPlan.types import GeometryType


class FP_VerEntsorgung(MixedGeometry, FP_Objekt):
    """ Flächen für Versorgungsanlagen, für die Abfallentsorgung und Abwasserbeseitigung sowie für Ablagerungen
    (§5, Abs. 2, Nr. 4 BauGB) """

    __tablename__ = 'fp_versorgung'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_versorgung',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(ARRAY(Enum(XP_ZweckbestimmungVerEntsorgung)), info={'xplan_version': XPlanVersion.FIVE_THREE})

    rel_zweckbestimmung = relationship("FP_KomplexeZweckbestVerEntsorgung", back_populates="versorgung",
                                       cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'zweckbestimmung'
                                       })

    textlicheErgaenzung = Column(String, info={'xplan_version': XPlanVersion.FIVE_THREE})
    zugunstenVon = Column(String)

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

        fill = QgsSimpleFillSymbolLayer(QColor('#f7ff5a'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('Versorgung', QgsSymbol.defaultSymbol(geom_type),
                                 'BP_Ver_und_Entsorgung', geometry_type=geom_type,
                                 scale_factor=5)
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')


class FP_ZentralerVersorgungsbereich(PolygonGeometry, UeberlagerungsObjekt, FP_Objekt):
    """ Darstellung zentraler Versorgungsbereiche nach § 5 Abs. 2 Nr. 2d BauGB. """

    __tablename__ = 'fp_zentraler_versorgungsbereich'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }
    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    auspraegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    auspraegung = relationship("FP_ZentralerVersorgungsbereichAuspraegung",
                               back_populates="fp_zentraler_versorgungsbereich",
                               foreign_keys=[auspraegung_id], info={
                                   'form-type': 'inline'
                               })

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        colored_strip = QgsSimpleLineSymbolLayer(QColor('#001be4'))
        colored_strip.setWidth(2.0)
        colored_strip.setOffset(1.0)
        colored_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        colored_strip.setPenJoinStyle(Qt.PenJoinStyle.MiterJoin)
        symbol.appendSymbolLayer(colored_strip)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            raise ValueError('Renderer of FP_ZentralerVersorgungsbereich should only be called with polygon geometry')
