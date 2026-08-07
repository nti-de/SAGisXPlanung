import logging
from _operator import or_
from dataclasses import dataclass
from enum import Flag, auto
from functools import reduce
from typing import List

from sqlalchemy import Column

from SAGisXPlanung import XPlanVersion

logger = logging.getLogger(__name__)


class LayerPriorityType(Flag):
    """ Enum to configure the layer priority of XPlanung layers when adding to the layer tree """

    Top = auto()  # Layer prefers to stay at top
    Bottom = auto()  # Layer prefers to stay at the bottom
    CustomLayerOrder = auto()  # Layer is affected by the custom layer order from Settings/QgsConfig
    OutlineStyle = auto()  # Layer has a style that only affects the outline, and should therefore stay above others


def xp_version(versions: List[XPlanVersion]):
    """ Class-Decorator to denote the XPlan-Version a class belongs to."""
    def decorator_versions(cls):
        setattr(cls, 'xp_versions', versions)
        return cls
    return decorator_versions


def with_limits(enumeration):
    """ add NONE and ALL psuedo-members to enumeration """
    none_mbr = enumeration(0)
    all_mbr = enumeration(reduce(or_, enumeration))
    enumeration.NONE = none_mbr
    enumeration.ALL = all_mbr
    enumeration._member_map_['NONE'] = none_mbr
    enumeration._member_map_['ALL'] = all_mbr
    return enumeration


@with_limits
class SchemaSection(Flag):
    BP = auto()
    FP = auto()
    LP = auto()
    RP = auto()
    SO = auto()

    @classmethod
    def from_plan_string(cls, string_list: List[str]):
        result = cls(0)  # Start with an empty flag
        for string in string_list:
            base_name = string.replace("_Plan", "")
            if hasattr(cls, base_name):
                result |= getattr(cls, base_name)
        return result
