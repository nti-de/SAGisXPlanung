import logging
import os
from enum import Enum
from typing import Union

from qgis.gui import QgsMapToolIdentify, QgsMapCanvas, QgsHighlight, QgsMapMouseEvent
from qgis.core import (QgsIdentifyContext, QgsFeature, QgsMapLayer, QgsWkbTypes, QgsRectangle, QgsRenderedItemResults,
                       QgsRenderedAnnotationItemDetails, QgsProject, QgsAnnotationLayer, QgsAnnotationItem,
                       QgsAnnotationPointTextItem, QgsGeometry, QgsTextBackgroundSettings)
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import pyqtSignal, QPoint
from qgis.PyQt.QtGui import QIcon, QColor, QTransform

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.core.buildingtemplate.template_item import BuildingTemplateItem
from SAGisXPlanung.XPlan.feature_types import XP_Objekt
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry, MixedGeometry
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.widgets import QBuildingTemplateEdit
from SAGisXPlanung.utils import CLASSES, full_version_required_warning

logger = logging.getLogger(__name__)


class ActionType(Enum):
    AddPlanContent = 1
    AccessAttributes = 2
    AddAnnotationItem = 3
    HighlightObjectTreeItem = 4
    MultiEdit = 5


class ContextMenuTool(QgsMapToolIdentify):
    accessAttributesRequested = pyqtSignal(XPlanungItem)
    highlightObjectTreeRequested = pyqtSignal(XPlanungItem)
    multiEditRequested = pyqtSignal(list)  # List[XPlanungItem]
    featureSaved = pyqtSignal(XPlanungItem)

    def __init__(self, canvas: QgsMapCanvas, parent):
        self.canvas = canvas
        self.iface = iface
        self.highlight = None
        self.multi_edit_action = None

        super(ContextMenuTool, self).__init__(self.canvas)

        self.setParent(parent)

    def activate(self):
        iface.mainWindow().statusBar().showMessage('Feature auf der Karte auswählen')
        super(ContextMenuTool, self).activate()

    def deactivate(self):
        iface.mainWindow().statusBar().clearMessage()
        super(ContextMenuTool, self).deactivate()

    def menu(self, identify_results, map_position=None) -> QMenu:
        menu = QMenu()
        menu.aboutToHide.connect(self.delete_highlight)

        # identified layers
        for result in identify_results:
            self.add_plancontent_menu_entries(menu, result, map_position)

        return menu

    def add_plancontent_menu_entries(self, menu, result_item, map_position):
        layer: QgsMapLayer = result_item.mLayer
        feature: QgsFeature = result_item.mFeature

        layer_menu = menu.addMenu(self.iconForWkbType(layer.wkbType()), layer.name())
        menu_action = layer_menu.menuAction()
        menu_action.hovered.connect(lambda lyr=layer, feat=feature: self.menu_action_hovered(lyr, feat))
        if layer.customProperties().contains(f'xplanung/feat-{feature.id()}'):
            # simple geometries don't have attributes to show
            xtype = layer.customProperties().value(f'xplanung/type')
            if xtype == 'XP_SimpleGeometry':
                return

            if self.multi_edit_action is None and layer.selectedFeatureCount() > 0:
                self.add_multi_edit_menu_entries(layer, menu)

            self.createCommonMenuEntries(layer_menu, layer, feature.id(), map_position)

        else:
            layer_action = layer_menu.addAction('Als Planinhalt konfigurieren')
            layer_action.triggered.connect(lambda checked, lyr=layer, feat=feature:
                                           self.menu_action_triggered(ActionType.AddPlanContent, layer=lyr,
                                                                      feature=feat))
        return menu

    def add_multi_edit_menu_entries(self, layer, menu):
        items = []
        plan_xid = layer.customProperty(f'xplanung/plan-xid')
        xtype = layer.customProperty(f'xplanung/type')
        for feat in layer.selectedFeatures():
            xid = layer.customProperties().value(f'xplanung/feat-{feat.id()}')
            xplan_item = XPlanungItem(xid=xid, xtype=CLASSES[xtype], plan_xid=plan_xid)
            items.append(xplan_item)

        self.multi_edit_action = QAction(QIcon(os.path.join(BASE_DIR, 'gui/resources/edit_note.svg')),
                                         'Gewählte Objekte bearbeiten', menu)
        self.multi_edit_action.triggered.connect(lambda checked, arg=items:
                                                 self.menu_action_triggered(ActionType.MultiEdit, arg))

        if len(menu.actions()) > 0:
            before_action = menu.actions()[0]
            menu.insertAction(before_action, self.multi_edit_action)
            menu.insertSeparator(before_action)
        else:
            menu.addAction(self.multi_edit_action)
            menu.addSeparator()

    def createCommonMenuEntries(self, menu: QMenu, layer: QgsMapLayer, feat_id: int, map_position):
        xtype = layer.customProperties().value(f'xplanung/type')
        xplanung_id = layer.customProperties().value(f'xplanung/feat-{feat_id}')
        plan_xid = layer.customProperties().value(f'xplanung/plan-xid')
        xplan_item = XPlanungItem(xid=xplanung_id, xtype=CLASSES[xtype], plan_xid=plan_xid)

        highlight_action = menu.addAction('Im Objektbaum markieren')
        highlight_action.triggered.connect(lambda checked, xitem=xplan_item:
                                           self.menu_action_triggered(ActionType.HighlightObjectTreeItem, xitem))

        data_action = menu.addAction('Sachdaten abfragen')
        data_action.triggered.connect(lambda checked, xitem=xplan_item:
                                      self.menu_action_triggered(ActionType.AccessAttributes, xitem))

        # if plan content is an area, add option to annotate with PO
        if issubclass(xplan_item.xtype, (PolygonGeometry, MixedGeometry)) and issubclass(xplan_item.xtype, XP_Objekt):
            annotate_action = menu.addAction('Präsentationsobjekt hinzufügen')
            annotate_action.triggered.connect(lambda checked, xitem=xplan_item:
                self.menu_action_triggered(ActionType.AddAnnotationItem, xitem, map_position)
            )

    def menu_action_hovered(self, layer: QgsMapLayer, feature: Union[QgsFeature, QgsGeometry]):
        self.delete_highlight()
        self.highlight = QgsHighlight(self.canvas, feature, layer)
        self.highlight.setColor(QColor(255, 0, 0, 125))
        self.highlight.setBuffer(0.1)
        self.highlight.show()

    def menu_action_triggered(self, action_type: ActionType, *args, **kwargs):

        if action_type == ActionType.AddPlanContent:
            full_version_required_warning()
        elif action_type == ActionType.AddAnnotationItem:
            full_version_required_warning()
        elif action_type == ActionType.AccessAttributes:
            self.accessAttributesRequested.emit(*args)
        elif action_type == ActionType.HighlightObjectTreeItem:
            self.highlightObjectTreeRequested.emit(*args)
        elif action_type == ActionType.MultiEdit:
            full_version_required_warning()

    def canvasReleaseEvent(self, event: QgsMapMouseEvent):
        x = event.position().toPoint().x()
        y = event.position().toPoint().y()
        results = self.identify(x, y, QgsMapToolIdentify.IdentifyMode.TopDownAll, [],
                                QgsMapToolIdentify.Type.VectorLayer, QgsIdentifyContext())
        global_pos = self.canvas.mapToGlobal(QPoint(x + 5, y + 5))

        map_point = event.mapPoint()
        search_rect = QgsRectangle(map_point.x(), map_point.y(), map_point.x(), map_point.y())
        search_rect.grow(self.searchRadiusMU(self.canvas))

        # renderedItemResults: QgsRenderedItemResults = self.canvas.renderedItemResults(False)
        # annotation_items = renderedItemResults.renderedAnnotationItemsInBounds(search_rect)

        self.menu(results, map_position=map_point).exec(global_pos)

        super(ContextMenuTool, self).canvasReleaseEvent(event)
        self.multi_edit_action = None

    # from QGIS 3.20 use QgsIconUtils::iconForWkbType instead
    # https://www.qgis.org/api/classQgsIconUtils.html#a58d939a4422eb18db911ccd2aeebaa44
    def iconForWkbType(self, wkb_type):
        geometry_type = QgsWkbTypes.geometryType(wkb_type)
        if geometry_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QIcon(':/images/themes/default/mIconPolygonLayer.svg')
        if geometry_type == QgsWkbTypes.GeometryType.LineGeometry:
            return QIcon(':/images/themes/default/mIconLineLayer.svg')
        if geometry_type == QgsWkbTypes.GeometryType.PointGeometry:
            return QIcon(':/images/themes/default/mIconPointLayer.svg')

    def delete_highlight(self):
        if not self.highlight:
            return

        self.highlight.hide()
        self.canvas.scene().removeItem(self.highlight)
        self.highlight = None
