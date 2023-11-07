import uuid
from dataclasses import dataclass, field
from typing import List

from geoalchemy2 import WKTElement
from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterFile, QgsProcessingException)
from qgis.utils import iface
from shapely import wkt
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity
from sqlalchemy import create_engine, text
from sqlalchemy.event import listen

from SAGisXPlanung.BPlan.BP_Basisobjekte.enums import BP_PlanArt, BP_Rechtscharakter
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan, BP_Bereich
from SAGisXPlanung.BPlan.BP_Bebauung.enums import BP_BebauungsArt
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche, BP_BauGrenze, BP_BauLinie
from SAGisXPlanung.BPlan.BP_Gemeinbedarf_Spiel_und_Sportanlagen.feature_types import (BP_GemeinbedarfsFlaeche,
                                                                                      BP_SpielSportanlagenFlaeche)
from SAGisXPlanung.BPlan.BP_Landwirtschaft_Wald_und_Gruenflaechen.feature_types import BP_GruenFlaeche
from SAGisXPlanung.BPlan.BP_Naturschutz_Landschaftsbild_Naturhaushalt.feature_types import (BP_AnpflanzungBindungErhaltung,
                                                                                            BP_SchutzPflegeEntwicklungsFlaeche)
from SAGisXPlanung.BPlan.BP_Ver_und_Entsorgung.feature_types import BP_VerEntsorgung
from SAGisXPlanung.BPlan.BP_Verkehr.enums import BP_ZweckbestimmungStrassenverkehr
from SAGisXPlanung.BPlan.BP_Verkehr.feature_types import BP_StrassenVerkehrsFlaeche, BP_StrassenbegrenzungsLinie, \
    BP_VerkehrsflaecheBesondererZweckbestimmung
from SAGisXPlanung.BPlan.BP_Wasser.feature_types import BP_GewaesserFlaeche
from SAGisXPlanung.XPlan.data_types import XP_Gemeinde
from SAGisXPlanung.XPlan.enums import (XP_BedeutungenBereich, XP_ZweckbestimmungVerEntsorgung, XP_ZweckbestimmungGruen,
                                       XP_AllgArtDerBaulNutzung, XP_ABEMassnahmenTypen,
                                       XP_AnpflanzungBindungErhaltungsGegenstand,
                                       XP_BesondereArtDerBaulNutzung, XP_ZweckbestimmungGemeinbedarf,
                                       XP_ZweckbestimmungSpielSportanlage, XP_ZweckbestimmungGewaesser)
from SAGisXPlanung.XPlan.feature_types import XP_Objekt
from SAGisXPlanung.gui.widgets.QPlanComboBox import QPlanComboBox
from SAGisXPlanung.utils import query_existing, save_to_db


