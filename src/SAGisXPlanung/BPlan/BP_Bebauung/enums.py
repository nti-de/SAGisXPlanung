from enum import Enum

from SAGisXPlanung.XPlan.mixins import XPlanungEnumMixin


class BP_Dachform(XPlanungEnumMixin, Enum):
    """ Erlaubte Dachform innerhalb einer Bebauungsfläche. """

    Flachdach = 1000
    Pultdach = 2100
    VersetztesPultdach = 2200
    GeneigtesDach = 3000
    Satteldach = 3100
    Walmdach = 3200
    KrueppelWalmdach = 3300
    Mansarddach = 3400
    Zeltdach = 3500
    Kegeldach = 3600
    Kuppeldach = 3700
    Sheddach = 3800
    Bogendach = 3900
    Turmdach = 4000
    Tonnendach = 4100
    Mischform = 5000
    Sonstiges = 9999


class BP_Zulaessigkeit(XPlanungEnumMixin, Enum):
    """ Für urbane Gebiete oder Teile solcher Gebiete kann festgesetzt werden, dass in Gebäuden  im Erdgeschoss an der
        Straßenseite eine Wohnnutzung nicht oder nur ausnahmsweise zulässig ist """

    Zulaessig = 1000
    NichtZulaessig = 2000
    AusnahmsweiseZulaessig = 3000


class BP_Bauweise(XPlanungEnumMixin, Enum):
    """ Festsetzung der Bauweise (§9, Abs. 1, Nr. 2 BauGB) """

    KeineAngabe = None
    OffeneBauweise = 1000
    GeschlosseneBauweise = 2000
    AbweichendeBauweise = 3000


class BP_BebauungsArt(XPlanungEnumMixin, Enum):
    """ Detaillierte Festsetzung der Bauweise (§9, Abs. 1, Nr. 2 BauGB) """

    Einzelhaeuser = 1000
    Doppelhaeuser = 2000
    Hausgruppen = 3000
    EinzelDoppelhaeuser = 4000
    EinzelhaeuserHausgruppen = 5000
    DoppelhaeuserHausgruppen = 6000
    Reihenhaeuser = 7000
    EinzelhaeuserDoppelhaeuserHausgruppen = 8000


class BP_GrenzBebauung(XPlanungEnumMixin, Enum):
    """ Festsetzung der Bebauung der vorderen Grundstücksgrenze (§9, Abs. 1, Nr. 2 BauGB) """

    KeineAngabe = None
    Verboten = 1000
    Erlaubt = 2000
    Erzwungen = 3000


class BP_ZweckbestimmungNebenanlagen(XPlanungEnumMixin, Enum):
    """ Spezifikation der Zweckbestimmung einer Nebenanlage """

    Stellplaetze = 1000
    Garagen = 2000
    Spielplatz = 3000
    Carport = 3100
    Tiefgarage = 3200
    Nebengebaeude = 3300
    AbfallSammelanlagen = 3400
    EnergieVerteilungsanlagen = 3500
    AbfallWertstoffbehaelter = 3600
    Fahrradstellplaetze = 3700
    Sonstiges = 9999
