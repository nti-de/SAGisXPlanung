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

