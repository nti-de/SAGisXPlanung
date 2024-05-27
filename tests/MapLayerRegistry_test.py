import uuid

import pytest
from geoalchemy2 import WKTElement
from mock.mock import MagicMock
from qgis._core import QgsLayerTreeNode, QgsLayerTreeGroup
from qgis._gui import QgsMapCanvasItem

from qgis.core import QgsVectorLayer, QgsAnnotationLayer, QgsProject, QgsGeometry, QgsWkbTypes

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.BPlan.BP_Naturschutz_Landschaftsbild_Naturhaushalt.feature_types import BP_AnpflanzungBindungErhaltung
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry, CanvasItemRegistryItem
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_PTO
from SAGisXPlanung.XPlanungItem import XPlanungItem


plan_xid = 'c52aeb9d-34e2-4eca-b56b-e3f3752c94dd'
feat_xid = 'd52aeb9d-34e2-4eca-b56b-e3f3752c94dd'
feat1_xid = 'e52aeb9d-34e2-4eca-b56b-e3f3752c94dd'
feat2_xid = 'f52aeb9d-34e2-4eca-b56b-e3f3752c94dd'


@pytest.fixture()
def xitem() -> XPlanungItem:
    return XPlanungItem(xid=str(uuid.uuid4()), xtype=XP_PTO, plan_xid=plan_xid)


@pytest.fixture()
def vl() -> QgsVectorLayer:
    layer = QgsVectorLayer('polygon?crs=epsg:4326', "Scratch  layer", "memory")
    layer.setCustomProperty('xplanung/type', 'BP_BaugebietsTeilFlaeche')
    layer.setCustomProperty('xplanung/plan-xid', plan_xid)
    layer.setCustomProperty(f'xplanung/feat-1', feat_xid)
    return layer


@pytest.fixture()
def vl1() -> QgsVectorLayer:
    layer = QgsVectorLayer('point?crs=epsg:4326', "Scratch  layer", "memory")
    layer.setCustomProperty('xplanung/type', 'BP_AnpflanzungBindungErhaltung')
    layer.setCustomProperty('xplanung/plan-xid', plan_xid)
    layer.setCustomProperty(f'xplanung/feat-1', feat1_xid)
    return layer


@pytest.fixture()
def vl2() -> QgsVectorLayer:
    layer = QgsVectorLayer('polygon?crs=epsg:4326', "Scratch  layer", "memory")
    layer.setCustomProperty('xplanung/type', 'BP_AnpflanzungBindungErhaltung')
    layer.setCustomProperty('xplanung/plan-xid', plan_xid)
    layer.setCustomProperty(f'xplanung/feat-1', feat2_xid)
    return layer


@pytest.fixture()
def al(xitem) -> QgsVectorLayer:
    tpo = XP_PTO()
    tpo.id = xitem.xid
    tpo.position = WKTElement('POINT (1 1)', srid=25833)
    tpo.schriftinhalt = 'test'
    return tpo.asLayer(tpo.position.srid, xitem.plan_xid, 'TestLayer')


@pytest.fixture(scope="session")
def registry() -> MapLayerRegistry:
    reg = MapLayerRegistry()
    return reg


@pytest.fixture(autouse=True)
def clear_registry_after_test(registry):
    yield

    registry._layers = []
    QgsProject().instance().removeAllMapLayers()


