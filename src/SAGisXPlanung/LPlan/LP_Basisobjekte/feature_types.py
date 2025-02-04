from typing import List

from geoalchemy2 import Geometry, WKTElement
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSimpleLineSymbolLayer, QgsSingleSymbolRenderer,
                       QgsCoordinateReferenceSystem, QgsGeometry)

from sqlalchemy import Column, ForeignKey, Enum, String, Date, ARRAY, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.LPlan.LP_Basisobjekte.enums import LP_Rechtsstand, LP_PlanArt, LP_Raumkonkretisierung
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.data_types import XP_PlanXP_GemeindeAssoc
from SAGisXPlanung.XPlan.enums import XP_Bundeslaender
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt
from SAGisXPlanung.XPlan.types import GeometryType, Angle


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

    planungstraegerGKZ = Column(String(), info={'xplan_version': XPlanVersion.FIVE_THREE})
    planungstraeger = Column(String(), info={'xplan_version': XPlanVersion.FIVE_THREE})

    gemeinde = relationship("XP_Gemeinde", back_populates="lp_plans", secondary=XP_PlanXP_GemeindeAssoc,
                            doc='Gemeinde', info={
                                'form-type': 'inline'
                            })

    plangeber_id = Column(UUID(as_uuid=True), ForeignKey('xp_plangeber.id'),
                          info={'xplan_version': XPlanVersion.SIX})
    plangeber = relationship("XP_Plangeber", back_populates="lp_plans", doc='Plangeber', info={
                                'form-type': 'inline',
                                'xplan_version': XPlanVersion.SIX
                            })

    rechtsstand = Column(Enum(LP_Rechtsstand))
    aufstellungsbeschlussDatum = Column(Date())

    auslegungsDatum = Column(ARRAY(Date), info={'xplan_version': XPlanVersion.FIVE_THREE})
    tOeBbeteiligungsDatum = Column(ARRAY(Date), info={'xplan_version': XPlanVersion.FIVE_THREE})
    oeffentlichkeitsbeteiligungDatum = Column(ARRAY(Date), info={'xplan_version': XPlanVersion.FIVE_THREE})

    auslegungsStartDatum = Column(ARRAY(Date), info={'xplan_version': XPlanVersion.SIX})
    auslegungsEndDatum = Column(ARRAY(Date), info={'xplan_version': XPlanVersion.SIX})
    tOeBbeteiligungsStartDatum = Column(ARRAY(Date), info={'xplan_version': XPlanVersion.SIX})
    tOeBbeteiligungsEndDatum = Column(ARRAY(Date), info={'xplan_version': XPlanVersion.SIX})
    oeffentlichkeitsBetStartDatum = Column(ARRAY(Date), info={'xplan_version': XPlanVersion.SIX})
    oeffentlichkeitsBetEndDatum = Column(ARRAY(Date), info={'xplan_version': XPlanVersion.SIX})

    aenderungenBisDatum = Column(Date())
    entwurfsbeschlussDatum = Column(Date())
    planbeschlussDatum = Column(Date())
    inkrafttretenDatum = Column(Date())
    veroeffentlichungsDatum = Column(Date(), info={'xplan_version': XPlanVersion.SIX})
    sonstVerfahrensDatum = Column(Date())

    sonstVerfahrensText = Column(String(), info={'xplan_version': XPlanVersion.FIVE_THREE})
    startBedingungen = Column(String(), info={'xplan_version': XPlanVersion.FIVE_THREE})
    endeBedingungen = Column(String(), info={'xplan_version': XPlanVersion.FIVE_THREE})

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
    gehoertZuPlan = relationship('LP_Plan', back_populates='bereich',
                                 info={
                                     'link': 'xlink-only',
                                     'form-type': 'hidden'
                                 })

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        simple_line = QgsSimpleLineSymbolLayer.create({})
        symbol.appendSymbolLayer(simple_line)
        return QgsSingleSymbolRenderer(symbol)


class LP_Objekt(XP_Objekt):
    """ Basisklasse für alle spezifischen Inhalte eines Landschaftsplans """

    __tablename__ = 'lp_objekt'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }
    __readonly_columns__ = ['position']

    id = Column(ForeignKey("xp_objekt.id", ondelete='CASCADE'), primary_key=True)

    raumkonkretisierung = Column(Enum(LP_Raumkonkretisierung))
    rechtsCharText = Column(String)

    position = Column(Geometry(), CheckConstraint("GeometryType(position) NOT IN ('GEOMETRYCOLLECTION')",
                                                        name='prevent_geometry_collection'))
    flaechenschluss = Column(Boolean)
    flussrichtung = Column(Boolean)
    nordwinkel = Column(Angle)

    def srs(self):
        return QgsCoordinateReferenceSystem(f'EPSG:{self.position.srid}')

    def geometry(self):
        return geometry_from_spatial_element(self.position)

    def setGeometry(self, geom: QgsGeometry, srid: int = None):
        if srid is None and self.position is None:
            raise Exception('geometry needs a srid')
        self.position = WKTElement(geom.asWkt(), srid=srid or self.position.srid)

    def geomType(self) -> GeometryType:
        return self.geometry().type()

    @classmethod
    def hidden_inputs(cls):
        h = super(LP_Objekt, cls).hidden_inputs()
        return h + ['position']
