import pytest
from unittest.mock import patch

from qgis.PyQt.QtCore import QModelIndex
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel, QPaintEvent
from qgis.core import QgsWkbTypes

from SAGisXPlanung.gui.widgets.feature_browser_view import FeatureBrowserView, FilterCatalogProxyModel, SchemaSection
from SAGisXPlanung.utils import OBJECT_BASE_TYPES


class TestFeatureBrowserView:
    @pytest.fixture
    def view(self):
        return FeatureBrowserView()

    def test_initialization(self, view):
        assert view.model() == view.proxy
        assert view._model is not None
        assert isinstance(view.proxy, FilterCatalogProxyModel)
        assert view.header().isHidden()

    def test_clear_content(self, view):
        item = QStandardItem("Test Item")
        view._model.appendRow(item)
        assert view._model.rowCount() == 1

        view.clear_content()
        assert view._model.rowCount() == 0

    def test_filter_items(self, view):
        mock_schema_filter = SchemaSection.BP
        with patch.object(view.proxy, 'invalidateFilter') as mock_invalidate:
            view.filter_items(mock_schema_filter)
            assert view.proxy._schema_filter == mock_schema_filter
            mock_invalidate.assert_called_once()

    def test_reset_filter(self, view):
        with patch.object(view, 'filter_items') as mock_filter_items:
            view.reset_filter()
            mock_filter_items.assert_called_once_with(SchemaSection.ALL)

    def test_paint_event_no_results(self, view, qtbot):
        # Ensure the model is empty for the no-results condition
        view.clear_content()

        with patch.object(view, 'draw_no_results') as mock_draw_no_results:
            event = QPaintEvent(view.rect())
            view.paintEvent(event)
            mock_draw_no_results.assert_called_once()

    def test_setup(self, view):
        with patch.object(view, 'clear_content') as mock_clear_content, \
                patch.object(view, 'populate_tree') as mock_populate_tree, \
                patch.object(view, 'filter_items') as mock_filter_items:
            schema_filter = SchemaSection.BP | SchemaSection.SO
            view.setup(schema_filter, QgsWkbTypes.PolygonGeometry)

            mock_clear_content.assert_called_once()
            assert view.geometry_type == QgsWkbTypes.PolygonGeometry
            assert mock_populate_tree.call_count == len(OBJECT_BASE_TYPES)
            mock_filter_items.assert_called_once_with(schema_filter)


class TestFeatureBrowserModel:

    @pytest.fixture
    def model(self):
        return FilterCatalogProxyModel()

    @pytest.fixture
    def source_model(self):
        return QStandardItemModel()

    def test_set_schema_filter(self, model):
        schema_section = SchemaSection.BP | SchemaSection.FP
        model.set_schema_filter(schema_section)
        assert model._schema_filter == schema_section

    def test_flag_matches_no_filter(self, model):
        model.set_schema_filter(None)
        assert model.flag_matches('BP_Plan')

    def test_flag_matches_with_filter(self, model):
        model.set_schema_filter(SchemaSection.BP | SchemaSection.FP)
        assert model.flag_matches('BP_Plan')
        assert model.flag_matches('FP_Plan')
        assert not model.flag_matches('RP_Plan')

    def test_flag_matches_with_all(self, model):
        model.set_schema_filter(SchemaSection.ALL)
        assert model.flag_matches('BP_Plan')
        assert model.flag_matches('RP_Plan')

    def test_filterAcceptsRow_no_parent(self, model, source_model):
        item = QStandardItem("test data")
        item.setToolTip("tooltip")
        source_model.appendRow(item)
        model.setSourceModel(source_model)

        model.setFilterRegularExpression('test')
        assert model.filterAcceptsRow(0, QModelIndex())

        model.setFilterRegularExpression('tooltip')
        assert model.filterAcceptsRow(0, QModelIndex())

        model.setFilterRegularExpression('nomatch')
        assert not model.filterAcceptsRow(0, QModelIndex())

    def test_filterAcceptsRow_with_parent(self, model, source_model):
        parent_item = QStandardItem("parent data")
        child_item = QStandardItem("child data")
        parent_item.appendRow(child_item)
        source_model.appendRow(parent_item)

        model.setSourceModel(source_model)
        model.setFilterRegularExpression('parent')

        parent_index = source_model.indexFromItem(parent_item)
        assert model.filterAcceptsRow(0, QModelIndex())
        assert model.filterAcceptsRow(0, parent_index)

        model.setFilterRegularExpression('nomatch')
        assert not model.filterAcceptsRow(0, QModelIndex())
        assert not model.filterAcceptsRow(0, parent_index)