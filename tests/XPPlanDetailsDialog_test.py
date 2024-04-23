import os
import uuid

import pytest

from geoalchemy2 import WKTElement
from geoalchemy2.shape import from_shape
from qgis.PyQt import QtCore, QtTest
from qgis.core import QgsProject
from qgis.PyQt.QtCore import Qt

from shapely.geometry import Polygon

from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.core.canvas_display import create_raster_layer

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan, BP_Bereich
from SAGisXPlanung.gui.XPPlanDetailsDialog import XPPlanDetailsDialog
from SAGisXPlanung.gui.widgets.geometry_validation import ValidationResult, ValidationGeometryErrorTreeWidgetItem, \
    GeometryIntersectionType


@pytest.fixture()
def dialog(mocker):
    mocker.patch(
        'SAGisXPlanung.gui.XPPlanDetailsDialog.XPPlanDetailsDialog.initPlanData',
        return_value=None
    )
    dlg = XPPlanDetailsDialog("test")
    return dlg


@pytest.fixture()
def plan_correct():
    plan = BP_Plan()
    plan.raeumlicherGeltungsbereich = WKTElement(
        'MultiPolygon (((571610.14549999998416752 5940812.23180000018328428, 571618.8227999999653548 5940833.81209999974817038, 571637.57389999995939434 5940849.39109999965876341, 571665.17790000000968575 5940876.14549999963492155, 571689.51969999994616956 5940870.4834000002592802, 571689.51969999994616956 5940870.4834000002592802, 571693.32970000000204891 5940859.52969999983906746, 571681.63450000004377216 5940846.81230000033974648, 571672.13399999996181577 5940838.12349999975413084, 571640.81519999995362014 5940809.48080000001937151, 571610.14549999998416752 5940812.23180000018328428)))',
        srid=25832)
    plan.name = 'correct'

    bereich = BP_Bereich()
    bereich.name = 'correct'
    bereich.geltungsbereich = plan.raeumlicherGeltungsbereich

    bp_objekt_poly = BP_BaugebietsTeilFlaeche()
    bp_objekt_poly.flaechenschluss = True
    bp_objekt_poly.position = WKTElement(
        'MultiPolygon (((571610.14549999998416752 5940812.23180000018328428, 571640.81519999995362014 5940809.48080000001937151, 571672.13399999996181577 5940838.12349999975413084, 571637.57389999995939434 5940849.39109999965876341, 571618.8227999999653548 5940833.81209999974817038, 571610.14549999998416752 5940812.23180000018328428)))',
        srid=25832)
    bereich.planinhalt.append(bp_objekt_poly)

    bp_objekt_poly2 = BP_BaugebietsTeilFlaeche()
    bp_objekt_poly2.flaechenschluss = True
    bp_objekt_poly2.position = WKTElement(
        'MultiPolygon (((571672.13399999996181577 5940838.12349999975413084, 571681.63450000004377216 5940846.81230000033974648, 571693.32970000000204891 5940859.52969999983906746, 571689.51969999994616956 5940870.4834000002592802, 571665.17790000000968575 5940876.14549999963492155, 571637.57389999995939434 5940849.39109999965876341, 571672.13399999996181577 5940838.12349999975413084)))',
        srid=25832)
    bereich.planinhalt.append(bp_objekt_poly2)

    plan.bereich.append(bereich)
    return plan


