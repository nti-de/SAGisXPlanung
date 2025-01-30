from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class LP_KlassifizierungNaturschutzrecht(XPlanungEnumMixin, Enum):
    """ Kategorien der Schutzgebiete und sonstigen geschützten Bestandteilen von Natur und
    Landschaft nach Kap. 4 Bundesnaturschutzgesetz (BNatSchG) und Landes-Naturschutzgesetzen. """

    Naturschutzgebiet = 1000
    Nationalpark = 1100
    Biosphaerenreservat = 1200
    Landschaftsschutzgebiet = 1300
    Naturpark = 1400
    Naturdenkmal = 1500
    GeschuetzterLandschaftsbestandteil = 1600
    GesetzlichgeschuetztesBiotop = 1700
    Natura2000 = 1800
    GebietGemeinschaftlicherBedeutung = 18000
    EuropaeischesVogelschutzgebiet = 18001
    NationalesNaturmonument = 2000
    Sonstiges = 9999


class LP_RechtsstandSchutzGeb(XPlanungEnumMixin, Enum):
    """ Rechtsstand des Schutzgebiets oder des geschützten Bestandteils von Natur und Landschaft. """

    Geplant = 1000
    Bestehend = 2000
    Fortfallend = 3000
    Eignung = 4000
    Erweiterung = 5000
    Qualifizierung = 6000
    Sonstiges = 9999


class LP_GesGeschBiotopTyp(XPlanungEnumMixin, Enum):
    """ Angabe einer gesetzlich geschützten Biotoptypen-Art gemäß §30 Abs. 2 Ziffern 1-6 BNatSchG. """

    Gewaesserbiotope = 1000
    FeuchtUndNassbiotope = 2000
    Trockenbiotope = 3000
    Waldbiotope = 4000
    FelsenAlpineBiotope = 5000
    Kuestenbiotope = 6000
    Sonstiges = 9999


class LP_SchutzzonenNaturschutzrecht(XPlanungEnumMixin, Enum):
    """ Angabe der Schutzzone für zonierte Schutzgebiete, insbesondere Biosphärenreservate und Nationalparke. """

    Schutzzone1 = 1000
    Schutzzone2 = 1100
    Schutzzone3 = 1200
    Kernzone = 2000
    Pflegezone = 2100
    Entwicklungszone = 2200
    Regenerationszone = 2300
    Sonstiges = 9999
