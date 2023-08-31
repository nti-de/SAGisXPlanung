import datetime
from uuid import uuid4

from lxml import etree
from sqlalchemy import Column, String, Enum, Date, ForeignKey, CheckConstraint, Boolean, Table, event
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, deferred

from SAGisXPlanung import Base, XPlanVersion
from SAGisXPlanung.XPlan.codelists import CodeList
from SAGisXPlanung.XPlan.core import XPCol
from SAGisXPlanung.XPlan.enums import XP_ExterneReferenzArt, XP_ExterneReferenzTyp, XP_SPEMassnahmenTypen, \
    XP_ArtHoehenbezug, XP_ArtHoehenbezugspunkt
from SAGisXPlanung.XPlan.mixins import RelationshipMixin, ElementOrderMixin, ElementOrderDeclarativeInheritanceFixMixin
from SAGisXPlanung.XPlan.types import RefURL, RegExString, ConformityException, LargeString, Length

XP_PlanXP_GemeindeAssoc = Table('xp_plan_gemeinde', Base.metadata,
    Column('bp_plan_id', UUID(as_uuid=True), ForeignKey('bp_plan.id', ondelete='CASCADE')),
    Column('fp_plan_id', UUID(as_uuid=True), ForeignKey('fp_plan.id', ondelete='CASCADE')),
    XPCol('lp_plan_id', UUID(as_uuid=True), ForeignKey('lp_plan.id', ondelete='CASCADE'), version=XPlanVersion.SIX),
    Column('gemeinde_id', UUID(as_uuid=True), ForeignKey('xp_gemeinde.id'))
)


