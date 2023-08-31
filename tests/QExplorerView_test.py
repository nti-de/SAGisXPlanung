import uuid

import pytest

from qgis.PyQt.QtCore import QModelIndex, QItemSelection
from qgis.PyQt.QtTest import QSignalSpy

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.BPlan.BP_Bebauung.data_types import BP_Dachgestaltung
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche
from SAGisXPlanung.XPlan.data_types import XP_VerfahrensMerkmal
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.style import FlagNewRole
from SAGisXPlanung.gui.widgets.QExplorerView import ExplorerTreeModel, ClassNode, QExplorerView, XID_ROLE

xid = 'a8a1beff-0057-47e1-b855-4be26fdfa4fb'

@pytest.fixture()
def xplan_item():
    item = XPlanungItem(xid=xid, xtype=BP_Plan)
    return item


@pytest.fixture()
def view():
    return QExplorerView()


class TestQExplorerView:

    def test_inserting(self, xplan_item, view, qtmodeltester):
        model = view.model

        node = ClassNode(xplan_item, new=True)
        model.addChild(node)

        assert model._root.childCount() == 1
        assert model.data(model.index(0, 0)) == 'BP_Plan'
        assert model.data(model.index(0, 0), FlagNewRole)
        assert model.data(model.index(0, 0), XID_ROLE) == xid
        qtmodeltester.check(model)

    def test_adding_multiple_clearing(self, xplan_item, view, qtmodeltester):
        model = view.model

        node1 = ClassNode(xplan_item)
        node2 = ClassNode(xplan_item)
        model.addChild(node1)
        model.addChild(node2, node1)

        qtmodeltester.check(model)
        assert model._root.childCount() == 1
        assert node1.row() == 0
        assert node1.childCount() == 1

        view.clear()
        assert model._root.childCount() == 0
        qtmodeltester.check(model)

    def test_adding_multiple_remove(self, xplan_item, view, qtmodeltester):
        model = view.model

        node1 = ClassNode(xplan_item)
        node2 = ClassNode(xplan_item)
        node3 = ClassNode(xplan_item)
        node4 = ClassNode(xplan_item)
        model.addChild(node1)
        model.addChild(node3)
        model.addChild(node2, node1)
        model.addChild(node4, node1)

        qtmodeltester.check(model)
        assert model._root.childCount() == 2
        assert node3.row() == 1
        assert node1.childCount() == 2
        assert node2.row() == 0
        assert node4.row() == 1

        spy = QSignalSpy(view.model.rowsRemoved)
        view.removeItem(node2)
        assert len(spy) == 1
        assert node1.childCount() == 1
        assert node2.parent() is None
        assert node4.row() == 0
        qtmodeltester.check(model)

    def test_sorting_alphabetically(self, view, qtmodeltester):
        item1 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Plan)
        item2 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_BaugebietsTeilFlaeche)
        item3 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Dachgestaltung)

        node1 = ClassNode(item1)
        node2 = ClassNode(item2)
        node3 = ClassNode(item3)
        view.model.addChild(node1)
        view.model.addChild(node2, node1)

        view.sort(1)

        qtmodeltester.check(view.proxy)
        qtmodeltester.check(view.proxy.sourceModel())
        assert view.proxy.rowCount(QModelIndex()) == 2
        assert view.proxy.data(view.proxy.index(0, 0)) == 'BP_BaugebietsTeilFlaeche'
        assert view.proxy.data(view.proxy.index(1, 0)) == 'BP_Plan'

        # test automatic sorting after adding additional node
        view.model.addChild(node3, node2)

        qtmodeltester.check(view.proxy)
        qtmodeltester.check(view.proxy.sourceModel())
        assert view.proxy.rowCount(QModelIndex()) == 3
        assert view.proxy.data(view.proxy.index(0, 0)) == 'BP_BaugebietsTeilFlaeche'
        assert view.proxy.data(view.proxy.index(1, 0)) == 'BP_Dachgestaltung'
        assert view.proxy.data(view.proxy.index(2, 0)) == 'BP_Plan'

    def test_sorting_category(self, view, qtmodeltester):
        item1 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Plan)
        item2 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_BaugebietsTeilFlaeche)
        item3 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Dachgestaltung)

        node1 = ClassNode(item1)
        node2 = ClassNode(item2)
        node3 = ClassNode(item3)
        view.model.addChild(node1)
        view.model.addChild(node2, node1)
        view.model.addChild(node3, node1)

        view.sort(2)

        qtmodeltester.check(view.proxy)
        qtmodeltester.check(view.proxy.sourceModel())
        cat_proxy = view.proxy.sourceModel()
        assert cat_proxy.rowCount(QModelIndex()) == 2
        first_cat_index = cat_proxy.index(0, 0)
        second_cat_index = cat_proxy.index(1, 0)
        assert first_cat_index.isValid()
        assert second_cat_index.isValid()
        assert cat_proxy.data(first_cat_index) == 'BP_Basisobjekte'
        assert cat_proxy.data(second_cat_index) == 'BP_Bebauung'
        assert cat_proxy.rowCount(first_cat_index) == 1
        assert cat_proxy.rowCount(second_cat_index) == 2
        first_cat_first_child_index = cat_proxy.index(0, 0, first_cat_index)
        assert first_cat_first_child_index.isValid()
        assert first_cat_first_child_index.data() == 'BP_Plan'
        assert first_cat_first_child_index.internalPointer().xplan_module == 'BP_Basisobjekte'
        assert first_cat_first_child_index.parent().isValid()
        assert first_cat_first_child_index.parent() == first_cat_index
        assert first_cat_first_child_index.parent().data() == 'BP_Basisobjekte'
        assert not first_cat_first_child_index.parent().parent().isValid()
        second_cat_first_child_index = cat_proxy.index(0, 0, second_cat_index)
        assert second_cat_first_child_index.isValid()
        assert second_cat_first_child_index.internalPointer().xplan_module == 'BP_Bebauung'
        assert second_cat_first_child_index.data() == 'BP_BaugebietsTeilFlaeche'
        second_cat_second_child_index = cat_proxy.index(1, 0, second_cat_index)
        assert second_cat_second_child_index.isValid()
        assert second_cat_second_child_index.internalPointer().xplan_module == 'BP_Bebauung'
        assert second_cat_second_child_index.data() == 'BP_Dachgestaltung'

    def test_filter_for_id(self, xplan_item, view, qtmodeltester):
        xid1 = str(uuid.uuid4())
        xid2 = str(uuid.uuid4())
        item1 = XPlanungItem(xid=xid1, xtype=BP_Plan)
        item2 = XPlanungItem(xid=xid2, xtype=BP_BaugebietsTeilFlaeche)
        item3 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Dachgestaltung)

        node1 = ClassNode(item1)
        node2 = ClassNode(item2)
        node3 = ClassNode(item3)
        view.model.addChild(node1)
        view.model.addChild(node2, node1)
        view.model.addChild(node3, node1)

        top_index = view.proxy.index(0, 0, QModelIndex())
        assert view.proxy.rowCount(top_index) == 2

        # filter for parent
        view.proxy.setFilterRegularExpression(xid1[:5])

        assert view.proxy.rowCount(QModelIndex()) == 1
        assert view.proxy.rowCount(top_index) == 0

        # filter for child
        view.proxy.setFilterRegularExpression(xid2)

        assert view.proxy.rowCount(top_index) == 1
        child_index = view.proxy.index(0, 0, top_index)
        assert child_index.isValid()
        assert child_index.data() == 'BP_BaugebietsTeilFlaeche'

    def test_filter_for_object_type(self, xplan_item, view, qtmodeltester):
        item1 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Plan)
        item2 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_BaugebietsTeilFlaeche)
        item3 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Dachgestaltung)

        node1 = ClassNode(item1)
        node2 = ClassNode(item2)
        node3 = ClassNode(item3)
        view.model.addChild(node1)
        view.model.addChild(node2, node1)
        view.model.addChild(node3, node1)

        top_index = view.proxy.index(0, 0, QModelIndex())
        assert view.proxy.rowCount(top_index) == 2

        # filter for parent
        view.proxy.setFilterRegularExpression('plan')

        assert view.proxy.rowCount(QModelIndex()) == 1
        assert view.proxy.rowCount(top_index) == 0

        # filter for child
        view.proxy.setFilterRegularExpression('baugebiet')

        assert view.proxy.rowCount(top_index) == 1
        child_index = view.proxy.index(0, 0, top_index)
        assert child_index.isValid()
        assert child_index.data() == 'BP_BaugebietsTeilFlaeche'

    def test_three_level_and_signals(self, view, qtmodeltester):
        item1 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Plan)
        item2 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_BaugebietsTeilFlaeche)
        item3 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Dachgestaltung)
        item4 = XPlanungItem(xid=str(uuid.uuid4()), xtype=XP_VerfahrensMerkmal)

        node1 = ClassNode(item1)
        node2 = ClassNode(item2)
        node3 = ClassNode(item3)
        node4 = ClassNode(item4)

        spy = QSignalSpy(view.model.rowsInserted)
        view.model.addChild(node1)
        view.model.addChild(node2, node1)
        view.model.addChild(node3, node2)
        view.model.addChild(node4, node1)
        assert len(spy) == 4

        qtmodeltester.check(view.proxy)
        qtmodeltester.check(view.proxy.sourceModel())

        first_level_index = view.proxy.index(0, 0)
        assert first_level_index.data() == 'BP_Plan'
        assert view.proxy.rowCount(first_level_index) == 2
        second_level_index = view.proxy.index(0, 0, first_level_index)
        assert second_level_index.data() == 'BP_BaugebietsTeilFlaeche'
        assert view.proxy.rowCount(second_level_index) == 1
        second_level_index = view.proxy.index(1, 0, first_level_index)
        assert second_level_index.data() == 'XP_VerfahrensMerkmal'
        assert view.proxy.rowCount(second_level_index) == 0

        first_level_index = view.proxy.sourceModel().index(0, 0)
        assert first_level_index.data() == 'BP_Plan'
        assert view.proxy.sourceModel().rowCount(first_level_index) == 2
        second_level_index = view.proxy.sourceModel().index(0, 0, view.proxy.sourceModel().index(0, 0))
        assert second_level_index.data() == 'BP_BaugebietsTeilFlaeche'
        assert view.proxy.sourceModel().rowCount(second_level_index) == 1
        second_level_index = view.proxy.sourceModel().index(1, 0, first_level_index)
        assert second_level_index.data() == 'XP_VerfahrensMerkmal'
        assert view.proxy.sourceModel().rowCount(second_level_index) == 0

    def test_new_nodes_flag(self, view):
        item1 = XPlanungItem(xid=str(uuid.uuid4()), xtype=BP_Plan)
        node1 = ClassNode(item1, new=True)

        view.model.addChild(node1)

        index = view.model.index(0, 0)
        assert index.internalPointer().flag_new

        spy = QSignalSpy(view.model.dataChanged)
        view.selectionChanged(QItemSelection(), QItemSelection(index, index))

        assert len(spy) == 1
        assert not index.internalPointer().flag_new
