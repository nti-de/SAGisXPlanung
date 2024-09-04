from uuid import uuid4

from sqlalchemy import Column, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungSpielSportanlage, XP_ZweckbestimmungGemeinbedarf
from SAGisXPlanung.core.mixins.mixins import RelationshipMixin, ElementOrderMixin


class BP_KomplexeZweckbestSpielSportanlage(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Spiel-/ Sportanlage. """

    __tablename__ = 'bp_zweckbestimmung_sport'
    __avoidRelation__ = ['spiel_sportanlage']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungSpielSportanlage), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    spiel_sportanlage_id = Column(UUID(as_uuid=True), ForeignKey('bp_spiel_sportanlage.id', ondelete='CASCADE'))
    spiel_sportanlage = relationship('BP_SpielSportanlagenFlaeche', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['spiel_sportanlage_id']


class BP_KomplexeZweckbestGemeinbedarf(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Gemeinbedarfsfläche """

    __tablename__ = 'bp_zweckbestimmung_gemeinbedarf'
    __avoidRelation__ = ['gemeinbedarf']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungGemeinbedarf), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    gemeinbedarf_id = Column(UUID(as_uuid=True), ForeignKey('bp_gemeinbedarf.id', ondelete='CASCADE'))
    gemeinbedarf = relationship('BP_GemeinbedarfsFlaeche', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['gemeinbedarf_id']
