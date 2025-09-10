from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.codelists import CodeListValue


FP_DetailZweckbestVerEntsorgungCodelistAssoc = Table('assoc_detail_zweckversorgung', Base.metadata,
    Column('codelist_user_id', UUID(as_uuid=True), ForeignKey('fp_zweckbestimmung_versorgung.id', ondelete='CASCADE')),
    Column('codelist_id', UUID(as_uuid=True), ForeignKey('codelist_values.id'))
)


class FP_DetailZweckbestVerEntsorgung(CodeListValue):
    codelist_user = relationship("FP_KomplexeZweckbestVerEntsorgung", back_populates="detail",
                                 secondary=FP_DetailZweckbestVerEntsorgungCodelistAssoc)

    __mapper_args__ = {
        "polymorphic_identity": "FP_DetailZweckbestVerEntsorgung",
    }