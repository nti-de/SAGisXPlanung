from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class BP_WegerechtTypen(XPlanungEnumMixin, Enum):
    """ Typ des Wegerechts """

    Gehrecht = 1000
    Fahrrecht = 2000
    Radfahrrecht = 2500
    Leitungsrecht = 4000
    Sonstiges = 9999


class BP_AbgrenzungenTypen(XPlanungEnumMixin, Enum):
    """ Typ der Abgrenzung """

    Nutzungsartengrenze = 1000
    UnterschiedlicheHoehen = 2000
    SonstigeAbgrenzung = 9999
