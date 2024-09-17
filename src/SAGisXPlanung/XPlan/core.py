from dataclasses import dataclass
from enum import Flag, auto
from typing import List

from sqlalchemy import Column

from SAGisXPlanung import XPlanVersion


class XPCol(Column):
    inherit_cache = True

    def __init__(self, *args, version=XPlanVersion.FIVE_THREE, attribute=None, import_attr=None, **kwargs):
        self.version = version
        self.attribute = attribute
        self.import_attr = import_attr
        super(XPCol, self).__init__(*args, **kwargs)


@dataclass
class XPRelationshipProperty:
    rel_name: str
    xplan_attribute: str
    allowed_version: XPlanVersion


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
