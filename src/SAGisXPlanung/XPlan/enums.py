import logging
from enum import Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.enums import FP_Rechtscharakter
from SAGisXPlanung.XPlan.mixins import XPlanungEnumMixin

logger = logging.getLogger(__name__)


class XP_VerlaengerungVeraenderungssperre(XPlanungEnumMixin, Enum):
    """ Gibt an, ob die Veränderungssperre bereits ein-oder zweimal verlängert wurde. """

    Keine = 1000
    ErsteVerlaengerung = 2000
    ZweiteVerlaengerung = 3000


class XP_BedeutungenBereich(XPlanungEnumMixin, Enum):
    """ Spezifikation der semantischen Bedeutung eines Bereiches. """

    Teilbereich = 1600
    Kompensationsbereich = 1800
    Sonstiges = 9999


class XP_ExterneReferenzArt(XPlanungEnumMixin, Enum):
    """ Typisierung der referierten Dokumente: Beliebiges Dokument oder georeferenzierter Plan. """

    Dokument = "Dokument"
    PlanMitGeoreferenz = "PlanMitGeoreferenz"


class XP_ExterneReferenzTyp(XPlanungEnumMixin, Enum):
    """ Typ / Inhalt eines referierten Dokuments oder Rasterplans. """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Beschreibung = 1000
    Begruendung = 1010
    Legende = 1020
    Rechtsplan = 1030
    Plangrundlage = 1040
    Umweltbericht = 1050
    Satzung = 1060
    Verordnung = 1065
    Karte = 1070
    Erlaeuterung = 1080
    ZusammenfassendeErklaerung = 1090
    Koordinatenliste = 2000
    Grundstuecksverzeichnis = 2100
    Pflanzliste = 2200
    Gruenordnungsplan = 2300
    Erschliessungsvertrag = 2400
    Durchfuehrungsvertrag = 2500
    StaedtebaulicherVertrag = 2600
    UmweltbezogeneStellungnahmen = 2700
    Beschluss = 2800
    VorhabenUndErschliessungsplan = 2900
    MetadatenPlan = 3000
    Genehmigung = 4000
    Bekanntmachung = 5000
    Schutzgebietsverordnung = 6000, XPlanVersion.SIX
    Rechtsverbindlich = 9998
    Informell = 9999


class XP_Rechtsstand(XPlanungEnumMixin, Enum):
    """ Angabe, ob der Planinhalt bereits besteht, geplant ist, oder zukünftig wegfallen soll. """

    Geplant = 1000
    Bestehend = 2000
    Fortfallend = 3000


class XP_AllgArtDerBaulNutzung(XPlanungEnumMixin, Enum):
    """ Spezifikation der allgemeinen Art der baulichen Nutzung """

    WohnBauflaeche = 1000
    GemischteBauflaeche = 2000
    GewerblicheBauflaeche = 3000
    SonderBauflaeche = 4000
    Sonstiges = 9999


class XP_BesondereArtDerBaulNutzung(XPlanungEnumMixin, Enum):
    """ Festsetzung der Art der baulichen Nutzung (§9, Abs. 1, Nr. 1 BauGB) """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Kleinsiedlungsgebiet = 1000
    ReinesWohngebiet = 1100
    AllgWohngebiet = 1200
    BesonderesWohngebiet = 1300
    Dorfgebiet = 1400
    DoerflichesWohngebiet = 1450
    Mischgebiet = 1500
    UrbanesGebiet = 1550
    Kerngebiet = 1600
    Gewerbegebiet = 1700
    Industriegebiet = 1800
    SondergebietErholung = 2000
    SondergebietSonst = 2100
    Wochenendhausgebiet = 3000
    Sondergebiet = 4000
    SonstigesGebiet = 9999


