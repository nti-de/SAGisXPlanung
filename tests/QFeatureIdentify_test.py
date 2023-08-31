import pytest
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsField, QgsProject
from qgis.utils import iface

from SAGisXPlanung.Tools.IdentifyFeatureTool import IdentifyFeatureTool
from SAGisXPlanung.gui.widgets.QFeatureIdentify import load_geometry, QFeatureIdentify


@pytest.fixture
def vector_feat():

    def _vector_feat(wkt):
        layer = QgsVectorLayer(f"Polygon?crs=4326", "test", "memory")
        dp = layer.dataProvider()
        layer.startEditing()
        dp.addAttributes([QgsField("name", QVariant.String)])
        layer.updateFields()
        feat1 = QgsFeature()
        g = QgsGeometry.fromWkt(wkt)
        feat1.setGeometry(g)
        feat1.setAttributes(["test"])
        dp.addFeature(feat1)
        layer.commitChanges()

        return layer, feat1

    return _vector_feat


@pytest.fixture()
def widget():
    return QFeatureIdentify()


class TestQFeatureIdentify_loadLayer:

    def test_loadArea_with_polygon(self, vector_feat):
        _, feat = vector_feat('POLYGON ((0 0, 1 1, 1 0, 0 0))')
        geom = load_geometry(feat)
        assert geom.wkt == 'MULTIPOLYGON (((0 0, 1 1, 1 0, 0 0)))'

    def test_loadArea_with_multipolygon(self, vector_feat):
        _, feat = vector_feat('MULTIPOLYGON (((0 0, 1 1, 1 0, 0 0)))')
        geom = load_geometry(feat)
        assert geom.wkt == 'MULTIPOLYGON (((0 0, 1 1, 1 0, 0 0)))'


class TestQFeatureIdentify_createWidget:

    def test_createWidget(self, qtbot, widget):
        qtbot.addWidget(widget)
        assert widget.mapTool
        assert widget.bIdentify


class TestQFeatureIdentify_testFeatureIdentify:

    def test_identifyFeature(self, vector_feat, qtbot, widget):
        layer, _ = vector_feat('MULTIPOLYGON (((0 0, 1 1, 1 0, 0 0)))')
        QgsProject.instance().addMapLayer(layer)

        qtbot.addWidget(widget)
        qtbot.mouseClick(widget.bIdentify, Qt.LeftButton)

        assert widget.layer == layer
        assert iface.mapCanvas().mapTool().__class__ == IdentifyFeatureTool
        assert iface.mapCanvas().mapTool() == widget.mapTool
