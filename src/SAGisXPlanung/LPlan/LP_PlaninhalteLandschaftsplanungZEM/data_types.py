from uuid import uuid4

from sqlalchemy import Column, Enum, String, ForeignKey, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanungZEM.enums import LP_AdressatArt, LP_BioVfBestandteil, \
    LP_BioVfTiereArtSystematik, LP_BioVfTierArtRechtlicherSchutz, LP_BioVfTierArtHabitatanforderung, \
    LP_BodenAuspraegung, LP_ErholungFunktionen, LP_KlimaArt, LP_LandschaftsbildArt, LP_LuftArt, LP_SchutzgutArt, \
    LP_SchutzPflegeEntwicklung, LP_WasserAuspraegung, LP_ZielDimensionTyp, LP_BioVfPflanzenArtSystematik, \
    LP_BioVfPflanzenArtRechtlicherSchutz
from SAGisXPlanung.XPlan.core import XPCol
from SAGisXPlanung.XPlan.types import XPEnum
from SAGisXPlanung.core.mixins.mixins import RelationshipMixin, ElementOrderMixin


class LP_AdressatKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Angaben zu Adressaten, an den sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    __tablename__ = 'lp_adressat_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    adressatArt = Column(Enum(LP_AdressatArt), nullable=False)
    adressatText = Column(String)

    # [1..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="adressat")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


#region LP_BiologischeVielfaltKomplex
class LP_BiologischeVielfaltKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Angaben zum Planungsgegenstand „Biologische Vielfalt“ """

    __tablename__ = 'lp_biologische_vielfalt_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # [1]
    bioVielfaltTypus = relationship("LP_BiologischeVielfaltTypKomplex", back_populates="biologische_vielfalt_komplex",
                                    cascade="all, delete", passive_deletes=True,
                                    uselist=False, info={ 'nullable': False })

    # [0..*]
    bioVfPflanzenArt = relationship("LP_BioVfPflanzenArtKomplex", back_populates="biologische_vielfalt_komplex",
                                    cascade="all, delete", passive_deletes=True)

    # [0..*]
    bioVfTierArt = relationship("LP_BioVfTiereArtKomplex", back_populates="biologische_vielfalt_komplex",
                                    cascade="all, delete", passive_deletes=True)

    bioVfArtFFHAnhangII = Column(Boolean, nullable=False)

    # [0..*]
    bioVfBiotoptyp = relationship("LP_BioVfBiotoptypKomplex", back_populates="biologische_vielfalt_komplex",
                                  cascade="all, delete", passive_deletes=True)

    # [1..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="biologischeVielfalt")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_BiologischeVielfaltTypKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Angaben zu Adressaten, an den sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    __tablename__ = 'lp_biologische_vielfalt_typ_komplex'
    __avoidRelation__ = ['biologische_vielfalt_komplex']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    bioVielfaltTyp = Column(Enum(LP_BioVfBestandteil), nullable=False)
    bioVielfaltTypText = Column(String)

    # [1]
    biologische_vielfalt_komplex_id = Column(UUID(as_uuid=True),
                                             ForeignKey('lp_biologische_vielfalt_komplex.id', ondelete='CASCADE'))
    biologische_vielfalt_komplex = relationship("LP_BiologischeVielfaltKomplex", back_populates="bioVielfaltTypus")

    @classmethod
    def avoid_export(cls):
        return ['biologische_vielfalt_komplex_id']


class LP_BioVfBiotoptypKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit mindestens einer Angabe des Biotoptypen. """

    __tablename__ = 'lp_bio_vf_biotoptyp_komplex'
    __avoidRelation__ = ['biologische_vielfalt_komplex']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # [0..1]
    bioVfBiotoptyp_BKompV_id = XPCol(UUID(as_uuid=True), ForeignKey('codelist_values.id'),
                                     attribute='bioVfBiotoptyp_BKompV')
    bioVfBiotoptyp_BKompV = relationship("LP_BioVfBiotoptyp_BKompV", back_populates=__tablename__,
                                         foreign_keys=[bioVfBiotoptyp_BKompV_id], info={ 'form-type': 'inline' })

    # [0..1]
    bioVfBiotoptyp_LandesKS_id = XPCol(UUID(as_uuid=True), ForeignKey('codelist_values.id'),
                                       attribute='bioVfBiotoptyp_LandesKS')
    bioVfBiotoptyp_LandesKS = relationship("LP_BioVfBiotoptyp_LandesKS", back_populates=__tablename__,
                                           foreign_keys=[bioVfBiotoptyp_LandesKS_id], info={ 'form-type': 'inline' })

    # [0..1]
    bioVf_FFH_LRT_id = XPCol(UUID(as_uuid=True), ForeignKey('codelist_values.id'),
                             attribute='bioVf_FFH_LRT')
    bioVf_FFH_LRT = relationship("LP_BioVf_FFH_LRT", back_populates=__tablename__,
                                 foreign_keys=[bioVf_FFH_LRT_id], info={ 'form-type': 'inline' })

    bioVfBiotoptyp_Text = Column(String)

    # [0..*]
    biologische_vielfalt_komplex_id = Column(UUID(as_uuid=True),
                                             ForeignKey('lp_biologische_vielfalt_komplex.id', ondelete='CASCADE'))
    biologische_vielfalt_komplex = relationship("LP_BiologischeVielfaltKomplex", back_populates="bioVfBiotoptyp")

    @classmethod
    def avoid_export(cls):
        return ['biologische_vielfalt_komplex_id']


