import functools
from dataclasses import dataclass
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


def xp_version(versions: List[XPlanVersion]):
    """ Class-Decorator to denote the XPlan-Version a class belongs to."""
    def decorator_versions(cls):
        setattr(cls, 'xp_versions', versions)
        return cls
    return decorator_versions


def fallback_renderer(renderer_function):
    """
    Decorator for `renderer` classmethod in subclassed of :class:`SAGisXPlanung.XPlan.mixins.RendererMixin`.

    Tries to access renderer from QgsConfig, otherwise falls back to using the renderer_function
    """

    @functools.wraps(renderer_function)
    def wrapper(cls, geom_type=None):
        r = super(cls, cls).renderer(geom_type)
        if r is not None:
            return r

        return renderer_function(cls, geom_type)

    return wrapper
