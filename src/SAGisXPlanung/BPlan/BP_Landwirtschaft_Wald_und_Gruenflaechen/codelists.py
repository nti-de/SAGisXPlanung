from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.codelists import CodeListValue


BP_DetailZweckbestGruenFlaecheCodelistAssoc = Table('assoc_detail_zweckgruen', Base.metadata,
    Column('codelist_user_id', UUID(as_uuid=True), ForeignKey('bp_zweckbestimmung_gruen.id', ondelete='CASCADE')),
    Column('codelist_id', UUID(as_uuid=True), ForeignKey('codelist_values.id'))
)


class BP_DetailZweckbestGruenFlaeche(CodeListValue):
    codelist_user = relationship("BP_KomplexeZweckbestGruen", back_populates="detail",
                                 secondary=BP_DetailZweckbestGruenFlaecheCodelistAssoc)

    __mapper_args__ = {
        "polymorphic_identity": "BP_DetailZweckbestGruenFlaeche",
    }