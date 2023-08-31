from qgis.core import QgsGeometry, QgsWkbTypes

from SAGisXPlanung.GML.geometry import enforce_wkb_constraints, geometry_from_spatial_element, geom_type_as_layer_url
from geoalchemy2 import WKBElement, WKTElement


class TestGeometry_enforce_wkb_constraints:

    def test_enforce_wkb_constraints_using_ewkb(self):
        ewkb = '0103000020E6100000010000000500000000000000000000000000000000000000000000000000F03F0000000000000000000000000000F03F000000000000F03F0000000000000000000000000000F03F00000000000000000000000000000000'
        wkb = '0103000000010000000500000000000000000000000000000000000000000000000000F03F0000000000000000000000000000F03F000000000000F03F0000000000000000000000000000F03F00000000000000000000000000000000'

        assert len(ewkb) == len(wkb) + 8  # wkb should be 4 bytes less -> 8 digits in hex
        assert enforce_wkb_constraints(ewkb) == wkb

    def test_enforce_wkb_constraints_using_wkb(self):
        wkb = '0106000000010000000103000000010000000400000000000000000000000000000000000000000000000000f03f000000000000f03f000000000000f03f000000000000000000000000000000000000000000000000'

        assert enforce_wkb_constraints(wkb) == wkb


class TestGeometry_geometry_from_spatial_element:

    def test_enforce_wkb_constraints_using_wkt_element(self):
        wkt_element = WKTElement('POINT (1 1)', srid=25833)
        geom = geometry_from_spatial_element(wkt_element)
        assert isinstance(geom, QgsGeometry)
        assert not geom.isEmpty() and not geom.isNull()
        assert geom.asPoint().x() == 1
        assert geom.asPoint().y() == 1

    def test_enforce_wkb_constraints_using_wkb_element(self):
        wkb = '0106000000010000000103000000010000000400000000000000000000000000000000000000000000000000f03f000000000000f03f000000000000f03f000000000000000000000000000000000000000000000000'
        wkb_element = WKBElement(bytes.fromhex(wkb), srid=25833)
        geom = geometry_from_spatial_element(wkb_element)
        assert isinstance(geom, QgsGeometry)
        assert not geom.isEmpty() and not geom.isNull()


class TestGeometry_geom_type_as_layer_url:

    def test_geom_type_as_layer_url(self):
        assert geom_type_as_layer_url(QgsWkbTypes.PointGeometry).lower() == 'point'
        assert geom_type_as_layer_url(QgsWkbTypes.LineGeometry).lower() == 'linestring'
        assert geom_type_as_layer_url(QgsWkbTypes.PolygonGeometry).lower() == 'polygon'
