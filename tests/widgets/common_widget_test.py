import pytest

from qgis.PyQt.QtCore import Qt, QEvent
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QLineEdit

from SAGisXPlanung.gui.widgets.commons import (
    MultiSelectComboBox,
    ValidationManager,
    ValidationTrigger,
    RegexValidator,
    ErrorDisplayHandler,
)



class TestMultiSelectComboBox:
    @pytest.fixture
    def combo(self):
        return MultiSelectComboBox()

    def test_initial_state(self, combo):
        assert combo.empty_text == combo.display_text
        assert combo.model().rowCount() == 0

    def test_add_item(self, combo):
        combo.add_item("Item 1", data="data1", check_state=Qt.CheckState.Checked)
        combo.add_item("Item 2", data="data2", check_state=Qt.CheckState.Unchecked)

        assert combo.model().rowCount() == 2

        item1 = combo.model().item(0)
        assert item1.text() == "Item 1"
        assert item1.data(Qt.ItemDataRole.UserRole) == "data1"
        assert item1.checkState() == Qt.CheckState.Checked

        item2 = combo.model().item(1)
        assert item2.text() == "Item 2"
        assert item2.data(Qt.ItemDataRole.UserRole) == "data2"
        assert item2.checkState() == Qt.CheckState.Unchecked

    def test_on_item_pressed(self, combo):
        combo.add_item("Item 1", check_state=Qt.CheckState.Unchecked)
        index = combo.model().index(0, 0)
        combo.on_item_pressed(index)

        assert combo.model().item(0).checkState() == Qt.CheckState.Checked

        combo.on_item_pressed(index)
        assert combo.model().item(0).checkState() == Qt.CheckState.Unchecked

    def test_on_item_changed(self, combo):
        combo.add_item("Item 1", check_state=Qt.CheckState.Unchecked)
        item = combo.model().item(0)

        item.setCheckState(Qt.CheckState.Checked)
        combo.on_item_changed(item)

        assert combo.display_text == "Item 1"

        item.setCheckState(Qt.CheckState.Unchecked)
        combo.on_item_changed(item)

        assert combo.display_text == combo.empty_text

    def test_checked_items(self, combo):
        combo.add_item("Item 1", data="data1", check_state=Qt.CheckState.Checked)
        combo.add_item("Item 2", data="data2", check_state=Qt.CheckState.Unchecked)
        combo.add_item("Item 3", data="data3", check_state=Qt.CheckState.Checked)

        checked = combo.checked_items(Qt.ItemDataRole.UserRole)
        assert checked == ["data1", "data3"]
        checked = combo.checked_items()
        assert checked == ["Item 1", "Item 3"]

    def test_update_display_text(self, combo):
        combo.add_item("Item 1", check_state=Qt.CheckState.Checked)
        combo.add_item("Item 2", check_state=Qt.CheckState.Unchecked)

        combo.update_display_text()
        assert combo.display_text == "Item 1"

        combo.model().item(1).setCheckState(Qt.CheckState.Checked)
        combo.update_display_text()
        assert combo.display_text == "Item 1, Item 2"


@pytest.fixture
def form():
    widget = QWidget()
    layout = QVBoxLayout(widget)

    line_edit = QLineEdit()
    layout.addWidget(line_edit)

    widget.show()

    return widget, line_edit


@pytest.fixture
def validation_manager():
    return ValidationManager()


# =========================================================
# RegexValidator
# =========================================================

def test_regex_validator_accepts_valid_identifier():
    validator = RegexValidator(r"^[A-Za-z_][A-Za-z0-9_]*$")

    assert validator("valid_name")
    assert validator("_valid_name")
    assert validator("abc123")


def test_regex_validator_rejects_invalid_identifier():
    validator = RegexValidator(r"^[A-Za-z_][A-Za-z0-9_]*$")

    assert not validator("123abc")
    assert not validator("my-name")
    assert not validator("hello world")


# =========================================================
# ValidationManager registration
# =========================================================

def test_register_widget(validation_manager, form):
    _, line_edit = form

    validation_manager.register(
        line_edit,
        validator=lambda t: bool(t),
        error_message="Required"
    )

    assert line_edit in validation_manager.rules

    rule = validation_manager.rules[line_edit]

    assert rule.error_message == "Required"
    assert rule.trigger == ValidationTrigger.FOCUS_OUT


