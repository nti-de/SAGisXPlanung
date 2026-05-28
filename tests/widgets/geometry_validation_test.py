import pytest
from qgis.PyQt.QtCore import Qt

from SAGisXPlanung.core.geometry_validation import ValidationResult
from SAGisXPlanung.gui.widgets.geometry_validation import _error_detail_message, ValidationResultModel, \
    ValidationTreeView, ValidationWidget


class TestType:
    pass

@pytest.fixture
def make_result(msg="error"):
    return ValidationResult(
        xid="1",
        xtype=TestType,
        error_msg=msg,
        geom_wkt="LineString (0 0, 1 1)",
    )


def test_error_detail_message_with_related_object():
    result = ValidationResult(
        xid="1",
        xtype=TestType,
        error_msg="Topology error",
        other_xid="2",
        other_xtype=TestType,
    )

    msg = _error_detail_message(result)

    assert "Topology error" in msg
    assert "Betroffene Objekte" in msg
    assert "TestType: 1" in msg
    assert "TestType: 2" in msg


def test_model_row_count(make_result):
    model = ValidationResultModel([make_result, make_result])

    assert model.rowCount() == 2

def test_model_data_display_role(make_result):
    model = ValidationResultModel([make_result])

    index_type = model.index(0, 0)
    index_msg = model.index(0, 1)

    assert model.data(index_type, Qt.ItemDataRole.DisplayRole) == "TestType"
    assert model.data(index_msg, Qt.ItemDataRole.DisplayRole) == "error"

def test_model_tooltip_role(make_result):
    model = ValidationResultModel([make_result])

    index = model.index(0, 0)

    tooltip = model.data(index, Qt.ItemDataRole.ToolTipRole)

    assert "error" in tooltip
    assert tooltip.startswith("<qt>")

def test_model_add_items(make_result):
    model = ValidationResultModel()
    results = [make_result, make_result]

    model.add_items(results)

    assert model.rowCount() == 2

def test_model_clear(make_result):
    model = ValidationResultModel([make_result])

    model.clear()

    assert model.rowCount() == 0


def test_tree_add_result_items(qtbot, make_result):
    tree = ValidationTreeView()
    qtbot.addWidget(tree)
    results = [make_result, make_result]

    tree.add_result_items(results)

    assert tree.item_count() == 2

def test_tree_clear(qtbot, make_result):
    tree = ValidationTreeView()
    qtbot.addWidget(tree)

    tree.add_result_items([make_result])

    tree.clear()

    assert tree.item_count() == 0
    assert tree.validation_state.name == "UNKNOWN"

def test_widget_reset_validation(qtbot, make_result):
    widget = ValidationWidget()
    qtbot.addWidget(widget)

    widget._validation_result_label.setText("Some error")

    widget._validation_result_view.add_result_items([make_result])

    widget.reset_validation()

    assert widget._validation_result_label.text() == ""
    assert widget._validation_result_view.item_count() == 0

def test_set_plan_info_resets_state(qtbot):
    widget = ValidationWidget()
    qtbot.addWidget(widget)

    widget._validation_result_label.setText("something")

    widget.set_plan_info("plan123", TestType)

    assert widget.plan_xid == "plan123"
    assert widget.plan_type == TestType
    assert widget._validation_result_label.text() == ""

def test_validate_plan_geometric(monkeypatch, qtbot, make_result):
    widget = ValidationWidget()
    qtbot.addWidget(widget)

    widget.plan_xid = "plan1"
    widget.plan_type = TestType

    def fake_validation(plan_xid, short_type):
        return [make_result]

    monkeypatch.setattr(
        "SAGisXPlanung.gui.widgets.geometry_validation.INTERNAL_VALIDATION_FUNCTIONS",
        [fake_validation],
    )

    widget.validate_plan_geometric(lambda: None)

    assert widget._validation_result_view.item_count() == 1

import pytest


@pytest.mark.asyncio
async def test_start_validation_success(monkeypatch, qtbot):
    widget = ValidationWidget()
    qtbot.addWidget(widget)

    widget.plan_xid = "1"
    widget.plan_type = TestType

    monkeypatch.setattr(widget, "validate_plan_geometric", lambda: None)

    await widget.start_validation()

    assert "Keine Fehler gefunden" in widget._validation_result_label.text()