class XP_Sondernutzungen(XPlanungEnumMixin, Enum):
    """ Differenziert Sondernutzungen nach §10 und §11 der BauNVO von 1977 und 1990. """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Wochendhausgebiet = 1000
    Ferienhausgebiet = 1100
    Campingplatzgebiet = 1200
    Kurgebiet = 1300
    SonstSondergebietErholung = 1400
    Einzelhandelsgebiet = 1500
    GrossflaechigerEinzelhandel = 1600
    Ladengebiet = 16000
    Einkaufszentrum = 16001
    SonstGrossflEinzelhandel = 16002
    SondergebietGrosshandel = 1650, XPlanVersion.SIX
    Verkehrsuebungsplatz = 1700
    Hafengebiet = 1800
    SondergebietErneuerbareEnergie = 1900
    SondergebietMilitaer = 2000
    SondergebietLandwirtschaft = 2100
    SondergebietSport = 2200
    SondergebietGesundheitSoziales = 2300
    Klinikgebiet = 23000
    Golfplatz = 2400
    SondergebietKultur = 2500
    SondergebietTourismus = 2600
    SondergebietBueroUndVerwaltung = 2700
    SondergebietJustiz = 2720
    SondergebietHochschuleForschung = 2800
    SondergebietMesse = 2900
    SondergebietAndereNutzungen = 9999


class XP_AbweichungBauNVOTypen(XPlanungEnumMixin, Enum):
    """ Art der zulässigen Abweichung von der BauNVO """

    KeineAbweichung = None
    EinschraenkungNutzung = 1000
    AusschlussNutzung = 2000
    AusweitungNutzung = 3000
    SonstAbweichung = 9999


class XP_Nutzungsform(XPlanungEnumMixin, Enum):
    """ Art der Nutzungsform """

    Privat = 1000
    Oeffentlich = 2000


class XP_ZweckbestimmungLandwirtschaft(XPlanungEnumMixin, Enum):
    """ Zweckbestimmungen für landwirtschaftliche Flächen """

    LandwirtschaftAllgemein = 1000
    Ackerbau = 1100
    WiesenWeidewirtschaft = 1200
    GartenbaulicheErzeugung = 1300
    Obstbau = 1400
    Weinbau = 1500
    Imkerei = 1600
    Binnenfischerei = 1700
    Sonstiges = 9999


class XP_ZweckbestimmungWald(XPlanungEnumMixin, Enum):
    """ Zweckbestimmungen für Waldflächen """

    Naturwald = 1000
    Waldschutzgebiet = 10000
    Nutzwald = 1200
    Erholungswald = 1400
    Schutzwald = 1600
    Bodenschutzwald = 16000
    Biotopschutzwald = 16001
    NaturnaherWald = 16002
    SchutzwaldSchaedlicheUmwelteinwirkungen = 16003
    Schonwald = 16004
    Bannwald = 1700
    FlaecheForstwirtschaft = 1800
    ImmissionsgeschaedigterWald = 1900
    Sonstiges = 9999


class XP_EigentumsartWald(XPlanungEnumMixin, Enum):
    """ Festlegung der Eigentumsart eines Waldes"""

    OeffentlicherWald = 1000
    Staatswald = 1100
    Koerperschaftswald = 1200
    Kommunalwald = 12000
    Stiftungswald = 12001
    Privatwald = 2000
    Gemeinschaftswald = 20000
    Genossenschaftswald = 20001
    Kirchenwald = 3000
    Sonstiges = 9999


class XP_WaldbetretungTyp(XPlanungEnumMixin, Enum):  # TODO: this should probably be a checkable combobox
    """ Festlegung zusätzlicher, normalerweise nicht-gestatteter Aktivitäten, die in dem
        Wald ausgeführt werden dürfen, nach §14 Abs. 2 Bundeswaldgesetz """

    KeineZusaetzlicheBetretung = None
    Radfahren = 1000
    Reiten = 2000
    Fahren = 3000
    Hundesport = 4000
    Sonstiges = 9999


class XP_ZweckbestimmungGewaesser(XPlanungEnumMixin, Enum):
    """ Zweckbestimmungen für Wasserflächen"""

    Hafen = 1000
    Sportboothafen = 10000
    Wasserflaeche = 1100
    Fliessgewaesser = 1200
    Sonstiges = 9999


