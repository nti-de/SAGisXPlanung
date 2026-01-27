import copy
import datetime
import os
import uuid
import zipfile
from io import BytesIO
from pathlib import PurePath

import pytest
from geoalchemy2 import WKTElement, WKBElement
from geoalchemy2.shape import from_shape, to_shape
from lxml import etree
from shapely.geometry import Polygon, MultiPolygon, MultiLineString, Point

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.enums import BP_PlanArt, BP_Rechtscharakter
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan, BP_Bereich
from SAGisXPlanung.BPlan.BP_Bebauung.data_types import BP_Dachgestaltung
from SAGisXPlanung.BPlan.BP_Bebauung.enums import BP_Dachform
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche, BP_BauGrenze
from SAGisXPlanung.BPlan.BP_Landwirtschaft_Wald_und_Gruenflaechen.feature_types import BP_GruenFlaeche
from SAGisXPlanung.BPlan.BP_Naturschutz_Landschaftsbild_Naturhaushalt.feature_types import BP_AnpflanzungBindungErhaltung
from SAGisXPlanung.BPlan.BP_Sonstiges.enums import BP_WegerechtTypen
from SAGisXPlanung.BPlan.BP_Sonstiges.feature_types import BP_Wegerecht
from SAGisXPlanung.BPlan.BP_Umwelt.enums import BP_Laermpegelbereich
from SAGisXPlanung.BPlan.BP_Umwelt.feature_types import BP_Immissionsschutz
from SAGisXPlanung.FPlan.FP_Basisobjekte.enums import FP_Rechtscharakter, FP_PlanArt
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Plan
from SAGisXPlanung.FPlan.FP_Bebauung.codelists import FP_DetailArtDerBaulNutzung
from SAGisXPlanung.FPlan.FP_Bebauung.feature_types import FP_BebauungsFlaeche
from SAGisXPlanung.FPlan.FP_Landwirtschaft_Wald_und_Gruen.feature_types import FP_WaldFlaeche
from SAGisXPlanung.GML.GMLWriter import writeTextNode, GMLWriter
from SAGisXPlanung.LPlan.LP_Basisobjekte.enums import LP_PlanArt, LP_Raumkonkretisierung
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Plan, LP_Bereich
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanung.data_types import LP_TypBioVerbundKomplex
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanung.enums import LP_PlanungsEbene, LP_BioVerbundsystemArt, \
    LP_FlaechenTypBVSpeziell, LP_FlaechenTypBV
from SAGisXPlanung.LPlan.LP_PlaninhalteLandschaftsplanung.feature_types import LP_BiotopverbundBiotopvernetzung
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_Nutzungsschablone, XP_PTO
from SAGisXPlanung.XPlan.codelists import CodeList
from SAGisXPlanung.XPlan.data_types import XP_Gemeinde, XP_Plangeber, XP_SpezExterneReferenz, XP_ExterneReferenz, \
    XP_Hoehenangabe, XP_GesetzlicheGrundlage
from SAGisXPlanung.XPlan.enums import XP_WaldbetretungTyp, XP_ArtHoehenbezugspunkt, XP_ImmissionsschutzTypen, \
    XP_ExterneReferenzTyp, XP_ExterneReferenzArt, XP_Bundeslaender, XP_Rechtscharakter

SCHEMA_VERSIONS = ["53", "60"]
XPLAN_VERSION_MAP = {
    "53": XPlanVersion.FIVE_THREE,
    "60": XPlanVersion.SIX,
}


