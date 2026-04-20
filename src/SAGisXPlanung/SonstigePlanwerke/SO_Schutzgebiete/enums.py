from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


class SO_SchutzzonenNaturschutzrecht(XPlanungEnumMixin, Enum):
    """ Klassifizierung der Schutzzone im Naturschutzrecht """

    Schutzzone_1 = 1000
    Schutzzone_2 = 1100
    Schutzzone_3 = 1200
    Kernzone = 2000
    Pflegezone = 2100
    Entwicklungszone = 2200
    Regenerationszone = 2300


class SO_SchutzzonenWasserrecht(XPlanungEnumMixin, Enum):
    """ Klassifizierung der Schutzzone im WSG """

    Zone_1 = 1000
    Zone_2 = 1100
    Zone_3 = 1200
    Zone_3a = 1300
    Zone_3b = 1400
    Zone_4 = 1500


class SO_KlassifizSchutzgebietWasserrecht(XPlanungEnumMixin, Enum):
    """ Klassifizierung des Schutzgebietes im WSG """

    Wasserschutzgebiet = 1000
    QuellGrundwasserSchutzgebiet = 10000
    OberflaechengewaesserSchutzgebiet = 10001
    Heilquellenschutzgebiet = 2000
    Sonstiges = 9999


class SO_KlassifizSchutzgebietSonstRecht(XPlanungEnumMixin, Enum):
    """ Klassifizierung von Schutzgebieten nach sonstigem Recht (v5.3). """

    Laermschutzbereich = 1000
    SchutzzoneLeitungstrasse = 2000
    Sonstiges = 9999

