from uuid import uuid4

from sqlalchemy import Column, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGruen, XP_ZweckbestimmungLandwirtschaft, XP_ZweckbestimmungWald
from SAGisXPlanung.core.mixins.mixins import RelationshipMixin, ElementOrderMixin


class FP_KomplexeZweckbestGruen(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Grünfläche """

    __tablename__ = 'fp_zweckbestimmung_gruen'
    __avoidRelation__ = ['gruenflaeche']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungGruen), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    gruenflaeche_id = Column(UUID(as_uuid=True), ForeignKey('fp_gruen.id', ondelete='CASCADE'))
    gruenflaeche = relationship('FP_Gruen', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['gruenflaeche_id']


class FP_KomplexeZweckbestLandwirtschaft(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Fläche für die Landwirtschaft """

    __tablename__ = 'fp_zweckbestimmung_landwirtschaft'
    __avoidRelation__ = ['landwirtschaft']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungLandwirtschaft), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    landwirtschaft_id = Column(UUID(as_uuid=True), ForeignKey('fp_landwirtschaft.id', ondelete='CASCADE'))
    landwirtschaft = relationship('FP_Landwirtschaft', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['landwirtschaft_id']


class FP_KomplexeZweckbestWald(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Waldfläche """

    __tablename__ = 'fp_zweckbestimmung_wald'
    __avoidRelation__ = ['waldflaeche']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungWald), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    waldflaeche_id = Column(UUID(as_uuid=True), ForeignKey('fp_wald.id', ondelete='CASCADE'))
    waldflaeche = relationship('FP_WaldFlaeche', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['waldflaeche_id']
