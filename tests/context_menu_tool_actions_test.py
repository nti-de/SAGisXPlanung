import uuid

import pytest
from geoalchemy2 import WKTElement

from qgis.core import QgsAnnotationLayer, QgsAnnotationItem, QgsPointXY

from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_PTO
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.actions import MoveAnnotationItemAction

xid = 'a8a1beff-0057-47e1-b855-4be26fdfa4fb'


@pytest.fixture()
def xplan_item():
    item = XPlanungItem(xid=xid, xtype=XP_PTO)
    return item


@pytest.fixture()
def tpo() -> XP_PTO:
    tpo = XP_PTO()
    tpo.id = xid
    tpo.position = WKTElement('POINT (1 1)', srid=25833)
    tpo.schriftinhalt = 'test'
    tpo.skalierung = 0.5
    tpo.drehwinkel = 0
    return tpo


@pytest.fixture()
def move_annotation_action(xplan_item) -> MoveAnnotationItemAction:
    return MoveAnnotationItemAction(xplan_item, None)


class TestMoveAnnotationItemAction:

    def test_action_triggered(self, mocker, move_annotation_action, tpo):
        mocker.patch(
            'SAGisXPlanung.gui.actions.MoveAnnotationItemAction.beginMove',
            return_value=None
        )

        tpo.toCanvas(None)

        move_annotation_action.onActionTriggered(checked=False)

        assert move_annotation_action.annotation_layer
        assert isinstance(move_annotation_action.annotation_layer, QgsAnnotationLayer)
        assert move_annotation_action.annotation_item
        assert isinstance(move_annotation_action.annotation_item, QgsAnnotationItem)

    def test_set_center(self, mocker, tpo, move_annotation_action):
        point = QgsPointXY(10, 10)
        move_annotation_action.setCenter(point)

        assert move_annotation_action.annotation_item is None

        item = tpo.asFeature()
        move_annotation_action.annotation_item = item
        layer_mock = mocker.MagicMock()
        move_annotation_action.annotation_layer = layer_mock

        move_annotation_action.setCenter(point)

        assert move_annotation_action.annotation_item.point() == point
        layer_mock.triggerRepaint.assert_called_once()
