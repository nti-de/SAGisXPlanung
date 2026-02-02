from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.codelists import CodeListValue


XP_DetailTechnVorkehrungImmissionsschutzCodelistAssoc = Table('assoc_detail_vorkehrung_immissionschutz', Base.metadata,
    Column('codelist_user_id', UUID(as_uuid=True), ForeignKey('fp_nutzungsbeschraenkung.id', ondelete='CASCADE')),
    Column('codelist_id', UUID(as_uuid=True), ForeignKey('codelist_values.id'))
)


class XP_DetailTechnVorkehrungImmissionsschutz(CodeListValue):
    """ Detaillierte Klassifizierung der auf der Fläche zu treffenden baulichen oder
        sonstigen technischen Vorkehrungen. """

    codelist_user = relationship("FP_Nutzungsbeschraenkung",
                                 back_populates="detaillierteTechnVorkehrung",
                                 secondary=XP_DetailTechnVorkehrungImmissionsschutzCodelistAssoc)

    __mapper_args__ = {
        "polymorphic_identity": "XP_DetailTechnVorkehrungImmissionsschutz "
    }