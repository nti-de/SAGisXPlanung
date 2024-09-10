from typing import List

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsSymbol, QgsWkbTypes, QgsSimpleLineSymbolLayer, QgsSingleSymbolRenderer

from sqlalchemy import Column, ForeignKey, Enum, String, Date, ARRAY, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.LPlan.LP_Basisobjekte.enums import LP_Rechtsstand, LP_PlanArt
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.data_types import XP_PlanXP_GemeindeAssoc
from SAGisXPlanung.XPlan.enums import XP_Bundeslaender
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich
from SAGisXPlanung.XPlan.types import GeometryType


class LP_Plan(XP_Plan):
    """ Die Klasse modelliert ein Planwerk mit landschaftsplanerischen Festlegungen, Darstellungen bzw. Festsetzungen. """

    def __init__(self):
        super().__init__()
        self.auslegungsEndDatum = []
        self.auslegungsStartDatum = []
        self.traegerbeteiligungsStartDatum = []
        self.traegerbeteiligungsEndDatum = []

    __tablename__ = 'lp_plan'
    __mapper_args__ = {
        'polymorphic_identity': 'lp_plan',
    }

    id = Column(ForeignKey("xp_plan.id", ondelete='CASCADE'), primary_key=True)

    bundesland = Column(Enum(XP_Bundeslaender), nullable=False)
    rechtlicheAussenwirkung = Column(Boolean, nullable=False)
    planArt = Column(ARRAY(Enum(LP_PlanArt)), nullable=False)

    planungstraegerGKZ = XPCol(String(), version=XPlanVersion.FIVE_THREE)
    planungstraeger = XPCol(String(), version=XPlanVersion.FIVE_THREE)

    gemeinde = relationship("XP_Gemeinde", back_populates="lp_plans", secondary=XP_PlanXP_GemeindeAssoc, doc='Gemeinde')

    plangeber_id = XPCol(UUID(as_uuid=True), ForeignKey('xp_plangeber.id'), version=XPlanVersion.SIX)
    plangeber = relationship("XP_Plangeber", back_populates="lp_plans", doc='Plangeber')

    rechtsstand = Column(Enum(LP_Rechtsstand))
    aufstellungsbeschlussDatum = Column(Date())

    auslegungsDatum = XPCol(ARRAY(Date), version=XPlanVersion.FIVE_THREE)
    tOeBbeteiligungsDatum = XPCol(ARRAY(Date), version=XPlanVersion.FIVE_THREE)
    oeffentlichkeitsbeteiligungDatum = XPCol(ARRAY(Date), version=XPlanVersion.FIVE_THREE)

    auslegungsStartDatum = XPCol(ARRAY(Date), version=XPlanVersion.SIX)
    auslegungsEndDatum = XPCol(ARRAY(Date), version=XPlanVersion.SIX)
    tOeBbeteiligungsStartDatum = XPCol(ARRAY(Date), version=XPlanVersion.SIX)
    tOeBbeteiligungsEndDatum = XPCol(ARRAY(Date), version=XPlanVersion.SIX)
    oeffentlichkeitsBetStartDatum = XPCol(ARRAY(Date), version=XPlanVersion.SIX)
    oeffentlichkeitsBetEndDatum = XPCol(ARRAY(Date), version=XPlanVersion.SIX)

    aenderungenBisDatum = Column(Date())
    entwurfsbeschlussDatum = Column(Date())
    planbeschlussDatum = Column(Date())
    inkrafttretenDatum = Column(Date())
    veroeffentlichungsDatum = XPCol(Date(), version=XPlanVersion.SIX)
    sonstVerfahrensDatum = Column(Date())

    sonstVerfahrensText = XPCol(String(), version=XPlanVersion.SIX)
    startBedingungen = XPCol(String(), version=XPlanVersion.SIX)
    endeBedingungen = XPCol(String(), version=XPlanVersion.SIX)

    bereich = relationship("LP_Bereich", back_populates="gehoertZuPlan", cascade="all, delete", doc='Bereich')

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.8)
        line.setPenStyle(Qt.SolidLine)

        symbol.appendSymbolLayer(line)
        return QgsSingleSymbolRenderer(symbol)


class LP_Bereich(XP_Bereich):
    """ Ein Bereich eines Landschaftsplans. """

    __tablename__ = 'lp_bereich'
    __mapper_args__ = {
        'polymorphic_identity': 'lp_bereich',
    }

    id = Column(ForeignKey("xp_bereich.id", ondelete='CASCADE'), primary_key=True)

    gehoertZuPlan_id = Column(UUID(as_uuid=True), ForeignKey('lp_plan.id', ondelete='CASCADE'))
    gehoertZuPlan = relationship('LP_Plan', back_populates='bereich')

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        return QgsSingleSymbolRenderer(symbol)
