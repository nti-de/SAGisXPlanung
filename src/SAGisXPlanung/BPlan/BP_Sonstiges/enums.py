from enum import Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class BP_WegerechtTypen(XPlanungEnumMixin, Enum):
    """ Typ des Wegerechts """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Gehrecht = 1000
    Fahrrecht = 2000
    Radfahrrecht = 2500
    GehFahrrecht = 3000, XPlanVersion.FIVE_THREE
    Leitungsrecht = 4000
    GehLeitungsrecht = 4100, XPlanVersion.FIVE_THREE
    FahrLeitungsrecht = 4200, XPlanVersion.FIVE_THREE
    GehFahrLeitungsrecht = 5000, XPlanVersion.FIVE_THREE
    Sonstiges = 9999


class BP_AbgrenzungenTypen(XPlanungEnumMixin, Enum):
    """ Typ der Abgrenzung """

    Nutzungsartengrenze = 1000
    UnterschiedlicheHoehen = 2000
    SonstigeAbgrenzung = 9999


class BP_AbstandsMassTypen(XPlanungEnumMixin, Enum):
    """ Typ des Abstandsmaß-Objekts. """

    Masspfeil = 1000
    Masskreis = 2000
