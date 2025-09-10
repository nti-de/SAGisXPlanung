from sqlalchemy.orm import relationship

from SAGisXPlanung.XPlan.codelists import CodeListValue


class BP_SonstPlanArt(CodeListValue):

    bp_plans = relationship("BP_Plan", back_populates="sonstPlanArt", foreign_keys='BP_Plan.sonstPlanArt_id')

    __mapper_args__ = {
        "polymorphic_identity": "BP_SonstPlanArt",
    }


class BP_Status(CodeListValue):

    bp_plans = relationship("BP_Plan", back_populates="status", foreign_keys='BP_Plan.status_id')

    __mapper_args__ = {
        "polymorphic_identity": "BP_Status",
    }
