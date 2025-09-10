from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.codelists import CodeListValue


FP_DetailZweckbestGemeinbedarfCodelistAssoc = Table('assoc_detail_zweckgemeinbedarf', Base.metadata,
    Column('codelist_user_id', UUID(as_uuid=True), ForeignKey('fp_gemeinbedarf.id', ondelete='CASCADE')),
    Column('codelist_user_v6_id', UUID(as_uuid=True), ForeignKey('fp_zweckbestimmung_gemeinbedarf.id', ondelete='CASCADE')),
    Column('codelist_id', UUID(as_uuid=True), ForeignKey('codelist_values.id'))
)


class FP_DetailZweckbestGemeinbedarf(CodeListValue):
    codelist_user = relationship("FP_Gemeinbedarf", back_populates="detaillierteZweckbestimmung",
                                 secondary=FP_DetailZweckbestGemeinbedarfCodelistAssoc)
    codelist_user_v6 = relationship("FP_KomplexeZweckbestGemeinbedarf", back_populates="detail",
                                    secondary=FP_DetailZweckbestGemeinbedarfCodelistAssoc)

    __mapper_args__ = {
        "polymorphic_identity": "FP_DetailZweckbestGemeinbedarf",
    }