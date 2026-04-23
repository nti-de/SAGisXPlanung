import logging

from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import Column, Enum, String, Date, ARRAY, Boolean, ForeignKey, event, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship

from qgis.core import (QgsSimpleLineSymbolLayer, QgsSingleSymbolRenderer, QgsSymbol, QgsWkbTypes, QgsGeometry,
                       QgsCoordinateReferenceSystem, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.XPlan.conversions import BP_Rechtscharakter_EnumType
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.data_types import XP_PlanXP_GemeindeAssoc, XP_PlanXP_GesetzlicheGrundlageAssoc
from SAGisXPlanung.XPlan.enums import XP_VerlaengerungVeraenderungssperre
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt, XP_TextAbschnitt, xp_textabschnitt_assoc
from SAGisXPlanung.BPlan.BP_Basisobjekte.enums import BP_Verfahren, BP_Rechtsstand, BP_PlanArt, BP_Rechtscharakter
from SAGisXPlanung.XPlan.types import XPEnum, GeometryType

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

    planArt = Column(ARRAY(Enum(BP_PlanArt)),
                     CheckConstraint('"planArt" <> \'{}\' and array_position("planArt", null) is null',
                                     name='ck_planart_not_empty_no_nulls'),
                     nullable=False,
                     doc='Art des Planwerks')
    sonstPlanArt_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    sonstPlanArt = relationship("BP_SonstPlanArt", back_populates="bp_plans", foreign_keys=[sonstPlanArt_id], info={
                                'form-type': 'inline'
                                })

    verfahren = Column(XPEnum(BP_Verfahren, include_default=True), doc='Verfahren',
                       info={'xplan_version': XPlanVersion.FIVE_THREE})
    rechtsstand = Column(XPEnum(BP_Rechtsstand, include_default=True), doc='Rechtsstand')

    status_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    status = relationship("BP_Status", back_populates="bp_plans", foreign_keys=[status_id], info={
                              'form-type': 'inline'
                          })

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

    versionBauNVO_id = Column(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                             info={'xplan_version': XPlanVersion.SIX})
    versionBauNVO = relationship("XP_GesetzlicheGrundlage", back_populates="bp_bau_nvo",
                                 foreign_keys=[versionBauNVO_id],
                                 info={
                                    'xplan_version': XPlanVersion.SIX,
                                    'form-type': 'inline'
                                 })
    versionBauGB_id = Column(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                            info={'xplan_version': XPlanVersion.SIX})
    versionBauGB = relationship("XP_GesetzlicheGrundlage", back_populates="bp_bau_gb", foreign_keys=[versionBauGB_id],
                                info={
                                    'xplan_version': XPlanVersion.SIX,
                                    'form-type': 'inline'
                                })

    versionSonstRechtsgrundlage = relationship("XP_GesetzlicheGrundlage", back_populates="bp_bau_sonst",
                                               secondary=XP_PlanXP_GesetzlicheGrundlageAssoc,
                                               info={
                                                   'xplan_version': XPlanVersion.SIX,
                                                   'form-type': 'inline'
                                               })

    bereich = relationship("BP_Bereich", back_populates="gehoertZuPlan", cascade="all, delete", doc='Bereich')

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        symbol.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        dashed_border = QgsSimpleLineSymbolLayer.create({})
        dashed_border.setColor(QColor(0, 0, 0))
        dashed_border.setWidth(2)
        dashed_border.setOffset(-1)
        dashed_border.setPenStyle(Qt.PenStyle.DashLine)
        dashed_border.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.25)
        border.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        symbol.appendSymbolLayer(dashed_border)
        symbol.appendSymbolLayer(border)
        return QgsSingleSymbolRenderer(symbol)

    def _flaechenschluss_config(self) -> XP_Plan.FlaechenschlussConfig:
        from SAGisXPlanung.BPlan.BP_Sonstiges.feature_types import BP_FlaecheOhneFestsetzung

        return XP_Plan.FlaechenschlussConfig(
            class_type=BP_FlaecheOhneFestsetzung,
            rechtscharakter_enum=BP_Rechtscharakter,
        )

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
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
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

    # XP_TextAbschnitt [0..*] (v5.3)
    refTextInhalt = relationship("XP_TextAbschnitt",
        secondary=xp_textabschnitt_assoc,
        back_populates="bp_objekte",
        cascade="all, delete", passive_deletes=True,
        info={
            'xplan_version': XPlanVersion.FIVE_THREE,
            'link-type': 'abstract'
        })

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


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class BP_TextAbschnitt(XP_TextAbschnitt):
    """ Texlich formulierter Inhalt eines Bebauungsplans, der einen anderen Rechtscharakter als das zugrunde liegende
        Fachobjekt hat (Attribut rechtscharakter des Fachobjektes), oder dem Plan als Ganzes zugeordnet ist. """

    __tablename__ = 'bp_text_abschnitt'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }
    __avoidRelation__ = ['bp_baugebiet', 'bp_nebenanlagen_ausschluss_flaeche']

    id = Column(ForeignKey("xp_text_abschnitt.id", ondelete='CASCADE'), primary_key=True)

    rechtscharakter = Column(BP_Rechtscharakter_EnumType(BP_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    # BP_BaugebietsTeilFlaeche [0..*] (v5.3)
    bp_baugebiet_id = Column(UUID(as_uuid=True), ForeignKey('bp_baugebiet.id', ondelete='CASCADE'))
    bp_baugebiet = relationship("BP_BaugebietsTeilFlaeche", back_populates="abweichungText_v5",
                                foreign_keys=[bp_baugebiet_id],
                                info={'xplan_version': XPlanVersion.FIVE_THREE})

    # BP_NebenanlagenAusschlussFlaeche [0..*] (v5.3)
    bp_nebenanlagen_ausschluss_flaeche_id = Column(UUID(as_uuid=True),
                                                   ForeignKey('bp_nebenanlagen_ausschluss_flaeche.id',
                                                              ondelete='CASCADE'))
    bp_nebenanlagen_ausschluss_flaeche = relationship("BP_NebenanlagenAusschlussFlaeche",
                                                      back_populates="abweichungText_v5",
                                                      foreign_keys=[bp_nebenanlagen_ausschluss_flaeche_id],
                                                      info={'xplan_version': XPlanVersion.FIVE_THREE})

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
