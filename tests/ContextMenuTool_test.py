import uuid

import pytest
from geoalchemy2 import WKTElement
from qgis.PyQt import QtTest

from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsAnnotationLayer, QgsRenderedAnnotationItemDetails, QgsProject
from qgis.gui import QgsHighlight, QgsMapToolIdentify
from qgis.utils import iface

from SAGisXPlanung.Tools.ContextMenuTool import ContextMenuTool, ActionType
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_PTO
from SAGisXPlanung.XPlanungItem import XPlanungItem


@pytest.fixture()
def tool(mocker) -> ContextMenuTool:
    return ContextMenuTool(iface.mapCanvas(), None)


@pytest.fixture()
def feat(mocker) -> QgsFeature:
    feat = QgsFeature()
    g = QgsGeometry.fromWkt('Point(10 10)')
    feat.setGeometry(g)
    return feat


@pytest.fixture()
def vl(feat) -> QgsVectorLayer:
    layer = QgsVectorLayer('point?crs=epsg:4326', "Scratch point layer",  "memory")
    dp = layer.dataProvider()
    layer.startEditing()
    _, newFeatures = dp.addFeatures([feat])
    layer.commitChanges()
    return layer


@pytest.fixture()
def al() -> QgsAnnotationLayer:
    tpo = XP_PTO()
    tpo.id = uuid.uuid4()
    tpo.position = WKTElement('POINT (1 1)', srid=25833)
    tpo.schriftinhalt = 'test'
    tpo.skalierung = 0.5
    tpo.drehwinkel = 0
    layer: QgsAnnotationLayer = tpo.asLayer(tpo.position.srid, uuid.uuid4(), 'TestLayer')
    item = tpo.asFeature()
    layer.addItem(item)
    return layer


class TestContextMenuTool:

    def delete_highlight(self, tool: ContextMenuTool, vl, feat):
        tool.highlight = QgsHighlight(iface.mapCanvas(), feat, vl)
        tool.delete_highlight()
        assert tool.highlight is None
        assert len(tool.canvas.scene().items()) == 0

    def test_menu_action_hovered(self, tool: ContextMenuTool, vl, feat):
        prev = len(tool.canvas.scene().items())
        tool.menu_action_hovered(vl, feat)
        assert tool.highlight
        assert len(tool.canvas.scene().items()) == prev + 1

    def test_menu_action_accessAttributes(self, tool: ContextMenuTool):
        spy = QtTest.QSignalSpy(tool.accessAttributesRequested)
        tool.menu_action_triggered(ActionType.AccessAttributes, XPlanungItem(xid='1', xtype=None, plan_xid='2'))
        assert len(spy) == 1

    def test_menu_action_highlightObjectTree(self, tool: ContextMenuTool):
        spy = QtTest.QSignalSpy(tool.highlightObjectTreeRequested)
        tool.menu_action_triggered(ActionType.HighlightObjectTreeItem, XPlanungItem(xid='1', xtype=None, plan_xid='2'))
        assert len(spy) == 1

    def test_menu(self, tool: ContextMenuTool, vl, feat, al):
        xplan_layer = vl.clone()
        xplan_layer.setCustomProperty('xplanung/type', 'BP_BauGrenze')
        xplan_layer.setCustomProperty('xplanung/plan-name', 'Plan1')
        xplan_layer.setCustomProperty('xplanung/feat-1', '14356316-413643-46136-413')
        results = [QgsMapToolIdentify.IdentifyResult(vl, feat, {'test': '1'}),
                   QgsMapToolIdentify.IdentifyResult(xplan_layer, feat, {'test': '2'})]
        QgsProject().instance().addMapLayer(al)

        a_items = [QgsRenderedAnnotationItemDetails(al.id(), item_id) for item_id in al.items().keys()]
        menu = tool.menu(results, annotation_items=a_items)

        assert len(menu.actions()) == 3
        assert len(menu.actions()[0].menu().actions()) == 3
