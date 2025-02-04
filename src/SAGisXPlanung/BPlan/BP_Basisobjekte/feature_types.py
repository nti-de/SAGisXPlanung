import logging
import uuid

from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import Column, Enum, String, Date, ARRAY, Boolean, ForeignKey, event, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, declared_attr

from qgis.core import (QgsSimpleLineSymbolLayer, QgsSingleSymbolRenderer, QgsSymbol, QgsWkbTypes, QgsGeometry,
                       QgsCoordinateReferenceSystem, QgsProject, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.XPlan.conversions import BP_Rechtscharakter_EnumType
from SAGisXPlanung.XPlan.core import XPCol
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.data_types import XP_PlanXP_GemeindeAssoc
from SAGisXPlanung.XPlan.enums import XP_VerlaengerungVeraenderungssperre
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt
from SAGisXPlanung.BPlan.BP_Basisobjekte.enums import BP_Verfahren, BP_Rechtsstand, BP_PlanArt, BP_Rechtscharakter
from SAGisXPlanung.XPlan.types import XPEnum, GeometryType
from SAGisXPlanung.XPlanungItem import XPlanungItem

logger = logging.getLogger(__name__)


class BP_Plan(XP_Plan):
    """ Die Klasse modelliert einen Bebauungsplan. """

    def __init__(self):
        self.auslegungsEndDatum = []
        self.auslegungsStartDatum = []
        self.traegerbeteiligungsStartDatum = []
        self.traegerbeteiligungsEndDatum = []

    __tablename__ = 'bp_plan'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_plan',
    }

    id = Column(ForeignKey("xp_plan.id", ondelete='CASCADE'), primary_key=True)

    gemeinde = relationship("XP_Gemeinde", back_populates="bp_plans", secondary=XP_PlanXP_GemeindeAssoc,
                            doc='Gemeinde', info={
                                'form-type': 'inline',
                                'nullable': False
                            })

    plangeber_id = Column(UUID(as_uuid=True), ForeignKey('xp_plangeber.id'))
    plangeber = relationship("XP_Plangeber", back_populates="bp_plans", doc='Plangeber', info={
                                'form-type': 'inline'
                            })

    planArt = Column(Enum(BP_PlanArt), nullable=False, doc='Art des Planwerks')
    # sonstPlanArt: BP_SonstPlanArt[0..1]
    verfahren = Column(Enum(BP_Verfahren), doc='Verfahren', info={'xplan_version': XPlanVersion.FIVE_THREE})
    rechtsstand = Column(Enum(BP_Rechtsstand), doc='Rechtsstand')
    # status: BP_Status[0..1]
    hoehenbezug = Column(String(), doc='Höhenbezug', info={'xplan_version': XPlanVersion.FIVE_THREE})
    aenderungenBisDatum = Column(Date(), doc='Änderungen bis')
    aufstellungsbeschlussDatum = Column(Date(), doc='Aufstellungsbeschlussdatum')

    veraenderungssperreBeschlussDatum = Column(Date(), doc='Beschlussdatum der Veränderungssperre',
                                               info={'xplan_version': XPlanVersion.FIVE_THREE})
    veraenderungssperreDatum = Column(Date(), doc='Beginn der Veränderungssperre',
                                      info={'xplan_version': XPlanVersion.FIVE_THREE})
    veraenderungssperreEndDatum = Column(Date(), doc='Ende der Veränderungssperre',
                                         info={'xplan_version': XPlanVersion.FIVE_THREE})
    verlaengerungVeraenderungssperre = Column(XPEnum(XP_VerlaengerungVeraenderungssperre, include_default=True),
                                              doc='Verlängerung der Veränderungssperre',
                                              info={'xplan_version': XPlanVersion.FIVE_THREE})

    rel_veraenderungssperre = relationship("BP_VeraenderungssperreDaten", back_populates="plan",
                                           cascade="all, delete", passive_deletes=True, uselist=False,
                                           info={
                                               'xplan_version': XPlanVersion.SIX,
                                               'xplan_attribute': 'veraenderungssperre'
                                           })

    auslegungsStartDatum = Column(ARRAY(Date), doc='Startdatum des Auslegungszeitraums')
    auslegungsEndDatum = Column(ARRAY(Date), doc='Enddatum des Auslegungszeitraums')
    traegerbeteiligungsStartDatum = Column(ARRAY(Date), doc='Startdatum der Trägerbeteiligung')
    traegerbeteiligungsEndDatum = Column(ARRAY(Date), doc='Enddatum der Trägerbeteiligung')
    satzungsbeschlussDatum = Column(Date(), doc='Datum des Satzungsbeschlusses')
    rechtsverordnungsDatum = Column(Date(), doc='Datum der Rechtsverordnung')
    inkrafttretensDatum = Column(Date(), doc='Datum des Inkrafttretens')
    ausfertigungsDatum = Column(Date(), doc='Datum der Ausfertigung')

    veraenderungssperre = Column(Boolean, doc='Veränderungssperre?', info={'xplan_version': XPlanVersion.FIVE_THREE})

    staedtebaulicherVertrag = Column(Boolean, doc='städtebaulicher Vertrag?')
    erschliessungsVertrag = Column(Boolean, doc='Erschließungsvertrag?')
    durchfuehrungsVertrag = Column(Boolean, doc='Durchführungsvertrag?')
    gruenordnungsplan = Column(Boolean, doc='Grünordnungsplan?')

    versionBauNVODatum = Column(Date(), doc='Datum der BauNVO',
                                info={'xplan_version': XPlanVersion.FIVE_THREE})
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

    versionBauNVO_id = XPCol(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                             info={'xplan_version': XPlanVersion.SIX}, attribute='versionBauNVO')
    versionBauNVO = relationship("XP_GesetzlicheGrundlage", back_populates="bp_bau_nvo",
                                 foreign_keys=[versionBauNVO_id],
                                 info={
                                    'xplan_version': XPlanVersion.SIX,
                                    'form-type': 'inline'
                                 })
    versionBauGB_id = XPCol(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                            info={'xplan_version': XPlanVersion.SIX}, attribute='versionBauGB')
    versionBauGB = relationship("XP_GesetzlicheGrundlage", back_populates="bp_bau_gb", foreign_keys=[versionBauGB_id],
                                info={
                                    'xplan_version': XPlanVersion.SIX,
                                    'form-type': 'inline'
                                })
    versionSonstRechtsgrundlage_id = XPCol(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                                           info={'xplan_version': XPlanVersion.SIX},
                                           attribute='versionSonstRechtsgrundlage')
    versionSonstRechtsgrundlage = relationship("XP_GesetzlicheGrundlage", back_populates="bp_bau_sonst",
                                               foreign_keys=[versionSonstRechtsgrundlage_id],
                                               info={
                                                   'xplan_version': XPlanVersion.SIX,
                                                   'form-type': 'inline'
                                               })

    bereich = relationship("BP_Bereich", back_populates="gehoertZuPlan", cascade="all, delete", doc='Bereich')

    @classmethod
    def avoid_export(cls):
        return super().avoid_export() + ['plangeber_id', 'versionBauNVO_id', 'versionBauGB_id',
                                        'versionSonstRechtsgrundlage_id']

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        symbol.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        dashed_border = QgsSimpleLineSymbolLayer.create({})
        dashed_border.setColor(QColor(0, 0, 0))
        dashed_border.setWidth(2)
        dashed_border.setOffset(-1)
        dashed_border.setPenStyle(Qt.DashLine)
        dashed_border.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.25)
        border.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        symbol.appendSymbolLayer(dashed_border)
        symbol.appendSymbolLayer(border)
        return QgsSingleSymbolRenderer(symbol)

    def enforceFlaechenschluss(self):
        from SAGisXPlanung.BPlan.BP_Sonstiges.feature_types import BP_FlaecheOhneFestsetzung

        geltungsbereich_geom = self.geometry()
        results = []

        for bereich in self.bereich:  # type: BP_Bereich
            # 1. build union of all flaechenschluss objects (without BP_FlaecheOhneFestsetzung)
            flaechenschluss_geoms = [p.geometry() for p in bereich.planinhalt
                                     if p.flaechenschluss and not isinstance(p, BP_FlaecheOhneFestsetzung)]
            combined = QgsGeometry.unaryUnion(flaechenschluss_geoms)

            # fill difference of 1. and Geltungsbereich with BP_FlaecheOhneFestsetzung
            diff = geltungsbereich_geom.difference(combined)

            areas_without_usage = [p for p in bereich.planinhalt if p.type == 'bp_flaeche_ohne_festsetzung']
            if areas_without_usage:
                fl = areas_without_usage[0]
                fl.setGeometry(diff, srid=QgsProject.instance().crs().postgisSrid())
            else:
                fl = BP_FlaecheOhneFestsetzung()
                fl.id = uuid.uuid4()
                fl.flaechenschluss = True
                fl.rechtscharakter = BP_Rechtscharakter.Unbekannt
                fl.setGeometry(diff, srid=QgsProject.instance().crs().postgisSrid())
                bereich.planinhalt.append(fl)

            results.append(XPlanungItem(xtype=fl.__class__, xid=str(fl.id), parent_xid=str(bereich.id)))

        return results