# =========================================================
# validate_widget
# =========================================================

def test_validate_widget_success(validation_manager, form):
    _, line_edit = form

    validation_manager.register(
        line_edit,
        validator=lambda t: t == "abc",
        error_message="Invalid"
    )

    line_edit.setText("abc")

    valid = validation_manager.validate_widget(line_edit)

    assert valid is True
    assert line_edit not in validation_manager.error_handler._containers


def test_validate_widget_failure(validation_manager, form):
    _, line_edit = form

    validation_manager.register(
        line_edit,
        validator=lambda t: t == "abc",
        error_message="Invalid"
    )

    line_edit.setText("wrong")

    valid = validation_manager.validate_widget(line_edit)

    assert valid is False
    assert line_edit in validation_manager.error_handler._containers


def test_validate_widget_unknown_widget_returns_true(validation_manager):
    widget = QLineEdit()

    assert validation_manager.validate_widget(widget) is True


# =========================================================
# validation_wrapper
# =========================================================

def test_validate_widget_skips_wrong_trigger(validation_manager, form):
    _, line_edit = form

    validation_manager.register(
        line_edit,
        validator=lambda t: False,
        error_message="Invalid",
        trigger=ValidationTrigger.MANUAL
    )

    valid = validation_manager.validate_widget(
        line_edit,
        trigger=ValidationTrigger.FOCUS_OUT
    )

    assert valid is True
    assert line_edit not in validation_manager.error_handler._containers


def test_validate_all_success(validation_manager, form):
    _, line_edit = form

    line_edit.setText("valid")

    validation_manager.register(
        line_edit,
        validator=lambda t: bool(t),
        error_message="Required"
    )

    assert validation_manager.validate_all() is True


def test_validate_all_failure(validation_manager, form):
    _, line_edit = form

    line_edit.setText("")

    validation_manager.register(
        line_edit,
        validator=lambda t: bool(t),
        error_message="Required"
    )

    assert validation_manager.validate_all() is False


def test_show_error_creates_container(form):
    _, line_edit = form

    handler = ErrorDisplayHandler()

    handler.show_error(line_edit, "Error")

    assert line_edit in handler._containers

    container, label = handler._containers[line_edit]

    assert container.objectName() == "validationWrapper"
    assert label.text() == "Error"


def test_show_error_does_not_duplicate_container(form):
    _, line_edit = form

    handler = ErrorDisplayHandler()

    handler.show_error(line_edit, "Error")
    first_container = handler._containers[line_edit]

    handler.show_error(line_edit, "Another Error")

    second_container = handler._containers[line_edit]

    assert first_container == second_container
    assert len(handler._containers) == 1


def test_clear_error_removes_container(form):
    _, line_edit = form

    handler = ErrorDisplayHandler()

    handler.show_error(line_edit, "Error")

    assert line_edit in handler._containers

    handler.clear_error(line_edit)

    assert line_edit not in handler._containers


def test_clear_error_on_unknown_widget_does_nothing(form):
    _, line_edit = form

    handler = ErrorDisplayHandler()

    handler.clear_error(line_edit)

    assert line_edit not in handler._containers


def test_focus_out_event_triggers_validation(validation_manager, form, monkeypatch):
    _, line_edit = form

    called = {
        "value": False
    }

    def fake_validate(widget, trigger):
        called["value"] = True

    monkeypatch.setattr(
        validation_manager,
        "validate_widget",
        fake_validate
    )

    event = QEvent(QEvent.Type.FocusOut)

    validation_manager.event_filter.eventFilter(
        line_edit,
        event
    )

    assert called["value"] is True


def test_non_focus_out_event_does_not_trigger_validation(
    validation_manager,
    form,
    monkeypatch
):
    _, line_edit = form

    called = {
        "value": False
    }

    def fake_validate(widget, trigger):
        called["value"] = True

    monkeypatch.setattr(
        validation_manager,
        "validate_widget",
        fake_validate
    )

    event = QEvent(QEvent.Type.KeyPress)

    validation_manager.event_filter.eventFilter(
        line_edit,
        event
    )

    assert called["value"] is False