import pytest
from qgis.PyQt.QtCore import QModelIndex, QItemSelectionModel
from mock import Mock, patch, MagicMock, AsyncMock

from SAGisXPlanung.XPlan.feature_types import XP_TextAbschnitt
from SAGisXPlanung.gui.widgets.select_related_widget import SelectRelatedWidget, RelatedObjectModel, RelatedObjectItem


@pytest.fixture
def mock_xplan_item():
    item = Mock()
    item.xid = "parent-123"
    item.xtype = Mock(__name__="TestType")
    return item


@pytest.fixture
def sample_items():
    items = []
    for i in range(5):
        xplan_item = Mock()
        xplan_item.xid = f"obj-{i}"
        items.append(RelatedObjectItem(
            code=f"CODE-{i}",
            title=f"§ 3 Abs. {i}",
            description=f"Description text for object {i}",
            xplan_item=xplan_item
        ))
    return items


@pytest.fixture
def widget(mock_xplan_item, sample_items):
    with patch.object(SelectRelatedWidget, 'load_data', new_callable=AsyncMock), patch('asyncio.create_task'):
        widget = SelectRelatedWidget(
            create_type=XP_TextAbschnitt,
            parent_item=mock_xplan_item,
            orm_attribute='test_attr'
        )

        # Manually populate the widget with test data
        widget.model.setItems(sample_items)
        widget._selected_ids = set()
        widget.update_selected_count()

    return widget


class TestRelatedObjectModel:

    def test_initial_state(self):
        model = RelatedObjectModel()
        assert model.rowCount() == 0

    def test_set_items(self):
        model = RelatedObjectModel()
        items = [
            RelatedObjectItem("CODE1", "Title1", "Desc1", Mock()),
            RelatedObjectItem("CODE2", "Title2", "Desc2", Mock())
        ]
        model.setItems(items)
        assert model.rowCount() == 2

    def test_data_retrieval(self):
        model = RelatedObjectModel()
        item = RelatedObjectItem("TEST-CODE", "Test Title", "Test Description", Mock())
        model.setItems([item])

        index = model.index(0, 0)
        assert model.data(index, RelatedObjectModel.CodeRole) == "TEST-CODE"
        assert model.data(index, RelatedObjectModel.TitleRole) == "Test Title"
        assert model.data(index, RelatedObjectModel.DescriptionRole) == "Test Description"

    def test_add_item(self):
        model = RelatedObjectModel()
        assert model.rowCount() == 0

        item = RelatedObjectItem("CODE", "Title", "Desc", Mock())
        model.addItem(item)
        assert model.rowCount() == 1

    def test_invalid_index(self):
        model = RelatedObjectModel()
        model.setItems([RelatedObjectItem("CODE", "Title", "Desc", Mock())])

        invalid_index = QModelIndex()
        assert model.data(invalid_index, RelatedObjectModel.CodeRole) is None


class TestSelectRelatedWidget:

    def test_widget_initialization(self, widget):
        assert widget is not None
        assert widget.tab_widget.count() == 2
        assert widget.tab_widget.tabText(0) == "Neu erstellen"
        assert widget.tab_widget.tabText(1) == "Vorhandene durchsuchen"

    def test_model_populated(self, widget, sample_items):
        assert widget.model.rowCount() == len(sample_items)

    def test_search_functionality(self, widget, sample_items):
        # Initially all items visible
        assert widget.proxy_model.rowCount() == len(sample_items)

        # Filter by search
        widget.search_edit.setText("CODE-1")
        assert widget.proxy_model.rowCount() == 1

        # Clear filter
        widget.search_edit.setText("")
        assert widget.proxy_model.rowCount() == len(sample_items)

    def test_selection_tracking(self, widget):
        assert len(widget._selected_ids) == 0

        # Select first item
        index = widget.proxy_model.index(0, 0)
        widget.list_view.selectionModel().select(
            index, QItemSelectionModel.SelectionFlag.Select
        )

        assert len(widget._selected_ids) == 1
        assert "obj-0" in widget._selected_ids

    def test_deselection_tracking(self, widget):
        # Select first item
        index = widget.proxy_model.index(0, 0)
        sel_model = widget.list_view.selectionModel()
        sel_model.select(index, QItemSelectionModel.SelectionFlag.Select)

        assert len(widget._selected_ids) == 1

        # Deselect
        sel_model.select(index, QItemSelectionModel.SelectionFlag.Deselect)
        assert len(widget._selected_ids) == 0

    def test_multi_selection(self, widget):
        sel_model = widget.list_view.selectionModel()

        # Select multiple items
        for i in range(3):
            index = widget.proxy_model.index(i, 0)
            sel_model.select(index, QItemSelectionModel.SelectionFlag.Select)

        assert len(widget._selected_ids) == 3

    def test_selected_count_label(self, widget):
        assert widget.selected_count.text() == "0"

        # Select items
        sel_model = widget.list_view.selectionModel()
        index = widget.proxy_model.index(0, 0)
        sel_model.select(index, QItemSelectionModel.SelectionFlag.Select)

        assert widget.selected_count.text() == "1"

    def test_is_create_new(self, widget):
        widget.tab_widget.setCurrentIndex(0)
        assert widget.is_create_new() is True

        widget.tab_widget.setCurrentIndex(1)
        assert widget.is_create_new() is False

    def test_get_selected_ids(self, widget):
        # Select some items
        sel_model = widget.list_view.selectionModel()
        for i in range(2):
            index = widget.proxy_model.index(i, 0)
            sel_model.select(index, QItemSelectionModel.SelectionFlag.Select)

        selected_ids = widget.get_selected_ids()
        assert len(selected_ids) == 2
        assert "obj-0" in selected_ids
        assert "obj-1" in selected_ids

    def test_search_preserves_selection(self, widget):
        # Select first item
        sel_model = widget.list_view.selectionModel()
        index = widget.proxy_model.index(0, 0)
        sel_model.select(index, QItemSelectionModel.SelectionFlag.Select)

        assert len(widget._selected_ids) == 1

        # Apply filter that includes selected item
        widget.search_edit.setText("CODE-0")

        # Selection should be preserved
        assert len(widget._selected_ids) == 1
        assert widget.list_view.selectionModel().hasSelection()

    def test_restore_view_selection(self, widget):
        # Manually add IDs to selected set
        widget._selected_ids.add("obj-2")
        widget._selected_ids.add("obj-3")

        # Restore selection in view
        widget.restore_view_selection()

        # Check view has correct items selected
        selected_indexes = widget.list_view.selectionModel().selectedIndexes()
        assert len(selected_indexes) == 2