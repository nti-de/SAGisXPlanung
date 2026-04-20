from sqlalchemy.orm import relationship

from SAGisXPlanung.XPlan.codelists import CodeListValue


class SO_DetailKlassifizGelaendemorphologie(CodeListValue):
    so_gelaendemorphologie = relationship("SO_Gelaendemorphologie", back_populates="detailArtDerFestlegung",
                                          foreign_keys='SO_Gelaendemorphologie.detailArtDerFestlegung_id')

    __mapper_args__ = {
        "polymorphic_identity": "SO_DetailKlassifizGelaendemorphologie",
    }


class SO_SonstGrenzeTypen(CodeListValue):
    so_grenze = relationship("SO_Grenze", back_populates="sonstTyp",
                             foreign_keys='SO_Grenze.sonstTyp_id')

    __mapper_args__ = {
        "polymorphic_identity": "SO_SonstGrenzeTypen",
    }
