import functools
from dataclasses import dataclass
from typing import List

from sqlalchemy import Column

from SAGisXPlanung import XPlanVersion


class XPCol(Column):

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


def xp_version(versions: List[XPlanVersion]):
    """ Class-Decorator to denote the XPlan-Version a class belongs to."""
    def decorator_versions(cls):
        setattr(cls, 'xp_versions', versions)
        return cls
    return decorator_versions