class TestMapLayerRegistry:

    def test_add_layer(self, registry, vl, al):
        registry.addLayer(vl)
        registry.addLayer(al)
        registry.addLayer(al)

        assert al in registry.layers
        assert vl in registry.layers
        # verify that duplicate isn't  added to registry
        assert len(registry.layers) == 2
        assert len(QgsProject().instance().mapLayersByName("Scratch  layer")) == 1

    def test_add_layer_into_group(self, registry, vl, al):
        root = QgsProject.instance().layerTreeRoot()
        layer_group = root.addGroup("Test_Group")

        registry.addLayer(vl, layer_group)
        registry.addLayer(al, layer_group)

        assert len(layer_group.children()) == 2
        assert layer_group.children()[0].layerId() == al.id()
        assert layer_group.children()[1].layerId() == vl.id()

    def test_remove_layer(self, registry, vl, al):
        registry.addLayer(vl)

        # remove non existent layer
        registry.removeLayer(al.id())
        # remove valid layer
        registry.removeLayer(vl.id())

        assert len(registry.layers) == 0

    def test_get_layer_by_xid(self, registry, al, xitem):
        registry.addLayer(al)

        layer = registry.layerByXid(xitem)

        assert isinstance(layer, QgsAnnotationLayer)

    def test_get_layer_by_xid_with_type(self, registry, vl1, vl2):
        registry.addLayer(vl1)
        registry.addLayer(vl2)

        xitem = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_AnpflanzungBindungErhaltung, plan_xid=plan_xid)
        layer = registry.layerByXid(xitem, QgsWkbTypes.PointGeometry)

        assert isinstance(layer, QgsVectorLayer)
        assert layer.geometryType() == QgsWkbTypes.PointGeometry

    def test_feature_is_shown(self, registry, vl):
        registry.addLayer(vl)

        assert registry.featureIsShown(feat_xid)
        assert not registry.featureIsShown(plan_xid)

    def test_layer_by_feature(self, registry, vl):
        registry.addLayer(vl)

        assert registry.layerByFeature(feat_xid)
        assert registry.layerByFeature(plan_xid) is None

    def test_geometries_changed(self, mocker, registry, vl):
        mocker.patch("SAGisXPlanung.MapLayerRegistry.MapLayerRegistry.layerById").return_value = vl

        poly = BP_Plan()
        poly.position = WKTElement('MULTIPOLYGON (((0 0, 1 1, 1 0, 0 0)))', srid=25833)
        session_mock = mocker.MagicMock()
        obj_mock = mocker.MagicMock()
        session_mock.query.return_value.get.return_value = obj_mock
        mocker.patch("SAGisXPlanung.Session.begin").return_value.__enter__.return_value = session_mock

        registry.onGeometriesChanged(vl.id(), {1: QgsGeometry()})

        obj_mock.setGeometry.assert_not_called()

    def test_add_canvas_item(self, mocker, registry):
        canvas_item_mock = mocker.patch("SAGisXPlanung.BuildingTemplateItem.BuildingTemplateItem").return_value

        registry.add_canvas_item(canvas_item_mock, feat_xid, plan_xid)

        assert len(registry._canvasItems) == 1
        assert registry.canvas_items_at_feat(feat_xid)[0] == canvas_item_mock

    def test_on_layer_visibility_changed(self, registry):
        mock_layer = MagicMock()
        mock_layer.customPropertyKeys.return_value = ['xplanung/feat-1']
        mock_layer.customProperty.return_value = 'feat1'
        mock_node = MagicMock()
        mock_node.layer.return_value = mock_layer
        mock_canvas_item = MagicMock()
        mock_canvas_item.isVisible.return_value = True
        registry._canvasItems = [
            CanvasItemRegistryItem(plan_xid='plan1', feat_xid='feat1', canvas_item=mock_canvas_item)
        ]

        registry.on_layer_visibility_changed(mock_node)

        # Check if the visibility of the canvas item has changed
        mock_canvas_item.setVisible.assert_called_with(False)

    def test_on_group_node_visibility_changed(self, registry):
        mock_layer = MagicMock()
        mock_layer.customPropertyKeys.return_value = ['xplanung/feat-1']
        mock_layer.customProperty.return_value = 'feat1'
        mock_node = MagicMock()
        mock_node.layer.return_value = mock_layer
        mock_group = MagicMock(spec=QgsLayerTreeGroup)
        mock_group.children.return_value = [mock_node]
        mock_canvas_item = MagicMock()
        mock_canvas_item.isVisible.return_value = True
        registry._canvasItems = [
            CanvasItemRegistryItem(plan_xid='plan1', feat_xid='feat1', canvas_item=mock_canvas_item)
        ]

        registry.on_group_node_visibility_changed(mock_group)

        mock_node.layer.assert_called()
        mock_canvas_item.setVisible.assert_called_with(False)