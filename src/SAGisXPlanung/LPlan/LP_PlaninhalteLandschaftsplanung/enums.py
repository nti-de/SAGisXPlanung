from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


#region LP_BiotopverbundBiotopvernetzung
class LP_PlanungsEbene(XPlanungEnumMixin, Enum):
    """ Nutzungsregelung (Klassifikation). """

    Biotopverbund = 1000
    Biotopvernetzung = 2000


class LP_RechtlicheSicherung(XPlanungEnumMixin, Enum):
    """ Rechtliche Sicherung für Flächen des Biotopverbunds und der Biotopvernetzung nach § 21 Abs. 4 BNatSchG. """

    Schutzerklaerung = 1000
    PlanungsrechtlicheFestlegung = 2000
    VertraglicheRegelung = 3000
    Sonstiges = 9999


class LP_BioVerbundsystemArt(XPlanungEnumMixin, Enum):
    """ Zeigt die Art des Verbundsystems an. """

    Allgemein = 1000
    OffenlandHalboffenland = 2000
    Wald = 3000
    Gewaesser = 4000


class LP_BioVStandortFeuchte(XPlanungEnumMixin, Enum):
    """ Zeigt die Ausprägung der Standortverhältnisse des Verbundsystems im Hinblick auf Feuchtigkeit an. """

    Feucht = 1000
    Mittel = 2000
    Trocken = 3000
#endregion


#region LP_Eingriffsregelung
class LP_Umsetzungsstand(XPlanungEnumMixin, Enum):
    """ Zeigt an, ob eine bereit umgesetzte oder angerechnete Kompensationsfläche oder -Maßnahme nachrichtlich
    übernommen oder für neue Kompensationsmaßenahmen vorgeschlagen wird. """

    NachrichtlichUmgesetztOderAngerechnet = 1000
    Vorschlag = 2000
    Unbekannt = 9998


class LP_MassnahmenTyp(XPlanungEnumMixin, Enum):
    """ Differenziert in nationalrechtliche und unionsrechtliche Kompensationsmaßnahmen. """

    Kompensationsmassnahme = 1000
    MassnahmeCEF = 2000
    MassnahmeFCS = 3000
    MassnahmeKohaerenzsicherung = 4000
    Unbekannt = 9998
#endregion


#region LP_EingriffsregelungKomplex
class LP_ERFlaechenArt(XPlanungEnumMixin, Enum):
    """ Differenzierung der Planungsaussagen mit Bezug zur Eingriffsregelung und der Bewältigung von Eingriffsfolgen. """

    PotenzielleFlaecheKompensation = 1000
    Flaechenpool = 2000
    KompensationEinzelflaeche = 3000
    Kompensationsverzeichnis = 4000
    Sonstiges = 9999
#endregion


#region LP_TypBioVerbundKomplex
class LP_FlaechenTypBV(XPlanungEnumMixin, Enum):
    """ Flächentyp des Biotopverbunds nach § 21 Abs. 3 BNatSchG. """

    Kernflaeche = 1000
    Verbindungsflaeche = 2000
    Verbindungselement = 3000


class LP_FlaechenTypBVSpeziell(XPlanungEnumMixin, Enum):
    """ Differenzierung des speziellen Flächentyp des Biotopverbunds nach § 21 Abs. 3 BNatSchG. """

    Verbindungsraeume = 1000
    Verbundachse = 2000
    Wildtierkorridor = 3000
    Entwicklungsflaeche = 4000
    Entwicklungsmassnahme = 5000
    Vernetzungselement = 6000
    Trittsteinbiotop = 7000
    Sonstiges = 9999
#endregion
