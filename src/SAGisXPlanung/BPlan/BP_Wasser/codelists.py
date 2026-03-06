from sqlalchemy import Table, ForeignKey, UUID, Column
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.codelists import CodeListValue

BP_DetailZweckbestWasserwirtschaftCodelistAssoc = Table('assoc_detail_zweckwasserwirtschaft', Base.metadata,
    Column('codelist_user_id', UUID(as_uuid=True), ForeignKey('bp_wasserwirtschaft.id', ondelete='CASCADE')),
    Column('codelist_id', UUID(as_uuid=True), ForeignKey('codelist_values.id'))
)


class BP_DetailZweckbestWasserwirtschaft(CodeListValue):
    """ Detaillierte Zweckbestimmung der Fläche für Wasserwirtschaft. """

    codelist_user = relationship("BP_WasserwirtschaftsFlaeche",
                                 back_populates="detaillierteZweckbestimmung",
                                 secondary=BP_DetailZweckbestWasserwirtschaftCodelistAssoc)

    __mapper_args__ = {
        "polymorphic_identity": "BP_DetailZweckbestWasserwirtschaft"
    }