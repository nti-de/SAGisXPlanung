from uuid import uuid4

from sqlalchemy import Column, Date, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.BPlan.BP_Basisobjekte.enums import BP_VerlaengerungVeraenderungssperre
from SAGisXPlanung.XPlan.mixins import RelationshipMixin, ElementOrderMixin


class BP_VeraenderungssperreDaten(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Daten für eine Veränderungssperre. """

    __tablename__ = 'bp_veraenderungssperre_daten'
    __avoidRelation__ = ['plan']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    startDatum = Column(Date, nullable=False)
    endDatum = Column(Date, nullable=False)
    verlaengerung = Column(Enum(BP_VerlaengerungVeraenderungssperre), nullable=False)
    beschlussDatum = Column(Date)

    refBeschluss = relationship("XP_ExterneReferenz", back_populates="veraenderungssperre",
                                cascade="all, delete", passive_deletes=True, uselist=False)

    plan_id = Column(UUID(as_uuid=True), ForeignKey('bp_plan.id', ondelete='CASCADE'))
    plan = relationship("BP_Plan", back_populates="rel_veraenderungssperre")

    @classmethod
    def avoid_export(cls):
        return ['plan_id']
