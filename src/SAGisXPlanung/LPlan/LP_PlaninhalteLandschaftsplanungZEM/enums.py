from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


#region LP_AdressatKomplex
class LP_AdressatArt(XPlanungEnumMixin, Enum):
    """ Art des Adressaten, an den sich das Ziel, das Erfordernis oder die Maßnahme richtet """

    Naturschutz = 1000
    Bauleitplanung = 2000
    Raumordnung = 3000
    Flurneuordnung = 4000
    Forstwirtschaft = 5100
    Landwirtschaft = 5200
    Wasserwirtschaft = 5300
    Fischereiwirtschaft = 5400
    Jagd = 5500
    RohstoffgewinnungUndBergbau = 6100
    VerteidigungSicherungDerZivilbevoelkerung = 6200
    Verkehrsplanung = 6300
    Energiegewinnung = 6400
    Abfallwirtschaft = 6500
    Bodenschutz = 7000
    KommunaleKoerperschaften = 8100
    LandKreisverwaltung = 8200
    Land = 8300
    Unbekannt = 9998
    Sonstiges = 9999
#endregion


#region LP_BiologischeVielfaltTypKomplex
class LP_BioVfBestandteil(XPlanungEnumMixin, Enum):
    """ Zeigt an, auf welchen Bestandteil der Biologischen Vielfalt sich das Objekt bezieht. """

    Art = 1000
    BiotopLebensraum = 2000
    LebensstaetteArthabitat = 4000
    Sonstiges = 9999
#endregion


#region LP_BioVfPflanzenArtKomplex
class LP_BioVfPflanzenArtSystematik(XPlanungEnumMixin, Enum):
    """ Gibt systematische Einordnung einer Pflanzenart an. """

    Gefaesspflanze = 1000
    MooseUndFlechten = 2000
    Pilze = 3000
    Sonstiges = 9999


class LP_BioVfPflanzenArtRechtlicherSchutz(XPlanungEnumMixin, Enum):
    """ Rechtliche Grundlage für den Schutz einer Pflanzenart an. """

    AnhangIVFFHRL = 1000
    Anlage1BArtSchV = 2000
    Verantwortungsart = 3000
    Sonstige = 9999
#endregion


#region LP_BioVfTiereArtKomplex
class LP_BioVfTiereArtSystematik(XPlanungEnumMixin, Enum):
    """ Gibt systematische Einordnung einer Tierart an. """

    Grosssaeuger = 1100
    Wolf = 1120
    Luchs = 1110
    Mittelsaeuger = 1200
    Wildkatze = 1210
    Fischotter = 1220
    Biber = 1230
    Marder = 1240
    Kleinsaeuger = 1300
    KleinsaeugerNagetiere = 1310
    Feldhamster = 1311
    Maeuse = 1312
    KleinsaeugerHasenartige = 1320
    KleinsaeugerInsektenfresser = 1330
    Spitzmaeuse = 1331
    KleinsaeugerFledermaeuse = 1340
    Meeressaeuger = 1400
    Voegel = 2100
    Zugvoegel = 2110
    Brutvoegel = 2120
    Reptilien = 2200
    Amphibien = 2300
    Fische = 2400
    Gliederfuesser = 3000
    Libellen = 3110
    Tagfalter = 3120
    Kaefer = 3130
    Heuschrecken = 3140
    Spinnen = 3150
    Krebstiere = 3200
    Mollusken = 4100
    Sonstiges = 9999


class LP_BioVfTierArtRechtlicherSchutz(XPlanungEnumMixin, Enum):
    """ Rechtliche Grundlage für den Schutz einer Tierart an. """

    ArtAnhangIVFFHRL = 1000
    ArtAnhangIArt4Abs2VSRL = 2000
    ArtAnlage1BArtSchV = 3000
    Verantwortungsart = 5000
    Sonstige = 9999


class LP_BioVfTierArtHabitatanforderung(XPlanungEnumMixin, Enum):
    """ Gibt besondere Habitatanforderungen einer Tierart an. """

    GrosserHabitatsAnspruch = 1000
    Gebaeudebewohnend = 2000
    Sonstige = 9999
#endregion


