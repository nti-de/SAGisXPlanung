import functools
from dataclasses import dataclass
from typing import List

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsSymbol, QgsWkbTypes, QgsUnitTypes, QgsSingleSymbolRenderer
from sqlalchemy import Column

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.XPlan.types import GeometryType


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


def generic_objects_renderer(geom_type: GeometryType):
    if geom_type is None:
        raise Exception('parameter geom_type should not be None')

    symbol = QgsSymbol.defaultSymbol(geom_type)
    if geom_type == QgsWkbTypes.PointGeometry:
        point = symbol.symbolLayer(0)
        point.setColor(QColor('#cbcbcb'))
        point.setSize(4)
        point.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
    elif geom_type == QgsWkbTypes.LineGeometry:
        line = symbol.symbolLayer(0)
        line.setColor(QColor('#cbcbcb'))
        line.setWidth(0.75)
        line.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
    else:
        fill = symbol.symbolLayer(0)
        fill.setFillColor(QColor('#cbcbcb'))
        fill.setBrushStyle(Qt.BDiagPattern)
        fill.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
    return QgsSingleSymbolRenderer(symbol)