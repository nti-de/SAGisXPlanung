from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsSymbol, QgsSingleSymbolRenderer, QgsWkbTypes, QgsSimpleLineSymbolLayer, QgsUnitTypes

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Objekt
from SAGisXPlanung.LPlan.LP_SchutzgebieteBestandteileNaturschutzrecht.enums import LP_KlassifizierungNaturschutzrecht, \
    LP_RechtsstandSchutzGeb, LP_GesGeschBiotopTyp, LP_SchutzzonenNaturschutzrecht
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum
from SAGisXPlanung.core.mixins.mixins import MixedGeometry


@xp_version(versions=[XPlanVersion.SIX])
class LP_SchutzBestimmterTeileVonNaturUndLandschaft(MixedGeometry, LP_Objekt):
    """ Schutzgebietskategorien gemäß Kapitel 4 BNatSchG „Schutz bestimmter Teile von Natur und Landschaft“. """

    __tablename__ = 'lp_schutz_bestimmter_teile_von_natur_und_landschaft'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("lp_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(LP_KlassifizierungNaturschutzrecht), nullable=False)
    artDerFestlegungText = Column(String)

    rechtsstandSchG = Column(XPEnum(LP_RechtsstandSchutzGeb), nullable=False)
    rechtsstandSchGText = Column(String)

    name = Column(String)
    nummer = Column(String)

    gesetzlGeschBiotop = Column(XPEnum(LP_GesGeschBiotopTyp, include_default=True))
    gesetzlGeschBiotopText = Column(String)

    # [0..1]
    detailGesetzlGeschBiotopLR_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailGesetzlGeschBiotopLR = relationship("LP_DetailGesetzlGeschBiotopLR", back_populates=__tablename__,
                                              foreign_keys=[detailGesetzlGeschBiotopLR_id], info={
                                                     'form-type': 'inline'
                                                 })

    schutzzone = Column(XPEnum(LP_SchutzzonenNaturschutzrecht, include_default=True))
    schutzzonenText = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        border = QgsSimpleLineSymbolLayer(QColor('black'))
        border.setWidth(0.5)
        border.setOffset(0.25)
        border.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        symbol.appendSymbolLayer(border)

        outline_strip = QgsSimpleLineSymbolLayer(QColor('#0df919'))
        outline_strip.setWidth(8)
        outline_strip.setOffset(4.25)
        outline_strip.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        outline_strip.setPenJoinStyle(Qt.MiterJoin)
        symbol.appendSymbolLayer(outline_strip)
        symbol.setOpacity(0.75)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')
