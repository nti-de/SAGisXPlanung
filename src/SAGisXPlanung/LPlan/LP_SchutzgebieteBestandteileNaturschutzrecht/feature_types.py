from qgis.core import QgsSymbol, QgsSingleSymbolRenderer

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Objekt
from SAGisXPlanung.LPlan.LP_SchutzgebieteBestandteileNaturschutzrecht.enums import LP_KlassifizierungNaturschutzrecht, \
    LP_RechtsstandSchutzGeb, LP_GesGeschBiotopTyp, LP_SchutzzonenNaturschutzrecht
from SAGisXPlanung.XPlan.core import xp_version, XPCol
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
    detailGesetzlGeschBiotopLR_id = XPCol(UUID(as_uuid=True), ForeignKey('codelist_values.id'),
                                          attribute='detailGesetzlGeschBiotopLR')
    detailGesetzlGeschBiotopLR = relationship("LP_DetailGesetzlGeschBiotopLR", back_populates=__tablename__,
                                              foreign_keys=[detailGesetzlGeschBiotopLR_id], info={
                                                     'form-type': 'inline'
                                                 })

    schutzzone = Column(XPEnum(LP_SchutzzonenNaturschutzrecht, include_default=True))
    schutzzonenText = Column(String)

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
