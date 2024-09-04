import functools
import logging
import os
from enum import Enum
from typing import Union

from qgis.gui import QgsMapToolIdentify, QgsMapCanvas, QgsHighlight, QgsMapMouseEvent
from qgis.core import (QgsIdentifyContext, QgsFeature, QgsMapLayer, QgsWkbTypes, QgsRectangle, QgsRenderedItemResults,
                       QgsRenderedAnnotationItemDetails, QgsProject, QgsAnnotationLayer, QgsAnnotationItem,
                       QgsAnnotationPointTextItem, QgsGeometry, QgsTextBackgroundSettings)
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMenu
from qgis.PyQt.QtCore import pyqtSignal, QPoint
from qgis.PyQt.QtGui import QIcon, QColor, QTransform

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.BuildingTemplateItem import BuildingTemplateItem
from SAGisXPlanung.XPlan.feature_types import XP_Objekt
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.po_annotations_dialog import CreateAnnotateDialog
from SAGisXPlanung.gui.actions import EditBuildingTemplateAction, MoveAnnotationItemAction
from SAGisXPlanung.gui.widgets import QBuildingTemplateEdit
from SAGisXPlanung.utils import CLASSES, full_version_required_warning

logger = logging.getLogger(__name__)


class ActionType(Enum):
    AddPlanContent = 1
    AccessAttributes = 2
    AddAnnotationItem = 3
    HighlightObjectTreeItem = 4


