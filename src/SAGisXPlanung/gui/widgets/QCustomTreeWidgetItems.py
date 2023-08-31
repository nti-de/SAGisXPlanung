from enum import Enum

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape

from qgis.PyQt import QtWidgets, QtGui
from qgis.gui import QgsGeometryRubberBand, QgsVertexMarker
from qgis.core import QgsPolygon, QgsWkbTypes, QgsPointXY, QgsRectangle, QgsGeometry
from qgis.utils import iface


class GeometryIntersectionType(Enum):
    """ Gibt an, welcher Grund einen Überschneidungsfehler hevorgerufen hat. """

    Planinhalt = 'Flächenschlussobjekt weist Überschneidung auf'
    Bereich = 'Planinhalt liegt nicht vollständig im Bereich'
    Plan = 'Bereich liegt nicht vollständig im Geltungsbereich des Plans'
    NotCovered = 'Kein Flächenschluss vorliegend'


class QFilePathTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """ QTreeWidgetItem, dass zusätzlich einen Dateipfad speichert.
    Nützlich für die Auswahl von Dateien in einem QTreeWidget """
    def __init__(self, *args, **kwargs):
        self.filepath = kwargs.pop('filepath')
        super(QFilePathTreeWidgetItem, self).__init__(*args, **kwargs)


class QIdentifierTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """ QTreeWidgetItem, dass zusätzlich die UUID und die Klasse eines Objekts des XPlanung Objektmodells speichert. """
    def __init__(self, *args, uid=None, cls_type=None, parent_attribute=None, **kwargs):
        self.xplanung_id = uid
        self.xplanung_type = cls_type
        self.parent_attribute = parent_attribute
        super().__init__(*args, **kwargs)


class QGeometryValidationTreeWidgetItem(QIdentifierTreeWidgetItem):
    """ Abstrakte Oberklasse für QTreeWidgetItems, die Fehler bei der Geometrievalidierung enthalten"""
    def __init__(self, *args, uid=None, cls_type=None, error_msg=None, **kwargs):
        super().__init__(*args, uid=uid, cls_type=cls_type, **kwargs)
        self.error_msg = error_msg
        self.setText(0, self.xplanung_type.__name__)
        self.setText(1, self.error_msg)
        self.isVisible = False

    def removeFromCanvas(self):
        raise NotImplementedError

    def displayErrorOnCanvas(self):
        raise NotImplementedError

    def extent(self):
        raise NotImplementedError


class QGeometryPolygonTreeWidgetItem(QGeometryValidationTreeWidgetItem):
    """ QTreeWidgetItem, dass Daten zu einem Überschneidungsfehler bei der Geometrievalidierung hält"""

    def __init__(self, *args, uid=None, cls_type=None, polygon=None,
                 intersection_type=GeometryIntersectionType.Planinhalt, **kwargs):
        self.error_msg = intersection_type.value
        super().__init__(*args, uid=uid, cls_type=cls_type, error_msg=self.error_msg, **kwargs)

        self.polygon = QgsPolygon()
        self.polygon.fromWkt(polygon)
        self.rubber_band = QgsGeometryRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setFillColor(QtGui.QColor(0, 0, 0, 0))
        self.rubber_band.setStrokeWidth(3)
        self.rubber_band.setGeometry(self.polygon)
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


class QGeometryDuplicateVerticesTreeWidgetItem(QGeometryValidationTreeWidgetItem):
    """ QTreeWidgetItem, dass Daten zu einem Stützpunktfehler bei der Geometrievalidierung hält"""
    def __init__(self, *args, uid=None, cls_type=None, polygon=None, **kwargs):
        self.error_msg = f'Planinhalt besitzt doppelte Stützpunkte'
        super().__init__(*args, uid=uid, cls_type=cls_type, error_msg=self.error_msg, **kwargs)
        self.polygon = QgsPolygon()
        self.polygon.fromWkt(polygon)
        self.rubber_band = QgsGeometryRubberBand(iface.mapCanvas(), QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setFillColor(QtGui.QColor(0, 0, 0, 0))
        self.rubber_band.setStrokeWidth(3)
        self.rubber_band.setVertexDrawingEnabled(False)
        self.rubber_band.setGeometry(self.polygon)
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


class QGeometryInvalidVerticesTreeWidgetItem(QGeometryValidationTreeWidgetItem):
    """ QTreeWidgetItem, dass Daten zu einem Stützpunkten enthält, die die Flächenschlussbedingung nicht erfüllen """
    def __init__(self, *args, uid=None, cls_type=None, vertices=None, **kwargs):
        self.error_msg = f'Stützpunkte erfüllen den Flächenschluss nicht'
        super().__init__(*args, uid=uid, cls_type=cls_type, error_msg=self.error_msg, **kwargs)

        self.vertex_markers = []
        for vertex in vertices:
            marker = QgsVertexMarker(iface.mapCanvas())
            marker.setCenter(QgsPointXY(vertex[0], vertex[1]))
            marker.setIconSize(5)
            marker.setPenWidth(2)
            marker.hide()
            self.vertex_markers.append(marker)

    def __del__(self):
        for marker in self.vertex_markers:
            iface.mapCanvas().scene().removeItem(marker)

    def removeFromCanvas(self):
        for marker in self.vertex_markers:
            marker.hide()
        self.isVisible = False

    def displayErrorOnCanvas(self):
        for marker in self.vertex_markers:
            marker.show()
        self.isVisible = True

    def extent(self) -> QgsRectangle:
        marker_geometries = [QgsGeometry.fromPointXY(marker.center()) for marker in self.vertex_markers]
        collection = QgsGeometry.collectGeometry(marker_geometries)
        return collection.boundingBox()
