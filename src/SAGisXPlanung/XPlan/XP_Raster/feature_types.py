from uuid import uuid4

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.core.mixins.mixins import FeatureType, ElementOrderMixin, RelationshipMixin


class XP_Rasterdarstellung(FeatureType, RelationshipMixin, ElementOrderMixin, Base):
    """ Georeferenzierte Rasterdarstellung eines Plans. Das über refScan referierte Rasterbild zeigt den Basisplan,
        dessen Geltungsbereich durch den Geltungsbereich des Gesamtplans (Attribut geltungsbereich von XP_Plan)
        repräsentiert ist """

    __tablename__ = 'xp_rasterdarstellung'
    __avoidRelation__ = ['bereich']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    # [1..*]
    refScan = relationship("XP_ExterneReferenz", back_populates="xp_rasterdarstellung_scan",
                           cascade="all, delete", passive_deletes=True,
                           foreign_keys='XP_ExterneReferenz.xp_rasterdarstellung_scan_id')
    # [0..1]
    refText = relationship("XP_ExterneReferenz", back_populates="xp_rasterdarstellung_text",
                           cascade="all, delete", passive_deletes=True, uselist=False,
                           foreign_keys='XP_ExterneReferenz.xp_rasterdarstellung_text_id')
    # [0..*]
    refLegende = relationship("XP_ExterneReferenz", back_populates="xp_rasterdarstellung_legende",
                           cascade="all, delete", passive_deletes=True,
                           foreign_keys='XP_ExterneReferenz.xp_rasterdarstellung_legende_id')

    bereich_id = Column(UUID(as_uuid=True), ForeignKey('xp_bereich.id', ondelete='CASCADE'))
    bereich = relationship("XP_Bereich", back_populates="rasterBasis")

    @classmethod
    def avoid_export(cls):
        return ['bereich']