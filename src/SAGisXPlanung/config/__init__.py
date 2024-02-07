import html
import logging
import yaml
from typing import Union
from pathlib import Path

from SAGisXPlanung import XPlanVersion, Base

from qgis.PyQt.QtCore import QSettings

from .qgis_config import QgsConfig, GeometryValidationConfig, GeometryCorrectionMethod

try:
    from functools import cache
except ImportError:
    from functools import lru_cache as cache


logger = logging.getLogger(__name__)


SVG_CONFIG = yaml.safe_load(Path(__file__).with_name('svg_config.yaml').read_text())


def table_name_to_class(table_name: str) -> type:
    for mapper in Base.registry.mappers:
        if mapper.class_.__tablename__ == table_name:
            return mapper.class_


@cache
def docstring_config(version: XPlanVersion):
    return yaml.safe_load(Path(__file__).with_name(f'doc_string_config_{version.short_id()}.yaml').read_text())


def xplan_tooltip(xtype: type, attribute_name: str, plain=False) -> Union[None, str]:
    """
    Returns XPlanung description as rich-text html div, which can be used for tooltips for given class and attribute.
    Returns None if no description could be found.
    """
    try:
        _table = getattr(xtype, attribute_name).property.columns[0].table
        _class = table_name_to_class(_table.name)
        if not _class:
            return ""
        config = docstring_config(export_version())
        tooltip = config[_class.__name__]['attributes'][attribute_name]['doc']

        if plain:
            return tooltip

        # hackish solution for https://bugreports.qt.io/browse/QTBUG-41051
        # Convert plaintext tooltip into a rich text tooltip which allows word-wrap and doesnt grow to infinite width:
        # * Escape all possible HTML syntax
        # * Embed tooltip in weird "<qt>...</qt>" tag.
        return '<qt>{}</qt>'.format(html.escape(tooltip))
    except (KeyError, AttributeError) as e:
        logger.warning(f'Could not find tooltip in config: {e} for super class {xtype.__name__}')


def export_version():
    qs = QSettings()
    version = qs.value(f"plugins/xplanung/export_version", None)
    if version is None:
        return XPlanVersion.FIVE_THREE
    return XPlanVersion(version)