class XP_ZweckbestimmungVerEntsorgung(XPlanungEnumMixin, Enum):
    """ Zweckbestimmungen für Ver-/Entsorgungsflächen"""

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Elektrizitaet = 1000
    Hochspannungsleitung = 10000
    TrafostationUmspannwerk = 10001
    Solarkraftwerk = 10002
    Windkraftwerk = 10003
    Geothermiekraftwerk = 10004
    Elektrizitaetswerk = 10005
    Wasserkraftwerk = 10006
    BiomasseKraftwerk = 10007
    Kabelleitung = 10008
    Niederspannungsleitung = 10009
    Leitungsmast = 10010
    Kernkraftwerk = 10011
    Kohlekraftwerk = 10012
    Gaskraftwerk = 10013
    Gas = 1200
    Ferngasleitung = 12000
    Gaswerk = 12001
    Gasbehaelter = 12002
    Gasdruckregler = 12003
    Gasstation = 12004
    Gasleitung = 12005
    Erdoel = 1300
    Erdoelleitung = 13000
    Bohrstelle = 13001
    Erdoelpumpstation = 13002
    Oeltank = 13003
    Waermeversorgung = 1400
    Blockheizkraftwerk = 14000
    Fernwaermeleitung = 14001
    Fernheizwerk = 14002
    Wasser = 1600
    Wasserwerk = 16000
    Wasserleitung = 16001
    Wasserspeicher = 16002
    Brunnen = 16003
    Pumpwerk = 16004
    Quelle = 16005
    Abwasser = 1800
    Abwasserleitung = 18000
    Abwasserrueckhaltebecken = 18001
    Abwasserpumpwerk = 18002
    Klaeranlage = 18003
    AnlageKlaerschlamm = 18004
    SonstigeAbwasserBehandlungsanlage = 18005, XPlanVersion.FIVE_THREE
    SalzOderSoleleitungen = 18006
    Regenwasser = 2000
    RegenwasserRueckhaltebecken = 20000
    Niederschlagswasserleitung = 20001
    Abfallentsorgung = 2200
    Muellumladestation = 22000
    Muellbeseitigungsanlage = 22001
    Muellsortieranlage = 22002
    Recyclinghof = 22003
    Ablagerung = 2400
    Erdaushubdeponie = 24000
    Bauschuttdeponie = 24001
    Hausmuelldeponie = 24002
    Sondermuelldeponie = 24003
    StillgelegteDeponie = 24004
    RekultivierteDeponie = 24005
    Telekommunikation = 2600
    Fernmeldeanlage = 26000
    Mobilfunkanlage = 26001
    Fernmeldekabel = 26002
    ErneuerbareEnergien = 2800
    KraftWaermeKopplung = 3000
    Sonstiges = 9999
    Produktenleitung = 99990


class XP_ABEMassnahmenTypen(XPlanungEnumMixin, Enum):
    """ Art der Maßnahme: Anpflanzung, Bindung, Erhaltung"""

    BindungErhaltung = 1000
    Anpflanzung = 2000
    # AnpflanzungBindungErhaltung = 3000  # TODO: does this even make sense?


class XP_AnpflanzungBindungErhaltungsGegenstand(XPlanungEnumMixin, Enum):
    """ Gegenstand der Maßnahme: Anpflanzung, Bindung, Erhaltung"""

    Baeume = 1000
    Kopfbaeume = 1100
    Baumreihe = 1200
    Straeucher = 2000
    BaeumeUndStraeucher = 2050
    Hecke = 2100
    Knick = 2200
    SonstBepflanzung = 3000
    Gewaesser = 4000
    Fassadenbegruenung = 5000
    Dachbegruenung = 6000


class XP_SPEZiele(XPlanungEnumMixin, Enum):
    """ Gegenstand der Maßnahme: Anpflanzung, Bindung, Erhaltung"""

    SchutzPflege = 1000
    Entwicklung = 2000
    Anlage = 3000
    SchutzPflegeEntwicklung = 4000
    Sonstiges = 9999


class XP_SPEMassnahmenTypen(XPlanungEnumMixin, Enum):
    """ Gegenstand der Maßnahme: Anpflanzung, Bindung, Erhaltung"""

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    ArtenreicherGehoelzbestand = 1000
    NaturnaherWald = 1100
    ExtensivesGruenland = 1200
    Feuchtgruenland = 1300
    Obstwiese = 1400
    NaturnaherUferbereich = 1500
    Roehrichtzone = 1600
    Ackerrandstreifen = 1700
    Ackerbrache = 1800
    Gruenlandbrache = 1900
    Sukzessionsflaeche = 2000
    Hochstaudenflur = 2100
    Trockenrasen = 2200
    Heide = 2300
    Moor = 2400, XPlanVersion.SIX
    Sonstiges = 9999


