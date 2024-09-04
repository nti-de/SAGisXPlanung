from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class BP_ZweckbestimmungStrassenverkehr(XPlanungEnumMixin, Enum):
    """ Zweckbestimmungen für Strassenverkehrsflächen"""

    Parkierungsflaeche = 1000
    Fussgaengerbereich = 1100
    VerkehrsberuhigterBereich = 1200
    RadGehweg = 1300
    Radweg = 1400
    Gehweg = 1500
    Wanderweg = 1550
    ReitKutschweg = 1560
    Wirtschaftsweg = 1580
    FahrradAbstellplatz = 1600
    UeberfuehrenderVerkehrsweg = 1700
    UnterfuehrenderVerkehrsweg = 1800
    P_RAnlage = 2000
    Platz = 2100
    Anschlussflaeche = 2200
    LandwirtschaftlicherVerkehr = 2300
    Verkehrsgruen = 2400
    Rastanlage = 2500
    Busbahnhof = 2600
    CarSharing = 3000
    BikeSharing = 3100
    B_RAnlage = 3200
    Parkhaus = 3300
    Mischverkehrsflaeche = 3400
    Ladestation = 3500
    Sonstiges = 9999


class BP_BereichOhneEinAusfahrtTypen (XPlanungEnumMixin, Enum):
    """ Typ des Bereiches ohne Ein- und Ausfahrt """

    KeineEinfahrt = 1000
    KeineAusfahrt = 2000
    KeineEinAusfahrt = 3000


class BP_EinfahrtTypen(XPlanungEnumMixin, Enum):
    """ Typ der Einfahrt """

    Einfahrt = 1000
    Ausfahrt = 2000
    EinAusfahrt = 3000
