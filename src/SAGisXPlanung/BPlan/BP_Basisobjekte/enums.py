from enum import Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class BP_PlanArt(XPlanungEnumMixin, Enum):
    """ Typ des vorliegenden Bebauungsplans. """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    BPlan = 1000
    EinfacherBPlan = 10000
    QualifizierterBPlan = 10001
    BebauungsplanZurWohnraumversorgung = 10002, XPlanVersion.SIX
    VorhabenbezogenerBPlan = 3000
    VorhabenUndErschliessungsplan = 3100
    InnenbereichsSatzung = 4000
    KlarstellungsSatzung = 40000
    EntwicklungsSatzung = 40001
    ErgaenzungsSatzung = 40002
    AussenbereichsSatzung = 5000
    OertlicheBauvorschrift = 7000
    Sonstiges = 9999


class BP_Verfahren(XPlanungEnumMixin, Enum):
    """ Verfahrensart der BPlan-Aufstellung oder -Änderung. """

    Normal = 1000
    Parag13 = 2000
    Parag13a = 3000
    Parag13b = 4000


class BP_Rechtsstand(XPlanungEnumMixin, Enum):
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
    Satzung = 3000
    InkraftGetreten = 4000
    TeilweiseUntergegangen = 4500
    TeilweiseAufgehoben = 45000, XPlanVersion.SIX
    TeilweiseAusserKraft = 45001, XPlanVersion.SIX
    Untergegangen = 5000
    Aufgehoben = 50000
    AusserKraft = 50001


class BP_Rechtscharakter(XPlanungEnumMixin, Enum):
    """ Rechtliche Charakterisierung des Planinhaltes """

    Festsetzung = 1000
    NachrichtlicheUebernahme = 2000
    Hinweis = 3000
    Vermerk = 4000
    Kennzeichnung = 5000
    Unbekannt = 9998

    def to_xp_rechtscharakter(self):
        from SAGisXPlanung.XPlan.enums import XP_Rechtscharakter

        if self.value == 1000:
            return XP_Rechtscharakter.FestsetzungBPlan
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


class BP_VerlaengerungVeraenderungssperre(XPlanungEnumMixin, Enum):
    """ Gibt an, ob die Veränderungssperre bereits ein-oder zweimal verlängert wurde. """

    Keine = 1000
    ErsteVerlaengerung = 2000
    ZweiteVerlaengerung = 3000