@pytest.fixture
def plan_factory():
    def _create_plan(plan_type):
        if plan_type == BP_Plan:
            plan = BP_Plan()
            plan.raeumlicherGeltungsbereich = WKTElement(
                'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)))',
                srid=4326
            )
            plan.name = 'test'
            plan.traegerbeteiligungsStartDatum = [datetime.date(2000, 9, 10), datetime.date(2000, 10, 10)]
            plan.planArt = BP_PlanArt.BPlan
            gemeinde = XP_Gemeinde()
            gemeinde.gemeindeName = 'test'
            gemeinde.ags = '19613526'
            plan.gemeinde.append(gemeinde)
            plangeber = XP_Plangeber()
            plangeber.name = 'test'
            plan.plangeber = plangeber
            baugb = XP_GesetzlicheGrundlage()
            baugb.name = 'Baugesetzbuch'
            baugb.datum = datetime.date(2024, 1, 1)
            plan.versionBauGB = baugb

            ref = XP_SpezExterneReferenz()
            ref.beschreibung = 'test'
            with open(os.path.join(os.path.dirname(__file__), 'data/bp_plan.tif'), 'rb') as file:
                file_bytes = file.read()
            ref.file = file_bytes
            ref.referenzURL = 'data/bp_plan.tif'
            ref.referenzName = 'Referenz1'
            ref.art = XP_ExterneReferenzArt.Dokument
            ref.typ = XP_ExterneReferenzTyp.Karte
            plan.externeReferenz.append(ref)

            ref1 = XP_ExterneReferenz()
            ref1.beschreibung = 'test'
            ref1.file = file_bytes

            bereich = BP_Bereich()
            bereich.nummer = 0
            bereich.name = 'test'
            bereich.geltungsbereich = plan.raeumlicherGeltungsbereich
            bereich.refScan.append(ref1)

            bp_objekt_poly = BP_BaugebietsTeilFlaeche()
            bp_objekt_poly.id = uuid.uuid4()
            bp_objekt_poly.position = WKBElement(to_shape(bereich.geltungsbereich).wkb, srid=4326)
            bp_objekt_poly.GRZ = 0.4

            nutzungschablone = XP_Nutzungsschablone()
            nutzungschablone.id = uuid.uuid4()
            nutzungschablone.dientZurDarstellungVon_id = bp_objekt_poly.id
            nutzungschablone.position = from_shape(Point(0, 0))
            nutzungschablone.hidden = False
            nutzungschablone.zeilenAnz = 3
            nutzungschablone.spaltenAnz = 2
            bp_objekt_poly.wirdDargestelltDurch.append(nutzungschablone)

            hoehenangabe = XP_Hoehenangabe()
            hoehenangabe.bezugspunkt = XP_ArtHoehenbezugspunkt.TH
            hoehenangabe.h = 4.5
            bp_dach = BP_Dachgestaltung()
            bp_dach.dachform = BP_Dachform.Walmdach
            bp_dach.DN = 20
            bp_dach.hoehenangabe = copy.deepcopy(hoehenangabe)
            bp_objekt_poly.dachgestaltung.append(bp_dach)
            bp_objekt_poly.hoehenangabe.append(hoehenangabe)

            pto = XP_PTO()
            pto.position = WKTElement('POINT (1 1)', srid=25833)
            pto.schriftinhalt = 'test'
            pto.drehwinkel = 45
            pto.skalierung = 0.25
            bp_objekt_poly.wirdDargestelltDurch.append(pto)
            bereich.planinhalt.append(bp_objekt_poly)

            point_object = BP_AnpflanzungBindungErhaltung()
            point_object.position = from_shape(Point(0, 0))
            bereich.planinhalt.append(point_object)

            bp_objekt_line = BP_BauGrenze()
            bp_objekt_line.position = WKTElement('LINESTRING (30.5 10.2, 31.0 11.8, 32.25 12.0)', srid=4326)

            bp_objekt_line.bautiefe = 5.3
            bp_objekt_line.aufschrift = 'baugrenze'
            bereich.planinhalt.append(bp_objekt_line)

            bp_wegerecht = BP_Wegerecht()
            bp_wegerecht.position = plan.raeumlicherGeltungsbereich
            bp_wegerecht.typ = [BP_WegerechtTypen.Gehrecht, BP_WegerechtTypen.Fahrrecht]
            bereich.planinhalt.append(bp_wegerecht)

            o_with_empty_array = BP_Wegerecht()
            o_with_empty_array.position = plan.raeumlicherGeltungsbereich
            o_with_empty_array.typ = []
            bereich.planinhalt.append(o_with_empty_array)

            bp_immissionsschutz = BP_Immissionsschutz()
            bp_immissionsschutz.position = plan.raeumlicherGeltungsbereich
            bp_immissionsschutz.typ = XP_ImmissionsschutzTypen.Schutzflaeche
            bp_immissionsschutz.laermpegelbereich = BP_Laermpegelbereich.III
            bereich.planinhalt.append(bp_immissionsschutz)

            plan.bereich.append(bereich)

        elif plan_type == FP_Plan:
            plan = FP_Plan()
            plan.raeumlicherGeltungsbereich = WKTElement(
                'MULTIPOLYGON (((30 30, 10 35, 35 20, 30 30)))',
                srid=4326
            )
            plan.name = 'FP Test'
            plan.planArt = FP_PlanArt.FPlan
            plan.rechtscharakter = FP_Rechtscharakter.Darstellung
            gemeinde = XP_Gemeinde()
            gemeinde.gemeindeName = 'test'
            gemeinde.ags = '19613526'
            plan.gemeinde.append(gemeinde)

        elif plan_type == LP_Plan:
            plan = LP_Plan()
            plan.raeumlicherGeltungsbereich = WKTElement(
                'MULTIPOLYGON (((30 30, 10 35, 35 20, 30 30)))',
                srid=4326
            )
            plan.name = 'LP Test'
            plan.planArt = [LP_PlanArt.Landschaftsplan, LP_PlanArt.Landschaftsprogramm]
            plan.bundesland = XP_Bundeslaender.BE
            plan.rechtlicheAussenwirkung = False
            gemeinde = XP_Gemeinde()
            gemeinde.gemeindeName = 'test'
            gemeinde.ags = '19613526'
            plan.gemeinde.append(gemeinde)

            bereich = LP_Bereich()
            bereich.nummer = 0
            bereich.name = 'test'
            bereich.geltungsbereich = plan.raeumlicherGeltungsbereich

            lp_objekt = LP_BiotopverbundBiotopvernetzung()
            lp_objekt.id = uuid.uuid4()
            lp_objekt.position = plan.raeumlicherGeltungsbereich
            lp_objekt.rechtscharakter = XP_Rechtscharakter.GeplanteFestsetzungImLP
            lp_objekt.raumkonkretisierung = LP_Raumkonkretisierung.Scharf
            lp_objekt.planungsEbene = [LP_PlanungsEbene.Biotopverbund, LP_PlanungsEbene.Biotopvernetzung]
            lp_objekt.bioVerbundsystemArt = LP_BioVerbundsystemArt.Allgemein

            typ_komplex = LP_TypBioVerbundKomplex()
            typ_komplex.flaechenTypBV = LP_FlaechenTypBV.Kernflaeche
            typ_komplex.flaechentypBVSpeziell = LP_FlaechenTypBVSpeziell.Verbundachse
            lp_objekt.typBioVerbund.append(typ_komplex)
        else:
            raise ValueError(f"Unsupported plan type: {plan_type}")

        return plan

    return _create_plan


