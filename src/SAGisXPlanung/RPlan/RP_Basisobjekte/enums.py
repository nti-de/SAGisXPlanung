from enum import Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class RP_Art(XPlanungEnumMixin, Enum):
    """ Art des Raumordnungsplans. """

    Regionalplan = 1000
    SachlicherTeilplanRegionalebene = 2000
    SachlicherTeilplanLandesebene = 2001
    Braunkohlenplan = 3000
    LandesweiterRaumordnungsplan = 4000
    StandortkonzeptBund = 5000
    AWZPlan = 5001
    RaeumlicherTeilplan = 6000
    Sonstiges = 9999


class RP_Verfahren(XPlanungEnumMixin, Enum):
    """ Verfahrensstatus des Plans """

    Aenderung = 1000
    Teilfortschreibung = 2000
    Neuaufstellung = 3000
    Gesamtfortschreibung = 4000
    Aktualisierung = 5000
    Neubekanntmachung = 6000


class RP_Rechtsstand(XPlanungEnumMixin, Enum):
    """ Rechtsstand des Plans """

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
    EntwurfGenehmigt = 2001
    EntwurfGeaendert = 2002
    EntwurfAufgegeben = 2003
    EntwurfRuht = 2004
    Plan = 3000
    Inkraftgetreten = 4000
    AllgemeinePlanungsabsicht = 5000
    TeilweiseAusserKraft = 5500, XPlanVersion.SIX
    AusserKraft = 6000
    PlanUngueltig = 7000


# 5.3
class RP_Rechtscharakter(XPlanungEnumMixin, Enum):
    """ Rechtliche Charakterisierung des Planinhaltes """

    ZielDerRaumordnung = 1000
    GrundsatzDerRaumordnung = 2000
    NachrichtlicheUebernahme = 3000
    NachrichtlicheUebernahmeZiel = 4000
    NachrichtlicheUebernahmeGrundsatz = 5000
    NurInformationsgehalt = 6000
    TextlichesZiel = 7000
    ZielundGrundsatz = 8000
    Vorschlag = 9000
    Unbekannt = 9998

    def to_xp_rechtscharakter(self):
        from SAGisXPlanung.XPlan.enums import XP_Rechtscharakter

        if self.value == 1000:
            return XP_Rechtscharakter.ZielDerRaumordnung
        elif self.value == 2000:
            return XP_Rechtscharakter.GrundsatzDerRaumordnung
        elif self.value == 3000:
            return XP_Rechtscharakter.NachrichtlicheUebernahme
        elif self.value == 4000:
            return XP_Rechtscharakter.NachrichtlicheUebernahmeZiel
        elif self.value == 5000:
            return XP_Rechtscharakter.NachrichtlicheUebernahmeGrundsatz
        elif self.value == 6000:
            return XP_Rechtscharakter.NurInformationsgehaltRPlan
        elif self.value == 7000:
            return XP_Rechtscharakter.TextlichesZielRaumordnung
        elif self.value == 8000:
            return XP_Rechtscharakter.ZielUndGrundsatzRaumordnung
        elif self.value == 9000:
            return XP_Rechtscharakter.VorschlagRaumordnung
        elif self.value == 9998:
            return XP_Rechtscharakter.Unbekannt

