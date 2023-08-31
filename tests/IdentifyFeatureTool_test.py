import pytest

from qgis.utils import iface
from qgis.PyQt.QtCore import Qt, QPoint

from SAGisXPlanung.Tools.IdentifyFeatureTool import IdentifyFeatureTool


@pytest.fixture()
def map_tool():
    return IdentifyFeatureTool(iface.mapCanvas())


class TestIdentifyFeatureTool_canvas_click:

    def test_maptool_canvas_release(self, map_tool, qtbot):
        canvas = iface.mapCanvas()
        canvas.setMapTool(map_tool)
        assert canvas.mapTool() == map_tool

        # map_tool.canvasReleaseEvent = MagicMock()
        qtbot.addWidget(canvas)
        qtbot.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(int(canvas.center().x()), int(canvas.center().y())))
        # sleep(1)
        # assert map_tool.canvasReleaseEvent.called

    def test_maptool_canvas_release_right(self, map_tool, qtbot):
        canvas = iface.mapCanvas()
        canvas.setMapTool(map_tool)
        assert canvas.mapTool() == map_tool

        qtbot.addWidget(canvas)
        qtbot.mouseRelease(canvas, Qt.RightButton)
        # sleep(1)
        # assert canvas.mapTool() != map_tool
