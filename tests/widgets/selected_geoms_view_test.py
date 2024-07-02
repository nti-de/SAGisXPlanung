import sys

import pytest
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsWkbTypes

from SAGisXPlanung.gui.widgets import QSelectedGeometriesView


@pytest.fixture
def view():
    feat = QgsFeature()
    g = QgsGeometry.fromWkt('Point(10 10)')
    feat.setGeometry(g)
    layer = QgsVectorLayer('point?crs=epsg:4326', "Scratch point layer", "memory")
    dp = layer.dataProvider()
    layer.startEditing()
    dp.addFeature(feat)
    layer.commitChanges()
    return QSelectedGeometriesView(data=[[feat.id()]], layer=layer)


class TestQSelectedGeometriesView:

    def test_itemCount(self, view):
        assert view.itemCount() == 1

        new_feat = QgsFeature()
        g = QgsGeometry.fromWkt('Point(20 20)')
        new_feat.setGeometry(g)
        view.model.addChild([new_feat.id()])

        assert view.itemCount() == 2

    def test_geometries(self, view):
        feat_with_z = QgsFeature()
        g = QgsGeometry.fromWkt('PointZ(20 20 20)')
        feat_with_z.setGeometry(g)
        view.model.addChild([feat_with_z.id()])

        assert len(view.geometries()) == 2
        assert not any(QgsWkbTypes.hasZ(geom.wkbType()) for geom in view.geometries())