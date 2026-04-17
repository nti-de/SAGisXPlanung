from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class BP_SchallleistungspegelBerechnungsgrundlage(XPlanungEnumMixin, Enum):
    """ Technische Grundlage fuer die Berechnung der Schallleistungspegel. """

    DIN45691 = 1000
    DIN18005 = 2000
    VDI2714 = 3000
    ISO9613_2 = 4000


class BP_SchallleistungspegelTypen(XPlanungEnumMixin, Enum):
    """ Typ der festgesetzten Schallleistungspegel. """

    LEK = 1000
    IFSP = 2000
    FSP = 3000
