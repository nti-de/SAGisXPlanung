from datetime import date
import enum

from qgis.PyQt.QtWidgets import QLineEdit
from sqlalchemy import ARRAY, Column, Enum, Integer

from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_NebenanlagenFlaeche
from SAGisXPlanung.gui.widgets.inputs.input_widgets import QComboBoxNoScroll, QDateListInput, QTextListInput, \
    QDateEditNoScroll, QCheckableComboBoxInput, QIntegerListInput
from SAGisXPlanung.gui.widgets.inputs.widget_factory import create_widget


class TestEnum(enum.Enum):
    A = 1
    B = 2
    C = 3


class TestWidgetFactory:
    def test_widget_factory_enum_array(self):
        field_type = ARRAY(Enum(TestEnum))

        widget = create_widget(field_type)

        assert isinstance(widget, QCheckableComboBoxInput)
        assert widget.enum_type == TestEnum
        assert widget.count() == 3

    def test_widget_factory_integer_array(self):
        field_type = ARRAY(Integer)

        widget = create_widget(field_type)

        assert isinstance(widget, QIntegerListInput)


class TestComboBox:

    def test_value_include_default(self, qtbot):
        cb = QComboBoxNoScroll(qtbot, items=['1', '2', '3'], include_default=True)
        assert not cb.value()

        cb.setDefault('1')
        assert cb.currentIndex() == 1
        assert cb.value() == '1'

    def test_value_no_default(self, qtbot):
        cb = QComboBoxNoScroll(qtbot, items=['1', '2', '3'], include_default=False)
        assert cb.value() == '1'

        cb.setDefault('1')
        assert cb.currentIndex() == 0
        assert cb.value() == '1'
        cb.setDefault('3')
        assert cb.currentIndex() == 2
        assert cb.value() == '3'