class XP_Gemeinde(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation einer für die Aufstellung des Plans zuständigen Gemeinde. """

    __tablename__ = 'xp_gemeinde'
    __accessColumn__ = 'gemeindeName'  # column to access by name/string representation
    __avoidRelation__ = ['bp_plans', 'fp_plans']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    bp_plans = relationship("BP_Plan", back_populates="gemeinde", secondary=XP_PlanXP_GemeindeAssoc)
    fp_plans = relationship("FP_Plan", back_populates="gemeinde", secondary=XP_PlanXP_GemeindeAssoc)
    lp_plans = relationship("LP_Plan", back_populates="gemeinde", secondary=XP_PlanXP_GemeindeAssoc)

    ags = Column(RegExString(r'\d{8}\b', 8, error_msg='Gemeindeschlüssel muss aus 8 Ziffern bestehen'),
                 doc='Gemeindeschlüssel (AGS)')
    rs = Column(RegExString(r'\d{12}\b', 12, error_msg='Regionalschlüssel muss aus 12 Ziffern bestehen'),
                doc='Regionalschlüssel')
    gemeindeName = Column(String(), nullable=False, doc='Name der Gemeinde')
    ortsteilName = Column(String(), doc='Ortsteilbezeichnung')

    def __str__(self):
        return self.gemeindeName + f"{f', OT {self.ortsteilName}' if self.ortsteilName else ''}"

    def __eq__(self, other):
        if type(other) is type(self):
            return self.ags == other.ags and self.ortsteilName == other.ortsteilName
        return False

    def validate(self):
        if not self.ags and not self.rs:
            raise ConformityException('Die Attribute <code>ags</code> und <code>rs</code> dürfen nicht beide unbelegt sein',
                                      '3.2.5.1', self.__class__.__name__)


@event.listens_for(XP_Gemeinde, 'before_insert')
@event.listens_for(XP_Gemeinde, 'before_update')
def checkIntegrityXP_Gemeinde(mapper, connection, xp_gemeinde):
    if not xp_gemeinde.ags and not xp_gemeinde.rs:
        raise IntegrityError("Die Attribute 'ags' und 'rs' dürfen nicht beide unbelegt sein",
                             {
                                 'name': "Konsistenz  der  Attribute  ags  (Amtlicher  Gemeindeschlüssel)  und  rs  (Regionalschlüssel)",
                                 'nummer': '3.2.5.1'
                             },
                             xp_gemeinde)


class XP_ExterneReferenz(RelationshipMixin, ElementOrderMixin, Base):
    """ XP_ExterneReferenz

    Verweis auf ein extern gespeichertes Dokument oder einen extern gespeicherten, georeferenzierten Plan.
    Einer der beiden Attribute "referenzName" bzw. "referenzURL" muss belegt sein.
    """

    __tablename__ = 'xp_externe_referenz'
    __table_args__ = (
        CheckConstraint('NOT("referenzName" IS NULL AND "referenzURL" IS NULL)'),
    )
    __avoidRelation__ = ['bereich', 'baugebiet', 'bp_schutzflaeche_massnahme', 'bp_schutzflaeche_plan',
                         'veraenderungssperre']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    georefURL = Column(String, doc='Verweis auf Georeferenzierungs-Datei')
    art = Column(Enum(XP_ExterneReferenzArt), doc='Art der Referenz')
    referenzName = Column(String, nullable=False, doc='Name bzw. Titel')
    referenzURL = Column(RefURL, nullable=False, doc='URI der Referenz')
    referenzMimeType = Column(Enum(*CodeList.XP_MIME_TYPES, name="xp_mime_types"), doc='Dateityp')
    beschreibung = Column(LargeString, doc='Beschreibung')
    datum = Column(Date, doc='Datum')

    file = deferred(Column(BYTEA))

    bereich_id = Column(UUID(as_uuid=True), ForeignKey('xp_bereich.id', ondelete='CASCADE'))
    bereich = relationship("XP_Bereich", back_populates="refScan")

    baugebiet_id = Column(UUID(as_uuid=True), ForeignKey('bp_baugebiet.id', ondelete='CASCADE'))
    baugebiet = relationship("BP_BaugebietsTeilFlaeche", back_populates="refGebaeudequerschnitt")

    bp_schutzflaeche_massnahme_id = Column(UUID(as_uuid=True), ForeignKey('bp_schutzflaeche.id', ondelete='CASCADE'))
    bp_schutzflaeche_massnahme = relationship("BP_SchutzPflegeEntwicklungsFlaeche",
                                              foreign_keys=[bp_schutzflaeche_massnahme_id],
                                              back_populates="refMassnahmenText")

    bp_schutzflaeche_plan_id = Column(UUID(as_uuid=True), ForeignKey('bp_schutzflaeche.id', ondelete='CASCADE'))
    bp_schutzflaeche_plan = relationship("BP_SchutzPflegeEntwicklungsFlaeche", foreign_keys=[bp_schutzflaeche_plan_id],
                                         back_populates="refLandschaftsplan")

    veraenderungssperre_id = Column(UUID(as_uuid=True), ForeignKey('bp_veraenderungssperre_daten.id', ondelete='CASCADE'))
    veraenderungssperre = relationship("BP_VeraenderungssperreDaten", back_populates="refBeschluss")

    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'xp_externe_referenz',
        'polymorphic_on': type
    }

    def validate(self):
        if not self.referenzName and not self.referenzURL:
            raise ConformityException('Mindestens eines der Attribute <code>referenzName</code> und '
                                      '<code>referenzURL</code> muss belegt sein.',
                                      '3.2.4.2', self.__class__.__name__)

    @classmethod
    def hidden_inputs(cls):
        return ['file']

    @classmethod
    def avoid_export(cls):
        return ['file', 'baugebiet_id', 'bereich_id', 'bereich', 'bp_schutzflaeche_massnahme_id',
                'bp_schutzflaeche_plan_id', 'veraenderungssperre_id']


class XP_SpezExterneReferenz(XP_ExterneReferenz):
    """ Ergänzung des Datentyps XP_ExterneReferenz um ein Attribut zur semantischen Beschreibung des referierten Dokuments. """

    __tablename__ = 'xp_spez_externe_referenz'
    __mapper_args__ = {
        'polymorphic_identity': 'xp_spez_externe_referenz',
    }

    id = Column(ForeignKey("xp_externe_referenz.id", ondelete='CASCADE'), primary_key=True)

    typ = Column(Enum(XP_ExterneReferenzTyp), doc='Typ/Inhalt der Referenz')
    plan_id = Column(UUID(as_uuid=True), ForeignKey('xp_plan.id', ondelete='CASCADE'))
    plan = relationship("XP_Plan", back_populates="externeReferenz")

    @classmethod
    def avoid_export(cls):
        base = super(XP_SpezExterneReferenz, cls).avoid_export()
        return base + ['plan_id']


class XP_Plangeber(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Institution, die für den Plan verantwortlich ist. """

    __tablename__ = 'xp_plangeber'
    __accessColumn__ = 'name'
    __avoidRelation__ = ['bp_plans', 'fp_plans', 'lp_plans']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    bp_plans = relationship("BP_Plan", back_populates="plangeber")
    fp_plans = relationship("FP_Plan", back_populates="plangeber")
    lp_plans = relationship("LP_Plan", back_populates="plangeber")

    name = Column(String, nullable=False, doc='Name')
    kennziffer = Column(String, doc='Kennziffer')

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        return False


@event.listens_for(XP_Plangeber, 'before_insert')
@event.listens_for(XP_Plangeber, 'before_update')
def checkIntegrityXP_Plangeber(mapper, connection, xp_plangeber):
    if not xp_plangeber.name:
        raise IntegrityError("Das Attribut 'name' benötigt einen Wert", None, xp_plangeber)


class XP_VerfahrensMerkmal(RelationshipMixin, ElementOrderMixin, Base):
    """ Vermerk eines am Planungsverfahrens beteiligten Akteurs. """

    __tablename__ = "xp_verfahrens_merkmal"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('xp_plan.id', ondelete='CASCADE'))
    plan = relationship("XP_Plan", back_populates="verfahrensMerkmale")

    vermerk = Column(LargeString, nullable=False)
    datum = Column(Date, nullable=False)
    signatur = Column(String, nullable=False)
    signiert = Column(Boolean, nullable=False)

    @classmethod
    def avoid_export(cls):
        return ['plan_id']


