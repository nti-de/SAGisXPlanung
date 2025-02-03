from datetime import date

from PyQt5.QtWidgets import QLineEdit

from SAGisXPlanung.gui.widgets.inputs.input_widgets import QComboBoxNoScroll, QDateListInput, QTextListInput, \
    QDateEditNoScroll


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
