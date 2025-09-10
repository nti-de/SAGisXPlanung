from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSimpleLineSymbolLayer, QgsSingleSymbolRenderer,
                       QgsGeometry, QgsCoordinateReferenceSystem)

from sqlalchemy import Column, ForeignKey, Enum, String, Date, ARRAY, event, Boolean, types, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from geoalchemy2 import WKBElement, Geometry, WKTElement

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.enums import FP_PlanArt, FP_Verfahren, FP_Rechtsstand, FP_Rechtscharakter
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.XPlan.conversions import FP_Rechtscharakter_EnumType
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.data_types import XP_PlanXP_GemeindeAssoc, XP_PlanXP_GesetzlicheGrundlageAssoc
from SAGisXPlanung.XPlan.enums import XP_Rechtscharakter
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt, XP_TextAbschnitt
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
    __mapper_args__ = {
        'polymorphic_identity': 'fp_plan',
    }

    id = Column(ForeignKey("xp_plan.id", ondelete='CASCADE'), primary_key=True)

    gemeinde = relationship("XP_Gemeinde", back_populates="fp_plans", secondary=XP_PlanXP_GemeindeAssoc,
                            doc='Gemeinde', info={
                                'form-type': 'inline',
                                'nullable': False
                            })

    plangeber_id = Column(UUID(as_uuid=True), ForeignKey('xp_plangeber.id'))
    plangeber = relationship("XP_Plangeber", back_populates="fp_plans", doc='Plangeber', info={
                                'form-type': 'inline'
                            })

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

    versionBauNVODatum = Column(Date(), doc='Datum der BauNVO', info={'xplan_version': XPlanVersion.FIVE_THREE})
    versionBauNVOText = Column(String(), doc='Textl. Spezifikation der BauNVO',
                               info={'xplan_version': XPlanVersion.FIVE_THREE})
    versionBauGBDatum = Column(Date(), doc='Datum des BauGB',
                               info={'xplan_version': XPlanVersion.FIVE_THREE})
    versionBauGBText = Column(String(), doc='Textl. Spezifikation des BauGB',
                              info={'xplan_version': XPlanVersion.FIVE_THREE})
    versionSonstRechtsgrundlageDatum = Column(Date(), doc='Datum sonst. Rechtsgrundlage',
                                              info={'xplan_version': XPlanVersion.FIVE_THREE})
    versionSonstRechtsgrundlageText = Column(String(), doc='Textl. Spezifikation sonst. Rechtsgrundlage',
                                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    versionBauNVO_id = Column(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                             info={'xplan_version': XPlanVersion.SIX})
    versionBauNVO = relationship("XP_GesetzlicheGrundlage", back_populates="fp_bau_nvo",
                                 foreign_keys=[versionBauNVO_id], info={
                                    'xplan_version': XPlanVersion.SIX,
                                    'form-type': 'inline'
                                 })
    versionBauGB_id = Column(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                            info={'xplan_version': XPlanVersion.SIX})
    versionBauGB = relationship("XP_GesetzlicheGrundlage", back_populates="fp_bau_gb", foreign_keys=[versionBauGB_id],
                                info={
                                    'xplan_version': XPlanVersion.SIX,
                                    'form-type': 'inline'
                                })

    versionSonstRechtsgrundlage = relationship("XP_GesetzlicheGrundlage", back_populates="fp_bau_sonst",
                                               secondary=XP_PlanXP_GesetzlicheGrundlageAssoc,
                                               info={
                                                   'xplan_version': XPlanVersion.SIX,
                                                   'form-type': 'inline'
                                               })

    bereich = relationship("FP_Bereich", back_populates="gehoertZuPlan", cascade="all, delete", doc='Bereich')

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
    gehoertZuPlan = relationship('FP_Plan', back_populates='bereich', info={
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


class FP_Objekt(XP_Objekt):
    """ Basisklasse für alle Fachobjekte des Flächennutzungsplans """

    __tablename__ = 'fp_objekt'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_objekt',
    }
    __readonly_columns__ = ['position']

    id = Column(ForeignKey("xp_objekt.id", ondelete='CASCADE'), primary_key=True)

    rechtscharakter = Column(FP_Rechtscharakter_EnumType(FP_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    # XP_TextAbschnitt [0..*] (v5.3)
    refTextInhalt = relationship("XP_TextAbschnitt", back_populates="fp_objekt",
                                 cascade="all, delete", passive_deletes=True,
                                 info={'xplan_version': XPlanVersion.FIVE_THREE})

    vonGenehmigungAusgenommen = Column(Boolean)

    position = Column(Geometry(), CheckConstraint("GeometryType(position) NOT IN ('GEOMETRYCOLLECTION')",
                                                        name='prevent_geometry_collection'))
    flaechenschluss = Column(Boolean, doc='Flächenschluss')

    # TODO: why was this required in the first place? there is nothing similar for BP?
    # def __getattribute__(self, name):
    #     if name == 'rechtscharakter' and export_version() == XPlanVersion.FIVE_THREE:
    #         super_value = super().__getattribute__(name)
    #         if isinstance(super_value, XP_Rechtscharakter):
    #             return super_value.to_fp_rechtscharakter()
    #         return super_value
    #     else:
    #         return super().__getattribute__(name)

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


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class FP_TextAbschnitt(XP_TextAbschnitt):
    """ Texlich formulierter Inhalt eines Flächennutzungsplans, der einen anderen Rechtscharakter als das zugrunde
        liegende Fachobjekt hat (Attribut rechtscharakter des Fachobjektes), oder dem Plan als Ganzes zugeordnet ist """

    __tablename__ = 'fp_text_abschnitt'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("xp_text_abschnitt.id", ondelete='CASCADE'), primary_key=True)

    rechtscharakter = Column(FP_Rechtscharakter_EnumType(FP_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
