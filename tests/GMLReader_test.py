import datetime
import os
import pytest
from lxml import etree
from geoalchemy2 import WKTElement, WKBElement

from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche
from SAGisXPlanung.GML.GMLReader import GMLReader
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_PPO, XP_PTO, XP_Nutzungsschablone
from SAGisXPlanung.XPlan.data_types import XP_Gemeinde, XP_Plangeber, XP_VerbundenerPlan
from SAGisXPlanung.XPlan.enums import XP_ExterneReferenzTyp, XP_ExterneReferenzArt


def side_effect(*args):
    if args[0].__class__ == XP_Gemeinde:
        return XP_Gemeinde()
    elif args[0].__class__ == XP_Plangeber:
        return XP_Plangeber()


@pytest.fixture
def gml_reader(request, mocker):
    mocker.patch(
        'SAGisXPlanung.GML.GMLReader.query_existing',
        side_effect=side_effect
    )
    gml = etree.parse(os.path.join(os.path.dirname(__file__), f'gml/{request.param}'))
    return GMLReader(etree.tostring(gml))


class TestGMLReader_read_data_object:

    @pytest.mark.parametrize('gml_reader', ['bp_plan.gml'], indirect=True)
    def test_read_data_object(self, gml_reader):
        string = '<xplan:XP_Gemeinde xmlns:xplan="http://www.xplanung.de/xplangml/5/3">' \
                    '<xplan:ags>4326436</xplan:ags>' \
                    '<xplan:gemeindeName>Berlin</xplan:gemeindeName>' \
                 '</xplan:XP_Gemeinde>'
        gml = etree.fromstring(string)

        obj = GMLReader.read_data_object(gml)

        assert obj.__class__.__name__ == "XP_Gemeinde"
        assert obj.ags == '4326436'
        assert obj.gemeindeName == 'Berlin'

    @pytest.mark.parametrize('gml_reader', ['bp_plan.gml'], indirect=True)
    def test_read_data_object_enum(self, gml_reader):
        string = '<xplan:XP_SpezExterneReferenz xmlns:xplan="http://www.xplanung.de/xplangml/5/3">' \
                  '<xplan:art>Dokument</xplan:art>' \
                  '<xplan:referenzName>ref1</xplan:referenzName>' \
                  r'<xplan:referenzURL>D:\Downloads\document.pdf</xplan:referenzURL>' \
                  '<xplan:referenzMimeType>application/pdf</xplan:referenzMimeType>' \
                  '<xplan:datum>2021-08-19</xplan:datum>' \
                  '<xplan:typ>1000</xplan:typ>' \
                '</xplan:XP_SpezExterneReferenz>'

        gml = etree.fromstring(string)

        obj = GMLReader.read_data_object(gml)

        assert obj.__class__.__name__ == "XP_SpezExterneReferenz"
        assert obj.art == XP_ExterneReferenzArt.Dokument
        assert obj.typ == XP_ExterneReferenzTyp.Beschreibung


class TestGMLReader_readPlan:

    @pytest.mark.parametrize('gml_reader', ['bp_plan.gml'], indirect=True)
    def test_readPlan(self, gml_reader):
        plan = gml_reader.plan
        assert plan.name == 'bp_plan'
        assert isinstance(plan.technHerstellDatum, datetime.date)
        assert plan.technHerstellDatum.strftime('%Y-%m-%d') == '2021-06-04'
        assert len(plan.auslegungsStartDatum) == 2
        assert len(plan.externeReferenz) == 1
        assert plan.externeReferenz[0].referenzName == 'ref1'
        assert len(plan.aendert) == 1
        assert len(plan.wurdeGeaendertVon) == 1
        assert isinstance(plan.aendert[0], XP_VerbundenerPlan)
        assert isinstance(plan.wurdeGeaendertVon[0], XP_VerbundenerPlan)

        assert len(plan.bereich) == 2
        assert len(plan.bereich[1].planinhalt) == 4
        assert plan.bereich[1].planinhalt[1].__class__.__name__ == 'BP_Wegerecht'
        assert len(plan.bereich[1].planinhalt[1].typ) == 2

        baugebiet = plan.bereich[1].planinhalt[2]
        assert isinstance(baugebiet, BP_BaugebietsTeilFlaeche)
        assert len(baugebiet.wirdDargestelltDurch) == 3
        assert isinstance(baugebiet.wirdDargestelltDurch[0], XP_Nutzungsschablone)
        assert not baugebiet.wirdDargestelltDurch[0].hidden
        assert isinstance(baugebiet.wirdDargestelltDurch[1], XP_PPO)
        assert baugebiet.wirdDargestelltDurch[1].drehwinkel == '4.20'
        assert isinstance(baugebiet.wirdDargestelltDurch[2], XP_PTO)
        assert baugebiet.wirdDargestelltDurch[2].schriftinhalt == '(B)'

    @pytest.mark.parametrize('gml_reader', ['bp_plan1.gml'], indirect=True)
    def test_readPlan_top_level_ns_issue24(self, gml_reader):
        plan = gml_reader.plan
        assert plan.name == 'Denkmalbereichssatzung Eisenbahnersiedlung'
        assert len(plan.externeReferenz) == 1
        assert plan.externeReferenz[0].referenzName == 'Satzung Denkmalbereichssatzung "Eisenbahnersiedlung"'


class TestGMLReader_readGeometries:

    @pytest.mark.parametrize('gml_reader', ['bp_plan.gml'], indirect=True)
    def test_readGeometry(self, gml_reader: GMLReader):
        string = '<gml:Point xmlns:gml="http://www.opengis.net/gml/3.2" gml:id="GML_9e8e1182-5f37-4d1a-84be-3f9076d6a29f" srsName="EPSG:25832">' \
                 '<gml:pos srsDimension="2">571665.1779 5940876.1455</gml:pos>' \
                 '</gml:Point>'
        gml = etree.fromstring(string)

        wkt_element = gml_reader.readGeometry(gml)

        assert isinstance(wkt_element, WKTElement)
        assert wkt_element.data == 'POINT (571665.1779 5940876.1455)'
