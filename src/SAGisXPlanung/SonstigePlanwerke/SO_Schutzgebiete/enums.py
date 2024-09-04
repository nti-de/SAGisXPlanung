from enum import Enum

from SAGisXPlanung.core.mixins.enum_mixin import XPlanungEnumMixin


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

