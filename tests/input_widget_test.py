from SAGisXPlanung.gui.widgets.QXPlanInputElement import QComboBoxNoScroll


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
