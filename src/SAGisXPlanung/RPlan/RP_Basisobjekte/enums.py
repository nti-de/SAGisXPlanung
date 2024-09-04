from enum import Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class RP_Art(XPlanungEnumMixin, Enum):
    """ Art des Raumordnungsplans. """

    Regionalplan = 1000
    SachlicherTeilplanRegionalebene = 2000
    SachlicherTeilplanLandesebene = 2001
    Braunkohlenplan = 3000
    LandesweiterRaumordnungsplan = 4000
    StandortkonzeptBund = 5000
    AWZPlan = 5001
    RaeumlicherTeilplan = 6000
    Sonstiges = 9999


class RP_Verfahren(XPlanungEnumMixin, Enum):
    """ Verfahrensstatus des Plans """

    Aenderung = 1000
    Teilfortschreibung = 2000
    Neuaufstellung = 3000
    Gesamtfortschreibung = 4000
    Aktualisierung = 5000
    Neubekanntmachung = 6000


class RP_Rechtsstand(XPlanungEnumMixin, Enum):
    """ Rechtsstand des Plans """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Aufstellungsbeschluss = 1000
    Entwurf = 2000
    EntwurfGenehmigt = 2001
    EntwurfGeaendert = 2002
    EntwurfAufgegeben = 2003
    EntwurfRuht = 2004
    Plan = 3000
    Inkraftgetreten = 4000
    AllgemeinePlanungsabsicht = 5000
    TeilweiseAusserKraft = 5500, XPlanVersion.SIX
    AusserKraft = 6000
    PlanUngueltig = 7000
