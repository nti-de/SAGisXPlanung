import pytest
from mock.mock import MagicMock, AsyncMock

from qgis.PyQt.QtCore import QModelIndex, Qt
from qgis.utils import iface

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan, BP_Bereich
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.XPlanungDialog import XPlanungDialog
from SAGisXPlanung.utils import is_url
from SAGisXPlanung.gui.widgets.QExplorerView import ClassNode, XID_ROLE


@pytest.fixture
def dialog(mocker):
    mocker.patch(
        'SAGisXPlanung.gui.XPlanungDialog.QPlanComboBox.refresh',
        return_value=None
    )
    dialog = XPlanungDialog()
    return dialog


class TestXPlanungDialog_is_url:

    def test_is_url_valid(self):
        url = 'http://test.com'
        assert is_url(url)

    def test_is_url_invalid(self):
        url = 'smtp://test.com'
        assert is_url(url)


class TestXPlanungDialog:

    @pytest.mark.asyncio
    async def test_on_index_changed(self, dialog):
        # Setup
        details_dialog = dialog.details_dialog
        details_dialog.initPlanData = AsyncMock()
        export_button = dialog.bExport
        info_button = dialog.bInfo

        # index change to -1
        await dialog.onIndexChanged(-1)

        assert not export_button.isEnabled()
        assert not info_button.isEnabled()
        assert not details_dialog.isVisible()

        # index change to valid index 0
        await dialog.onIndexChanged(0)

        assert export_button.isEnabled()
        assert info_button.isEnabled()
        details_dialog.initPlanData.assert_called_once()


    def test_onIdentifyClicked(self, dialog, qtbot):
        qtbot.mouseClick(dialog.bIdentify, Qt.LeftButton)

        assert dialog.identifyTool is not None
        assert iface.mapCanvas().mapTool() == dialog.identifyTool

    @pytest.mark.asyncio
    async def test_onFeatureSaved(self, mocker, dialog):
        session_mock = mocker.MagicMock()
        obj_mock = mocker.MagicMock()
        session_mock.query.return_value.get.return_value = obj_mock
        mocker.patch("SAGisXPlanung.Session.begin").return_value.__enter__.return_value = session_mock

        bplan_item = XPlanungItem(xid='1', xtype=BP_Plan, plan_xid='1')
        bpbereich_item = XPlanungItem(xid='2', xtype=BP_Bereich, plan_xid='1')
        dialog.details_dialog.objectTree.model.addChild(ClassNode(bplan_item))
        dialog.details_dialog.plan_xid = '1'

        model = dialog.details_dialog.objectTree.model
        await dialog.onFeatureSaved(bpbereich_item)

        index_list = model.match(model.index(0, 0), XID_ROLE, bpbereich_item.xid, -1, Qt.MatchWildcard | Qt.MatchRecursive)
        assert index_list
        assert index_list[0].parent().isValid()
        assert index_list[0].internalPointer().flag_new

    @pytest.mark.asyncio
    async def test_selectTreeItem(self, mocker, dialog):
        session_mock = mocker.MagicMock()
        obj_mock = mocker.MagicMock()
        session_mock.query.return_value.get.return_value = obj_mock
        mocker.patch("SAGisXPlanung.Session.begin").return_value.__enter__.return_value = session_mock

        bplan_item = XPlanungItem(xid='1', xtype=BP_Plan, plan_xid='1')
        dialog.details_dialog.objectTree.model.addChild(ClassNode(bplan_item))
        dialog.details_dialog.plan_xid = '1'

        await dialog.selectTreeItem(bplan_item)

        index_list = dialog.details_dialog.objectTree.selectionModel().selectedIndexes()
        assert index_list
        assert index_list[0].data(Qt.DisplayRole) == 'BP_Plan'

