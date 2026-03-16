import uuid

import pytest
from geoalchemy2 import WKTElement
from mock.mock import MagicMock

from qgis.core import QgsVectorLayer, QgsProject, QgsGeometry, QgsWkbTypes, QgsSingleSymbolRenderer

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche, BP_BauGrenze
from SAGisXPlanung.BPlan.BP_Naturschutz_Landschaftsbild_Naturhaushalt.feature_types import BP_AnpflanzungBindungErhaltung
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_PTO
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import QgsConfig

plan_xid = 'c52aeb9d-34e2-4eca-b56b-e3f3752c94dd'
feat_xid = 'd52aeb9d-34e2-4eca-b56b-e3f3752c94dd'
feat1_xid = 'e52aeb9d-34e2-4eca-b56b-e3f3752c94dd'
feat2_xid = 'f52aeb9d-34e2-4eca-b56b-e3f3752c94dd'


@pytest.fixture()
def xitem() -> XPlanungItem:
    return XPlanungItem(xid=str(uuid.uuid4()), xtype=XP_PTO, plan_xid=plan_xid)


@pytest.fixture()
def vl(request) -> QgsVectorLayer:
    layer = QgsVectorLayer('polygon?crs=epsg:4326', request.param, "memory")
    layer.setCustomProperty('xplanung/type', request.param)
    layer.setCustomProperty('xplanung/plan-xid', plan_xid)
    layer.setCustomProperty(f'xplanung/feat-1', feat_xid)
    layer.setCustomProperty(f'xplanung/layer-priority', LayerPriorityType.CustomLayerOrder)
    return layer


@pytest.fixture()
def vl1() -> QgsVectorLayer:
    layer = QgsVectorLayer('point?crs=epsg:4326', "Scratch  layer", "memory")
    layer.setCustomProperty('xplanung/type', 'BP_AnpflanzungBindungErhaltung')
    layer.setCustomProperty('xplanung/plan-xid', plan_xid)
    layer.setCustomProperty(f'xplanung/feat-1', feat1_xid)
    layer.setCustomProperty(f'xplanung/layer-priority', LayerPriorityType.CustomLayerOrder)
    return layer


@pytest.fixture()
def vl2() -> QgsVectorLayer:
    layer = QgsVectorLayer('polygon?crs=epsg:4326', "Scratch  layer", "memory")
    layer.setCustomProperty('xplanung/type', 'BP_AnpflanzungBindungErhaltung')
    layer.setCustomProperty('xplanung/plan-xid', plan_xid)
    layer.setCustomProperty(f'xplanung/feat-1', feat2_xid)
    layer.setCustomProperty(f'xplanung/layer-priority', LayerPriorityType.CustomLayerOrder)
    return layer


@pytest.fixture()
def pto_layer(xitem) -> QgsVectorLayer:
    tpo = XP_PTO()
    tpo.id = xitem.xid
    tpo.position = WKTElement('POINT (1 1)', srid=25833)
    tpo.schriftinhalt = 'test'
    return tpo.asLayer(tpo.position.srid, xitem.plan_xid, 'TestLayer')


@pytest.fixture
def mock_iface(monkeypatch):
    mock_scene = MagicMock()
    mock_scene.removeItem = MagicMock()
    mock_canvas = MagicMock()
    mock_canvas.scene.return_value = mock_scene
    iface_mock = MagicMock()
    iface_mock.mapCanvas.return_value = mock_canvas
    monkeypatch.setattr("SAGisXPlanung.MapLayerRegistry.iface", iface_mock)
    return iface_mock


@pytest.fixture(scope="session")
def registry() -> MapLayerRegistry:
    reg = MapLayerRegistry()
    return reg


@pytest.fixture(autouse=True)
def clear_registry_after_test(registry):
    yield

    registry._layers = []
    registry._canvasItems = []
    QgsProject().instance().removeAllMapLayers()


