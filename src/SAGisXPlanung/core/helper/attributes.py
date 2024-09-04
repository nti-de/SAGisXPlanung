from inspect import getmro

from SAGisXPlanung import Base
from SAGisXPlanung.config import export_version

try:
    from functools import cache
except ImportError:
    from functools import lru_cache as cache


@cache
def base_models(_class: type):
    return [c for c in list(getmro(_class)) if issubclass(c, Base)]


def find_true_class(_class: type, attribute_name: str):
    version = export_version()
    base_classes = base_models(_class)
    true_cls = next(c for c in reversed(base_classes) if hasattr(c, attribute_name) and c.attr_fits_version(attribute_name, version))
    return true_cls


def get_field_type(_class: type, attribute_name: str):
    true_cls = find_true_class(_class, attribute_name)
    field_type = getattr(true_cls, attribute_name).property.columns[0].type
    return field_type
