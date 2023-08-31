from uuid import uuid4

from sqlalchemy import Column, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGemeinbedarf, XP_ZweckbestimmungSpielSportanlage
from SAGisXPlanung.XPlan.mixins import RelationshipMixin, ElementOrderMixin


class FP_KomplexeZweckbestGemeinbedarf(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Fläche für Gemeinbedarf """

    __tablename__ = 'fp_zweckbestimmung_gemeinbedarf'
    __avoidRelation__ = ['gemeinbedarf']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungGemeinbedarf), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    gemeinbedarf_id = Column(UUID(as_uuid=True), ForeignKey('fp_gemeinbedarf.id', ondelete='CASCADE'))
    gemeinbedarf = relationship('FP_Gemeinbedarf', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['gemeinbedarf_id']


class FP_KomplexeZweckbestSpielSportanlage(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Spiel- und Sportanlage."""

    __tablename__ = 'fp_zweckbestimmung_sport'
    __avoidRelation__ = ['sportanlage']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungSpielSportanlage), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    sportanlage_id = Column(UUID(as_uuid=True), ForeignKey('fp_spiel_sportanlage.id', ondelete='CASCADE'))
    sportanlage = relationship('FP_SpielSportanlage', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['sportanlage_id']
