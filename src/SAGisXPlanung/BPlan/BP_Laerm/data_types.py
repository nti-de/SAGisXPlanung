from uuid import uuid4

from sqlalchemy import Column, String, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base, XPlanVersion
from SAGisXPlanung.BPlan.BP_Laerm.enums import BP_SchallleistungspegelTypen, BP_SchallleistungspegelBerechnungsgrundlage
from SAGisXPlanung.XPlan.types import Sound, XPEnum, Angle
from SAGisXPlanung.core.mixins.mixins import RelationshipMixin, ElementOrderMixin


class BP_EmissionskontingentLaerm(RelationshipMixin, ElementOrderMixin, Base):
    """ Laermemissionskontingent eines Teilgebietes. """

    __tablename__ = 'bp_emissionskontingent_laerm'
    __avoidRelation__ = ['bp_objekt', 'so_objekt', 'bp_objekt_gebiet', 'so_objekt_gebiet']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String(50))

    pegelTyp = Column(XPEnum(BP_SchallleistungspegelTypen), info={'xplan_version': XPlanVersion.SIX})
    berechnungsgrundlage = Column(XPEnum(BP_SchallleistungspegelBerechnungsgrundlage),
                                  info={'xplan_version': XPlanVersion.SIX})
    berechnungsgrundlageDatum = Column(Date, info={'xplan_version': XPlanVersion.SIX})

    ekwertTag = Column(Sound, nullable=False)
    ekwertNacht = Column(Sound, nullable=False)
    erlaeuterung = Column(String)

    bp_objekt_id = Column(UUID(as_uuid=True), ForeignKey('bp_objekt.id', ondelete='CASCADE'))
    bp_objekt = relationship('BP_Objekt', back_populates='laermkontingent', foreign_keys=[bp_objekt_id])

    so_objekt_id = Column(UUID(as_uuid=True), ForeignKey('so_objekt.id', ondelete='CASCADE'))
    so_objekt = relationship('SO_Objekt', back_populates='laermkontingent', foreign_keys=[so_objekt_id])

    bp_objekt_gebiet_id = Column(UUID(as_uuid=True), ForeignKey('bp_objekt.id', ondelete='CASCADE'))
    bp_objekt_gebiet = relationship('BP_Objekt', back_populates='laermkontingentGebiet',
                                    foreign_keys=[bp_objekt_gebiet_id])

    so_objekt_gebiet_id = Column(UUID(as_uuid=True), ForeignKey('so_objekt.id', ondelete='CASCADE'))
    so_objekt_gebiet = relationship('SO_Objekt', back_populates='laermkontingentGebiet',
                                    foreign_keys=[so_objekt_gebiet_id])

    __mapper_args__ = {
        'polymorphic_identity': 'bp_emissionskontingent_laerm',
        'polymorphic_on': type
    }

    @classmethod
    def avoid_export(cls):
        return ['bp_objekt', 'so_objekt', 'bp_objekt_gebiet', 'so_objekt_gebiet']


class BP_EmissionskontingentLaermGebiet(BP_EmissionskontingentLaerm):
    """ Emissionskontingent fuer ein bestimmtes Immissionsgebiet ausserhalb des B-Plans. """

    __tablename__ = 'bp_emissionskontingent_laerm_gebiet'

    id = Column(ForeignKey('bp_emissionskontingent_laerm.id', ondelete='CASCADE'), primary_key=True)
    gebietsbezeichnung = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'bp_emissionskontingent_laerm_gebiet',
    }


class BP_Richtungssektor(RelationshipMixin, ElementOrderMixin, Base):
    """ Zusatzkontingente Tag/Nacht der Laermemission fuer einen Richtungssektor. """

    __tablename__ = 'bp_richtungssektor'
    __avoidRelation__ = ['zusatzkontingent', 'zusatzkontingentFlaeche']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    winkelAnfang = Column(Angle, nullable=False)
    winkelEnde = Column(Angle, nullable=False)
    zkWertTag = Column(Sound, nullable=False)
    zkWertNacht = Column(Sound, nullable=False)

    zusatzkontingent_id = Column(UUID(as_uuid=True), ForeignKey('bp_zusatzkontingent_laerm.id', ondelete='CASCADE'))
    zusatzkontingent = relationship('BP_ZusatzkontingentLaerm', back_populates='richtungssektor')

    zusatzkontingentFlaeche_id = Column(UUID(as_uuid=True),
                                        ForeignKey('bp_zusatzkontingent_laerm_flaeche.id', ondelete='CASCADE'))
    zusatzkontingentFlaeche = relationship('BP_ZusatzkontingentLaermFlaeche', back_populates='richtungssektor')

    @classmethod
    def avoid_export(cls):
        return ['zusatzkontingent', 'zusatzkontingentFlaeche']
