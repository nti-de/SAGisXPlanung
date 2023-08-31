from enum import Enum

from SAGisXPlanung.XPlan.mixins import XPlanungEnumMixin


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