class ContextMenuTool(QgsMapToolIdentify):
    editBuildingTemplateRequested = pyqtSignal(QBuildingTemplateEdit)
    accessAttributesRequested = pyqtSignal(XPlanungItem)
    highlightObjectTreeRequested = pyqtSignal(XPlanungItem)
    featureSaved = pyqtSignal(XPlanungItem)

    def __init__(self, canvas: QgsMapCanvas, parent):
        self.canvas = canvas
        self.iface = iface
        self.highlight = None

        super(ContextMenuTool, self).__init__(self.canvas)

        self.setParent(parent)

    def activate(self):
        iface.mainWindow().statusBar().showMessage('Feature auf der Karte auswählen')
        super(ContextMenuTool, self).activate()

    def deactivate(self):
        iface.mainWindow().statusBar().clearMessage()
        super(ContextMenuTool, self).deactivate()

    def menu(self, identify_results, canvas_item=None, annotation_items=None) -> QMenu:
        menu = QMenu()
        menu.aboutToHide.connect(self.delete_highlight)

        # identified canvas items (e.g. XP_Nutzungsschablone)
        if canvas_item:
            canvas_item_menu = menu.addMenu(QIcon(os.path.join(BASE_DIR, 'gui/resources/table.svg')), canvas_item.xtype)
            edit_canvas_item_action = EditBuildingTemplateAction(canvas_item.parent, parent=menu)
            edit_canvas_item_action.editFormCreated.connect(lambda w: self.editBuildingTemplateRequested.emit(w))
            canvas_item_menu.addAction(edit_canvas_item_action)
            move_canvas_item_action = canvas_item_menu.addAction(f'Nutzungsschablone verschieben')
            move_canvas_item_action.triggered.connect(lambda c: canvas_item.beginMove())

        # identified annotation items (e.g SVG symbols)
        if annotation_items:
            for item_detail in annotation_items:  # type: QgsRenderedAnnotationItemDetails
                layer: QgsAnnotationLayer = QgsProject().instance().mapLayer(item_detail.layerId())
                item: QgsAnnotationItem = layer.item(item_detail.itemId())

                symbol_path = ':/images/themes/default/mIconFieldText.svg'

                # TODO: dont run the following statement in CI, it sometimes causes python segfaults
                # accessing item.format().background().type() seems to be problematic? maybe text annotation does not have background?
                if not os.environ.get('CI'):
                    if isinstance(item, QgsAnnotationPointTextItem) and item.format().background().type() == QgsTextBackgroundSettings.ShapeSVG:
                        symbol_path = item.format().background().svgFile()

                xtype = layer.customProperties().value(f'xplanung/type')
                annotation_item_menu = menu.addMenu(QIcon(symbol_path), xtype)
                if isinstance(item, QgsAnnotationPointTextItem):
                    geom = QgsGeometry.fromPointXY(item.point())
                else:
                    geom = QgsGeometry(item.geometry())
                annotation_item_menu.menuAction().hovered.connect(lambda lyr=layer, g=geom:
                                                                  self.menu_action_hovered(lyr, geom))

                # get details from custom property, add common actions + move annatotation action
                xplanung_id = layer.customProperties().value(f'xplanung/feat-{item_detail.itemId()}')
                plan_xid = layer.customProperties().value(f'xplanung/plan-xid')
                xplan_item = XPlanungItem(xid=xplanung_id, xtype=CLASSES[xtype], plan_xid=plan_xid)

                self.createCommonMenuEntries(annotation_item_menu, layer, item_detail.itemId())

                move_annotation_item_action = MoveAnnotationItemAction(xplan_item, menu)
                annotation_item_menu.addAction(move_annotation_item_action)

        # identified layers
        for result in identify_results:
            layer: QgsMapLayer = result.mLayer
            feature: QgsFeature = result.mFeature
            layer_menu = menu.addMenu(self.iconForWkbType(layer.wkbType()), layer.name())
            menu_action = layer_menu.menuAction()
            menu_action.hovered.connect(lambda lyr=layer, feat=feature: self.menu_action_hovered(lyr, feat))
            if layer.customProperties().contains(f'xplanung/feat-{feature.id()}'):
                # simple geometries don't have attributes to show
                xtype = layer.customProperties().value(f'xplanung/type')
                if xtype == 'XP_SimpleGeometry':
                    continue

                self.createCommonMenuEntries(layer_menu, layer, feature.id())

            else:
                layer_action = layer_menu.addAction('Als Planinhalt konfigurieren')
                layer_action.triggered.connect(lambda checked, lyr=layer, feat=feature:
                                               self.menu_action_triggered(ActionType.AddPlanContent, layer=lyr,
                                                                          feature=feat))
        return menu

    def createCommonMenuEntries(self, menu: QMenu, layer: QgsMapLayer, feat_id: str, is_annotation=False):
        xtype = layer.customProperties().value(f'xplanung/type')
        xplanung_id = layer.customProperties().value(f'xplanung/feat-{feat_id}')
        plan_xid = layer.customProperties().value(f'xplanung/plan-xid')
        xplan_item = XPlanungItem(xid=xplanung_id, xtype=CLASSES[xtype], plan_xid=plan_xid)

        highlight_action = menu.addAction('Im Objektbaum markieren')
        highlight_action.triggered.connect(lambda checked, xitem=xplan_item:
                                           self.menu_action_triggered(ActionType.HighlightObjectTreeItem,
                                                                      xplan_item=xitem))

        data_action = menu.addAction('Sachdaten abfragen')
        data_action.triggered.connect(lambda checked, xitem=xplan_item:
                                      self.menu_action_triggered(ActionType.AccessAttributes, xplan_item=xitem))

        if is_annotation:
            return

        # if plan content is an area, add option to annotate with PO
        if issubclass(xplan_item.xtype, PolygonGeometry) and issubclass(xplan_item.xtype, XP_Objekt):
            annotate_action = menu.addAction('Präsentationsobjekt hinzufügen')
            annotate_action.triggered.connect(
                functools.partial(self.menu_action_triggered, ActionType.AddAnnotationItem, xplan_item))

    def menu_action_hovered(self, layer: QgsMapLayer, feature: Union[QgsFeature, QgsGeometry]):
        self.delete_highlight()
        self.highlight = QgsHighlight(self.canvas, feature, layer)
        self.highlight.setColor(QColor(255, 0, 0, 125))
        self.highlight.setBuffer(0.1)
        self.highlight.show()

    def menu_action_triggered(self, action_type: ActionType, xplan_item: XPlanungItem = None, layer=None, feature=None):
        if action_type == ActionType.AddPlanContent:
            full_version_required_warning()
        elif action_type == ActionType.AddAnnotationItem:
            dialog = CreateAnnotateDialog(xplan_item)
            dialog.annotationSaved.connect(self.featureSaved.emit)
            dialog.show()
        elif action_type == ActionType.AccessAttributes:
            self.accessAttributesRequested.emit(xplan_item)
        elif action_type == ActionType.HighlightObjectTreeItem:
            self.highlightObjectTreeRequested.emit(xplan_item)

    def canvasReleaseEvent(self, event: QgsMapMouseEvent):
        results = self.identify(event.x(), event.y(), QgsMapToolIdentify.TopDownAll, [],
                                QgsMapToolIdentify.VectorLayer, QgsIdentifyContext())
        global_pos = self.canvas.mapToGlobal(QPoint(event.x() + 5, event.y() + 5))
        canvas_pos = self.canvas.mapToScene(event.pos())

        topmost_item = self.canvas.scene().itemAt(canvas_pos, QTransform())
        canvas_item = topmost_item if isinstance(topmost_item, BuildingTemplateItem) else None

        map_point = event.mapPoint()
        search_rect = QgsRectangle(map_point.x(), map_point.y(), map_point.x(), map_point.y())
        search_rect.grow(self.searchRadiusMU(self.canvas))

        renderedItemResults: QgsRenderedItemResults = self.canvas.renderedItemResults(False)
        annotation_items = renderedItemResults.renderedAnnotationItemsInBounds(search_rect)

        self.menu(results, canvas_item=canvas_item, annotation_items=annotation_items).exec(global_pos)

        super(ContextMenuTool, self).canvasReleaseEvent(event)

    # from QGIS 3.20 use QgsIconUtils::iconForWkbType instead
    # https://www.qgis.org/api/classQgsIconUtils.html#a58d939a4422eb18db911ccd2aeebaa44
    def iconForWkbType(self, wkb_type):
        geometry_type = QgsWkbTypes.geometryType(wkb_type)
        if geometry_type == QgsWkbTypes.PolygonGeometry:
            return QIcon(':/images/themes/default/mIconPolygonLayer.svg')
        if geometry_type == QgsWkbTypes.LineGeometry:
            return QIcon(':/images/themes/default/mIconLineLayer.svg')
        if geometry_type == QgsWkbTypes.PointGeometry:
            return QIcon(':/images/themes/default/mIconPointLayer.svg')

    def delete_highlight(self):
        if not self.highlight:
            return

        self.highlight.hide()
        self.canvas.scene().removeItem(self.highlight)
        self.highlight = None
