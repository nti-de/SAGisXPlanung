from sqlalchemy.orm import relationship

from SAGisXPlanung.XPlan.codelists import CodeListValue


class SO_DetailKlassifizNachDenkmalschutzrecht(CodeListValue):
    so_denkmalschutz = relationship("SO_Denkmalschutzrecht", back_populates="detailArtDerFestlegung",
                                    foreign_keys='SO_Denkmalschutzrecht.detailArtDerFestlegung_id')

    __mapper_args__ = {
        "polymorphic_identity": "SO_DetailKlassifizNachDenkmalschutzrecht",
    }


class SO_DetailKlassifizNachBodenschutzrecht(CodeListValue):
    so_bodenschutz = relationship("SO_Bodenschutzrecht", back_populates="detailArtDerFestlegung",
                                    foreign_keys='SO_Bodenschutzrecht.detailArtDerFestlegung_id')

    __mapper_args__ = {
        "polymorphic_identity": "SO_DetailKlassifizNachBodenschutzrecht",
    }


class SO_DetailKlassifizNachSchienenverkehrsrecht(CodeListValue):
    so_schienenverkehr = relationship("SO_Schienenverkehrsrecht", back_populates="detailArtDerFestlegung",
                                      foreign_keys='SO_Schienenverkehrsrecht.detailArtDerFestlegung_id')

    __mapper_args__ = {
        "polymorphic_identity": "SO_DetailKlassifizNachSchienenverkehrsrecht",
    }


class SO_DetailKlassifizNachLuftverkehrsrecht(CodeListValue):
    so_luftverkehr = relationship("SO_Luftverkehrsrecht", back_populates="detailArtDerFestlegung",
                                  foreign_keys='SO_Luftverkehrsrecht.detailArtDerFestlegung_id')

    __mapper_args__ = {
        "polymorphic_identity": "SO_DetailKlassifizNachLuftverkehrsrecht",
    }


class SO_DetailKlassifizNachSonstigemRecht(CodeListValue):
    so_sonstiges_recht = relationship("SO_SonstigesRecht", back_populates="detailArtDerFestlegung",
                                  foreign_keys='SO_SonstigesRecht.detailArtDerFestlegung_id')

    __mapper_args__ = {
        "polymorphic_identity": "SO_DetailKlassifizNachSonstigemRecht",
    }