class TestMapLayerRegistry:

    @pytest.mark.parametrize("vl", ['BP_BaugebietsTeilFlaeche'], indirect=True)
    def test_add_layer(self, registry, vl, pto_layer):
        registry.addLayer(vl)
        registry.addLayer(pto_layer)
        registry.addLayer(pto_layer)

        assert pto_layer in registry.layers
        assert vl in registry.layers
        # verify that duplicate isn't added to registry
        assert len(registry.layers) == 2
        assert len(QgsProject().instance().mapLayersByName("BP_BaugebietsTeilFlaeche")) == 1

    @pytest.mark.parametrize("vl", ['BP_BaugebietsTeilFlaeche'], indirect=True)
    def test_add_layer_into_group(self, registry, vl, pto_layer):
        root = QgsProject.instance().layerTreeRoot()
        layer_group = root.addGroup("Test_Group")

        registry.addLayer(vl, layer_group)
        registry.addLayer(pto_layer, layer_group)

        assert len(layer_group.children()) == 2
        assert layer_group.children()[0].layerId() == pto_layer.id()
        assert layer_group.children()[1].layerId() == vl.id()

    def test_add_layer_with_priority(self, registry):
        root = QgsProject.instance().layerTreeRoot()
        layer_group = root.addGroup("Test_Group")

        # setup custom layer order
        QgsConfig.set_layer_priority(BP_BauGrenze, GeometryType.LineGeometry, 1)
        QgsConfig.set_layer_priority(BP_BaugebietsTeilFlaeche, GeometryType.PolygonGeometry, 2)
        QgsConfig.set_layer_priority(BP_Plan, GeometryType.PolygonGeometry, 0)

        layer1 = BP_BauGrenze.asLayer(25833, plan_xid, 'layer1', GeometryType.LineGeometry)
        layer2 = BP_Plan.asLayer(25833, plan_xid, 'layer2', GeometryType.PolygonGeometry)
        layer3 = BP_BaugebietsTeilFlaeche.asLayer(25833, plan_xid, 'layer3', GeometryType.PolygonGeometry)

        registry.addLayer(layer1, layer_group)
        registry.addLayer(layer2, layer_group)
        registry.addLayer(layer3, layer_group)

        assert len(layer_group.children()) == 3
        assert layer_group.children()[0].layerId() == layer2.id()
        assert layer_group.children()[1].layerId() == layer1.id()
        assert layer_group.children()[2].layerId() == layer3.id()

    def test_add_layer_with_top_priority(self, registry):
        root = QgsProject.instance().layerTreeRoot()
        layer_group = root.addGroup("Test_Group")

        layer1 = QgsVectorLayer('polygon?crs=epsg:4326', 'layer1', "memory")
        layer1.setCustomProperty('xplanung/layer-priority', LayerPriorityType.Top)
        layer1.setCustomProperty('xplanung/type', BP_BaugebietsTeilFlaeche.__name__)

        layer2 = QgsVectorLayer('polygon?crs=epsg:4326', 'layer2', "memory")
        layer2.setCustomProperty('xplanung/layer-priority', LayerPriorityType.CustomLayerOrder)
        layer2.setCustomProperty('xplanung/type', BP_BaugebietsTeilFlaeche.__name__)

        registry.addLayer(layer2, layer_group)
        registry.addLayer(layer1, layer_group)  # Should be inserted at position 0

        assert layer_group.children()[0].layerId() == layer1.id()

    @pytest.mark.parametrize("vl", ['BP_BaugebietsTeilFlaeche'], indirect=True)
    def test_remove_layer(self, registry, vl, pto_layer):
        registry.addLayer(vl)

        # remove non existent layer
        registry.removeLayer(pto_layer.id())
        # remove valid layer
        registry.removeLayer(vl.id())

        assert len(registry.layers) == 0

    def test_get_layer_by_xid(self, registry, pto_layer, xitem):
        registry.addLayer(pto_layer)

        layer = registry.layerByXid(xitem)

        assert isinstance(layer, QgsVectorLayer)

    def test_get_layer_by_xid_with_geomtype(self, registry, vl1, vl2):
        registry.addLayer(vl1)
        registry.addLayer(vl2)

        xitem = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_AnpflanzungBindungErhaltung, plan_xid=plan_xid)
        layer = registry.layerByXid(xitem, QgsWkbTypes.PointGeometry)

        assert isinstance(layer, QgsVectorLayer)
        assert layer.geometryType() == QgsWkbTypes.PointGeometry

    @pytest.mark.parametrize("vl", ['BP_Bereich'], indirect=True)
    def test_get_layer_by_display_name(self, registry, vl):
        registry.addLayer(vl)

        layer = registry.layer_by_display_name('BP_Bereich', plan_xid)

        assert isinstance(layer, QgsVectorLayer)
        assert layer.geometryType() == QgsWkbTypes.PolygonGeometry
        assert len(registry._layers) == 1

    @pytest.mark.parametrize("vl", ['BP_BaugebietsTeilFlaeche'], indirect=True)
    def test_feature_is_shown(self, registry, vl):
        registry.addLayer(vl)

        assert registry.featureIsShown(feat_xid)
        assert not registry.featureIsShown(plan_xid)

    @pytest.mark.parametrize("vl", ['BP_BaugebietsTeilFlaeche'], indirect=True)
    def test_layer_by_feature(self, registry, vl):
        registry.addLayer(vl)

        assert registry.layer_by_orm_id(feat_xid)
        assert registry.layer_by_orm_id(plan_xid) is None

    @pytest.mark.parametrize("vl", ['BP_BaugebietsTeilFlaeche'], indirect=True)
    def test_geometries_changed(self, mocker, registry, vl):
        mocker.patch("SAGisXPlanung.MapLayerRegistry.MapLayerRegistry.layerById").return_value = vl

        poly = BP_Plan()
        poly.position = WKTElement('MULTIPOLYGON (((0 0, 1 1, 1 0, 0 0)))', srid=25833)
        session_mock = mocker.MagicMock()
        obj_mock = mocker.MagicMock()
        session_mock.get.return_value = obj_mock
        mocker.patch("SAGisXPlanung.Session.begin").return_value.__enter__.return_value = session_mock

        registry.onGeometriesChanged(vl.id(), {1: QgsGeometry()})

        obj_mock.setGeometry.assert_not_called()








