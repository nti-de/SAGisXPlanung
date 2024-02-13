import pytest

from qgis.core import (QgsSimpleLineSymbolLayer, QgsRuleBasedRenderer, QgsSimpleFillSymbolLayer, QgsWkbTypes,
                       QgsSingleSymbolRenderer)
from qgis.PyQt.QtGui import QColor

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche, BP_BauGrenze
from SAGisXPlanung.BPlan.BP_Gemeinbedarf_Spiel_und_Sportanlagen.feature_types import BP_SpielSportanlagenFlaeche, \
    BP_GemeinbedarfsFlaeche
from SAGisXPlanung.BPlan.BP_Landwirtschaft_Wald_und_Gruenflaechen.feature_types import BP_GruenFlaeche, \
    BP_LandwirtschaftsFlaeche, BP_WaldFlaeche
from SAGisXPlanung.BPlan.BP_Naturschutz_Landschaftsbild_Naturhaushalt.feature_types import BP_AnpflanzungBindungErhaltung
from SAGisXPlanung.BPlan.BP_Ver_und_Entsorgung.feature_types import BP_VerEntsorgung
from SAGisXPlanung.BPlan.BP_Verkehr.feature_types import BP_StrassenVerkehrsFlaeche, \
    BP_VerkehrsflaecheBesondererZweckbestimmung
from SAGisXPlanung.BPlan.BP_Wasser.feature_types import BP_GewaesserFlaeche
from SAGisXPlanung.XPlan.enums import XP_AllgArtDerBaulNutzung


class TestRenderer:

    @pytest.mark.parametrize('cls_type, expected_color, expected_renderer',
                             [(BP_Plan, QColor(0, 0, 0), QgsSimpleLineSymbolLayer),
                              (BP_BaugebietsTeilFlaeche, QColor('#f4c3b4'), QgsRuleBasedRenderer),
                              (BP_BauGrenze, QColor('#1e8ebe'), QgsSimpleLineSymbolLayer),
                              (BP_LandwirtschaftsFlaeche, QColor('#befe9d'), QgsSimpleFillSymbolLayer),
                              (BP_WaldFlaeche, QColor('#17a8a5'), QgsSimpleFillSymbolLayer),
                              (BP_StrassenVerkehrsFlaeche, QColor('#fbdd19'), QgsSimpleFillSymbolLayer),
                              ])
    def test_renderer(self, cls_type, expected_color, expected_renderer):
        c = cls_type()
        if cls_type == BP_BaugebietsTeilFlaeche:
            c.allgArtDerBaulNutzung = XP_AllgArtDerBaulNutzung.WohnBauflaeche
        r = c.renderer()

        if isinstance(r, QgsRuleBasedRenderer):
            assert isinstance(r, expected_renderer)
            assert any(rule.symbol().color() == expected_color for rule in r.rootRule().children())
            return

        symbol = r.symbol()
        assert symbol.symbolLayerCount()
        assert isinstance(symbol.symbolLayer(0), expected_renderer)
        assert symbol.symbolLayer(0).color() == expected_color

    def test_spiel_sportanlage_renderer(self):
        r = BP_SpielSportanlagenFlaeche.renderer()

        assert isinstance(r, QgsRuleBasedRenderer)
        assert len(r.rootRule().children()) == 3
        assert any(rule.isElse() for rule in r.rootRule().children())

    def test_gruenflaeche_renderer(self):
        r = BP_GruenFlaeche.renderer()

        assert isinstance(r, QgsRuleBasedRenderer)
        assert len(r.rootRule().children()) == 8
        assert any(rule.isElse() for rule in r.rootRule().children())

    def test_gewaesser_renderer(self):
        r = BP_GewaesserFlaeche.renderer()

        assert isinstance(r, QgsRuleBasedRenderer)
        assert len(r.rootRule().children()) == 2
        assert any(rule.isElse() for rule in r.rootRule().children())

    def test_gemeinbedarf_renderer(self):
        r = BP_GemeinbedarfsFlaeche.renderer()

        assert isinstance(r, QgsRuleBasedRenderer)
        assert len(r.rootRule().children()) == 12
        assert any(rule.isElse() for rule in r.rootRule().children())

    def test_besonderer_verkehr_renderer(self):
        r = BP_VerkehrsflaecheBesondererZweckbestimmung.renderer(QgsWkbTypes.PolygonGeometry)

        assert isinstance(r, QgsRuleBasedRenderer)
        assert len(r.rootRule().children()) == 4
        assert any(rule.isElse() for rule in r.rootRule().children())

    def test_ver_entsorgung_renderer(self):
        r = BP_VerEntsorgung.renderer(geom_type=QgsWkbTypes.PolygonGeometry)

        assert isinstance(r, QgsRuleBasedRenderer)
        assert len(r.rootRule().children()) == 10
        assert any(rule.isElse() for rule in r.rootRule().children())

    def test_pflanzung_renderer(self):
        r = BP_AnpflanzungBindungErhaltung.renderer(QgsWkbTypes.PointGeometry)

        assert isinstance(r, QgsRuleBasedRenderer)
        assert len(r.rootRule().children()) == 6

        r = BP_AnpflanzungBindungErhaltung.renderer(QgsWkbTypes.PolygonGeometry)

        assert isinstance(r, QgsSingleSymbolRenderer)

