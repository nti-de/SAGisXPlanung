from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.codelists import CodeListValue


LP_ZweckbestimmungGenerischeObjekteCodelistAssoc = Table('assoc_detail_zweckgenerischeobjekte', Base.metadata,
    Column('codelist_user_id', UUID(as_uuid=True), ForeignKey('lp_generisches_objekt.id', ondelete='CASCADE')),
    Column('codelist_id', UUID(as_uuid=True), ForeignKey('codelist_values.id'))
)


class LP_ZweckbestimmungGenerischeObjekte(CodeListValue):
    """ Zweckbestimmung des Generischen Objektes. """

    codelist_user = relationship("LP_GenerischesObjekt",
                                 back_populates="zweckbestimmung",
                                 secondary=LP_ZweckbestimmungGenerischeObjekteCodelistAssoc)

    __mapper_args__ = {
        "polymorphic_identity": "LP_ZweckbestimmungGenerischeObjekte"
    }
