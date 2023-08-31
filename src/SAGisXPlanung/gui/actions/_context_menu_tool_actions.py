from qgis.PyQt.QtCore import pyqtSlot, pyqtSignal, QObject, QEvent, Qt
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsPointXY, QgsAnnotationLayer, QgsGeometry
from qgis.utils import iface
from sqlalchemy.orm import load_only

from SAGisXPlanung import Session
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlanungItem import XPlanungItem


class MoveAnnotationItemAction(QAction):
    """ QAction zur Nutzung im ContextMenuTool. Kann auf Objekte des Typs XP_AbstraktesPräsentationsobjekt angewandt
        werden, um die Position der zugehörigen Annotationen auf der Karte zu verändern. """

    def __init__(self, item: XPlanungItem, parent=None):

        self.text = 'Präsentationsobjekt verschieben'
        self.xplan_item = item
        self.event_filter = None
        self.annotation_layer = None
        self.annotation_item = None

        super(MoveAnnotationItemAction, self).__init__(self.text, parent)

        self.triggered.connect(self.onActionTriggered)

    @pyqtSlot(bool)
    def onActionTriggered(self, checked: bool):
        self.event_filter = AnnotationMoveEventFilter(iface.mapCanvas(), self)

        self.annotation_layer: QgsAnnotationLayer = MapLayerRegistry().layerByFeature(self.xplan_item.xid)

        if not self.annotation_layer:
            return

        for item_id, item in self.annotation_layer.items().items():
            id_prop = self.annotation_layer.customProperties().value(f'xplanung/feat-{item_id}')
            if id_prop == str(self.xplan_item.xid):
                self.annotation_item = item
                break

        self.beginMove()

    def setCenter(self, point: QgsPointXY):
        if not self.annotation_item:
            return
        self.annotation_item.setPoint(point)
        self.annotation_layer.triggerRepaint()

    def beginMove(self):
        iface.mapCanvas().viewport().installEventFilter(self.event_filter)
        self.event_filter.initial_pos = self.annotation_item.point()

    def endMove(self):
        iface.mapCanvas().viewport().removeEventFilter(self.event_filter)

        with Session.begin() as session:
            xp_po = session.get(self.xplan_item.xtype, self.xplan_item.xid, [load_only('id', 'position')])

            xp_po.setGeometry(QgsGeometry.fromPointXY(self.event_filter.last_pos))


class AnnotationMoveEventFilter(QObject):

    def __init__(self, canvas, action, parent=None):
        self.canvas = canvas
        self.action = action

        self.last_pos = None
        self.initial_pos = None

        super(AnnotationMoveEventFilter, self).__init__(parent)

    def eventFilter(self, obj, event):
        # on mouse move let canvas item follow mouse position
        if event.type() == QEvent.MouseMove:
            point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            self.action.setCenter(point)
            self.last_pos = point
        # on left click dont propagate the event and finish moving the canvas item
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                return False
            if event.button() == Qt.LeftButton:
                self.action.endMove()
            if event.button() == Qt.RightButton:
                self.action.setCenter(self.initial_pos)
                self.initial_pos = None
                self.action.endMove()
            return True
        return False
