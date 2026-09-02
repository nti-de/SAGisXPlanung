import pytest

from qgis.PyQt.QtCore import Qt, QEvent
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QLineEdit

from SAGisXPlanung.gui.widgets.commons import (
    MultiSelectComboBox,
    ValidationManager,
    ValidationTrigger,
    RegexValidator,
    ErrorDisplayHandler, picker,
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


@pytest.fixture
def settings_store(monkeypatch):
    """Isolate ItemMetadataStore from the user's real QGIS settings."""
    data = {}

    class FakeSettings:
        def value(self, key, default=None):
            return data.get(key, default)

        def setValue(self, key, value):
            data[key] = value

        def remove(self, key):
            data.pop(key, None)

    monkeypatch.setattr(picker, "QSettings", FakeSettings)
    return data


@pytest.fixture
def metadata_store(settings_store):
    return picker.ItemMetadataStore("test/picker/metadata")


@pytest.fixture
def items():
    return [
        picker.PickerItem("1", "Plan 10", "A", search_terms=("Wohnung",)),
        picker.PickerItem("2", "Plan 2", "B", search_terms=("Gewerbe",)),
        picker.PickerItem("3", "Alpha", "A", search_terms=("Bebauung",)),
    ]


@pytest.fixture
def model(qtbot, items, metadata_store):
    model = picker.PickerModel(items, metadata_store=metadata_store)
    return model


def model_items(model):
    """Return visible item texts, excluding section headers."""
    result = []
    for row in range(model.rowCount()):
        if not model._is_section(row):
            item = model._item_at_row(row)
            if item is not None:
                result.append(item.text)
    return result


def test_natural_sort_key_sorts_numbers_numerically():
    values = ["Plan 10", "Plan 2", "Plan 1", "plan 11"]
    assert sorted(values, key=picker.natural_sort_key) == [
        "Plan 1", "Plan 2", "Plan 10", "plan 11"
    ]


def test_picker_item_builds_casefolded_search_stack():
    item = picker.PickerItem(
        "1", "Straße", search_terms=("Wohnung", "ALT")
    )

    assert item._search_stack == "strasse wohnung alt"


def test_picker_item_update_text_recomputes_search_stack():
    item = picker.PickerItem("1", "Old", search_terms=("foo",))

    item.update_text("New")

    assert item.text == "New"
    assert item._search_stack == "new foo"


def test_picker_item_update_search_terms_recomputes_search_stack():
    item = picker.PickerItem("1", "Name", search_terms=("old",))

    item.update_search_terms(("new", "extra"))

    assert item.search_terms == ("new", "extra")
    assert item._search_stack == "name new extra"


def test_metadata_store_get_set_unset(metadata_store):
    assert metadata_store.get("item", "field") is None

    metadata_store.set("item", "field", "value")
    assert metadata_store.get("item", "field") == "value"

    metadata_store.unset("item", "field")
    assert metadata_store.get("item", "field") is None


def test_metadata_store_unset_removes_empty_item(metadata_store, settings_store):
    metadata_store.set("item", "field", "value")
    metadata_store.unset("item", "field")

    assert "item" not in settings_store


def test_metadata_store_unset_unknown_value_is_noop(metadata_store, settings_store):
    metadata_store.unset("missing", "field")
    assert settings_store == {}


def test_metadata_store_favorites_are_persisted(metadata_store):
    assert not metadata_store.is_favorite("item")

    metadata_store.set_favorite("item", True)
    assert metadata_store.is_favorite("item")

    metadata_store.set_favorite("item", False)
    assert not metadata_store.is_favorite("item")


def test_metadata_store_forget_item(metadata_store, settings_store):
    metadata_store.set("item", "favorite", True)
    metadata_store.set("item", "last_used", 123)

    metadata_store.forget_item("item")

    assert "item" not in settings_store


def test_metadata_store_prune_removes_only_stale_items(metadata_store):
    metadata_store.set("keep", "favorite", True)
    metadata_store.set("drop", "favorite", True)

    metadata_store.prune({"keep"})

    assert metadata_store.is_favorite("keep")
    assert not metadata_store.is_favorite("drop")


def test_metadata_store_prune_without_stale_items_does_not_change_data(
    metadata_store, settings_store
):
    metadata_store.set("keep", "favorite", True)
    before = dict(settings_store)

    metadata_store.prune({"keep"})

    assert settings_store == before


def test_metadata_store_clear(metadata_store, settings_store):
    metadata_store.set("item", "favorite", True)

    metadata_store.clear()

    assert settings_store == {}


def test_category_model_adds_categories_and_prevents_duplicates(qtbot):
    model = picker.CategoryChipModel()
    category = picker.Category("a", "Alpha")

    model.addCategory(category)
    model.addCategory(picker.Category("a", "Duplicate"))

    assert model.rowCount() == 1
    assert model.ids() == ["a"]
    assert model.contains("a")
    assert model.indexOf("a") == 0
    assert model.indexOf("missing") == -1
    assert model.data(model.index(0, 0), picker.CategoryChipModel.LabelRole) == "Alpha"


def test_category_model_set_data_changes_checked_state(qtbot):
    model = picker.CategoryChipModel()
    model.addCategory(picker.Category("a", "Alpha"))

    index = model.index(0, 0)
    model.setData(index, True, picker.CategoryChipModel.CheckedRole)

    assert model.data(index, picker.CategoryChipModel.CheckedRole) is True


def test_category_model_remove_and_clear(qtbot):
    model = picker.CategoryChipModel()
    model.setCategories([
        picker.Category("a", "Alpha"),
        picker.Category("b", "Beta"),
    ])

    model.removeCategory("a")
    assert model.ids() == ["b"]

    model.removeCategory("missing")
    assert model.ids() == ["b"]

    model.clear()
    assert model.rowCount() == 0


def test_category_model_categories_returns_copy(qtbot):
    model = picker.CategoryChipModel()
    model.addCategory(picker.Category("a", "Alpha"))

    categories = model.categories()
    categories.clear()

    assert model.rowCount() == 1


def test_picker_model_without_favorites_has_one_section(model):
    assert model.rowCount() == len(model._items) + 1
    assert model._is_section(0)
    assert model._section_title(0) == "Alle Pläne"
    assert model._item_at_row(0) is None
    assert model._item_at_row(1).id == "1"


def test_picker_model_with_favorites_has_two_sections(model):
    model._items[1].is_favorite = True
    model._items[2].is_favorite = True

    assert model.rowCount() == len(model._items) + 2 + 2
    assert model._is_section(0)
    assert model._section_title(0) == "Favoriten"
    assert model._item_at_row(1).id == "2"
    assert model._item_at_row(2).id == "3"

    all_header = len(model._favorite_items()) + 1
    assert model._is_section(all_header)
    assert model._section_title(all_header) == "Alle Pläne"
    assert model._item_at_row(all_header + 1).id == "1"


def test_picker_model_data_and_flags_distinguish_sections_from_items(model):
    header = model.index(0, 0)
    item_index = model.index(1, 0)

    assert model.data(header, picker.Qt.ItemDataRole.DisplayRole) == "Alle Pläne"
    assert model.data(item_index, picker.Qt.ItemDataRole.DisplayRole) == "Plan 10"
    assert model.data(item_index, picker.Qt.ItemDataRole.ToolTipRole) == "Plan 10"

    assert model.flags(header) == picker.Qt.ItemFlag.ItemIsEnabled
    assert model.flags(item_index) == (
        picker.Qt.ItemFlag.ItemIsEnabled | picker.Qt.ItemFlag.ItemIsSelectable
    )


def test_picker_model_applies_persisted_favorites_and_prunes_metadata(
    metadata_store, settings_store, items
):
    metadata_store.set_favorite("2", True)
    metadata_store.set("stale", "favorite", True)

    model = picker.PickerModel(metadata_store=metadata_store)
    model.set_items(items)

    assert items[1].is_favorite is True
    assert items[0].is_favorite is False
    assert "stale" not in settings_store


def test_picker_model_toggle_favorite_updates_item_and_metadata(
    model, metadata_store
):
    model.toggle_favorite("1")
    assert model._find_item("1").is_favorite
    assert metadata_store.is_favorite("1")

    model.toggle_favorite("1")
    assert not model._find_item("1").is_favorite
    assert not metadata_store.is_favorite("1")


def test_picker_model_toggle_unknown_item_is_noop(model, settings_store):
    model.toggle_favorite("missing")
    assert settings_store == {}


def test_picker_model_remove_item_returns_status_and_forgets_metadata(
    model, metadata_store
):
    metadata_store.set("2", "favorite", True)

    assert model.remove_item("2") is True
    assert model._find_item("2") is None
    assert not metadata_store.get("2", "favorite", False)

    assert model.remove_item("missing") is False


def test_picker_model_update_item_updates_text_and_search_terms(model):
    assert model.update_item(
        "1", text="Updated", search_terms=("new term",)
    ) is True

    item = model._find_item("1")
    assert item.text == "Updated"
    assert item.search_terms == ("new term",)
    assert "updated new term" == item._search_stack

    assert model.update_item("missing", text="Nope") is False


def test_proxy_search_matches_item_text_and_search_terms(qtbot, model, metadata_store):
    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)

    proxy.set_search_text("wohnung")

    visible = [
        proxy._item_at_row(row).id
        for row in range(proxy.rowCount())
        if not proxy._is_section(row)
    ]

    assert visible == ["1"]


