import pytest
from unittest.mock import MagicMock

from qgis.PyQt.QtCore import QByteArray

from SAGisXPlanung.gui.style import (
    ApplicationColor,
    apply_color,
    with_color_palette
)


@pytest.fixture
def mock_widget():
    return MagicMock()


def test_apply_color(mock_widget):
    apply_color(mock_widget, ApplicationColor.Primary)
    mock_widget.setProperty.assert_called_once_with('Primary', True)


def test_remove_previous_color(mock_widget):
    mock_widget.dynamicPropertyNames.return_value = [QByteArray('Primary'.encode()), QByteArray('Tertiary'.encode())]
    apply_color(mock_widget, ApplicationColor.Primary)
    assert mock_widget.setProperty.call_count == 3  # 2 unloads, one for settings new color
    mock_widget.setProperty.assert_any_call('Primary', None)
    mock_widget.setProperty.assert_any_call('Tertiary', None)
    mock_widget.setProperty.assert_any_call('Primary', True)


def test_with_color_palette(mock_widget):
    colors = [ApplicationColor.Primary, ApplicationColor.Tertiary]
    with_color_palette(mock_widget, colors)
    expected_stylesheet = (
        '''
        [Primary=true] {
                color: #000000;
            }
        [Tertiary=true] {
                color: #4b5563;
            }
        '''
    )
    mock_widget.setStyleSheet.assert_called_once_with(mock_widget.styleSheet() + expected_stylesheet)
