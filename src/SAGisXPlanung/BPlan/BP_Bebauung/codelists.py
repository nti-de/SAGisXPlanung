from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.XPlan.codelists import CodeListValue


class BP_DetailArtDerBaulNutzung(CodeListValue):
    bp_baugebiet = relationship("BP_BaugebietsTeilFlaeche", back_populates="detaillierteArtDerBaulNutzung",
                                foreign_keys='BP_BaugebietsTeilFlaeche.detaillierteArtDerBaulNutzung_id')

    __mapper_args__ = {
        "polymorphic_identity": "BP_DetailArtDerBaulNutzung",
    }


class BP_DetailDachform(CodeListValue):
    bp_dachgestaltung = relationship("BP_Dachgestaltung", back_populates="detaillierteDachform",
                                     foreign_keys='BP_Dachgestaltung.detaillierteDachform_id')

    __mapper_args__ = {
        "polymorphic_identity": "BP_DetailDachform",
    }


BP_DetailSondernutzungCodelistAssoc = Table('assoc_detail_sondernutzung', Base.metadata,
    Column('codelist_user_id', UUID(as_uuid=True), ForeignKey('bp_komplexe_sondernutzung.id', ondelete='CASCADE')),
    Column('codelist_id', UUID(as_uuid=True), ForeignKey('codelist_values.id'))
)


class BP_DetailSondernutzung(CodeListValue):
    codelist_user = relationship("BP_KomplexeSondernutzung", back_populates="detail",
                                 secondary=BP_DetailSondernutzungCodelistAssoc)

    __mapper_args__ = {
        "polymorphic_identity": "BP_DetailSondernutzung",
    }