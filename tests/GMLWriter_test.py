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
from SAGisXPlanung.FPlan.FP_Basisobjekte.enums import FP_Rechtscharakter
from SAGisXPlanung.FPlan.FP_Landwirtschaft_Wald_und_Gruen.feature_types import FP_WaldFlaeche
from SAGisXPlanung.GML.GMLWriter import writeTextNode, GMLWriter
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_Nutzungsschablone, XP_PTO
from SAGisXPlanung.XPlan.data_types import XP_Gemeinde, XP_Plangeber, XP_SpezExterneReferenz, XP_ExterneReferenz, \
    XP_Hoehenangabe, XP_GesetzlicheGrundlage
from SAGisXPlanung.XPlan.enums import XP_WaldbetretungTyp, XP_ArtHoehenbezugspunkt, XP_ImmissionsschutzTypen


@pytest.fixture()
def gml_writer():
    plan = BP_Plan()
    plan.raeumlicherGeltungsbereich = WKTElement(
        'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)),((20 35, 45 20, 30 5, 10 10, 10 30, 20 35),(30 20, 20 25, 20 15, 30 20)))',
        srid=4326)
    plan.name = 'test'
    plan.traegerbeteiligungsStartDatum = [datetime.date(2000, 9, 10), datetime.date(2000, 10, 10)]
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

    bp_dach = BP_Dachgestaltung()
    bp_dach.dachform = BP_Dachform.Walmdach
    bp_dach.DN = 20
    bp_objekt_poly.dachgestaltung.append(bp_dach)
    hoehenangabe = XP_Hoehenangabe()
    hoehenangabe.bezugspunkt = XP_ArtHoehenbezugspunkt.TH
    hoehenangabe.h = 4.5
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
    bp_objekt_line.position = from_shape(MultiLineString([((0, 0), (1, 1)), ((-1, 0), (1, 0))]))
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
    return GMLWriter(plan)


@pytest.fixture()
def bplan_schema():
    xmlschema_doc = etree.parse(os.path.join(os.path.dirname(__file__), 'xsd/XPlanGML_BPlan.xsd'))
    return etree.XMLSchema(xmlschema_doc)


@pytest.fixture()
def fplan_schema():
    xmlschema_doc = etree.parse(os.path.join(os.path.dirname(__file__), 'xsd/XPlanGML_FPlan.xsd'))
    return etree.XMLSchema(xmlschema_doc)


@pytest.fixture()
def xplan_schema():
    xmlschema_doc = etree.parse(os.path.join(os.path.dirname(__file__), 'xsd/XPlanung-Operationen.xsd'))
    return etree.XMLSchema(xmlschema_doc)


@pytest.fixture()
def gml_schema():
    xmlschema_doc = etree.parse(os.path.join(os.path.dirname(__file__), 'xsd/gmlProfile/gmlProfilexplan.xsd'))
    return etree.XMLSchema(xmlschema_doc)


class TestGMLWriter_writeTextNode:

    @pytest.mark.parametrize('text,expected', [(BP_PlanArt.BPlan, '1000'),
                                               ('BP_Plan2070', 'BP_Plan2070'),
                                               (1000, '1000'),
                                               (False, 'false')])
    def test_writeTextNode(self, text, expected):
        result = writeTextNode(text)
        assert result == expected


class TestGMLWriter_writeSubObject:

    def test_writeSubObject(self, gml_writer, xplan_schema):
        obj = XP_Gemeinde()
        obj.ags = "12345678"
        obj.gemeindeName = "Berlin"

        root = gml_writer.writeSubObject(obj)

        assert xplan_schema.validate(root)


class TestGMLWriter_export:

    def test_root_valid(self, gml_writer, xplan_schema):
        xplan_schema.assertValid(gml_writer.root[-1:][0])

    def test_toArchive(self, gml_writer):

        archive = gml_writer.toArchive()
        zip_archive = zipfile.ZipFile(archive)

        assert type(archive) == BytesIO
        assert len(zip_archive.namelist()) == 2
        assert any(PurePath(file_name).suffix == '.gml' for file_name in zip_archive.namelist())
        assert any(PurePath(file_name).suffix == '.tif' for file_name in zip_archive.namelist())