@pytest.fixture
def gml_writer(request, plan_factory):

    params = getattr(request, "param", {}) or {}
    plan_type = params.get("plan_type", BP_Plan)  # Default to BP_Plan
    schema_version = params.get("schema_version", "53")  # Default to "53"

    version_enum = XPLAN_VERSION_MAP.get(schema_version, XPlanVersion.FIVE_THREE)

    plan = plan_factory(plan_type)
    return GMLWriter(plan, version=version_enum)




@pytest.fixture()
def bplan_schema():
    xmlschema_doc = etree.parse(os.path.join(os.path.dirname(__file__), 'xsd/53/XPlanGML_BPlan.xsd'))
    return etree.XMLSchema(xmlschema_doc)


@pytest.fixture()
def fplan_schema():
    xmlschema_doc = etree.parse(os.path.join(os.path.dirname(__file__), 'xsd/53/XPlanGML_FPlan.xsd'))
    return etree.XMLSchema(xmlschema_doc)


@pytest.fixture()
def xplan_schema():
    xmlschema_doc = etree.parse(os.path.join(os.path.dirname(__file__), 'xsd/53/XPlanung-Operationen.xsd'))
    return etree.XMLSchema(xmlschema_doc)


@pytest.fixture
def xplan_schemas():
    schema_dir = os.path.join(os.path.dirname(__file__), "xsd")
    versions = [d for d in os.listdir(schema_dir) if d.isdigit()]  # Get all numeric folders (versions)

    schemas = {}
    for version in versions:
        schema_path = os.path.join(schema_dir, version, "XPlanung-Operationen.xsd")
        if os.path.exists(schema_path):
            schema_root = etree.parse(schema_path)
            schemas[version] = etree.XMLSchema(schema_root)

    return schemas



class TestGMLWriter_writeTextNode:

    @pytest.mark.parametrize('text,expected', [(BP_PlanArt.BPlan, '1000'),
                                               ('BP_Plan2070', 'BP_Plan2070'),
                                               (1000, '1000'),
                                               (False, 'false')])
    def test_writeTextNode(self, text, expected):
        result = writeTextNode(text)
        assert result == expected