def test_proxy_search_is_case_insensitive_and_trimmed(qtbot, model, metadata_store):
    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)

    proxy.set_search_text("  GEWERBE  ")

    assert proxy._search_text == "GEWERBE"
    assert [
        proxy._item_at_row(row).id
        for row in range(proxy.rowCount())
        if not proxy._is_section(row)
    ] == ["2"]


def test_proxy_category_filter(qtbot, model, metadata_store):
    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)

    proxy.set_categories({"A"})

    visible = [
        proxy._item_at_row(row).id
        for row in range(proxy.rowCount())
        if not proxy._is_section(row)
    ]
    assert set(visible) == {"1", "3"}


def test_proxy_combines_category_and_search_filters(qtbot, model, metadata_store):
    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)

    proxy.set_categories({"A"})
    proxy.set_search_text("wohnung")

    visible = [
        proxy._item_at_row(row).id
        for row in range(proxy.rowCount())
        if not proxy._is_section(row)
    ]
    assert visible == ["1"]


def test_proxy_section_is_hidden_when_no_items_match(qtbot, model, metadata_store):
    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)

    proxy.set_search_text("does-not-exist")

    assert proxy.rowCount() == 0


def test_proxy_sort_mode_toggles_direction_when_selected_twice(
    qtbot, model, metadata_store
):
    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)

    assert proxy._sort_mode == picker.PickerSortMode.NAME
    assert proxy.sortOrder() == picker.Qt.SortOrder.AscendingOrder

    proxy.set_sort_mode(picker.PickerSortMode.NAME)
    assert proxy.sortOrder() == picker.Qt.SortOrder.DescendingOrder

    proxy.set_sort_mode(picker.PickerSortMode.NAME)
    assert proxy.sortOrder() == picker.Qt.SortOrder.AscendingOrder


