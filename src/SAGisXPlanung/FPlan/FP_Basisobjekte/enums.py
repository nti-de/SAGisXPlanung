from enum import Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class FP_PlanArt(XPlanungEnumMixin, Enum):
    """ Typ des FPlans """

    FPlan = 1000
    GemeinsamerFPlan = 2000
    RegFPlan = 3000
    FPlanRegPlan = 4000
    SachlicherTeilplan = 8000
    Sonstiges = 9999


class FP_Verfahren(XPlanungEnumMixin, Enum):
    """ Verfahren nach dem ein FPlan aufgestellt oder geändert wird. """

    Normal = 1000
    Parag13 = 2000


class FP_Rechtsstand(XPlanungEnumMixin, Enum):
    """ Aktueller Rechtsstand des Plans. """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Aufstellungsbeschluss = 1000
    Entwurf = 2000
    FruehzeitigeBehoerdenBeteiligung = 2100
    FruehzeitigeOeffentlichkeitsBeteiligung = 2200
    Entwurfsbeschluss = 2250, XPlanVersion.SIX
    BehoerdenBeteiligung = 2300
    OeffentlicheAuslegung = 2400
    Plan = 3000
    Wirksamkeit = 4000
    Untergegangen = 5000
    Aufgehoben = 50000
    AusserKraft = 50001


class FP_Rechtscharakter(XPlanungEnumMixin, Enum):
    """ Rechtliche Charakterisierung des Planinhaltes """

    Darstellung = 1000
    NachrichtlicheUebernahme = 2000
    Hinweis = 3000
    Vermerk = 4000
    Kennzeichnung = 5000
    Unbekannt = 9998

    def to_xp_rechtscharakter(self):
        from SAGisXPlanung.XPlan.enums import XP_Rechtscharakter

        if self.value == 1000:
            return XP_Rechtscharakter.DarstellungFPlan
        elif self.value == 2000:
            return XP_Rechtscharakter.NachrichtlicheUebernahme
        elif self.value == 3000:
            return XP_Rechtscharakter.Hinweis
        elif self.value == 4000:
            return XP_Rechtscharakter.Vermerk
        elif self.value == 5000:
            return XP_Rechtscharakter.Kennzeichnung
        elif self.value == 9998:
            return XP_Rechtscharakter.Unbekannt
