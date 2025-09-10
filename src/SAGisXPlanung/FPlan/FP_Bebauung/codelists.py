from sqlalchemy.orm import relationship

from SAGisXPlanung.XPlan.codelists import CodeListValue


class FP_DetailArtDerBaulNutzung(CodeListValue):
    fp_baugebiet = relationship("FP_BebauungsFlaeche", back_populates="detaillierteArtDerBaulNutzung",
                                foreign_keys='FP_BebauungsFlaeche.detaillierteArtDerBaulNutzung_id')

    __mapper_args__ = {
        "polymorphic_identity": "FP_DetailArtDerBaulNutzung",
    }