def test_proxy_switching_sort_mode_resets_to_ascending(
    qtbot, model, metadata_store
):
    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)

    proxy.set_sort_mode(picker.PickerSortMode.NAME)
    assert proxy.sortOrder() == picker.Qt.SortOrder.DescendingOrder

    proxy.set_sort_mode(picker.PickerSortMode.LAST_USED)
    assert proxy._sort_mode == picker.PickerSortMode.LAST_USED
    assert proxy.sortOrder() == picker.Qt.SortOrder.AscendingOrder


def test_proxy_name_sort_uses_natural_sorting(qtbot, metadata_store):
    model = picker.PickerModel(
        [
            picker.PickerItem("1", "Plan 10"),
            picker.PickerItem("2", "Plan 2"),
            picker.PickerItem("3", "Plan 1"),
        ],
        metadata_store=metadata_store,
    )
    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)
    proxy.sort(0, picker.Qt.SortOrder.AscendingOrder)

    assert model_items(proxy) == ["Plan 1", "Plan 2", "Plan 10"]


def test_proxy_last_used_sort_puts_never_used_last_and_recent_first(
    qtbot, metadata_store
):
    model = picker.PickerModel(
        [
            picker.PickerItem("old", "Old"),
            picker.PickerItem("new", "New"),
            picker.PickerItem("never", "Never"),
        ],
        metadata_store=metadata_store,
    )
    metadata_store.set("old", "last_used", 10)
    metadata_store.set("new", "last_used", 20)

    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)
    proxy.set_sort_mode(picker.PickerSortMode.LAST_USED)

    assert model_items(proxy) == ["New", "Old", "Never"]


