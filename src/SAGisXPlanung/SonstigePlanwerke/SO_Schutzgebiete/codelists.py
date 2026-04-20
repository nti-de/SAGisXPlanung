from sqlalchemy.orm import relationship

from SAGisXPlanung.XPlan.codelists import CodeListValue


class SO_DetailKlassifizSchutzgebietSonstRecht(CodeListValue):
    so_schutzgebiet_sonstiges_recht = relationship(
        "SO_SchutzgebietSonstigesRecht",
        back_populates="detailArtDerFestlegung",
        foreign_keys='SO_SchutzgebietSonstigesRecht.detailArtDerFestlegung_id'
    )

    __mapper_args__ = {
        "polymorphic_identity": "SO_DetailKlassifizSchutzgebietSonstRecht",
    }
