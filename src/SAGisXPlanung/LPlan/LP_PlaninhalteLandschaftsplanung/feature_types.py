from qgis.core import QgsSymbol, QgsSingleSymbolRenderer

from sqlalchemy import Column, ForeignKey, Enum, String, ARRAY
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Objekt
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanung.enums import LP_PlanungsEbene, LP_RechtlicheSicherung, \
    LP_BioVerbundsystemArt, LP_BioVStandortFeuchte, LP_Umsetzungsstand, LP_MassnahmenTyp
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum
from SAGisXPlanung.core.mixins.mixins import MixedGeometry


@xp_version(versions=[XPlanVersion.SIX])
class LP_BiotopverbundBiotopvernetzung(MixedGeometry, LP_Objekt):
    """ Flächen und Elemente für Biotopverbund und Biotopvernetzung. """

    __tablename__ = 'lp_biotopverbund_biotopvernetzung'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("lp_objekt.id", ondelete='CASCADE'), primary_key=True)

    planungsEbene = Column(ARRAY(Enum(LP_PlanungsEbene)))

    typBioVerbund = relationship("LP_TypBioVerbundKomplex", back_populates="biotopverbund_biotopvernetzung",
                                 cascade="all, delete", passive_deletes=True)

    rechtlicheSicherung = Column(XPEnum(LP_RechtlicheSicherung, include_default=True))
    rechtlicheSicherungText = Column(String)

    bioVerbundsystemArt = Column(XPEnum(LP_BioVerbundsystemArt), nullable=False)
    bioVStandortFeuchte = Column(XPEnum(LP_BioVStandortFeuchte, include_default=True))
    bioVerbundsystemText = Column(String)
    foerdermoeglichkeit = Column(ARRAY(String))

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


@xp_version(versions=[XPlanVersion.SIX])
class LP_Eingriffsregelung(MixedGeometry, LP_Objekt):
    """ Planungsaussagen mit Bezug zur Eingriffsregelung und der Bewältigung von Eingriffsfolgen. """

    __tablename__ = 'lp_eingriffsregelung'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("lp_objekt.id", ondelete='CASCADE'), primary_key=True)

    eingriffsregelungFlaechenTyp = relationship("LP_EingriffsregelungKomplex", back_populates="eingriffsregelung",
                                                cascade="all, delete", passive_deletes=True,
                                                info={ 'nullable': False })

    umsetzungsstand = Column(XPEnum(LP_Umsetzungsstand), nullable=False)
    massnahmentyp = Column(ARRAY(Enum(LP_MassnahmenTyp)), nullable=False)
    kompensationText = Column(String)

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
