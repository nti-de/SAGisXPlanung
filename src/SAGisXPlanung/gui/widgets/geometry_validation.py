import re
from dataclasses import dataclass
from enum import Enum

from qgis.PyQt import QtWidgets, QtGui
from qgis.gui import QgsGeometryRubberBand
from qgis.core import (QgsPolygon, QgsRectangle, QgsWkbTypes,  QgsLineString, QgsMultiLineString, QgsMultiPolygon,
                    QgsCircularString, QgsCompoundCurve, QgsCurvePolygon, QgsMultiCurve, QgsMultiSurface)
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
    other_xid: str = None
    other_xtype: type = None


def _error_detail_message(error_msg: str, validation_result: ValidationResult) -> str:
    detail_message = f'<qt>{error_msg}'
    if validation_result.other_xid and validation_result.other_xtype:
        detail_message += (f'<br><br>Betroffene Objekte: <ul>'
                           f'<li>{validation_result.xtype.__name__}: {validation_result.xid}</li>'
                           f'<li>{validation_result.other_xtype.__name__}: {validation_result.other_xid}</li>'
                           f'</ul>')

    detail_message += '</qt>'
    return detail_message


class ValidationBaseTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """ Abstrakte Oberklasse für QTreeWidgetItems, die Fehler bei der Geometrievalidierung enthalten"""
    def __init__(self, validation_result: ValidationResult):
        super().__init__()

        self.validation_result = validation_result
        self.xplanung_id = validation_result.xid
        self.xplanung_type = validation_result.xtype
        self.setText(0, self.xplanung_type.__name__)
        self.setText(1, self.error_msg)
        self.detail_error = _error_detail_message(self.error_msg, self.validation_result)
        self.setToolTip(0, self.detail_error)
        self.setToolTip(1, self.detail_error)
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

        # create geometry from wkt
        # copy of QgsGeometryFactory::geomFromWkt because it's not available in python bindings
        # QgsGeometry::fromWkt does not work here and crashes QGIS -> has something to do with the wkt cache
        # but currently not able to figure the exact problem.
        wkt = self.validation_result.geom_wkt.strip()
        if re.match('LineString', wkt, re.I):
            self.geometry = QgsLineString()
        elif re.match('MultiLineString', wkt, re.I):
            self.geometry = QgsMultiLineString()
        elif re.match('Polygon', wkt, re.I):
            self.geometry = QgsPolygon()
        elif re.match('MultiPolygon', wkt, re.I):
            self.geometry = QgsMultiPolygon()
        elif re.match('MultiSurface', wkt, re.I):
            self.geometry = QgsMultiSurface()
        elif re.match('MultiCurve', wkt, re.I):
            self.geometry = QgsMultiCurve()
        elif re.match('CurvePolygon', wkt, re.I):
            self.geometry = QgsCurvePolygon()
        elif re.match('CompoundCurve', wkt, re.I):
            self.geometry = QgsCompoundCurve()
        elif re.match('CircularString', wkt, re.I):
            self.geometry = QgsCircularString()
        else:
            raise ValueError(f'No matching abstract geometry type for wkt: {wkt}')

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