#region LP_BodenKomplex
class LP_BodenAuspraegung(XPlanungEnumMixin, Enum):
    """ Ausprägungen in Bezug auf Boden, an die sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    Ablagerungen = 1110
    Altablagerungsflaeche = 1120
    Altlastenverdachtsflaeche = 1130
    BodenFilterUndPufferfunktion = 2110
    BodenHoheBodenfruchtbarkeit = 2120
    BodenHoherFunktionglobalerKlimaschutz = 2130
    BodenKulturgeschichtlicheBedeutung = 2210
    BodenNaturgeschichtlicheBedeutung = 2220
    BodenGeowissenschaftlicheBedeutung = 2230
    NatuerlicheBoeedenExtremstandort = 2240
    EhemaligerMilitaerischGenutzterStandort = 3100
    Erosionsgefaehrdet = 4100
    ErosionsgefaehrdetWind = 4110
    ErosionsgefaehrdetWasser = 4120
    Geotop = 5110
    SelteneBodenform = 5120
    NaturnaherBoden = 5210
    BoedenHohesRetentionspotenzial = 6100
    EntsiegelungOderWiederherstellungBodenfunktion = 6200
    Sonstiges = 9999
#endregion


#region LP_ErholungKomplex
class LP_ErholungFunktionen(XPlanungEnumMixin, Enum):
    """ Art der Erholungsfunktion oder -Infrastruktur, an die sich das Ziel,
        das Erfordernis oder die Maßnahme richtet. """

    Gruenflaechen = 1000
    ParkanlageGruenanlage = 1100
    Dauerkleingaerten = 1200
    Sportplatz = 1300
    Spielplatz = 1400
    BadeplatzFreibad = 1500
    Liegewiese = 1600
    Erholungsinfrastruktur = 2000
    Schutzhuette = 2100
    Rastplatz = 2110
    Informationstafel = 2120
    FeuerstelleGrillplatz = 2130
    Aussichtsturm = 2200
    Aussichtspunkt = 2210
    Angelteich = 2300
    Modellflugplatz = 2400
    Gleitschirmplatz = 2410
    WildgehegeSchaugatter = 2500
    Parkplatz = 2600
    ZeltplatzCampingplatz = 2700
    JugendzeltplatzEinzelcamp = 2750
    ErholungsInfrastrukturMitBesondererBedeutung = 2900
    WandernAllgemein = 3000
    Wanderweg = 3100
    Lehrpfad = 3200
    Reitweg = 3300
    Radweg = 3400
    Wintersport = 4000
    Skiabfahrt = 4100
    Skilanglaufloipe = 4200
    RodelbahnBobbahn = 4300
    WassersportSchifffahrt = 5000
    Wasserwanderweg = 5100
    Schifffahrtsroute = 5200
    AnlegestelleMitMotorbooten = 5300
    AnlegestelleOhneMotorboote = 5310
    Seilbahn = 6000
    SesselliftSchlepplift = 6100
    Kabinenseilbahn = 6200
    Bildungsstaette = 7000
    Umweltbildungsstaette = 7100
    Museum = 7200
    Sonstiges = 9999
#endregion


#region LP_KlimaKomplex
class LP_KlimaArt(XPlanungEnumMixin, Enum):
    """ Art des Planungsgegenstand für Klima, an die sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    BioklimatischeFunktion = 1000
    Luftleitbahn = 2000
    Frischluftbahn = 3100
    Frischluftentstehungsgebiet = 3200
    Kaltluftbahn = 4100
    Kaltluftentstehungsgebiet = 4200
    Stadtklima = 5000
    THGSenkenKlimaschutzflaechen = 6000
    Sonstiges = 9999
#endregion


#region LP_LandschaftsbildKomplex
class LP_LandschaftsbildArt(XPlanungEnumMixin, Enum):
    """ Art des Planungsgegenstand für das Landschaftsbild, an die sich das Ziel,
        das Erfordernis oder die Maßnahme richtet. """

    KircheKlosterKapelle = 1100
    BurgSchloss = 1200
    Turm = 1300
    HistorischesOrtsbild = 1500
    Ruine = 1400
    KulturgeschichtlichWertvollerOrtsteil = 1600
    Aussichtspunkt = 2100
    Aussichtsturm = 2200
    LandschaftsgerechteEinbindung = 3100
    LandschaftsgerechterSiedlungsrand = 3200
    Strukturvielfalt = 4100
    LandschaftMitHoherEigenart = 4200
    Landschaftsachsen = 5100
    Landschaftsraeume = 5200
    HistorischeWaldinsel = 6100
    Waldraender = 6200
    Kulturlandschaft = 7000
    HistorischeKulturlandschaft = 7100
    Kulturlandschaftselement = 7200
    Hohlweg = 7300
    Gartendenkmal = 8000
    Sonstiges = 9999
