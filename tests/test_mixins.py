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
