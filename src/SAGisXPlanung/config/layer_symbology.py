import glob
import os
from dataclasses import dataclass
from typing import List

from qgis.core import QgsWkbTypes, QgsVectorLayer

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.GML.geometry import geom_type_as_layer_url
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.config import QgsConfig
from SAGisXPlanung.core.mixins.mixins import FlaechenschlussObjekt, GeometryObject, MixedGeometry
from SAGisXPlanung.utils import OBJECT_BASE_TYPES, CLASSES


@dataclass
class StyleItem:
    base_xtype: type
    xtype: type
    geometry_type: GeometryType
    layer_priority: LayerPriorityType = LayerPriorityType.CustomLayerOrder
    is_mixed_geometry: bool = False


def load_symbol_defaults():
    """ loads the default layer symbology and priority into the QgsConfig data store (if not already set)"""
    # load all file-based styles into the QgsConfig if they are not already present
    folder_path = os.path.join(BASE_DIR, 'symbole/')
    qml_files = glob.glob(os.path.join(folder_path, "**/*.qml"))

    for qml_file in qml_files:
        base_name = os.path.basename(qml_file)
        class_name, geometry_type = os.path.splitext(base_name)[0].rsplit('-', 1)

        if QgsConfig.class_renderer(CLASSES[class_name], geometry_type):
            continue

        qgs_geom_type = GeometryType(int(geometry_type))
        layer = QgsVectorLayer(geom_type_as_layer_url(qgs_geom_type), "result", "memory")
        layer.loadNamedStyle(qml_file)

        QgsConfig.set_class_renderer(CLASSES[class_name], geometry_type, layer.renderer())

    # set display priority -> order of layers in layertree
    display_priority = 1
    style_items = generate_default_style_items()
    for i, style_item in enumerate(style_items):
        stored_priority = QgsConfig.layer_priority(style_item.xtype, style_item.geometry_type)
        if stored_priority is None:
            QgsConfig.set_layer_priority(style_item.xtype, style_item.geometry_type, display_priority)
        display_priority += 1


def generate_default_style_items():
    items = []
    for base_type in OBJECT_BASE_TYPES:
        for xplan_class in base_type.__subclasses__():
            if not issubclass(xplan_class, GeometryObject):
                continue
            if not issubclass(xplan_class, MixedGeometry):
                style_item = StyleItem(
                    base_type,
                    xplan_class,
                    xplan_class.__geometry_type__,
                    layer_priority=xplan_class.__LAYER_PRIORITY__
                )
                items.append(style_item)
            else:
                for geom_type in [QgsWkbTypes.PolygonGeometry, QgsWkbTypes.LineGeometry, QgsWkbTypes.PointGeometry]:
                    items.append(StyleItem(
                        base_type,
                        xplan_class,
                        geom_type,
                        layer_priority=xplan_class.__LAYER_PRIORITY__,
                        is_mixed_geometry=True
                    ))

    return _sort_style_items(items)


def _sort_style_items(style_items: List[StyleItem]) -> List[StyleItem]:
    geometry_order = {
        GeometryType.PointGeometry: 0,
        GeometryType.LineGeometry: 1,
        GeometryType.PolygonGeometry: 2
    }

    def sort_key(item: StyleItem):
        has_mixin = issubclass(item.xtype, FlaechenschlussObjekt)
        is_outlined_style = LayerPriorityType.OutlineStyle in item.layer_priority
        return (
            # item.base_xtype.__name__,  # sort by category TODO: does it make more sense to group by category first?
            geometry_order[item.geometry_type],  # First, sort by geometry type
            not is_outlined_style,  # Second, objects with outlined style should appear above
            has_mixin  # Third, sort by presence of the FlaechenschlussObjekt mixin (False before True)
        )

    return sorted(style_items, key=sort_key)