class ImportCivil3DAlgorithm(QgsProcessingAlgorithm):
    """
    Verarbeitungswerkzeug zum Importieren von Planwerken aus Civil3D
    """

    INPUT_FILE = 'INPUT_FILE'

    def createInstance(self):
        return ImportCivil3DAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'importcivil3d'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'Aus Civil3D importieren (.sqlite)'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return 'Import'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'sagis-xplanung-import'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return 'Ein Planwerk aus Civil3D in die XPlanung Datenbank einlesen.'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_FILE,
                'Eingabedatei (.sqlite)',
                extension='sqlite'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        input_path = self.parameterAsString(parameters, self.INPUT_FILE, context)

        if not input_path:
            feedback.reportError('Eingabedatei nicht gefunden', True)
            return {}

        engine = create_engine(f'sqlite:///{input_path}')
        listen(engine, 'connect', load_spatialite)

        with engine.connect() as conn:

            spatiallite_version = conn.execute(text("SELECT spatialite_version() as version;")).scalar_one()
            feedback.pushInfo(f"Spatialite Version: {spatiallite_version}")

            plan_ids = conn.execute(text("SELECT id FROM civil_plan"))
            for row in plan_ids:
                feedback.pushInfo(f"Plan mit id {row.id} wird importiert...")
                plan = self.processPlan(row.id, conn, feedback)

                save_to_db(plan)

        return {}

    def processPlan(self, plan_xid, conn, feedback) -> BP_Plan:
        plan = BP_Plan()
        plan.id = plan_xid

        s = text("SELECT art, gemeinde_id, name  FROM civil_plan WHERE id = :xid")
        res = conn.execute(s, {"xid": plan_xid}).first()

        gemeinde = self.processGemeinde(res.gemeinde_id, conn, feedback)
        plan.gemeinde.append(gemeinde)

        plan.name = res.name
        plan.planArt = BP_PlanArt[res.art]

        # RemoveRepeatedPoints does not remove duplicated points from geometry column directly, most likely a bug???
        # dump to wkt and create new geometry as workaround
        s = text("SELECT ST_AsText(RemoveRepeatedPoints(ST_GeomFromText(ST_AsText(ST_Multi(u.geometry))))) AS g, ST_SRID(u.geometry) AS srid FROM "
                 "(SELECT ST_Union(geom) AS geometry FROM civil_line WHERE plan_id = :xid AND layer LIKE "
                 "'%15.13-Geltungsbereich%') u;")
        res = conn.execute(s, {"xid": plan_xid}).first()
        srid = res.srid

        s = text("SELECT auth_name FROM spatial_ref_sys WHERE srid = :srid")
        crs_name = conn.execute(s, {"srid": srid}).scalar_one()
        feedback.pushInfo(f'Koordinatenbezug: {crs_name}:{srid}')

        geometry = wkt.loads(res.g)
        if not geometry.is_valid:
            raise QgsProcessingException(f'Geometrie ist nicht gültig: {explain_validity(geometry)}')

        if geometry.is_empty or geometry is None:
            raise QgsProcessingException(f'Geometrie des Geltungsbereich ist leer.')

        geltungsbereich_polygons = []
        for line in geometry.geoms:
            if not line.is_ring:
                raise QgsProcessingException(f'Geltungsbereich ist kein geschlossener Umring')

            geltungsbereich_polygons.append(Polygon(line))

        geltungsbereich_geom = MultiPolygon(geltungsbereich_polygons)
        plan.raeumlicherGeltungsbereich = WKTElement(geltungsbereich_geom.wkt, srid=srid)

        mappings = {"civil_area": CIVIL_STYLE_AREAS, "civil_point": CIVIL_STYLE_POINTS, "civil_line": CIVIL_STYLE_LINES}
        for i, bereich_poly in enumerate(geltungsbereich_polygons):
            bereich = BP_Bereich()
            bereich.id = uuid.uuid4()
            bereich.name = 'Geltungsbereich'
            bereich.nummer = i + 1
            bereich.bedeutung = XP_BedeutungenBereich.Teilbereich
            bereich.geltungsbereich = WKTElement(bereich_poly.wkt, srid=srid)

            plan.bereich.append(bereich)

            for table, mapper in mappings.items():
                s = text(f"SELECT id FROM {table} WHERE plan_id = :xid AND ST_INTERSECTS(geom, ST_GeomFromText(:wkt))")
                res = conn.execute(s, {"xid": plan_xid, "wkt": bereich_poly.wkt})
                for row in res:
                    feedback.pushDebugInfo(f"Verarbeitung des Planinhalts: {row.id}")
                    planinhalt = self.processPlaninhalt(row.id, table, mapper, conn, feedback)
                    if planinhalt:
                        bereich.planinhalt.append(planinhalt)

        return plan

    def processPlaninhalt(self, planinhalt_xid, table, mapper, conn, feedback) -> XP_Objekt:
        # RemoveRepeatedPoints does not remove duplicated points from geometry column directly, most likely a bug???
        # dump to wkt and create new geometry as workaround
        s = text(f"SELECT layer, rechtscharakter, ST_AsText(RemoveRepeatedPoints(ST_GeomFromText(ST_AsText(geom)))) AS g, ST_SRID(geom) AS srid FROM {table} WHERE id = :xid")
        res = conn.execute(s, {"xid": planinhalt_xid}).first()

        # for each civil-styleid, check if the id is in the layer string, if yes create the corresponding object
        for civil_style in mapper:
            if civil_style.civil_id not in res.layer:
                continue

            # create instance and assign mandatory attributes
            bp_objekt = civil_style.createInstance()
            bp_objekt.rechtscharakter = BP_Rechtscharakter[res.rechtscharakter]

            # parse and assign geometry
            geometry = wkt.loads(res.g)
            if not geometry.is_valid:
                raise QgsProcessingException(f'Geometrie ist nicht gültig: {explain_validity(geometry)}')
            bp_objekt.position = WKTElement(geometry.wkt, srid=res.srid)
            if civil_style.property_table == PARCEL_TABLE:
                bp_objekt.flaechenschluss = True

            # parse properties from Civil3D
            if civil_style.civil_properties:
                s = text(f"SELECT name, value FROM {civil_style.property_table.table_name} WHERE {civil_style.property_table.id_column} = :xid")
                res = conn.execute(s, {"xid": planinhalt_xid})
                for row in res:
                    for civil_prop in civil_style.civil_properties:
                        if civil_prop.civil_id not in row.name:
                            continue

                        if row.value in (None, ''):
                            continue
                        if civil_prop.enum_value:
                            if row.value == 'True':  # note the string comparison here; values from sqlite are string
                                setattr(bp_objekt, civil_prop.xplanung_attribute, civil_prop.enum_value)
                            continue

                        setattr(bp_objekt, civil_prop.xplanung_attribute, row.value)

            return bp_objekt

    def processGemeinde(self, gemeinde_xid, conn, feedback) -> XP_Gemeinde:
        gemeinde = XP_Gemeinde()
        gemeinde.id = gemeinde_xid

        s = text("SELECT * FROM civil_gemeinde WHERE id = :xid")
        res = conn.execute(s, {"xid": gemeinde_xid}).first()
        feedback.pushInfo(f"Gemeindeschlüssel: {res.ags} Gemeindename: {res.gemeindeName}")

        gemeinde.ags = res.ags
        gemeinde.rs = res.rs
        gemeinde.gemeindeName = res.gemeindeName
        gemeinde.ortsteilName = res.ortsteilName

        # find if gemeinde already exists in database
        existing_gemeinde = query_existing(gemeinde)

        return existing_gemeinde or gemeinde

    def postProcessAlgorithm(self, context, feedback):
        # refresh plan combobox in post-processing
        cb = iface.mainWindow().findChild(QPlanComboBox)
        if cb is None:
            return {}

        prev_id = cb.currentPlanId()
        cb.refresh()
        cb.setCurrentPlan(prev_id)

        return {}

    def translateProgress(self, value, left_min, left_max, right_min, right_max):
        # Figure out how 'wide' each range is
        leftSpan = left_max - left_min
        rightSpan = right_max - right_min

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - left_min) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return right_min + (valueScaled * rightSpan)