class TestGMLWriter_writeFeature:

    def test_write_simple_object(self, gml_writer, xplan_schema):
        obj = XP_Gemeinde()
        obj.ags = "12345678"
        obj.gemeindeName = "Berlin"

        parent = etree.Element('gemeinde')
        gml_writer.write_feature(obj, parent, only_attributes=True)

        assert xplan_schema.validate(parent[0])


    def test_write_nutzungschablone(self, gml_writer, xplan_schema):
        obj = XP_Nutzungsschablone()
        obj.id = uuid.uuid4()
        obj.dientZurDarstellungVon_id = uuid.uuid4()
        obj.position = from_shape(Point(0, 0))
        obj.hidden = False
        obj.drehwinkel = 0
        obj.skalierung = 0.5
        obj.zeilenAnz = 3
        obj.spaltenAnz = 2

        root = gml_writer.write_feature(obj)

        xplan_schema.assertValid(root)

    def test_write_textannotation(self, gml_writer, xplan_schema):
        obj = XP_PTO()
        obj.position = from_shape(Point(0, 0))
        obj.schriftinhalt = 'test'
        obj.drehwinkel = 45
        obj.skalierung = 0.25

        root = gml_writer.write_feature(obj)

        xplan_schema.assertValid(root)

    def test_write_feature_with_codelist(self, gml_writer, fplan_schema):
        codelist = CodeList()
        codelist.name = "FP_DetailArtDerBaulNutzung"
        codelist.uri = "https://"
        codelist_value = FP_DetailArtDerBaulNutzung()
        codelist_value.codelist = codelist
        codelist_value.id = uuid.uuid4()
        codelist_value.value = 'Solarpark'
        codelist_value.definition = 'Photovoltaikanlage'

        fp_bau = FP_BebauungsFlaeche()
        fp_bau.rechtscharakter = FP_Rechtscharakter.Darstellung
        fp_bau.flaechenschluss = True
        fp_bau.position = WKTElement('MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)))', srid=4326)
        fp_bau.detaillierteArtDerBaulNutzung = codelist_value
        fp_bau.detaillierteArtDerBaulNutzung_id = codelist_value.id

        gml_writer.write_feature(fp_bau)
        assert gml_writer.root[-1:] is not None
        fplan_schema.assertValid(gml_writer.root[-1:][0])

    def test_writeXPObject_empty_array_enum_value_issue23(self, gml_writer, fplan_schema):
        obj = FP_WaldFlaeche()

        obj.betreten = []
        obj.rechtscharakter = FP_Rechtscharakter.Darstellung
        obj.position = WKTElement('MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)))', srid=4326)
        obj.flaechenschluss = True

        gml_writer.write_feature(obj)
        assert gml_writer.root[-1:] is not None
        fplan_schema.assertValid(gml_writer.root[-1:][0])

    def test_writeXPObject_array_enum_value_issue23(self, gml_writer, fplan_schema):
        obj = FP_WaldFlaeche()

        obj.betreten = [XP_WaldbetretungTyp.Reiten, XP_WaldbetretungTyp.Fahren]
        obj.rechtscharakter = FP_Rechtscharakter.Darstellung
        obj.position = WKTElement('MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)))', srid=4326)
        obj.flaechenschluss = True

        gml_writer.write_feature(obj)
        assert gml_writer.root[-1:] is not None
        fplan_schema.assertValid(gml_writer.root[-1:][0])

    def test_objects_should_have_flaechenschluss_attribute_issue_54(self, gml_writer, bplan_schema):
        obj = BP_GruenFlaeche()

        obj.rechtscharakter = BP_Rechtscharakter.Festsetzung
        obj.position = WKTElement('MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)))', srid=4326)

        gml_writer.write_feature(obj)
        assert gml_writer.root[-1:] is not None
        bplan_schema.assertValid(gml_writer.root[-1:][0])


class TestGMLWriter_export:

    @pytest.mark.parametrize("gml_writer", [
        pytest.param({"plan_type": BP_Plan, "schema_version": version}, id=f"BP_Plan_v{version}")
        for version in SCHEMA_VERSIONS
    ] + [
        pytest.param({"plan_type": FP_Plan, "schema_version": version}, id=f"FP_Plan_v{version}")
        for version in SCHEMA_VERSIONS
    ] + [
        pytest.param({"plan_type": LP_Plan, "schema_version": "60"}, id=f"LP_Plan_v60")
    ], indirect=True)
    def test_root_valid(self, gml_writer, xplan_schemas):
        """Test that the generated GML is valid against all schema versions."""
        schema_version = gml_writer.version.short_id()
        schema = xplan_schemas[schema_version]
        schema.assertValid(gml_writer.root[-1:][0])

    def test_toArchive(self, gml_writer):

        archive = gml_writer.toArchive()
        zip_archive = zipfile.ZipFile(archive)

        assert type(archive) == BytesIO
        assert len(zip_archive.namelist()) == 2
        assert any(PurePath(file_name).suffix == '.gml' for file_name in zip_archive.namelist())
        assert any(PurePath(file_name).suffix == '.tif' for file_name in zip_archive.namelist())
