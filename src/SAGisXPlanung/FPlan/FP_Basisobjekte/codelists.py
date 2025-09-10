from sqlalchemy.orm import relationship

from SAGisXPlanung.XPlan.codelists import CodeListValue


class FP_SonstPlanArt(CodeListValue):

    fp_plans = relationship("FP_Plan", back_populates="sonstPlanArt", foreign_keys='FP_Plan.sonstPlanArt_id')

    __mapper_args__ = {
        "polymorphic_identity": "FP_SonstPlanArt",
    }


class FP_Status(CodeListValue):

    fp_plans = relationship("FP_Plan", back_populates="status", foreign_keys='FP_Plan.status_id')

    __mapper_args__ = {
        "polymorphic_identity": "FP_Status",
    }
