from uuid import uuid4

from sqlalchemy import Column, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen.enums import SO_ZweckbestimmungStrassenverkehr, \
    SO_KlassifizGewaesser
from SAGisXPlanung.XPlan.mixins import RelationshipMixin, ElementOrderMixin


class SO_KomplexeZweckbestStrassenverkehr(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Fläche oder Anlage für den Strassenverkehr. """

    __tablename__ = 'so_zweckbestimmung_strassenverkehr'
    __avoidRelation__ = ['strassenverkehr']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(SO_ZweckbestimmungStrassenverkehr), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    strassenverkehr_id = Column(UUID(as_uuid=True), ForeignKey('so_strassenverkehr.id', ondelete='CASCADE'))
    strassenverkehr = relationship('SO_Strassenverkehr', back_populates='artDerFestlegung')

    @classmethod
    def avoid_export(cls):
        return ['strassenverkehr_id']


class SO_KomplexeFestlegungGewaesser(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung der Fläche. """

    __tablename__ = 'so_festlegung_gewaesser'
    __avoidRelation__ = ['gewaesser']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(SO_KlassifizGewaesser), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    gewaesser_id = Column(UUID(as_uuid=True), ForeignKey('so_gewaesser.id', ondelete='CASCADE'))
    gewaesser = relationship('SO_Gewaesser', back_populates='artDerFestlegung')

    @classmethod
    def avoid_export(cls):
        return ['gewaesser_id']
