from enum import Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class FP_ZweckbestimmungPrivilegiertesVorhaben(XPlanungEnumMixin, Enum):
    """ Zweckbestimmungen für privilegierte Außenbereichsvorhabe"""

    LandForstwirtschaft = 1000
    Aussiedlerhof = 10000
    Altenteil = 10001
    Reiterhof = 10002
    Gartenbaubetrieb = 10003
    Baumschule = 10004
    OeffentlicheVersorgung = 1200
    Wasser = 12000
    Gas = 12001
    Waerme = 12002
    Elektrizitaet = 12003
    Telekommunikation = 12004
    Abwasser = 12005
    OrtsgebundenerGewerbebetrieb = 1400
    BesonderesVorhaben = 1600
    BesondereUmgebungsAnforderung = 16000
    NachteiligeUmgebungsWirkung = 16001
    BesondereZweckbestimmung = 16002
    ErneuerbareEnergien = 1800
    Windenergie = 18000
    Wasserenergie = 18001
    Solarenergie = 18002
    Biomasse = 18003
    Kernenergie = 2000
    NutzungKernerergie = 20000
    EntsorgungRadioaktiveAbfaelle = 20001
    Sonstiges = 9999
    StandortEinzelhof = 99990
    BebauteFlaecheAussenbereich = 99991


class FP_MassnahmeKlimawandelTypen(XPlanungEnumMixin, Enum):
    """ Klassifikation von Massnahmen zur Anpassung an den Klimawandel. """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    ErhaltFreiflaechen = 1000
    ErhaltPrivGruen = 10000
    ErhaltOeffentlGruen = 10001
    ErhaltKaltluftschneise = 10002, XPlanVersion.SIX
    SonstMassnahme = 9999
