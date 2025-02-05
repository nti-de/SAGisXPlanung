from sqlalchemy.orm import relationship

from SAGisXPlanung.XPlan.codelists import CodeListValue


class LP_BioVfBiotoptyp_BKompV(CodeListValue):
    """ Biotoptypen-Katalog der Bundeskompensationsverordnung (Anlage 2 (zu § 5 Absatz 1 BKompV ) """

    # [0..1]
    lp_bio_vf_biotoptyp_komplex = relationship("LP_BioVfBiotoptypKomplex",
                                               back_populates="bioVfBiotoptyp_BKompV",
                                               foreign_keys='LP_BioVfBiotoptypKomplex.bioVfBiotoptyp_BKompV_id')

    __mapper_args__ = {
        "polymorphic_identity": "LP_BioVfBiotoptyp_BKompV"
    }


class LP_BioVfBiotoptyp_LandesKS(CodeListValue):
    """ Biotoptyp gem. eines Landeskartierschlüssels """

    # [0..1]
    lp_bio_vf_biotoptyp_komplex = relationship("LP_BioVfBiotoptypKomplex",
                                               back_populates="bioVfBiotoptyp_LandesKS",
                                               foreign_keys='LP_BioVfBiotoptypKomplex.bioVfBiotoptyp_LandesKS_id')

    __mapper_args__ = {
        "polymorphic_identity": "LP_BioVfBiotoptyp_LandesKS"
    }


class LP_BioVf_FFH_LRT(CodeListValue):
    """ FFH-Lebensraumtypen gem. Anhang I der Fauna Flora Habitatrichtlinie """

    # [0..1]
    lp_bio_vf_biotoptyp_komplex = relationship("LP_BioVfBiotoptypKomplex",
                                               back_populates="bioVf_FFH_LRT",
                                               foreign_keys='LP_BioVfBiotoptypKomplex.bioVf_FFH_LRT_id')

    __mapper_args__ = {
        "polymorphic_identity": "LP_BioVf_FFH_LRT"
    }
