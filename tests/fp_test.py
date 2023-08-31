import pytest

from SAGisXPlanung.FPlan.FP_Bebauung.feature_types import FP_BebauungsFlaeche
from SAGisXPlanung.XPlan.enums import XP_Sondernutzungen, XP_AllgArtDerBaulNutzung, XP_BesondereArtDerBaulNutzung
from SAGisXPlanung.XPlan.types import ConformityException


class TestFP_BebauungsFlaeche:

    def test_validation_sondernutzung_case1(self):
        o = FP_BebauungsFlaeche()

        o.sonderNutzung = [XP_Sondernutzungen.Ferienhausgebiet.name]
        o.allgArtDerBaulNutzung = XP_AllgArtDerBaulNutzung.SonderBauflaeche.name
        o.besondereArtDerBaulNutzung = XP_BesondereArtDerBaulNutzung.AllgWohngebiet

        with pytest.raises(ConformityException) as exc_info:
            o.validate()

        assert exc_info.value.code == '5.3.1.2'

    def test_validation_sondernutzung_case2(self):
        o = FP_BebauungsFlaeche()

        o.sonderNutzung = [XP_Sondernutzungen.Einkaufszentrum.name]
        o.allgArtDerBaulNutzung = XP_AllgArtDerBaulNutzung.SonderBauflaeche.name
        o.besondereArtDerBaulNutzung = XP_BesondereArtDerBaulNutzung.AllgWohngebiet

        with pytest.raises(ConformityException) as exc_info:
            o.validate()

        assert exc_info.value.code == '5.3.1.2'

    def test_validation_sondernutzung_valid(self):
        o = FP_BebauungsFlaeche()

        o.sonderNutzung = [XP_Sondernutzungen.Einkaufszentrum.name]
        o.allgArtDerBaulNutzung = XP_AllgArtDerBaulNutzung.SonderBauflaeche.name
        o.besondereArtDerBaulNutzung = XP_BesondereArtDerBaulNutzung.SondergebietSonst.name

        o.validate()

    def test_validation_gfz_case1(self):
        o = FP_BebauungsFlaeche()
        o.GFZ = 0.5
        o.GFZmin = 0.2

        with pytest.raises(ConformityException) as exc_info:
            o.validate()

        assert exc_info.value.code == '5.3.1.4'

    def test_validation_gfz_case2(self):
        o = FP_BebauungsFlaeche()
        o.GFZmax = 0.9

        with pytest.raises(ConformityException) as exc_info:
            o.validate()

        assert exc_info.value.code == '5.3.1.4'

    def test_validation_gfz_valid_case1(self):
        o = FP_BebauungsFlaeche()
        o.GFZ = 0.5
        o.validate()

    def test_validation_gfz_valid_case2(self):
        o = FP_BebauungsFlaeche()
        o.GFZmin = 0.5
        o.GFZmax = 0.7
        o.validate()

    def test_validation_baunutzung_case1(self):
        o = FP_BebauungsFlaeche()
        o.allgArtDerBaulNutzung = XP_AllgArtDerBaulNutzung.WohnBauflaeche.name
        o.besondereArtDerBaulNutzung = XP_BesondereArtDerBaulNutzung.Industriegebiet.name

        with pytest.raises(ConformityException) as exc_info:
            o.validate()

        assert exc_info.value.code == '5.3.1.1'

    def test_validation_baunutzung_case2(self):
        o = FP_BebauungsFlaeche()
        o.allgArtDerBaulNutzung = XP_AllgArtDerBaulNutzung.WohnBauflaeche.name
        o.besondereArtDerBaulNutzung = XP_BesondereArtDerBaulNutzung.Dorfgebiet.name

        with pytest.raises(ConformityException) as exc_info:
            o.validate()

        assert exc_info.value.code == '5.3.1.1'