@event.listens_for(BP_Plan, 'before_insert')
@event.listens_for(BP_Plan, 'before_update')
def checkIntegrity(mapper, connection, xp_plan):
    if not xp_plan.gemeinde:
        raise IntegrityError("Planwerk benötigt mindestens eine Gemeinde", None, xp_plan)
    if not xp_plan.raeumlicherGeltungsbereich:
        raise IntegrityError('Planwerk benötigt mindestens einen Geltungsbereich!', None, xp_plan)


class BP_Bereich(XP_Bereich):
    """ Diese Klasse modelliert einen Bereich eines Bebauungsplans, z.B. einen räumlichen oder sachlichen
    Teilbereich. """

    __tablename__ = 'bp_bereich'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_bereich',
    }

    id = Column(ForeignKey("xp_bereich.id", ondelete='CASCADE'), primary_key=True)

    verfahren = Column(Enum(BP_Verfahren), doc='Verfahren', info={'xplan_version': XPlanVersion.SIX})

    versionBauGBDatum = Column(Date(), doc='Datum des BauGB', info={'xplan_version': XPlanVersion.FIVE_THREE})
    versionBauGBText = Column(String(), doc='Textl. Spezifikation des BauGB',
                              info={'xplan_version': XPlanVersion.FIVE_THREE})
    versionSonstRechtsgrundlageDatum = Column(Date(), doc='Datum sonst. Rechtsgrundlage',
                                              info={'xplan_version': XPlanVersion.FIVE_THREE})
    versionSonstRechtsgrundlageText = Column(String(), doc='Textl. Spezifikation sonst. Rechtsgrundlage',
                                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    gehoertZuPlan_id = Column(UUID(as_uuid=True), ForeignKey('bp_plan.id', ondelete='CASCADE'))
    gehoertZuPlan = relationship('BP_Plan', back_populates='bereich', info={
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


class BP_Objekt(XP_Objekt):
    """ Basisklasse für alle raumbezogenen Festsetzungen, Hinweise, Vermerke und Kennzeichnungen eines  Bebauungsplans """

    __tablename__ = 'bp_objekt'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_objekt',
    }
    __readonly_columns__ = ['position']

    id = Column(ForeignKey("xp_objekt.id", ondelete='CASCADE'), primary_key=True)

    rechtscharakter = Column(BP_Rechtscharakter_EnumType(BP_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    position = Column(Geometry(), CheckConstraint("GeometryType(position) NOT IN ('GEOMETRYCOLLECTION')",
                                                        name='prevent_geometry_collection'))
    flaechenschluss = Column(Boolean, doc='Flächenschluss')

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
        h = super(BP_Objekt, cls).hidden_inputs()
        return h + ['position']
