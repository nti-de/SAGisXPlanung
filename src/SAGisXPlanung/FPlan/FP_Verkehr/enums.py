from enum import Enum

from SAGisXPlanung.XPlan.mixins import XPlanungEnumMixin


class FP_ZweckbestimmungStrassenverkehr(XPlanungEnumMixin, Enum):
    """ Zweckbestimmung des Straßen-Objektes """

    Autobahn = 1000
    Hauptverkehrsstrasse = 1200
    Ortsdurchfahrt = 1300
    SonstigerVerkehrswegAnlage = 1400
    VerkehrsberuhigterBereich = 14000
    Platz = 14001
    Fussgaengerbereich = 14002
    RadGehweg = 14003
    Radweg = 14004
    Gehweg = 14005
    Wanderweg = 14006
    ReitKutschweg = 14007
    Rastanlage = 14008
    Busbahnhof = 14009
    UeberfuehrenderVerkehrsweg = 140010
    UnterfuehrenderVerkehrsweg = 140011
    Wirtschaftsweg = 140012
    LandwirtschaftlicherVerkehr = 140013
    RuhenderVerkehr = 1600
    Parkplatz = 16000
    FahrradAbstellplatz = 16001
    P_RAnlage = 16002
    CarSharing = 3000
    BikeSharing = 3100
    B_RAnlage = 3200
    Parkhaus = 3300
    Mischverkehrsflaeche = 3400
    Ladestation = 3500
    Sonstiges = 9999
