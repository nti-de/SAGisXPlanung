from uuid import uuid4

from sqlalchemy import Column, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.enums import XP_Sondernutzungen
from SAGisXPlanung.core.mixins.mixins import RelationshipMixin, ElementOrderMixin


class FP_KomplexeSondernutzung(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation einer Sondernutzung. """

    __tablename__ = 'fp_komplexe_sondernutzung'
    __avoidRelation__ = ['baugebiet']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_Sondernutzungen), nullable=False)

    nutzungText = Column(String)
    aufschrift = Column(String)

    baugebiet_id = Column(UUID(as_uuid=True), ForeignKey('fp_baugebiet.id', ondelete='CASCADE'))
    baugebiet = relationship('FP_BebauungsFlaeche', back_populates='rel_sondernutzung')

    @classmethod
    def avoid_export(cls):
        return ['baugebiet_id']
