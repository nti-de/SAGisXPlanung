from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.BPlan.BP_Gemeinbedarf_Spiel_und_Sportanlagen.feature_types import BP_GemeinbedarfsFlaeche

class TestElementOrderMixin:
    def test_element_order_with_geom_exclude(self):
        _class = BP_Plan()
        attribute_names = _class.element_order(with_geometry=False)
        assert 'raeumlicherGeltungsbereich' not in attribute_names

        _class = BP_GemeinbedarfsFlaeche()
        attribute_names = _class.element_order(with_geometry=False)
        assert 'position' not in attribute_names

    def test_element_order_with_base_include(self):
        _class = BP_Plan()
        attribute_names = _class.element_order(include_base=False)
        assert 'uuid' not in attribute_names

    def test_xplan_attribute_name_valid(self):
        _class = BP_Plan()
        assert _class.xplan_attribute_name('veraenderungssperre') == 'veraenderungssperre'
        assert _class.xplan_attribute_name('rel_veraenderungssperre') == 'veraenderungssperre'

    def test_attribute_by_version_valid(self):
        _class = BP_Plan()
        assert _class.attribute_by_version('veraenderungssperre', XPlanVersion.FIVE_THREE) == 'veraenderungssperre'
        assert _class.attribute_by_version('veraenderungssperre', XPlanVersion.SIX) == 'rel_veraenderungssperre'

    def test_attribute_by_version_simple_attribute(self):
        _class = BP_Plan()
        assert _class.attribute_by_version('name', XPlanVersion.FIVE_THREE) == 'name'
        assert _class.attribute_by_version('name', XPlanVersion.SIX) == 'name'