class TestMultiInputs:

    def test_qdate_list_input_initialization(self):
        """Test if QDateListInput initializes with one date input field."""
        widget = QDateListInput()
        assert len(widget.inputs) == 1
        assert isinstance(widget.first_input, QDateEditNoScroll)

    def test_qtext_list_input_initialization(self):
        """Test if QTextListInput initializes with one text input field."""
        widget = QTextListInput()
        assert len(widget.inputs) == 1
        assert isinstance(widget.first_input, QLineEdit)

    def test_add_input_qdate_list(self):
        """Test adding additional date input fields."""
        widget = QDateListInput()
        initial_count = len(widget.inputs)

        widget.add_input()
        assert len(widget.inputs) == initial_count + 1  # Should increase by 1

    def test_add_input_qtext_list(self):
        """Test adding additional text input fields."""
        widget = QTextListInput()
        initial_count = len(widget.inputs)

        widget.add_input()
        assert len(widget.inputs) == initial_count + 1  # Should increase by 1

    def test_remove_input_qdate_list(self):
        """Test removing an input field from QDateListInput."""
        widget = QDateListInput()
        widget.add_input()
        initial_count = len(widget.inputs)

        # Simulate clicking the remove button
        remove_button = widget.inputs[-1].itemAt(1).widget()
        remove_button.clicked.emit()

        assert len(widget.inputs) == initial_count - 1  # Should decrease by 1

    def test_remove_input_qtext_list(self):
        """Test removing an input field from QTextListInput."""
        widget = QTextListInput()
        widget.add_input()
        initial_count = len(widget.inputs)

        # Simulate clicking the remove button
        remove_button = widget.inputs[-1].itemAt(1).widget()
        remove_button.clicked.emit()

        assert len(widget.inputs) == initial_count - 1  # Should decrease by 1

    def test_value_qdate_list(self):
        """Test retrieving values from QDateListInput."""
        widget = QDateListInput()

        date1 = date(2023, 1, 1)
        date2 = date(2023, 1, 2)
        widget.first_input.setDate(date1)

        widget.add_input().setDate(date2)

        values = widget.value()

        assert values == [date1, date2]  # Ensure formatted correctly

    def test_value_qtext_list(self):
        """Test retrieving values from QTextListInput."""
        widget = QTextListInput()

        widget.first_input.setText("Test 1")
        widget.add_input().setText("Test 2")

        values = widget.value()

        assert values == ["Test 1", "Test 2"]

    def test_set_default_qdate_list(self):
        """Test setting default values in QDateListInput."""
        widget = QDateListInput()
        widget.setDefault("01.01.2023, 02.02.2023")

        assert widget.first_input.date().toString("dd.MM.yyyy") == "01.01.2023"
        assert widget.inputs[1].itemAt(0).widget().date().toString("dd.MM.yyyy") == "02.02.2023"

        widget = QDateListInput()
        widget.setDefault([date(2023, 1, 3), date(2023, 1, 4)])
        assert widget.first_input.date().toString("dd.MM.yyyy") == "03.01.2023"
        assert widget.inputs[1].itemAt(0).widget().date().toString("dd.MM.yyyy") == "04.01.2023"

    def test_set_default_qtext_list(self):
        """Test setting default values in QTextListInput."""
        widget = QTextListInput()

        widget.setDefault("Hello, World")

        assert widget.first_input.text() == "Hello"
        assert widget.inputs[1].itemAt(0).widget().text() == "World"

    def test_qinteger_list_input_initialization(self):
        """Test if QIntegerListInput initializes with one integer input field."""
        widget = QIntegerListInput()
        assert len(widget.inputs) == 1

    def test_add_input_qinteger_list(self):
        """Test adding additional integer input fields."""
        widget = QIntegerListInput()
        initial_count = len(widget.inputs)

        widget.add_input()
        assert len(widget.inputs) == initial_count + 1

    def test_remove_input_qinteger_list(self):
        """Test removing an input field from QIntegerListInput."""
        widget = QIntegerListInput()
        widget.add_input()
        initial_count = len(widget.inputs)

        remove_button = widget.inputs[-1].itemAt(1).widget()
        remove_button.clicked.emit()

        assert len(widget.inputs) == initial_count - 1

    def test_value_qinteger_list(self):
        """Test retrieving values from QIntegerListInput."""
        widget = QIntegerListInput()

        widget.first_input.setText("1")
        widget.add_input().setText("2")

        values = widget.value()

        assert values == [1, 2]

    def test_value_qinteger_list_ignores_empty(self):
        """Ensure empty fields are ignored."""
        widget = QIntegerListInput()

        widget.first_input.setText("1")
        widget.add_input().setText("")

        values = widget.value()

        assert values == [1]

    def test_set_default_qinteger_list_string(self):
        """Test setting default values from comma-separated string."""
        widget = QIntegerListInput()

        widget.setDefault("1, 2, 3")

        assert widget.first_input.text() == "1"
        assert widget.inputs[1].itemAt(0).widget().text() == "2"
        assert widget.inputs[2].itemAt(0).widget().text() == "3"

    def test_set_default_qinteger_list_list(self):
        """Test setting default values from list of integers."""
        widget = QIntegerListInput()

        widget.setDefault([4, 5])

        assert widget.first_input.text() == "4"
        assert widget.inputs[1].itemAt(0).widget().text() == "5"

    def test_validate_required_qinteger_list(self):
        """Validation should fail if required and no values provided."""
        widget = QIntegerListInput()

        assert widget.validate_widget(required=False)
        assert not widget.validate_widget(required=True)

    def test_validate_invalid_integer(self):
        """Validation should fail if one field contains invalid integer."""
        widget = QIntegerListInput()

        widget.first_input.setText("abc")

        assert not widget.validate_widget(required=False)

    def test_value_qinteger_list_mixed_with_zero(self):
        """Ensure zero is preserved alongside other integers."""
        widget = QIntegerListInput()

        widget.first_input.setText("0")
        widget.add_input().setText("5")
        widget.add_input().setText("")

        values = widget.value()

        assert values == [0, 5]