@pytest.fixture()
def plan():
    plan = BP_Plan()
    plan.raeumlicherGeltungsbereich = from_shape(Polygon([(0, 0), (0, 4), (4, 4), (4, 0)]), srid=25832)
    plan.name = 'test_invalid'

    bereich = BP_Bereich()
    bereich.name = 'test_invalid'
    bereich.geltungsbereich = plan.raeumlicherGeltungsbereich

    # polygon
    bp_objekt_poly = BP_BaugebietsTeilFlaeche()
    bp_objekt_poly.flaechenschluss = True
    bp_objekt_poly.position = from_shape(Polygon([(0, 3), (0, 4), (4, 4), (4, 3)]), srid=25832)
    bereich.planinhalt.append(bp_objekt_poly)

    # intersecting polygon
    bp_objekt_poly2 = BP_BaugebietsTeilFlaeche()
    bp_objekt_poly2.flaechenschluss = True
    bp_objekt_poly2.position = from_shape(Polygon([(3, 0), (3, 4), (4, 4), (4, 0)]), srid=25832)
    bereich.planinhalt.append(bp_objekt_poly2)

    # intersecting with bounds
    bp_objekt_poly3 = BP_BaugebietsTeilFlaeche()
    bp_objekt_poly3.flaechenschluss = True
    bp_objekt_poly3.position = from_shape(Polygon([(-1, 2), (-1, 3), (3, 3), (3, 2)]), srid=25832)
    bereich.planinhalt.append(bp_objekt_poly3)

    # adjacent polygon with duplicate vertices
    bp_objekt_poly4 = BP_BaugebietsTeilFlaeche()
    bp_objekt_poly4.flaechenschluss = True
    bp_objekt_poly4.position = from_shape(Polygon([(0, 1), (0, 2), (3, 2), (3, 2), (3, 0), (1, 0), (1, 1)]), srid=25832)
    bereich.planinhalt.append(bp_objekt_poly4)

    plan.bereich.append(bereich)
    return plan


class TestXPPlanDetailsDialog_constructExplorer:

    @pytest.mark.asyncio
    async def test_constructExplorer(self, dialog):
        plan = BP_Plan()
        plan.id = uuid.uuid4()
        plan.name = 'Test'
        bereich = BP_Bereich()
        bereich.name = 'Test'
        plan.bereich.append(bereich)

        await dialog.constructExplorer(plan)

        model = dialog.objectTree.model
        index_list = model.match(model.index(0, 0), Qt.DisplayRole, 'BP_Plan', -1, QtCore.Qt.MatchFixedString)
        assert len(index_list) == 1
        item = model.itemAtIndex(index_list[0])
        assert item._data.xtype == BP_Plan
        assert item.childCount() == 1
        assert item.data(0) == 'BP_Plan'
        assert item.row() == 0


class TestXPlanungDetailsDialog_GeometryValidation:

    def test_validateVertexUniqueness(self, dialog: XPPlanDetailsDialog, plan: XP_Plan):
        spy = QtTest.QSignalSpy(dialog.log.model().rowsInserted)

        dialog.validateUniqueVertices(plan)

        assert len(spy) == 1  # 1 area with duplicate vertex

    def test_highlight_error(self, dialog: XPPlanDetailsDialog, plan):
        validation_result = ValidationResult(
            xid=str(plan.id),
            xtype=plan.__class__,
            geom_wkt='MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)),((15 5, 40 10, 10 20, 5 10, 15 5)))',
            intersection_type=GeometryIntersectionType.Plan
        )

        item = ValidationGeometryErrorTreeWidgetItem(validation_result)
        dialog.log.addTopLevelItem(item)
        item.setSelected(True)

        dialog.highlightGeometryError()

        assert item.isVisible


class TestXPlanungDetailsDialog_displayOnMapCanvas:
    pass  # TODO: test map display


class TestXPlanungDialog_createRasterLayer:

    def test_createRasterLayer(self):
        with open(os.path.join(os.path.dirname(__file__), 'data/bp_plan.tif'), 'rb') as file:
            file_bytes = file.read()

        create_raster_layer("Raster", file_bytes)

        assert QgsProject.instance().mapLayersByName('Raster')

    def test_createRasterLayer_withGroup(self):
        root = QgsProject.instance().layerTreeRoot()
        layer_group = root.addGroup("Test_Raster")

        with open(os.path.join(os.path.dirname(__file__), 'data/bp_plan.tif'), 'rb') as file:
            file_bytes = file.read()

        create_raster_layer("Raster", file_bytes, group=layer_group)

        assert QgsProject.instance().mapLayersByName('Raster')
