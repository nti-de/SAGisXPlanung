import pytest

from qgis.PyQt.QtCore import QEvent
from qgis.PyQt.QtGui import QFocusEvent

from SAGisXPlanung.gui.widgets.QCollapsibleSearch import QCollapsibleSearch


@pytest.fixture()
def search_widget():
    return QCollapsibleSearch()


class TestQCollapsibleSearch:

    @pytest.mark.asyncio
    async def test_expand_and_shrink(self, search_widget, qtbot):
        qtbot.addWidget(search_widget)
        assert not search_widget.property('expanded')

        search_widget.search_icon_action.trigger()
        assert search_widget.property('expanded')

        search_widget.setText('search-query')
        search_widget.focusOutEvent(QFocusEvent(QEvent.FocusOut))
        assert search_widget.property('expanded')

        search_widget.setText('')
        search_widget.focusOutEvent(QFocusEvent(QEvent.FocusOut))
        assert not search_widget.property('expanded')