def load_spatialite(connection, _):
    connection.enable_load_extension(True)
    connection.execute("SELECT load_extension('mod_spatialite')")
    connection.enable_load_extension(False)


@dataclass
class CivilProperty:
    civil_id: str
    xplanung_attribute: str
    is_array_type: bool = False
    enum_value: object = None


@dataclass
class CivilPropertyTable:
    table_name: str
    id_column: str


PARCEL_TABLE = CivilPropertyTable("parcel_properties", "parcel_id")
LINE_TABLE = CivilPropertyTable("line_properties", "line_id")
POINT_TABLE = CivilPropertyTable("point_properties", "point_id")


@dataclass
class CivilStyle:
    civil_id: str
    xtype: type
    property_table: CivilPropertyTable
    civil_properties: List[CivilProperty] = field(default_factory=list)
    attributes: dict = field(default_factory=dict)

    def createInstance(self) -> XP_Objekt:
        obj = self.xtype()
        for attribute, value in self.attributes.items():
            setattr(obj, attribute, value)
        return obj


CIVIL_PROPERTIES_BEBAUUNG = [
    CivilProperty(civil_id='1_5_Zahl_der_Wohnungen', xplanung_attribute="MaxZahlWohnungen"),
    CivilProperty(civil_id='2_1_GFZ_Mindestmass', xplanung_attribute="GFZmin"),
    CivilProperty(civil_id='2_1_GFZ_Hoechstmass', xplanung_attribute="GFZmax"),
    CivilProperty(civil_id='2_4_BM', xplanung_attribute="BM"),
    CivilProperty(civil_id='2_5_GRZ', xplanung_attribute="GRZ"),
    CivilProperty(civil_id='2_6_GR', xplanung_attribute="GR"),
    CivilProperty(civil_id='2_7_VG_Hoechstmass', xplanung_attribute="Zmax"),
    CivilProperty(civil_id='2_7_VG_Mindestmass', xplanung_attribute="Zmin"),
    CivilProperty(civil_id='2_7_VG_zwingend', xplanung_attribute="Zzwingend"),
    CivilProperty(civil_id='3_1_1_nur_Einzelhaeuser_zulaessig', xplanung_attribute="bebauungsArt",
                  enum_value=BP_BebauungsArt.Einzelhaeuser, is_array_type=True),
    CivilProperty(civil_id='3_1_2_nur_Doppelhaeuser_zulaessig', xplanung_attribute="bebauungsArt",
                  enum_value=BP_BebauungsArt.Doppelhaeuser),
    CivilProperty(civil_id='3_1_3_nur_Hausgruppen_zulaessig', xplanung_attribute="bebauungsArt",
                  enum_value=BP_BebauungsArt.Hausgruppen),
    CivilProperty(civil_id='3_1_4_nur_Einzel_und_Doppelhaeuser_zulaessig', xplanung_attribute="bebauungsArt",
                  enum_value=BP_BebauungsArt.EinzelhaeuserHausgruppen),
]

