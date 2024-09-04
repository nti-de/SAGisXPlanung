from uuid import uuid4

from sqlalchemy import Column, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGruen, XP_ZweckbestimmungLandwirtschaft, XP_ZweckbestimmungWald
from SAGisXPlanung.core.mixins.mixins import RelationshipMixin, ElementOrderMixin


class BP_KomplexeZweckbestGruen(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Grünfläche. """

    __tablename__ = 'bp_zweckbestimmung_gruen'
    __avoidRelation__ = ['gruenflaeche']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungGruen), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    gruenflaeche_id = Column(UUID(as_uuid=True), ForeignKey('bp_gruenflaeche.id', ondelete='CASCADE'))
    gruenflaeche = relationship('BP_GruenFlaeche', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['gruenflaeche_id']


class BP_KomplexeZweckbestLandwirtschaft(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung für Landwirtschaft. """

    __tablename__ = 'bp_zweckbestimmung_landwirtschaft'
    __avoidRelation__ = ['landwirtschaft']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungLandwirtschaft), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    landwirtschaft_id = Column(UUID(as_uuid=True), ForeignKey('bp_landwirtschaft.id', ondelete='CASCADE'))
    landwirtschaft = relationship('BP_LandwirtschaftsFlaeche', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['landwirtschaft_id']


class BP_KomplexeZweckbestWald(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung für Waldflächen. """

    __tablename__ = 'bp_zweckbestimmung_wald'
    __avoidRelation__ = ['waldflaeche']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungWald), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    waldflaeche_id = Column(UUID(as_uuid=True), ForeignKey('bp_wald.id', ondelete='CASCADE'))
    waldflaeche = relationship('BP_WaldFlaeche', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['waldflaeche']
