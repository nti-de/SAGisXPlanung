from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


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

    def short_desc(self):
        _abbreviation_map = {
            BP_Dachform.Flachdach: 'FD',
            BP_Dachform.Pultdach: 'PD',
            BP_Dachform.VersetztesPultdach: 'VPD',
            BP_Dachform.GeneigtesDach: 'GD',
            BP_Dachform.Satteldach: 'SD',
            BP_Dachform.Walmdach: 'WD',
            BP_Dachform.KrueppelWalmdach: 'KWD',
            BP_Dachform.Mansarddach: 'MD',
            BP_Dachform.Zeltdach: 'ZD',
            BP_Dachform.Kegeldach: 'KeD',
            BP_Dachform.Kuppeldach: 'KuD',
            BP_Dachform.Sheddach: 'ShD',
            BP_Dachform.Bogendach: 'BD',
            BP_Dachform.Turmdach: 'TuD',
            BP_Dachform.Tonnendach: 'ToD',
            BP_Dachform.Mischform: 'GDF',
            BP_Dachform.Sonstiges: 'SDF',
        }
        return _abbreviation_map.get(self, None)


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


class BP_ZweckbestimmungGemeinschaftsanlagen(XPlanungEnumMixin, Enum):
    """ Spezifikation der Zweckbestimmung einer Gemeinschaftsanlage. """

    Gemeinschaftsstellplaetze = 1000
    Gemeinschaftsgaragen = 2000
    Spielplatz = 3000
    Carport = 3100
    GemeinschaftsTiefgarage = 3200
    Nebengebaeude = 3300
    AbfallSammelanlagen = 3400
    EnergieVerteilungsanlagen = 3500
    AbfallWertstoffbehaelter = 3600
    Freizeiteinrichtungen = 3700
    Laermschutzanlagen = 3800
    AbwasserRegenwasser = 3900
    Ausgleichsmassnahmen = 4000
    Fahrradstellplaetze = 4100
    Gemeinschaftsdachgaerten = 4200
    GemeinschaftlichNutzbareDachflaechen = 4300
    Sonstiges = 9999


class BP_NebenanlagenAusschlussTyp(XPlanungEnumMixin, Enum):
    """ Art des Ausschlusses. """

    Einschraenkung = 1000
    Ausschluss = 2000


class BP_TypWohngebaeudeFlaeche(XPlanungEnumMixin, Enum):
    """ Festlegung der zu errichtenden Gebäude gemäß §9 Absatz 2d Nr. 1 - 3 BauGB """

    Wohngebaeude = 1000
    GebaeudeFoerderung = 2000
    GebaeudeStaedtebaulicherVertrag = 3000


class BP_GebaeudeStellungTypen(XPlanungEnumMixin, Enum):
    """ Art der Spezifikation der Gebaeudestellung. """

    Firstrichtung = 1000
    Dachneigungsrichtung = 2000
    StellungBaulAnlagen = 3000