CIVIL_STYLE_AREAS = [
    # Baugebiete
    CivilStyle(civil_id='1.1 Wohnbauflächen', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG,
               property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.WohnBauflaeche}),
    CivilStyle(civil_id='1.1.1', xtype=BP_BaugebietsTeilFlaeche, civil_properties=CIVIL_PROPERTIES_BEBAUUNG,
               property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.WohnBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.Kleinsiedlungsgebiet}),
    CivilStyle(civil_id='1.1.2', xtype=BP_BaugebietsTeilFlaeche, civil_properties=CIVIL_PROPERTIES_BEBAUUNG,
               property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.WohnBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.ReinesWohngebiet}),
    CivilStyle(civil_id='1.1.3', xtype=BP_BaugebietsTeilFlaeche, civil_properties=CIVIL_PROPERTIES_BEBAUUNG,
               property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.WohnBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.AllgWohngebiet}),
    CivilStyle(civil_id='1.1.4', xtype=BP_BaugebietsTeilFlaeche, civil_properties=CIVIL_PROPERTIES_BEBAUUNG,
               property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.WohnBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.BesonderesWohngebiet}),

    CivilStyle(civil_id='1.2 Gemischte Bauflächen', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.GemischteBauflaeche}),
    CivilStyle(civil_id='1.2.1', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.GemischteBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.Dorfgebiet}),
    CivilStyle(civil_id='1.2.2', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.GemischteBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.Mischgebiet}),
    CivilStyle(civil_id='1.2.3', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.GemischteBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.Kerngebiet}),

    CivilStyle(civil_id='1.3 Gewerbliche Bauflächen', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.GewerblicheBauflaeche}),
    CivilStyle(civil_id='1.3.1', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.GewerblicheBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.Gewerbegebiet}),
    CivilStyle(civil_id='1.3.2', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.GewerblicheBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.Industriegebiet}),

    CivilStyle(civil_id='1.4 Sonderbauflächen', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.SonderBauflaeche}),
    CivilStyle(civil_id='1.4.1', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.SonderBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.SondergebietErholung}),
    CivilStyle(civil_id='1.4.2', xtype=BP_BaugebietsTeilFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"allgArtDerBaulNutzung": XP_AllgArtDerBaulNutzung.SonderBauflaeche,
                           "besondererArtderBaulNutzung": XP_BesondereArtDerBaulNutzung.SondergebietSonst}),

    # Gemeinbedarf
    CivilStyle(civil_id='4.1.1', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.OeffentlicheVerwaltung}),
    CivilStyle(civil_id='4.1.2', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.Schule}),
    CivilStyle(civil_id='4.1.3', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.Kirche}),
    CivilStyle(civil_id='4.1.4', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.Sozial}),
    CivilStyle(civil_id='4.1.5', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.Gesundheit}),
    CivilStyle(civil_id='4.1.6', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.Kultur}),
    CivilStyle(civil_id='4.1.7', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.Sport}),
    CivilStyle(civil_id='4.1.8', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.Post}),
    CivilStyle(civil_id='4.1.9', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.Schutzbauwerk}),
    CivilStyle(civil_id='4.1.10', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGemeinbedarf.Feuerwehr}),

    # Spiel- und Sportanlagen
    CivilStyle(civil_id='4.2.1', xtype=BP_SpielSportanlagenFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungSpielSportanlage.Sportanlage}),
    CivilStyle(civil_id='4.2.2', xtype=BP_GemeinbedarfsFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungSpielSportanlage.Spielanlage}),

    # Straßenverkehr
    CivilStyle(civil_id='6.1', xtype=BP_StrassenVerkehrsFlaeche, property_table=PARCEL_TABLE),
    CivilStyle(civil_id='6.3.1', xtype=BP_VerkehrsflaecheBesondererZweckbestimmung,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": BP_ZweckbestimmungStrassenverkehr.Parkierungsflaeche}),
    CivilStyle(civil_id='6.3.2', xtype=BP_VerkehrsflaecheBesondererZweckbestimmung,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": BP_ZweckbestimmungStrassenverkehr.Fussgaengerbereich}),
    CivilStyle(civil_id='6.3.3', xtype=BP_VerkehrsflaecheBesondererZweckbestimmung,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": BP_ZweckbestimmungStrassenverkehr.VerkehrsberuhigterBereich}),

    # Versorgung / Entsorgung
    CivilStyle(civil_id='7.1', xtype=BP_VerEntsorgung,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungVerEntsorgung.Elektrizitaet}),
    CivilStyle(civil_id='7.2', xtype=BP_VerEntsorgung,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungVerEntsorgung.Gas}),
    CivilStyle(civil_id='7.3', xtype=BP_VerEntsorgung,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungVerEntsorgung.Fernwaermeleitung}),
    CivilStyle(civil_id='7.4', xtype=BP_VerEntsorgung,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungVerEntsorgung.Wasser}),
    CivilStyle(civil_id='7.5', xtype=BP_VerEntsorgung,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungVerEntsorgung.Abwasser}),
    CivilStyle(civil_id='7.6', xtype=BP_VerEntsorgung, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungVerEntsorgung.Abfallentsorgung}),
    CivilStyle(civil_id='7.7', xtype=BP_VerEntsorgung, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungVerEntsorgung.Ablagerung}),

    # Gruenflächen
    CivilStyle(civil_id='9.1', xtype=BP_GruenFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGruen.Sonstiges}),
    CivilStyle(civil_id='9.2', xtype=BP_GruenFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGruen.Parkanlage}),
    CivilStyle(civil_id='9.3', xtype=BP_GruenFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGruen.Dauerkleingarten}),
    CivilStyle(civil_id='9.4', xtype=BP_GruenFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGruen.Sportplatz}),
    CivilStyle(civil_id='9.5', xtype=BP_GruenFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGruen.Spielplatz}),
    CivilStyle(civil_id='9.6', xtype=BP_GruenFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGruen.Zeltplatz}),
    CivilStyle(civil_id='9.7', xtype=BP_GruenFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGruen.Badeplatz}),
    CivilStyle(civil_id='9.8', xtype=BP_GruenFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGruen.Friedhof}),

    # Wasserflächen
    CivilStyle(civil_id='10.1.1', xtype=BP_GewaesserFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGewaesser.Wasserflaeche}),
    CivilStyle(civil_id='10.1.2', xtype=BP_GewaesserFlaeche,
               civil_properties=CIVIL_PROPERTIES_BEBAUUNG, property_table=PARCEL_TABLE,
               attributes={"zweckbestimmung": XP_ZweckbestimmungGewaesser.Hafen}),

    # Schutz, Pflege, Entwicklungsflächen
    CivilStyle(civil_id='13.3', xtype=BP_SchutzPflegeEntwicklungsFlaeche, property_table=PARCEL_TABLE),
]

CIVIL_STYLE_LINES = [
    CivilStyle(civil_id='3.4', xtype=BP_BauLinie, property_table=LINE_TABLE),
    CivilStyle(civil_id='3.5', xtype=BP_BauGrenze, property_table=LINE_TABLE),
    CivilStyle(civil_id='6.2', xtype=BP_StrassenbegrenzungsLinie, property_table=LINE_TABLE),
]

CIVIL_STYLE_POINTS = [
    CivilStyle(civil_id='13.2.1.2', xtype=BP_AnpflanzungBindungErhaltung, property_table=POINT_TABLE,
               attributes={"massnahme": XP_ABEMassnahmenTypen.Anpflanzung,
                           "gegenstand": XP_AnpflanzungBindungErhaltungsGegenstand.Baeume})
]