class XP_Bundeslaender(XPlanungEnumMixin, Enum):
    """ Zuständige Bundesländer für den Plan """

    BB = 1000
    BE = 1200
    BW = 1200
    BY = 1300
    HB = 1400
    HE = 1500
    HH = 1600
    MV = 1700
    NI = 1800
    NW = 1900
    RP = 2000
    SH = 2100
    SL = 2200
    SN = 2300
    ST = 2400
    TH = 2500
    Bund = 3000


class XP_ZweckbestimmungGemeinbedarf(XPlanungEnumMixin, Enum):
    """ Erlaubte Nutzungsformen für den Gemeinbedarf """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    OeffentlicheVerwaltung = 1000
    KommunaleEinrichtung = 10000
    BetriebOeffentlZweckbestimmung = 10001
    AnlageBundLand = 10002
    BildungForschung = 1200
    Schule = 12000
    Hochschule = 12001
    BerufsbildendeSchule = 12002
    Forschungseinrichtung = 12003
    Kirche = 1400
    Sakralgebaeude = 14000
    KirchlicheVerwaltung = 14001
    Kirchengemeinde = 14002
    Sozial = 1600
    EinrichtungKinder = 16000
    EinrichtungJugendliche = 16001
    EinrichtungFamilienErwachsene = 16002
    EinrichtungSenioren = 16003
    SonstigeSozialeEinrichtung = 16004, XPlanVersion.FIVE_THREE
    EinrichtungBehinderte = 16005
    Gesundheit = 1800
    Krankenhaus = 18000
    Kultur = 2000
    MusikTheater = 20000
    Bildung = 20001
    Sport = 2200
    Bad = 22000
    SportplatzSporthalle = 22001
    SicherheitOrdnung = 2400
    Feuerwehr = 24000
    Schutzbauwerk = 24001
    Justiz = 24002
    SonstigeSicherheitOrdnung = 24003, XPlanVersion.FIVE_THREE
    Infrastruktur = 2600
    Post = 26000
    SonstigeInfrastruktur = 26001, XPlanVersion.FIVE_THREE
    Sonstiges = 9999


class XP_ZweckbestimmungSpielSportanlage(XPlanungEnumMixin, Enum):
    """ Zweckbestimmungen für Spiel-Sportanlagen """

    Sportanlage = 1000
    Spielanlage = 2000
    SpielSportanlage = 3000
    Sonstiges = 9999


class XP_ZweckbestimmungGruen(XPlanungEnumMixin, Enum):
    """ Zweckbestimmungen für Grünflächen """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Parkanlage = 1000
    ParkanlageHistorisch = 10000
    ParkanlageNaturnah = 10001
    ParkanlageWaldcharakter = 10002
    NaturnaheUferParkanlage = 10003
    Dauerkleingarten = 1200
    ErholungsGaerten = 12000
    Sportplatz = 1400
    Reitsportanlage = 14000
    Hundesportanlage = 14001
    Wassersportanlage = 14002
    Schiessstand = 14003
    Golfplatz = 14004
    Skisport = 14005
    Tennisanlage = 14006
    Spielplatz = 1600
    Bolzplatz = 16000
    Abenteuerspielplatz = 16001
    Zeltplatz = 1800
    Campingplatz = 18000
    Badeplatz = 2000
    FreizeitErholung = 2200
    Kleintierhaltung = 22000
    Festplatz = 22001
    SpezGruenflaeche = 2400
    StrassenbegleitGruen = 24000
    BoeschungsFlaeche = 24001
    FeldWaldWiese = 24002, XPlanVersion.FIVE_THREE
    Uferschutzstreifen = 24003
    Abschirmgruen = 24004
    UmweltbildungsparkSchaugatter = 24005
    RuhenderVerkehr = 24006
    Friedhof = 2600
    Naturerfahrungsraum = 2700, XPlanVersion.SIX
    Sonstiges = 9999
    Gaertnerei = 99990


class XP_Traegerschaft(XPlanungEnumMixin, Enum):
    """ Trägerschaft einer Gemeinbedarfs-Fläche """

    EinrichtungBund = 1000
    EinrichtungLand = 2000
    EinrichtungKreis = 3000
    KommunaleEinrichtung = 4000
    ReligioeserTraeger = 5000
    SonstTraeger = 6000


