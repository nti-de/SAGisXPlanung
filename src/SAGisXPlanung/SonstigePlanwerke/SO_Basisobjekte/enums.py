from enum import Enum

from SAGisXPlanung.XPlan.mixins import XPlanungEnumMixin


class SO_Rechtscharakter(XPlanungEnumMixin, Enum):
    """ Rechtscharakter des Planinhalts """

    FestsetzungBPlan = 1000
    DarstellungFPlan = 1500
    InhaltLPlan = 1800
    NachrichtlicheUebernahme = 2000
    Hinweis = 3000
    Vermerk = 4000
    Kennzeichnung = 5000
    Unbekannt = 9998
    Sonstiges = 9999

    def to_xp_rechtscharakter(self):
        from SAGisXPlanung.XPlan.enums import XP_Rechtscharakter

        if self.value == 1000:
            return XP_Rechtscharakter.FestsetzungBPlan
        if self.value == 1500:
            return XP_Rechtscharakter.DarstellungFPlan
        if self.value == 1800:
            return XP_Rechtscharakter.FestsetzungImLP
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
        elif self.value == 9999:
            return XP_Rechtscharakter.Sonstiges
