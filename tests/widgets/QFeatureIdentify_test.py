import pytest
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsField, QgsProject, QgsWkbTypes
from qgis.utils import iface

from SAGisXPlanung.Tools.IdentifyFeatureTool import IdentifyFeatureTool
from SAGisXPlanung.gui.widgets.QFeatureIdentify import QFeatureIdentify


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
def widget(vector_feat):
    layer, feature = vector_feat('PointZ (10, 10, 10)')
    QgsProject.instance().addMapLayer(layer)
    widget = QFeatureIdentify()
    return widget


class TestQFeatureIdentify:

    def test_createWidget(self, qtbot, widget):
        qtbot.addWidget(widget)
        assert widget.mapTool
        assert widget.bIdentify

    def test_identifyFeature(self, vector_feat, qtbot, widget):
        layer, _ = vector_feat('MULTIPOLYGON (((0 0, 1 1, 1 0, 0 0)))')
        QgsProject.instance().addMapLayer(layer)

        qtbot.addWidget(widget)
        qtbot.mouseClick(widget.bIdentify, Qt.LeftButton)

        assert iface.mapCanvas().mapTool().__class__ == IdentifyFeatureTool
        assert iface.mapCanvas().mapTool() == widget.mapTool

    def test_on_feature_changed(self, widget, vector_feat):
        layer, feature = vector_feat('PointZ (1, 1, 1)')
        widget.layer = layer

        widget.onFeatureChanged(feature)

        assert widget.featureGeometry is not None
        assert not QgsWkbTypes.hasZ(widget.featureGeometry.wkbType())
        assert layer.selectedFeatureCount() == 1
        assert feature.id() in layer.selectedFeatureIds()

    def test_on_layer_changed(self, widget, vector_feat):
        layer, feature = vector_feat('PointZ (1, 1, 1)')
        QgsProject.instance().addMapLayer(layer)
        widget.mMapLayerComboBox.setLayer(layer)

        widget.onLayerChanged()

        assert widget.layer == layer
        assert widget.cbFeature.layer() == layer
