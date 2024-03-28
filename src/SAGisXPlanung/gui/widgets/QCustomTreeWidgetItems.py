import re
from dataclasses import dataclass
from enum import Enum

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape

from qgis.PyQt import QtWidgets, QtGui
from qgis.gui import QgsGeometryRubberBand, QgsVertexMarker
from qgis.core import QgsPolygon, QgsRectangle, QgsWkbTypes,  QgsLineString, QgsMultiLineString, QgsMultiPolygon
from qgis.utils import iface


class GeometryIntersectionType(Enum):
    """ Gibt an, welcher Grund einen Überschneidungsfehler hevorgerufen hat. """

    Planinhalt = 'Flächenschlussobjekt weist Überschneidung auf'
    Bereich = 'Planinhalt liegt nicht vollständig im Bereich'
    Plan = 'Bereich liegt nicht vollständig im Geltungsbereich des Plans'
    NotCovered = 'Kein Flächenschluss vorliegend'


@dataclass
class ValidationResult:
    xid: str
    xtype: type
    error_msg: str = None
    geom_wkt: str = None
    intersection_type: GeometryIntersectionType = None


class ValidationBaseTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """ Abstrakte Oberklasse für QTreeWidgetItems, die Fehler bei der Geometrievalidierung enthalten"""
    def __init__(self, validation_result: ValidationResult):
        super().__init__()

        self.validation_result = validation_result
        self.xplanung_id = validation_result.xid
        self.xplanung_type = validation_result.xtype
        self.setText(0, self.xplanung_type.__name__)
        self.setText(1, self.error_msg)
        self.isVisible = False

    def removeFromCanvas(self):
        raise NotImplementedError

    def displayErrorOnCanvas(self):
        raise NotImplementedError

    def extent(self):
        raise NotImplementedError


class ValidationGeometryErrorTreeWidgetItem(ValidationBaseTreeWidgetItem):
    """ QTreeWidgetItem, dass Daten zu einem Überschneidungsfehler bei der Geometrievalidierung hält"""

    def __init__(self, validation_result: ValidationResult):
        if validation_result.intersection_type is not None:
            self.error_msg = validation_result.intersection_type.value
        elif validation_result.error_msg is not None:
            self.error_msg = validation_result.error_msg
        else:
            self.error_msg = 'Fehler in der Geometrievalidierung'

        super().__init__(validation_result)

        wkt = self.validation_result.geom_wkt.strip()
        if re.match('LineString', wkt, re.I):
            self.geometry = QgsLineString()
        elif re.match('MultiLineString', wkt, re.I):
            self.geometry = QgsMultiLineString()
        elif re.match('Polygon', wkt, re.I):
            self.geometry = QgsPolygon()
        elif re.match('MultiPolygon', wkt, re.I):
            self.geometry = QgsMultiPolygon()
        self.geometry.fromWkt(self.validation_result.geom_wkt)
        self.rubber_band = QgsGeometryRubberBand(iface.mapCanvas(), QgsWkbTypes.geometryType(self.geometry.wkbType()))
        self.rubber_band.setFillColor(QtGui.QColor(0, 0, 0, 0))
        self.rubber_band.setStrokeWidth(3)
        self.rubber_band.setGeometry(self.geometry)
        self.removeFromCanvas()

    def __del__(self):
        iface.mapCanvas().scene().removeItem(self.rubber_band)

    def removeFromCanvas(self):
        self.rubber_band.hide()
        self.isVisible = False

    def displayErrorOnCanvas(self):
        self.rubber_band.show()
        self.isVisible = True

    def extent(self) -> QgsRectangle:
        return self.rubber_band.rect()
