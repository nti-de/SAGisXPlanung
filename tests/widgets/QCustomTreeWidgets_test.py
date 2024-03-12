from qgis.core import QgsWkbTypes

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Plan
from SAGisXPlanung.gui.widgets.QCustomTreeWidgets import QObjectTypeSelectionTreeWidget


class TestQObjectTypeSelectionTreeWidget:

    def test_setup_with_bp(self):
        widget = QObjectTypeSelectionTreeWidget()

        assert widget.topLevelItemCount() == 0
        assert widget.columnCount() == 1

        widget.setup(BP_Plan, QgsWkbTypes.PointGeometry)

        assert widget.topLevelItemCount()
        assert widget.topLevelItem(0).text(0).startswith('BP')

    def test_setup_with_fp(self):
        widget = QObjectTypeSelectionTreeWidget()

        assert widget.topLevelItemCount() == 0
        assert widget.columnCount() == 1

        widget.setup(FP_Plan, QgsWkbTypes.PolygonGeometry)

        assert widget.topLevelItemCount()
        assert widget.topLevelItem(0).text(0).startswith('FP')
