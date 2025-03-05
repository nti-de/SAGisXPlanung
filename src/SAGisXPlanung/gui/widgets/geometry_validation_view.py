import re
from typing import List

from qgis.PyQt.QtCore import QAbstractTableModel, QModelIndex, Qt
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QTreeView, QAbstractItemView, QMenu, QAction
from qgis.PyQt import sip
from qgis.gui import QgsGeometryRubberBand
from qgis.core import (QgsPolygon, QgsRectangle, QgsWkbTypes,  QgsLineString, QgsMultiLineString, QgsMultiPolygon,
                       QgsCircularString, QgsCompoundCurve, QgsCurvePolygon, QgsMultiCurve, QgsMultiSurface)
from qgis.utils import iface

from SAGisXPlanung.core.geometry_validation import ValidationResult
from SAGisXPlanung.gui.style import HighlightRowDelegate, HighlightRowProxyStyle


def _error_detail_message(validation_result: ValidationResult) -> str:
    detail_message = f'<qt>{validation_result.error_msg}'
    if validation_result.other_xid and validation_result.other_xtype:
        detail_message += (f'<br><br>Betroffene Objekte: <ul>'
                           f'<li>{validation_result.xtype.__name__}: {validation_result.xid}</li>'
                           f'<li>{validation_result.other_xtype.__name__}: {validation_result.other_xid}</li>'
                           f'</ul>')

    detail_message += '</qt>'
    return detail_message


class ValidationResultModel(QAbstractTableModel):
    def __init__(self, results: List[ValidationResult] = None, parent=None):
        super().__init__(parent)
        self.results = results or []
        self.headers = ["Fläche", "Fehler"]  # Column headers

    def rowCount(self, parent=QModelIndex()):
        return len(self.results)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            result = self.results[index.row()]
            if index.column() == 0:
                return result.xtype.__name__
            elif index.column() == 1:
                return result.error_msg if result.error_msg else ""
        if role == Qt.ToolTipRole:
            result = self.results[index.row()]
            return _error_detail_message(result)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def clear(self):
        self.beginResetModel()
        self.results = []
        self.endResetModel()

    def add_item(self, result: ValidationResult):
        self.beginInsertRows(QModelIndex(), len(self.results), len(self.results))
        self.results.append(result)
        self.endInsertRows()

    def add_items(self, new_results: List[ValidationResult]):
        if not new_results:
            return

        start_row = len(self.results)
        end_row = start_row + len(new_results) - 1

        self.beginInsertRows(QModelIndex(), start_row, end_row)
        self.results.extend(new_results)
        self.endInsertRows()


class ValidationTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.rubber_band = None
        self._model = ValidationResultModel()
        self.setModel(self._model)

        self.setItemDelegate(HighlightRowDelegate())
        self.proxy_style = HighlightRowProxyStyle('Fusion')
        self.proxy_style.setParent(self)
        self.setStyle(self.proxy_style)
        self.setMouseTracking(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.destroyed.connect(self.__del__)

    def __del__(self):
        if not sip.isdeleted(iface.mapCanvas()):
            iface.mapCanvas().scene().removeItem(self.rubber_band)

    def add_result_items(self, result_items: List[ValidationResult]):
        self._model.add_items(result_items)

    def clear(self):
        self._model.clear()

        if self.rubber_band and not sip.isdeleted(iface.mapCanvas()):
            iface.mapCanvas().scene().removeItem(self.rubber_band)

    def item_count(self) -> int:
        return self._model.rowCount()

    def show_context_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)
        flash_action = QAction(QIcon(':/images/themes/default/mActionScaleHighlightFeature.svg'),
                               'Geometriefehler auf Karte hervorheben')
        flash_action.triggered.connect(lambda: self.highlight_geometry_error(index))
        menu.addAction(flash_action)
        menu.exec_(self.viewport().mapToGlobal(position))

    def highlight_geometry_error(self, index: QModelIndex):
        """ Copy the error message of the selected row to the clipboard """
        item = self._model.results[index.row()]

        # create geometry from wkt
        # copy of QgsGeometryFactory::geomFromWkt because it's not available in python bindings
        # QgsGeometry::fromWkt does not work here and crashes QGIS -> has something to do with the wkt cache
        # but currently not able to figure the exact problem.
        wkt = item.geom_wkt.strip()
        if re.match('LineString', wkt, re.I):
            geometry = QgsLineString()
        elif re.match('MultiLineString', wkt, re.I):
            geometry = QgsMultiLineString()
        elif re.match('Polygon', wkt, re.I):
            geometry = QgsPolygon()
        elif re.match('MultiPolygon', wkt, re.I):
            geometry = QgsMultiPolygon()
        elif re.match('MultiSurface', wkt, re.I):
            geometry = QgsMultiSurface()
        elif re.match('MultiCurve', wkt, re.I):
            geometry = QgsMultiCurve()
        elif re.match('CurvePolygon', wkt, re.I):
            geometry = QgsCurvePolygon()
        elif re.match('CompoundCurve', wkt, re.I):
            geometry = QgsCompoundCurve()
        elif re.match('CircularString', wkt, re.I):
            geometry = QgsCircularString()
        else:
            raise ValueError(f'No matching abstract geometry type for wkt: {wkt}')

        geometry.fromWkt(wkt)

        self.rubber_band = QgsGeometryRubberBand(iface.mapCanvas(), QgsWkbTypes.geometryType(geometry.wkbType()))
        self.rubber_band.setFillColor(QColor(0, 0, 0, 0))
        self.rubber_band.setStrokeWidth(3)
        self.rubber_band.setGeometry(geometry)
        self.rubber_band.show()

        iface.mapCanvas().setCenter(self.rubber_band.rect().center())
        iface.mapCanvas().refresh()

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            self.highlight_geometry_error(index)
