from uuid import uuid4

from sqlalchemy import Column, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.FPlan.FP_Ver_und_Entsorgung.codelists import FP_DetailZweckbestVerEntsorgungCodelistAssoc
from SAGisXPlanung.XPlan.core import XPCol
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungVerEntsorgung
from SAGisXPlanung.XPlan.mixins import RelationshipMixin, ElementOrderMixin


class FP_KomplexeZweckbestVerEntsorgung(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Versorgungsfläche. """

    __tablename__ = 'fp_zweckbestimmung_versorgung'
    __avoidRelation__ = ['versorgung']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_ZweckbestimmungVerEntsorgung), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    versorgung_id = Column(UUID(as_uuid=True), ForeignKey('fp_versorgung.id', ondelete='CASCADE'))
    versorgung = relationship('FP_VerEntsorgung', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['versorgung_id']