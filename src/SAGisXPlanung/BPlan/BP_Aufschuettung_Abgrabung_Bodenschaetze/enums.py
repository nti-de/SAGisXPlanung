from enum import Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.XPlan.mixins import XPlanungEnumMixin


class BP_Laermpegelbereich(XPlanungEnumMixin, Enum):
    """ Festlegung der erforderlichen Luftschalldämmung von Außenbauteilen nach DIN 4109."""

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, version: XPlanVersion = None):
        self._xplan_version = version

    @property
    def version(self) -> XPlanVersion:
        return self._xplan_version

    I = 1000
    II = 1100
    III = 1200
    IV = 1300
    V = 1400
    VI = 1500
    VII = 1600
    SpezifizierungBereich = 1700, XPlanVersion.SIX