class XP_SPEMassnahmenDaten(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Attribute für einer Schutz-, Pflege- oder Entwicklungsmaßnahme """

    __tablename__ = 'xp_spe_daten'
    __avoidRelation__ = ['bp_schutzflaeche']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    klassifizMassnahme = Column(Enum(XP_SPEMassnahmenTypen))
    massnahmeText = Column(String)
    massnahmeKuerzel = Column(String)

    bp_schutzflaeche_id = Column(UUID(as_uuid=True), ForeignKey('bp_schutzflaeche.id', ondelete='CASCADE'))
    bp_schutzflaeche = relationship('BP_SchutzPflegeEntwicklungsFlaeche', back_populates='massnahme')

    @classmethod
    def avoid_export(cls):
        return ['bp_schutzflaeche_id']


class XP_GesetzlicheGrundlage(RelationshipMixin, ElementOrderMixin, Base):
    """ Angeben zur Spezifikation der gesetzlichen Grundlage eines Planinhalts. """

    __tablename__ = 'xp_gesetzliche_grundlage'
    __avoidRelation__ = ['xp_objekts',
                         'fp_bau_nvo', 'fp_bau_gb', 'fp_bau_sonst',
                         'bp_bau_nvo', 'bp_bau_gb', 'bp_bau_sonst']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    xp_objekts = relationship("XP_Objekt", back_populates="gesetzlicheGrundlage")

    fp_bau_nvo = relationship("FP_Plan", back_populates="versionBauNVO", foreign_keys='FP_Plan.versionBauNVO_id')
    fp_bau_gb = relationship("FP_Plan", back_populates="versionBauGB", foreign_keys='FP_Plan.versionBauGB_id')
    fp_bau_sonst = relationship("FP_Plan", back_populates="versionSonstRechtsgrundlage",
                                foreign_keys='FP_Plan.versionSonstRechtsgrundlage_id')

    bp_bau_nvo = relationship("BP_Plan", back_populates="versionBauNVO", foreign_keys='BP_Plan.versionBauNVO_id')
    bp_bau_gb = relationship("BP_Plan", back_populates="versionBauGB", foreign_keys='BP_Plan.versionBauGB_id')
    bp_bau_sonst = relationship("BP_Plan", back_populates="versionSonstRechtsgrundlage",
                                foreign_keys='BP_Plan.versionSonstRechtsgrundlage_id')

    name = Column(String)
    datum = Column(Date)
    detail = Column(String)

    def __str__(self):
        return f'{self.name}, {self.datum}'

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name and str(self.datum) == str(other.datum)
        return False


class XP_Hoehenangabe(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation einer Angabe zur vertikalen Höhe oder zu einem Bereich vertikaler Höhen. Es ist möglich,
    spezifische Höhenangaben (z.B. die First- oder Traufhöhe eines Gebäudes) vorzugeben oder einzuschränken,
    oder den Gültigkeitsbereich eines Planinhalts auf eine bestimmte Höhe (hZwingend) bzw. einen Höhenbereich
    (hMin - hMax) zu beschränken, was vor allem bei der höhenabhängigen Festsetzung einer überbaubaren
    Grundstücksfläche (BP_UeberbaubareGrundstuecksflaeche), einer Baulinie (BP_Baulinie) oder einer Baugrenze
    (BP_Baugrenze) relevant ist. In diesem Fall bleiben die Attribute bezugspunkt und abweichenderBezugspunkt
    unbelegt """

    __tablename__ = 'xp_hoehenangabe'
    __avoidRelation__ = ['xp_objekt', 'dachgestaltung']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    abweichenderHoehenbezug = Column(String)
    hoehenbezug = Column(Enum(XP_ArtHoehenbezug))
    abweichenderBezugspunkt = Column(String)
    bezugspunkt = Column(Enum(XP_ArtHoehenbezugspunkt))
    hMin = Column(Length)
    hMax = Column(Length)
    hZwingend = Column(Length)
    h = Column(Length)

    xp_objekt_id = Column(UUID(as_uuid=True), ForeignKey('xp_objekt.id', ondelete='CASCADE'))
    xp_objekt = relationship("XP_Objekt", back_populates="hoehenangabe")

    dachgestaltung_id = XPCol(UUID(as_uuid=True), ForeignKey('bp_dachgestaltung.id', ondelete='CASCADE'),
                              version=XPlanVersion.SIX)
    dachgestaltung = relationship("BP_Dachgestaltung", back_populates="hoehenangabe")

    def to_xplan_node(self, node=None, version=XPlanVersion.FIVE_THREE):
        from SAGisXPlanung.GML.GMLWriter import GMLWriter

        this_node = etree.SubElement(node, f"{{{node.nsmap['xplan']}}}{self.__class__.__name__}")
        GMLWriter.write_attributes(this_node, self, version)
        return node

    @classmethod
    def avoid_export(cls):
        return ['xp_objekt_id', 'dachgestaltung_id']

    @classmethod
    def hidden_inputs(cls):
        return ['dachgestaltung']
