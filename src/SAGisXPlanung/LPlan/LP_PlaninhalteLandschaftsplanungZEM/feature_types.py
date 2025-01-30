from qgis.core import QgsSymbol, QgsSingleSymbolRenderer

from sqlalchemy import Column, ForeignKey, Enum, String, ARRAY
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Objekt
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanungZEM.enums import LP_ZEMTyp
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.core.mixins.mixins import MixedGeometry


@xp_version(versions=[XPlanVersion.SIX])
class LP_ZieleErfordernisseMassnahmen(MixedGeometry, LP_Objekt):
    """ Schutzgebietskategorien gemäß Kapitel 4 BNatSchG „Schutz bestimmter Teile von Natur und Landschaft“. """

    __tablename__ = 'lp_ziele_erfordernisse_massnahmen'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("lp_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(ARRAY(Enum(LP_ZEMTyp)), nullable=False)

    # [1..*]
    schutzgut = relationship("LP_SchutzgutKomplex", back_populates="ziele_erfordernisse_massnahmen",
                             cascade="all, delete", passive_deletes=True,
                             info={ 'nullable': False })

    # [1..*]
    zielDimNatSchLaPfl = relationship("LP_ZielDimNatSchLaPflKomplex", back_populates="ziele_erfordernisse_massnahmen",
                                      cascade="all, delete", passive_deletes=True,
                                      info={ 'nullable': False })

    # [1..*]
    adressat = relationship("LP_AdressatKomplex", back_populates="ziele_erfordernisse_massnahmen",
                            cascade="all, delete", passive_deletes=True,
                            info={ 'nullable': False })

    # [1..*]
    schutzPflegeEntwicklung = relationship("LP_SPEKomplex", back_populates="ziele_erfordernisse_massnahmen",
                                           cascade="all, delete", passive_deletes=True,
                                           info={ 'nullable': False })

    # [0..*]
    biologischeVielfalt = relationship("LP_BiologischeVielfaltKomplex", back_populates="ziele_erfordernisse_massnahmen",
                                       cascade="all, delete", passive_deletes=True)

    # [0..*]
    boden = relationship("LP_BodenKomplex", back_populates="ziele_erfordernisse_massnahmen",
                         cascade="all, delete", passive_deletes=True)

    # [0..*]
    wasser = relationship("LP_WasserKomplex", back_populates="ziele_erfordernisse_massnahmen",
                          cascade="all, delete", passive_deletes=True)

    # [0..*]
    klima = relationship("LP_KlimaKomplex", back_populates="ziele_erfordernisse_massnahmen",
                         cascade="all, delete", passive_deletes=True)

    # [0..*]
    luft = relationship("LP_LuftKomplex", back_populates="ziele_erfordernisse_massnahmen",
                        cascade="all, delete", passive_deletes=True)

    # [0..*]
    landschaftsbild = relationship("LP_LandschaftsbildKomplex", back_populates="ziele_erfordernisse_massnahmen",
                                   cascade="all, delete", passive_deletes=True)

    # [0..*]
    erholung = relationship("LP_ErholungKomplex", back_populates="ziele_erfordernisse_massnahmen",
                            cascade="all, delete", passive_deletes=True)

    freiraeume = Column(ARRAY(String))  # TODO: CharacterString [0..*]
    foerdermoeglichkeit = Column(ARRAY(String))  # TODO: CharacterString [0..*]

    # [0..*]
    nutzungseinschraenkung = relationship("LP_NutzungseinschraenkungKomplex", back_populates="ziele_erfordernisse_massnahmen",
                                          cascade="all, delete", passive_deletes=True)

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