class XP_Rechtscharakter(XPlanungEnumMixin, Enum):
    """ Rechtliche Charakterisierung eines Planinhalts """

    FestsetzungBPlan = 1000
    NachrichtlicheUebernahme = 2000
    DarstellungFPlan = 3000
    ZielDerRaumordnung = 4000
    GrundsatzDerRaumordnung = 4100
    NachrichtlicheUebernahmeZiel = 4200
    NachrichtlicheUebernahmeGrundsatz = 4300
    NurInformationsgehaltRPlan = 4400
    TextlichesZielRaumordnung = 4500
    ZielUndGrundsatzRaumordnung = 4600
    VorschlagRaumordnung = 4700
    FestsetzungImLP = 5000
    GeplanteFestsetzungImLP = 5100
    DarstellungKennzeichnungImLP = 5200
    LandschaftsplanungsInhaltZurBeruecksichtigung = 5300
    Hinweis = 6000
    Kennzeichnung = 7000
    Vermerk = 8000
    Unbekannt = 9998
    Sonstiges = 9999

    def to_fp_rechtscharakter(self) -> FP_Rechtscharakter:
        if self.value == 3000:
            return FP_Rechtscharakter.Darstellung
        elif self.value == 4200 or self.value == 4300:
            return FP_Rechtscharakter.NachrichtlicheUebernahme
        elif self.value == 6000:
            return FP_Rechtscharakter.Hinweis
        elif self.value == 8000:
            return FP_Rechtscharakter.Vermerk


class XP_ArtHoehenbezug(XPlanungEnumMixin, Enum):
    """ Art des Höhenbezuges """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    absolutNHN = 1000
    absolutNN = 1100
    absolutDHHN = 1200
    relativGelaendeoberkante = 2000
    relativGehwegOberkante = 2500
    relativBezugshoehe = 3000
    relativStrasse = 3500
    relativEFH = 4000, XPlanVersion.SIX


class XP_ArtHoehenbezugspunkt(XPlanungEnumMixin, Enum):
    """ Bestimmung des Bezugspunktes der Höhenangaben """

    TH = 1000
    FH = 2000
    OK = 3000
    LH = 3500
    SH = 4000
    EFH = 4500
    HBA = 5000
    UK = 5500
    GBH = 6000
    WH = 6500
    GOK = 6600


class XP_RechtscharakterPlanaenderung(XPlanungEnumMixin, Enum):
    """ Rechtscharakter der Planänderung """

    Aenderung = 1000
    Ergaenzung = 1100
    Aufhebung = 2000
    Aufhebungsverfahren = 20000
    Ueberplanung = 20001


class XP_Aenderungsarten(XPlanungEnumMixin, Enum):
    """ Spezifikation der Art der Änderungsbeziehung zwischen den verbundenen Plan- bzw. Planbereichs-Objekten """

    Änderung = 1000
    Ersetzung = 10000
    Ergänzung = 10001
    Streichung = 10002
    Aufhebung = 2000
    Überplanung = 3000


class XP_ImmissionsschutzTypen(XPlanungEnumMixin, Enum):
    """ Differenzierung der Immissionsschutz-Fläche."""

    Schutzflaeche = 1000
    BesondereAnlagenVorkehrungen = 2000


class XP_TechnVorkehrungenImmissionsschutz(XPlanungEnumMixin, Enum):
    """ Klassifizierung der auf der Fläche zu treffenden baulichen oder sonstigen technischen Vorkehrungen"""

    Laermschutzvorkehrung = 1000
    FassadenMitSchallschutzmassnahmen = 10000
    Laermschutzwand = 10001
    Laermschutzwall = 10002
    SonstigeVorkehrung = 9999


class XP_ZweckbestimmungKennzeichnung(XPlanungEnumMixin, Enum):
    """ Zweckbestimmung der Kennzeichnungs-Fläche """

    Naturgewalten = 1000
    Abbauflaeche = 2000
    AeussereEinwirkungen = 3000
    SchadstoffBelastBoden = 4000
    LaermBelastung = 5000
    Bergbau = 6000
    Bodenordnung = 7000
    Vorhabensgebiet = 8000
    AndereGesetzlVorschriften = 9999