class LP_BioVfPflanzenArtKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben zum Planungsgegenstand Biologische Vielfalt / Pflanzen """

    __tablename__ = 'lp_bio_vf_pflanzen_art_komplex'
    __avoidRelation__ = ['biologische_vielfalt_komplex']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    bioVfPflanzenArtName = Column(String)

    bioVfPflanzenSystematik = Column(Enum(LP_BioVfPflanzenArtSystematik), nullable=False)
    bioVfPflanzenSystematikText = Column(String)

    bioVfPflanzenRechtlicherSchutz = Column(ARRAY(Enum(LP_BioVfPflanzenArtRechtlicherSchutz)))
    bioVfPflanzenRechtlicherSchutzText = Column(String)

    # [0..*]
    biologische_vielfalt_komplex_id = Column(UUID(as_uuid=True),
                                             ForeignKey('lp_biologische_vielfalt_komplex.id', ondelete='CASCADE'))
    biologische_vielfalt_komplex = relationship("LP_BiologischeVielfaltKomplex", back_populates="bioVfPflanzenArt")

    @classmethod
    def avoid_export(cls):
        return ['biologische_vielfalt_komplex_id']


class LP_BioVfTiereArtKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben zum Planungsgegenstand Biologische Vielfalt / Tiere """

    __tablename__ = 'lp_bio_vf_tiere_art_komplex'
    __avoidRelation__ = ['biologische_vielfalt_komplex']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    bioVfTierArtName = Column(String)

    bioVfTiereSystematik = Column(Enum(LP_BioVfTiereArtSystematik), nullable=False)
    bioVfTiereSystematikText = Column(String)

    bioVfTierArtRechtlicherSchutz = Column(ARRAY(Enum(LP_BioVfTierArtRechtlicherSchutz)))
    bioVfTierArtRechtlicherSchutzText = Column(String)

    bioVfTierArtHabitatanforderung = Column(XPEnum(LP_BioVfTierArtHabitatanforderung, include_default=True))
    bioVfTierArtHabitatanforderungText = Column(String)

    # [0..*]
    biologische_vielfalt_komplex_id = Column(UUID(as_uuid=True),
                                             ForeignKey('lp_biologische_vielfalt_komplex.id', ondelete='CASCADE'))
    biologische_vielfalt_komplex = relationship("LP_BiologischeVielfaltKomplex", back_populates="bioVfTierArt")

    @classmethod
    def avoid_export(cls):
        return ['biologische_vielfalt_komplex_id']
