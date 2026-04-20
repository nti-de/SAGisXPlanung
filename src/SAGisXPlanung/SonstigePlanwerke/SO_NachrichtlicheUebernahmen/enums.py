from enum import Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class SO_KlassifizNachSchienenverkehrsrecht(XPlanungEnumMixin, Enum):
    """ Rechtliche Klassifizierung der Festlegung nach Schienenverkehrsrecht"""

    Bahnanlage = 1000
    DB_Bahnanlage = 10000
    Personenbahnhof = 10001
    Fernbahnhof = 10002
    Gueterbahnhof = 10003
    Bahnlinie = 1200
    Personenbahnlinie = 12000
    Regionalbahn = 12001
    Kleinbahn = 12002
    Gueterbahnlinie = 12003
    WerksHafenbahn = 12004
    Seilbahn = 12005
    OEPNV = 1400
    Strassenbahn = 14000
    UBahn = 14001
    SBahn = 14002
    OEPNV_Haltestelle = 14003
    Sonstiges = 9999


class SO_KlassifizNachBodenschutzrecht(XPlanungEnumMixin, Enum):
    """ Rechtliche Klassifizierung der Festlegung nach Bodenschutzrecht"""

    SchaedlicheBodenveraenderung = 1000
    Altlast = 2000
    Altablagerung = 20000
    Altstandort = 20001
    AltstandortAufAltablagerung = 20002


class SO_KlassifizNachDenkmalschutzrecht(XPlanungEnumMixin, Enum):
    """ Rechtliche Klassifizierung der Festlegung nach Denkmalschutzrecht"""

    DenkmalschutzEnsemble = 1000
    DenkmalschutzEinzelanlage = 1100
    Grabungsschutzgebiet = 1200
    PufferzoneWeltkulturerbeEnger = 1300
    PufferzoneWeltkulturerbeWeiter = 1400
    ArcheologischesDenkmal = 1500
    Bodendenkmal = 1600
    Sonstiges = 9999


class SO_KlassifizNachStrassenverkehrsrecht(XPlanungEnumMixin, Enum):
    """ Rechtliche Klassifizierung für Festlegung nach Straßenverkehrsrecht """

    Bundesautobahn = 1000
    Bundesstrasse = 1100
    LandesStaatsstrasse = 1200
    Kreisstrasse = 1300
    SonstOeffentlStrasse = 9999


class SO_ZweckbestimmungStrassenverkehr(XPlanungEnumMixin, Enum):
    """ Allgemeine Zweckbestimmung der Fläche oder Anlage für Straßenverkehr"""

    AutobahnUndAehnlich = 1000
    Hauptverkehrsstrasse = 1200
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
    Anschlussflaeche = 14014
    Verkehrsgruen = 14015
    RuhenderVerkehr = 1600
    Parkplatz = 16000
    FahrradAbstellplatz = 16001
    P_RAnlage = 16002
    B_RAnlage = 16003
    Parkhaus = 16004
    CarSharing = 16005
    BikeSharing = 16006
    Mischverkehrsflaeche = 3400
    Ladestation = 3500
    Sonstiges = 9999


class SO_StrassenEinteilung(XPlanungEnumMixin, Enum):
    """ Straßeneinteilung nach Bundes-Fernstraßengesetz """

    Bundesautobahn = 1000
    Bundesstrasse = 1100
    LandesStaatsstrasse = 1200
    Kreisstrasse = 1300
    Gemeindestrasse = 1400
    SonstOeffentlStrasse = 9999


class SO_KlassifizGewaesser(XPlanungEnumMixin, Enum):
    """ Allgemeine Zweckbestimmung einer Gewaesserfläche """

    Gewaesser = 1000
    Fliessgewaesser = 2000
    Gewaesser1Ordnung = 20000
    Gewaesser2Ordnung = 20001
    Gewaesser3Ordnung = 20002
    StehendesGewaesser = 3000
    Hafen = 4000
    Sportboothafen = 40000
    Wasserstrasse = 5000
    Kanal = 6000
    Sonstiges = 9999

class SO_KlassifizGewaesserv5(XPlanungEnumMixin, Enum):
    """ Allgemeine Zweckbestimmung einer Gewaesserfläche """

    Gewaesser = 1000
    Fliessgewaesser = 2000
    Gewaesser1Ordnung = 10000
    Gewaesser2Ordnung = 10001
    Gewaesser3Ordnung = 10002
    StehendesGewaesser = 10003
    Hafen = 2000
    Sonstiges = 9999


class SO_KlassifizWasserwirtschaft(XPlanungEnumMixin, Enum):
    """ Klassifizierung der Festlegung einer Fläche für Wasserwirtschaft """

    HochwasserRueckhaltebecken = 1000
    Ueberschwemmgebiet = 1100
    Versickerungsflaeche = 1200
    Entwaesserungsgraben = 1300
    Deich = 1400
    RegenRueckhaltebecken = 1500
    Sonstiges = 9999

