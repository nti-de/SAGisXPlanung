import os
import uuid

import pytest
from unittest.mock import MagicMock

from geoalchemy2 import WKTElement
from qgis.core import QgsProject

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_PPO
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.widgets.QAttributeEditAnnotationItem import QAttributeEditAnnotationItem

xid = 'a8a1beff-0057-47e1-b855-4be26fdfa4fb'
plan_xid = 'c52aeb9d-34e2-4eca-b56b-e3f3752c94dd'


@pytest.fixture()
def xplan_item():
    item = XPlanungItem(xid=xid, xtype=XP_PPO, plan_xid=plan_xid)
    return item


@pytest.fixture()
def ppo():
    xp_ppo = XP_PPO()
    xp_ppo.id = xid
    xp_ppo.symbol_path = os.path.join('symbole', 'BP_Wasser', 'Hafen.svg')
    xp_ppo.skalierung = 0.5
    xp_ppo.drehwinkel = 0

    xp_ppo.position = WKTElement('POINT (1 1)', srid=25833)
    return xp_ppo


@pytest.fixture(scope="session")
def registry() -> MapLayerRegistry:
    reg = MapLayerRegistry()
    return reg


@pytest.fixture(autouse=True)
def clear_registry_after_test(registry):
    yield

    registry._layers = []
    QgsProject().instance().removeAllMapLayers()


@pytest.fixture
def widget(mocker, xplan_item, registry, ppo):
    mocker.patch("SAGisXPlanung.gui.widgets.QAttributeEditAnnotationItem.QAttributeEditAnnotationItem.set_form_values")

    root = QgsProject.instance().layerTreeRoot()
    group = root.addGroup("TestGroup")
    ppo.toCanvas(group, plan_xid=plan_xid)
    return QAttributeEditAnnotationItem(
        xplanung_item=xplan_item,
        data=[['drehwinkel', 0], ['skalierung', 0.21]]
    )


class TestAttributeEditAnnotationItem:

    @pytest.mark.skipif('GITHUB_ACTION' in os.environ, reason="does not run on qgis_testrunner.sh")
    @pytest.mark.asyncio
    async def test_annotation_item_svg_selected(self, mocker, widget):
        mocker.patch("SAGisXPlanung.gui.widgets.QAttributeEdit.QAttributeEdit.onAttributeChanged")
        assert isinstance(widget, QAttributeEditAnnotationItem)
        assert widget._annotation_layer is not None
        assert widget._annotation_item is not None

        path = os.path.join('symbole', 'BP_Wasser', 'Ueberschwemmungsgebiet.svg')
        await widget.onSvgSelected(path)

        assert widget._annotation_item.format().background().svgFile() == os.path.join(BASE_DIR, path)
