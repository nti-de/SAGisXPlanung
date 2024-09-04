import pytest
from qgis.core import QgsEditorWidgetSetup, QgsVectorLayer

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan, BP_Objekt
from SAGisXPlanung.BPlan.BP_Sonstiges.feature_types import BP_Wegerecht
from SAGisXPlanung.core.helper import get_field_type
from SAGisXPlanung.gui.attributetable.editor_widget import EditorWidgetBridge, FieldType

class TestEditorWidgetBridge:

    @pytest.mark.parametrize('xtype,field_name,expected_type', [
        (BP_Objekt, 'text', 'Text'),
        (BP_Wegerecht, 'typ', 'CheckableEnum'),
        (BP_Plan, 'planArt', 'ValueMap'),
        (BP_Plan, 'traegerbeteiligungsStartDatum', 'Hidden'),
        (BP_Plan, 'technHerstellDatum', 'DateTime'),
    ])
    def test_create(self, xtype,field_name, expected_type):
        field_type = get_field_type(xtype, field_name)
        layer = QgsVectorLayer('point?crs=epsg:4326', "Scratch point layer", "memory")
        layer.setCustomProperty('xplanung/type', xtype.__name__)

        widget_config = EditorWidgetBridge.create(field_type, layer)
        assert isinstance(widget_config, FieldType)

        assert isinstance(widget_config.get_editor_widget(), QgsEditorWidgetSetup)
        assert widget_config.get_editor_widget().type() == expected_type