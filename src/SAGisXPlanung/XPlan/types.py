import logging
import sys

from qgis.core import Qgis, QgsWkbTypes
from sqlalchemy import types

logger = logging.getLogger(__name__)

if Qgis.versionInt() >= 33000:
    GeometryType = Qgis.GeometryType
else:
    GeometryType = QgsWkbTypes.PointGeometry


class ConformityException(Exception):
    def __init__(self, message, code, object_type):
        self.code = code
        self.message = message
        self.object_type = object_type
        super(ConformityException, self).__init__(message)


class InvalidFormException(Exception):
    pass


class XPlanungMeasureType:
    pass


class LargeString(types.TypeDecorator):
    """ Datentyp für lange textliche Beschreibungen """
    impl = types.String
    python_type = str
    cache_ok = True


class RefURL(types.TypeDecorator):
    """ Datentyp für URLs zu externen Referenzen """

    impl = types.String
    python_type = str
    cache_ok = True


class Angle(types.TypeDecorator, XPlanungMeasureType):
    """ Repräsentation des XPlanGML AngleType """

    impl = types.Integer
    python_type = float
    cache_ok = True

    UOM = 'grad'
    MIN_VALUE = 0
    MAX_VALUE = 360


class Area(types.TypeDecorator, XPlanungMeasureType):
    """ Repräsentation des XPlanGML AreaType """

    impl = types.Float
    python_type = float
    cache_ok = True

    UOM = 'm2'
    MIN_VALUE = 0
    MAX_VALUE = sys.float_info.max


class Volume(types.TypeDecorator, XPlanungMeasureType):
    """ Repräsentation des XPlanGML VolumeType """

    impl = types.Float
    python_type = float
    cache_ok = True

    UOM = 'm3'
    MIN_VALUE = 0
    MAX_VALUE = sys.float_info.max


class Length(types.TypeDecorator, XPlanungMeasureType):
    """ Repräsentation des XPlanGML LengthType """

    impl = types.Float
    python_type = float
    cache_ok = True

    UOM = 'm'
    MIN_VALUE = 0
    MAX_VALUE = sys.float_info.max


class Scale(types.TypeDecorator, XPlanungMeasureType):
    """ Repräsentation des XPlanGML ScaleType """

    impl = types.Integer
    python_type = int
    cache_ok = True

    UOM = '%'
    MIN_VALUE = 0
    MAX_VALUE = 100


class RegExString(types.TypeDecorator):
    """ String-Datentyp, mit vorgegebenem RegEx-Muster """

    def __init__(self, expression, *args, error_msg=None, **kwargs):
        self.expression = expression
        self.error_msg = error_msg
        super(RegExString, self).__init__(args, kwargs)

    impl = types.String
    python_type = str
    cache_ok = True


class XPEnum(types.TypeDecorator):
    """ Enum-Datentyp der Information über die Möglichkeit der Anzeige eines Platzhalters enthält"""

    def __init__(self, *args, include_default=None, **kwargs):
        self.include_default = include_default
        super(XPEnum, self).__init__(*args, **kwargs)

    impl = types.Enum
    cache_ok = True
