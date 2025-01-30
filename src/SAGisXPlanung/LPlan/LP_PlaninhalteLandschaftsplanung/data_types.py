from uuid import uuid4

from sqlalchemy import Column, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanung.enums import LP_ERFlaechenArt, LP_FlaechenTypBV, \
    LP_FlaechenTypBVSpeziell
from SAGisXPlanung.XPlan.types import XPEnum
from SAGisXPlanung.core.mixins.mixins import RelationshipMixin, ElementOrderMixin


class LP_EingriffsregelungKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Datentyp mit Angaben für eine komplexe Eingriffsregelung """

    __tablename__ = 'lp_eingriffsregelung_komplex'
    __avoidRelation__ = ['eingriffsregelung']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    eRFlaechenArt = Column(Enum(LP_ERFlaechenArt), nullable=False)
    eRFlaechenArtText = Column(String)

    eingriffsregelung_id = Column(UUID(as_uuid=True),
                                  ForeignKey('lp_eingriffsregelung.id', ondelete='CASCADE'))
    eingriffsregelung = relationship("LP_Eingriffsregelung", back_populates="eingriffsregelungFlaechenTyp")

    @classmethod
    def avoid_export(cls):
        return ['eingriffsregelung_id']


class LP_TypBioVerbundKomplex(RelationshipMixin, ElementOrderMixin, Base):
    """ Datentyp mit Angaben zu Typen des Biotopverbunds. """

    __tablename__ = 'lp_typ_bioverbundkomplexe'
    __avoidRelation__ = ['biotopverbund_biotopvernetzung']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    flaechenTypBV = Column(Enum(LP_FlaechenTypBV), nullable=False)
    flaechentypBVSpeziell = Column(XPEnum(LP_FlaechenTypBVSpeziell, include_default=True))
    flaechentypSpeziellText = Column(String)

    biotopverbund_biotopvernetzung_id = Column(UUID(as_uuid=True),
                                               ForeignKey('lp_biotopverbund_biotopvernetzung.id', ondelete='CASCADE'))
    biotopverbund_biotopvernetzung = relationship('LP_BiotopverbundBiotopvernetzung', back_populates='typBioVerbund')

    @classmethod
    def avoid_export(cls):
        return ['biotopverbund_biotopvernetzung_id']
