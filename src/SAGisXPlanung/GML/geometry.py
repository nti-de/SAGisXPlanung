from typing import Union

from geoalchemy2 import WKBElement, WKTElement
from qgis.core import QgsGeometry, QgsWkbTypes

from SAGisXPlanung.XPlan.types import GeometryType

SRID_FLAG = 0x20000000  # flag byte denoting that a srid is embedded within EWKB


def enforce_wkb_constraints(ewkb: str) -> str:
    """ Enforces correctness of WKB hex string by converting possible EWKB to WKB in order to create QgsGeometry"""
    geomType_uint32 = int(int(ewkb[2:10], 16).to_bytes(4, byteorder='little').hex(), 16)
    if geomType_uint32 & SRID_FLAG == SRID_FLAG:
        geomType_uint32 = ~SRID_FLAG & geomType_uint32
        geomType_hex = geomType_uint32.to_bytes(4, byteorder='little').hex()
        ewkb = ewkb[:2] + geomType_hex + ewkb[18:]

    return ewkb


def geometry_from_spatial_element(element: Union[WKBElement, WKTElement]) -> QgsGeometry:
    """ Converts a geometry coming from a ORM object to a QgsGeometry object"""
    if isinstance(element, WKTElement):
        geom = QgsGeometry.fromWkt(element.data)
        return geom
    elif isinstance(element, WKBElement):
        wkb_hex = enforce_wkb_constraints(element.data.hex())
        geom = QgsGeometry()
        geom.fromWkb(bytes.fromhex(wkb_hex))
        return geom
    raise Exception('Could not convert to geometry. No WKBElement/WKTElement given')


def geom_type_as_layer_url(geom_type: GeometryType) -> str:
    """ Converts a GeometryType to a string that can be used in a layer url.
        This is required because the displayString returns 'Line' which is not accepted by QgsVectorLayer provider"""
    if geom_type == QgsWkbTypes.LineGeometry:
        return 'linestring'
    else:
        return QgsWkbTypes.geometryDisplayString(geom_type)
