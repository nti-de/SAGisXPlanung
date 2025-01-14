from enum import Enum

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
