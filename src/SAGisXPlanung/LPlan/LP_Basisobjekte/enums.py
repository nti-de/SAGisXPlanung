from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class LP_PlanArt(XPlanungEnumMixin, Enum):
    """ Typ des vorliegenden Landschaftsplans. """

    Landschaftsprogramm = 1000
    Landschaftsrahmenplan = 2000
    Landschaftsplan = 3000
    Gruenordnungsplan = 4000
    Sonstiges = 9999


class LP_Rechtsstand(XPlanungEnumMixin, Enum):
    """ Rechtsstand des Plans """

    Aufstellungsbeschluss = 1000
    Entwurf = 2000
    Plan = 3000
    Wirksamkeit = 4000
    Untergegangen = 5000


class LP_Raumkonkretisierung(XPlanungEnumMixin, Enum):
    """ Rechtsstand des Plans """

    Scharf = 1000
    Suchraum = 2000
    Unscharf = 3000
    Position = 4000
    Raumunkonkret = 5000
    Unbekannt = 9998


# 5.3
class LP_Rechtscharakter(XPlanungEnumMixin, Enum):
    """ Rechtliche Charakterisierung des Planinhaltes """

    Festsetzung = 1000
    Geplant = 2000
    NachrichtlicheUebernahme = 3000
    DarstellungKennzeichnung = 4000
    FestsetzungInBPlan = 5000
    Unbekannt = 9998
    SonstigerStatus = 9999

    def to_xp_rechtscharakter(self):
        from SAGisXPlanung.XPlan.enums import XP_Rechtscharakter

        if self.value == 1000:
            return XP_Rechtscharakter.FestsetzungImLP
        elif self.value == 2000:
            return XP_Rechtscharakter.GeplanteFestsetzungImLP
        elif self.value == 3000:
            return XP_Rechtscharakter.NachrichtlicheUebernahme
        elif self.value == 4000:
            return XP_Rechtscharakter.DarstellungKennzeichnungImLP
        elif self.value == 5000:
            return XP_Rechtscharakter.FestsetzungBPlan
        elif self.value == 9998:
            return XP_Rechtscharakter.Unbekannt
        elif self.value == 9998:
            return XP_Rechtscharakter.Sonstiges