def test_proxy_last_used_sort_breaks_equal_timestamps_by_name(
    qtbot, metadata_store
):
    model = picker.PickerModel(
        [
            picker.PickerItem("1", "Plan 10"),
            picker.PickerItem("2", "Plan 2"),
        ],
        metadata_store=metadata_store,
    )
    metadata_store.set("1", "last_used", 100)
    metadata_store.set("2", "last_used", 100)

    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)
    proxy.setSourceModel(model)
    proxy.set_sort_mode(picker.PickerSortMode.LAST_USED)

    assert model_items(proxy) == ["Plan 2", "Plan 10"]


def test_proxy_last_used_comparator_handles_all_timestamp_cases(
    metadata_store
):
    proxy = picker.PickerFilterProxyModel(metadata_store=metadata_store)

    left = picker.PickerItem("left", "A")
    right = picker.PickerItem("right", "B")

    metadata_store.set("left", "last_used", 20)
    metadata_store.set("right", "last_used", 10)
    assert proxy._less_than_last_used(left, right) is True

    metadata_store.unset("left", "last_used")
    assert proxy._less_than_last_used(left, right) is False
    assert proxy._less_than_last_used(right, left) is True

    metadata_store.unset("right", "last_used")
    assert proxy._less_than_last_used(left, right) is True


def test_popup_categories_changed_passes_checked_ids_to_proxy(qtbot, settings_store):
    popup = picker.PickerPopup()
    qtbot.addWidget(popup)

    popup.add_category("a", "Alpha", checked=True)
    popup.add_category("b", "Beta", checked=False)
    popup._categories_changed()

    assert popup.picker_proxy_model._categories == {"a"}

    popup.category_model.setData(
        popup.category_model.index(1, 0),
        True,
        picker.CategoryChipModel.CheckedRole,
    )
    assert popup.picker_proxy_model._categories == {"a", "b"}


def test_generic_picker_set_items_populates_combo_without_usage_tracking(qtbot, settings_store):
    combo = picker.GenericPicker()
    qtbot.addWidget(combo)

    items = [
        picker.PickerItem("1", "One"),
        picker.PickerItem("2", "Two"),
    ]

    combo.set_picker_items(items)

    assert combo.count() == 2
    assert [combo.itemData(i) for i in range(combo.count())] == ["1", "2"]
    assert combo._popup.picker_model._items == items
    assert settings_store == {}


def test_generic_picker_remove_item_keeps_combo_and_popup_in_sync(
    qtbot, settings_store
):
    combo = picker.GenericPicker()
    qtbot.addWidget(combo)
    combo.set_picker_items([
        picker.PickerItem("1", "One"),
        picker.PickerItem("2", "Two"),
    ])

    assert combo.remove_item("1") is True
    assert combo.findData("1") == -1
    assert combo._popup.picker_model._find_item("1") is None
    assert combo.remove_item("missing") is False


def test_generic_picker_current_index_change_marks_item_used(
    qtbot, settings_store
):
    combo = picker.GenericPicker()
    qtbot.addWidget(combo)
    combo.set_picker_items([
        picker.PickerItem("1", "One"),
        picker.PickerItem("2", "Two"),
    ])

    combo.setCurrentIndex(1)

    assert combo._popup.metadata_store.last_used("2") is not None


def test_generic_picker_suppresses_usage_tracking_during_set_items(
    qtbot, settings_store
):
    combo = picker.GenericPicker()
    qtbot.addWidget(combo)

    combo.set_picker_items([
        picker.PickerItem("1", "One"),
        picker.PickerItem("2", "Two"),
    ])

    assert combo._popup.metadata_store.last_used("1") is None
    assert combo._popup.metadata_store.last_used("2") is None
