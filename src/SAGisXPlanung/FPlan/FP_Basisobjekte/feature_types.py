from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSimpleLineSymbolLayer, QgsSingleSymbolRenderer,
                       QgsGeometry, QgsCoordinateReferenceSystem)

from sqlalchemy import Column, ForeignKey, Enum, String, Date, ARRAY, event, Boolean, types
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from geoalchemy2 import WKBElement, Geometry, WKTElement

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.enums import FP_PlanArt, FP_Verfahren, FP_Rechtsstand, FP_Rechtscharakter
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.XPlan.conversions import FP_Rechtscharakter_EnumType
from SAGisXPlanung.XPlan.core import XPCol
from SAGisXPlanung.XPlan.data_types import XP_PlanXP_GemeindeAssoc
from SAGisXPlanung.XPlan.enums import XP_Rechtscharakter
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.config import export_version


class FP_Plan(XP_Plan):
    """ Klasse zur Modellierung eines gesamten Flächennutzungsplans """

    def __init__(self):
        self.auslegungsEndDatum = []
        self.auslegungsStartDatum = []
        self.traegerbeteiligungsStartDatum = []
        self.traegerbeteiligungsEndDatum = []

    __tablename__ = 'fp_plan'
    __requiredRelationships__ = ["gemeinde"]
    __mapper_args__ = {
        'polymorphic_identity': 'fp_plan',
    }

    id = Column(ForeignKey("xp_plan.id", ondelete='CASCADE'), primary_key=True)

    gemeinde = relationship("XP_Gemeinde", back_populates="fp_plans", secondary=XP_PlanXP_GemeindeAssoc, doc='Gemeinde')

    plangeber_id = Column(UUID(as_uuid=True), ForeignKey('xp_plangeber.id'))
    plangeber = relationship("XP_Plangeber", back_populates="fp_plans", doc='Plangeber')

    planArt = Column(Enum(FP_PlanArt), nullable=False, doc='Art des Plans')
    # sonstPlanArt: FP_SonstPlanArt[0..1]
    sachgebiet = Column(String(), doc='Sachgebiet')
    verfahren = Column(Enum(FP_Verfahren), doc='Verfahren')
    rechtsstand = Column(Enum(FP_Rechtsstand), doc='Rechtsstand')
    # status: FP_Status[0..1]
    aufstellungsbeschlussDatum = Column(Date(), doc='Aufstellungsbeschlussdatum')
    auslegungsStartDatum = Column(ARRAY(Date), doc='Startdatum der Auslegung')
    auslegungsEndDatum = Column(ARRAY(Date), doc='Enddatum der Auslegung')
    traegerbeteiligungsStartDatum = Column(ARRAY(Date), doc='Start der Trägerbeteiligung')
    traegerbeteiligungsEndDatum = Column(ARRAY(Date), doc='Ende der Trägerbeteiligung')
    aenderungenBisDatum = Column(Date(), doc='Änderung bis')
    entwurfsbeschlussDatum = Column(Date(), doc='Datum des Entwurfsbeschluss')
    planbeschlussDatum = Column(Date(), doc='Datum des Planbeschlusses')
    wirksamkeitsDatum = Column(Date(), doc='Datum der Wirksamkeit')

    versionBauNVODatum = XPCol(Date(), doc='Datum der BauNVO', version=XPlanVersion.FIVE_THREE)
    versionBauNVOText = XPCol(String(), doc='Textl. Spezifikation der BauNVO', version=XPlanVersion.FIVE_THREE)
    versionBauGBDatum = XPCol(Date(), doc='Datum des BauGB', version=XPlanVersion.FIVE_THREE)
    versionBauGBText = XPCol(String(), doc='Textl. Spezifikation des BauGB', version=XPlanVersion.FIVE_THREE)
    versionSonstRechtsgrundlageDatum = XPCol(Date(), doc='Datum sonst. Rechtsgrundlage', version=XPlanVersion.FIVE_THREE)
    versionSonstRechtsgrundlageText = XPCol(String(), doc='Textl. Spezifikation sonst. Rechtsgrundlage', version=XPlanVersion.FIVE_THREE)

    versionBauNVO_id = XPCol(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                             version=XPlanVersion.SIX, attribute='versionBauNVO')
    versionBauNVO = relationship("XP_GesetzlicheGrundlage", back_populates="fp_bau_nvo", foreign_keys=[versionBauNVO_id])
    versionBauGB_id = XPCol(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                            version=XPlanVersion.SIX, attribute='versionBauGB')
    versionBauGB = relationship("XP_GesetzlicheGrundlage", back_populates="fp_bau_gb", foreign_keys=[versionBauGB_id])
    versionSonstRechtsgrundlage_id = XPCol(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                                           version=XPlanVersion.SIX, attribute='versionSonstRechtsgrundlage')
    versionSonstRechtsgrundlage = relationship("XP_GesetzlicheGrundlage", back_populates="fp_bau_sonst",
                                               foreign_keys=[versionSonstRechtsgrundlage_id])

    bereich = relationship("FP_Bereich", back_populates="gehoertZuPlan", cascade="all, delete", doc='Bereich')

    @classmethod
    def avoid_export(cls):
        return ['plangeber_id', 'versionBauNVO_id', 'versionBauGB_id', 'versionSonstRechtsgrundlage_id']

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.8)
        line.setPenStyle(Qt.SolidLine)

        symbol.appendSymbolLayer(line)
        return QgsSingleSymbolRenderer(symbol)


@event.listens_for(FP_Plan, 'before_insert')
@event.listens_for(FP_Plan, 'before_update')
def checkIntegrity(mapper, connection, xp_plan):
    if not xp_plan.gemeinde:
        raise IntegrityError("Planwerk benötigt mindestens eine Gemeinde", None, xp_plan)
    if not xp_plan.raeumlicherGeltungsbereich:
        raise IntegrityError('Planwerk benötigt mindestens einen Geltungsbereich!', None, xp_plan)


class FP_Bereich(XP_Bereich):
    """ Diese Klasse modelliert einen Bereich eines Flächennutzungsplans """

    __tablename__ = 'fp_bereich'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_bereich',
    }

    id = Column(ForeignKey("xp_bereich.id", ondelete='CASCADE'), primary_key=True)

    gehoertZuPlan_id = Column(UUID(as_uuid=True), ForeignKey('fp_plan.id', ondelete='CASCADE'))
    gehoertZuPlan = relationship('FP_Plan', back_populates='bereich')


class FP_Objekt(XP_Objekt):
    """ Basisklasse für alle Fachobjekte des Flächennutzungsplans """

    __tablename__ = 'fp_objekt'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_objekt',
    }
    __readonly_columns__ = ['position']

    id = Column(ForeignKey("xp_objekt.id", ondelete='CASCADE'), primary_key=True)

    rechtscharakter = XPCol(FP_Rechtscharakter_EnumType(FP_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                            version=XPlanVersion.FIVE_THREE)
    vonGenehmigungAusgenommen = Column(Boolean)

    position = Column(Geometry())
    flaechenschluss = Column(Boolean, doc='Flächenschluss')

    def __getattribute__(self, name):
        if name == 'rechtscharakter' and export_version() == XPlanVersion.FIVE_THREE:
            super_value = super().__getattribute__(name)
            if isinstance(super_value, XP_Rechtscharakter):
                return super_value.to_fp_rechtscharakter()
            return super_value
        else:
            return super().__getattribute__(name)

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
        h = super(FP_Objekt, cls).hidden_inputs()
        return h + ['position']