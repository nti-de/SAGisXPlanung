from sqlalchemy.orm import relationship

from SAGisXPlanung.XPlan.codelists import CodeListValue


class LP_DetailGesetzlGeschBiotopLR(CodeListValue):
    """ Über eine Codeliste definierte weitere gesetzlich geschützte Biotope z.B. nach Landesrecht. """

    # [0..1]
    lp_schutz_bestimmter_teile_von_natur_und_landschaft = relationship("LP_SchutzBestimmterTeileVonNaturUndLandschaft",
                                                                 back_populates="detailGesetzlGeschBiotopLR",
                                                                 foreign_keys='LP_SchutzBestimmterTeileVonNaturUndLandschaft.detailGesetzlGeschBiotopLR_id')

    __mapper_args__ = {
        "polymorphic_identity": __name__
    }
