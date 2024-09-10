from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsSymbol, QgsWkbTypes, QgsSimpleLineSymbolLayer, QgsSingleSymbolRenderer

from sqlalchemy import Column, ForeignKey, Enum, String, Date, ARRAY, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung.RPlan.RP_Basisobjekte.enums import RP_Art, RP_Rechtsstand, RP_Verfahren
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_Bundeslaender
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich
from SAGisXPlanung.XPlan.types import GeometryType


class RP_Plan(XP_Plan):
    """ Die Klasse RP_Plan modelliert einen Raumordnungsplan. """

    def __init__(self):
        self.auslegungsEndDatum = []
        self.auslegungsStartDatum = []
        self.traegerbeteiligungsStartDatum = []
        self.traegerbeteiligungsEndDatum = []

    __tablename__ = 'rp_plan'
    __mapper_args__ = {
        'polymorphic_identity': 'rp_plan',
    }

    id = Column(ForeignKey("xp_plan.id", ondelete='CASCADE'), primary_key=True)

    bundesland = Column(Enum(XP_Bundeslaender), doc='Zuständiges Bundesland')
    planArt = Column(Enum(RP_Art), nullable=False, doc='Art des Plans')
    planungsregion = Column(Integer(), doc='Kennziffer der Planungsregion')
    teilabschnitt = Column(Integer(), doc='Kennziffer des Teilabschnittes')
    rechtsstand = Column(Enum(RP_Rechtsstand), doc='Rechtsstand')
    aufstellungsbeschlussDatum = Column(Date(), doc='Aufstellungsbeschlussdatum')
    auslegungsStartDatum = Column(ARRAY(Date), doc='Startdatum der Auslegung')
    auslegungsEndDatum = Column(ARRAY(Date), doc='Enddatum der Auslegung')
    traegerbeteiligungsStartDatum = Column(ARRAY(Date), doc='Start der Trägerbeteiligung')
    traegerbeteiligungsEndDatum = Column(ARRAY(Date), doc='Ende der Trägerbeteiligung')
    aenderungenBisDatum = Column(Date(), doc='Änderung bis')
    entwurfsbeschlussDatum = Column(Date(), doc='Datum des Entwurfsbeschluss')
    planbeschlussDatum = Column(Date(), doc='Datum des Planbeschlusses')
    datumDesInkrafttretens = Column(Date(), doc='Datum des Inkrafttretens')
    verfahren = Column(Enum(RP_Verfahren), doc='Verfahren')
    amtlicherSchluessel = Column(String(), doc='Amtlicher Schlüssel')
    genehmigungsbehoerde = Column(String(), doc='Genehmigungsbehörde')
    bereich = relationship("RP_Bereich", back_populates="gehoertZuPlan", cascade="all, delete", doc='Bereich')

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


class RP_Bereich(XP_Bereich):
    """ Die Klasse RP_Bereich modelliert einen Bereich eines Raumordnungsplans. """

    __tablename__ = 'rp_bereich'
    __mapper_args__ = {
        'polymorphic_identity': 'rp_bereich',
    }

    id = Column(ForeignKey("xp_bereich.id", ondelete='CASCADE'), primary_key=True)

    versionBROG = Column(Date())
    versionBROGText = Column(String())
    versionLPLG = Column(Date())
    versionLPLGText = Column(String())
    geltungsmassstab = Column(Integer())

    gehoertZuPlan_id = Column(UUID(as_uuid=True), ForeignKey('rp_plan.id', ondelete='CASCADE'))
    gehoertZuPlan = relationship('RP_Plan', back_populates='bereich')

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        return QgsSingleSymbolRenderer(symbol)

