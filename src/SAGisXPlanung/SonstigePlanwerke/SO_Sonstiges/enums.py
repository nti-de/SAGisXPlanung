from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class SO_KlassifizGelaendemorphologie(XPlanungEnumMixin, Enum):
    """ Klassifikation der Gelaendestruktur. """

    Terassenkante = 1000
    Rinne = 1100
    EhemMaeander = 1200
    SonstigeStruktur = 9999