#endregion


#region LP_LuftKomplex
class LP_LuftArt(XPlanungEnumMixin, Enum):
    """ Art des Planungsgegenstand für Luft, an die sich das Ziel, das Erfordernis oder die Maßnahme richtet. """

    Geruchsbelastung = 1000
    Laermbelastung = 2000
    LufthygienischeFktStofflBelastung = 3000
    Staubbelastung = 4000
    Sonstiges = 9999
#endregion


#region LP_SchutzgutKomplex
class LP_SchutzgutArt(XPlanungEnumMixin, Enum):
    """ Schutzgüter von Naturschutz und Landschaftspflege, abgeleitet aus § 1 BNatSchG. """

    AlleSchutzgueter = 1000
    ArtenUndLebensgemeinschaften = 2000
    Biotope = 3000
    Boden = 4000
    Wasser = 5000
    Klima = 6000
    Luft = 7000
    Landschaftsbild = 8000
    ErholungInNaturUndLandschaft = 9000
    Unbekannt = 9998
    Sonstiges = 9999
#endregion

#region LP_SPEKomplex
class LP_SchutzPflegeEntwicklung(XPlanungEnumMixin, Enum):
    """ Differenzierung der Ziele, der Erfordernisse oder der Maßnahmen von Naturschutz und Landschaftspflege. """

    Schutz = 1100
    Pflege = 1200
    Entwicklung = 2000
    Anlage = 3000
    Wiederherstellung = 3500 
    Vermeidung = 5100
    Minderung = 5200
    Beseitigung = 5300
    Sonstiges = 9999
#endregion


#region LP_WasserKomplex
class LP_WasserAuspraegung(XPlanungEnumMixin, Enum):
    """ Ausprägungen in Bezug auf Planungsgegenstand Wasser, an die sich das Ziel,
        das Erfordernis oder die Maßnahme richtet. """

    Hochwasserschutz = 1100,
    Ueberschwemmungsgebiet = 1200
    Hochwasservorsorge = 1300
    Retentionsraum = 1310
    Polderflaeche = 1320
    Deichrueckverlegung = 1400
    Trinkwassergewinnung = 1500
    Trinkwasserschutz = 1600
    Grundwasserneubildungsgebiet = 1700
    LaengsdurchgaengigkeitGewaesser = 2100
    MindestwasserfuehrungGewaesser = 2200
    Drainage = 2300
    Entwaesserungsgraben = 2400
    NaturnaheGewaesser = 3100
    NaturnaheUferbereiche = 3200
    OekologischeFunktionFliessgewaesser = 3300
    OekologischeFunktionQuellbereich = 3400
    OekologischeFunktionStillgewaesser = 3500
    Gewaesserstruktur = 3600
    Gewaesserdynamik = 3700
    Gewaesserrandstreifen = 5100
    Gewaesserschutzstreifen = 5200
    Pufferzone = 5300
    Ufergehoelze = 5400
    FischaufstiegsOderAbstiegsanlage = 6100
    Wehr = 6200
    Verrohrung = 6300
    Sohlstufe = 6400
    Gewaesserguete = 7100
    StoffeintraegeInGrundwasser = 7200
    StoffeintraegeInOberflaechengewaesser = 7300
    Versickerungsflaeche = 8100
    Verlandungsbereiche = 8200
    Sonstiges = 9999
#endregion


#region LP_ZielDimNatSchLaPflKomplex
class LP_ZielDimensionTyp(XPlanungEnumMixin, Enum):
    """ Teilziele des Naturschutzes und der Landschaftspflege gemäß § 1 Abs. 1 Ziffern 1. bis 3. BNatSchG. """

    SchutzBiologischeVielfalt = 1000
    SchutzNaturhaushalt = 2000
    SchutzLandschaftsbildErholungsvorsorge = 3000
    Unbekannt = 9998
    Sonstiges = 9999
#endregion


#region LP_ZieleErfordernisseMassnahmen
class LP_ZEMTyp(XPlanungEnumMixin, Enum):
    """ Zeigt an, ob es sich bei dem Objekt um ein Ziel, ein Erfordernis und/oder um
        eine Maßnahme gemäß Kapitel 2 BNatSchG handelt. """

    Ziel = 1000
    Erfordernis = 2000
    Massnahme = 3000
#endregion
