import pytest
from qgis.PyQt.QtCore import Qt

from SAGisXPlanung.gui.widgets.commons import MultiSelectComboBox


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