#endregion


class LP_BodenKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben in Bezug auf Planungsgegenstand Boden,
        an die sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    __tablename__ = 'lp_boden_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    bodenAuspraegung = Column(Enum(LP_BodenAuspraegung), nullable=False)
    bodenText = Column(String)

    # [0..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="boden")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_ErholungKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben in Bezug auf Planungsgegenstand Erholung,
        an die sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    __tablename__ = 'lp_erholung_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    erholungFunktionArt = Column(Enum(LP_ErholungFunktionen), nullable=False)
    erholungFunktionText = Column(String)

    # [0..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="erholung")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_KlimaKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben in Bezug auf Planungsgegenstand Klima,
        an die sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    __tablename__ = 'lp_klima_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    klimaArt = Column(Enum(LP_KlimaArt), nullable=False)
    klimaText = Column(String)

    # [0..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="klima")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_LandschaftsbildKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben in Bezug auf Planungsgegenstand Landschaftsbild,
        an die sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    __tablename__ = 'lp_landschaftsbild_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    landschaftsbildArt = Column(Enum(LP_LandschaftsbildArt), nullable=False)
    landschaftsbildText = Column(String)

    # [0..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="landschaftsbild")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_LuftKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben in Bezug auf Planungsgegenstand Luft,
        an die sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    __tablename__ = 'lp_luft_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    luftArt = Column(Enum(LP_LuftArt), nullable=False)
    luftText = Column(String)

    # [0..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="luft")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_NutzungseinschraenkungKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben zu Nutzungseinschränkungen. """

    __tablename__ = 'lp_nutzungseinschraenkung_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    hatNutzungseinschraenkung = Column(Boolean, nullable=False)
    nutzungseinschraenkungText = Column(String, nullable=False)

    # [0..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="nutzungseinschraenkung")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_SchutzgutKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben zum Schutzgut/Schutzgütern,
        auf die sich die Ziele, Erfordernisse und Maßnahmen richten. """

    __tablename__ = 'lp_schutzgut_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    schutzgutArt = Column(Enum(LP_SchutzgutArt), nullable=False)
    schutzgutText = Column(String)

    # [1..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="schutzgut")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_SPEKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Angaben zur Differenzierung der Schutz-, Pflege und Entwicklungsziele von Naturschutz und Landschaftspflege. """

    __tablename__ = 'lp_spe_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    schutzPflegeEntwicklungTyp = Column(Enum(LP_SchutzPflegeEntwicklung), nullable=False)
    schutzPflegeEntwicklungText = Column(String)

    # [1..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="schutzPflegeEntwicklung")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_WasserKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Komplexes Attribut mit Angaben in Bezug auf Planungsgegenstand Wasser,uu    dssdwwwwd   cccc
        an die sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    __tablename__ = 'lp_wasser_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    wasserAuspraegung = Column(Enum(LP_WasserAuspraegung), nullable=False)
    wasserText = Column(String)

    # [0..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="wasser")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']


class LP_ZielDimNatSchLaPflKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Zieldimension von Naturschutz und Landschaftspflege;
        Teilziele des Naturschutzes und der Landschaftspflege gemäß § 1 Abs. 1 Ziffern 1. bis 3. BNatSchG """

    __tablename__ = 'lp_ziel_dim_nat_sch_la_pfl_komplex'
    __avoidRelation__ = ['ziele_erfordernisse_massnahmen']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    zielDimensionTyp = Column(Enum(LP_ZielDimensionTyp), nullable=False)
    zielDimensionText = Column(String)

    # [1..*]
    ziele_erfordernisse_massnahmen_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_ziele_erfordernisse_massnahmen.id', ondelete='CASCADE'))
    ziele_erfordernisse_massnahmen = relationship("LP_ZieleErfordernisseMassnahmen", back_populates="zielDimNatSchLaPfl")

    @classmethod
    def avoid_export(cls):
        return ['ziele_erfordernisse_massnahmen_id']