class SO_KlassifizNachWasserrecht(XPlanungEnumMixin, Enum):
    """ Klassifizierung der Festlegung nach Wasserhaushaltsgesetz (WHG) """

    Ueberschwemmungsgebiet = 2000
    FestgesetztesUeberschwemmungsgebiet = 20000
    NochNichtFestgesetztesUeberschwemmungsgebiet = 20001
    UeberschwemmGefaehrdetesGebiet = 20002
    Risikogebiet = 3000
    RisikogebietAusserhUeberschwemmgebiet = 4000
    Hochwasserentstehungsgebiet = 5000
    Sonstiges = 9999


class SO_KlassifizNachLuftverkehrsrecht(XPlanungEnumMixin, Enum):
    """ Rechtliche Klassifizierung der Festlegung für Luftverkehrsrecht """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Flughafen = 1000
    Landeplatz = 2000
    Segelfluggelaende = 3000
    HubschrauberLandeplatz = 4000
    Ballonstartplatz = 5000
    Haengegleiter = 5200
    Gleitsegler = 5400
    Laermschutzbereich = 6000
    Baubeschraenkungsbereich = 7000, XPlanVersion.FIVE_THREE
    Sonstiges = 9999


class SO_LaermschutzzoneTypen(XPlanungEnumMixin, Enum):
    """ Lärmschutzzone nach LuftVG """

    TagZone1 = 1000
    TagZone2 = 2000
    Nacht = 3000


class SO_KlassifizNachSonstigemRecht(XPlanungEnumMixin, Enum):
    """ Rechtliche Klassifizierung der Festlegung für SonstigesRecht """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Bauschutzbereich = 1000, XPlanVersion.FIVE_THREE
    Berggesetz = 1100
    Richtfunkverbindung = 1200
    Truppenuebungsplatz = 1300
    VermessungsKatasterrecht = 1400
    Rekultivierungsflaeche = 1500
    Renaturierungsflaeche = 1600
    Lärmschutzbereich = 1700, XPlanVersion.SIX
    SchutzzoneLeitungstrasse = 1800, XPlanVersion.SIX
    Sonstiges = 9999


class SO_KlassifizBauverbot(XPlanungEnumMixin, Enum):
    """ Klassifizierung von Bauverboten/Baubeschraenkungen (v5.3). """

    Bauverbotszone = 1000
    Baubeschraenkungszone = 2000
    Waldabstand = 3000
    SonstigeBeschraenkung = 9999


class SO_RechtlicheGrundlageBauverbot(XPlanungEnumMixin, Enum):
    """ Rechtliche Grundlage eines Bauverbots bzw. einer Baubeschraenkung (v5.3). """

    Luftverkehrsrecht = 1000
    Strassenverkehrsrecht = 2000
    SonstigesRecht = 9999


class SO_KlassifizBaubeschraenkung(XPlanungEnumMixin, Enum):
    """ Klassifizierung eines Bauverbots bzw. einer Baubeschraenkung (v6.0). """

    Bauverbotszone = 1000
    Baubeschraenkungszone = 2000
    Waldabstand = 3000
    SonstigeBeschraenkung = 9999


class SO_RechtlicheGrundlageBaubeschraenkung(XPlanungEnumMixin, Enum):
    """ Rechtliche Grundlage eines Bauverbots bzw. einer Baubeschraenkung (v6.0). """

    Luftverkehrsrecht = 1000
    Strassenverkehrsrecht = 2000
    SonstigesRecht = 9999


class SO_GebietsArt(XPlanungEnumMixin, Enum):
    """ Aufzaehlung von Gebietsausweisungen nach BauGB. """

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    Umlegungsgebiet = 1000
    StaedtebaulicheSanierung = 1100
    StaedtebaulicheEntwicklungsmassnahme = 1200
    Stadtumbaugebiet = 1300
    SozialeStadt = 1400
    BusinessImprovementDistrict = 1500
    HousingImprovementDistrict = 1600

    Erhaltungsverordnung = 1999, XPlanVersion.FIVE_THREE
    ErhaltungsverordnungStaedtebaulicheGestalt = 2000, XPlanVersion.FIVE_THREE
    ErhaltungsverordnungWohnbevoelkerung = 2100, XPlanVersion.FIVE_THREE
    ErhaltungsverordnungUmstrukturierung = 2200, XPlanVersion.FIVE_THREE

    Erhaltungsgebiet = 1700, XPlanVersion.SIX
    ErhaltungsgebietStaedtebaulicheGestalt = 17000, XPlanVersion.SIX
    ErhaltungsgebietWohnbevoelkerung = 17001, XPlanVersion.SIX
    ErhaltungsgebietUmstrukturierung = 17002, XPlanVersion.SIX
    StaedtebaulEntwicklungskonzeptInnenentwicklung = 2300, XPlanVersion.SIX
    GebietMitAngespanntemWohnungsmarkt = 2400, XPlanVersion.SIX
    GenehmigungWohnungseigentum = 2500, XPlanVersion.SIX

    Sonstiges = 9999


class SO_RechtsstandGebietTyp(XPlanungEnumMixin, Enum):
    """ Aufzaehlung der moeglichen Rechtsstaende eines Gebietes. """

    VorbereitendeUntersuchung = 1000
    Aufstellung = 2000
    Festlegung = 3000
    Abgeschlossen = 4000
    Verstetigung = 5000
    Sonstiges = 9999
