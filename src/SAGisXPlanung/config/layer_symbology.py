import glob
import logging
import os
import re
from dataclasses import dataclass
from typing import List

from qgis.core import QgsWkbTypes, QgsVectorLayer, QgsApplication

from SAGisXPlanung import BASE_DIR, PERSISTENT_CONFIG_DIR
from SAGisXPlanung.GML.geometry import geom_type_as_layer_url
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.config import QgsConfig
from SAGisXPlanung.core.mixins.mixins import FlaechenschlussObjekt, GeometryObject, MixedGeometry
from SAGisXPlanung.utils import OBJECT_BASE_TYPES, CLASSES

logger = logging.getLogger(__name__)

GEOMETRY_ORDER = {
    GeometryType.PointGeometry: 0,
    GeometryType.LineGeometry: 1,
    GeometryType.PolygonGeometry: 2
}


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
    default_folder_path = os.path.join(BASE_DIR, 'styles/default/')
    override_folder_path = os.path.join(PERSISTENT_CONFIG_DIR, 'styles/')

    qml_files = {os.path.basename(f): f for f in glob.glob(os.path.join(default_folder_path, "*.qml"))}
    qml_files.update({os.path.basename(f): f for f in glob.glob(os.path.join(override_folder_path, "*.qml"))})

    for base_name, qml_file in qml_files.items():
        match = re.match(r'^(.*?)-(\d+)', base_name)
        if not match:
            return

        class_name, geometry_type = match.group(1), int(match.group(2))

        qgs_geom_type = GeometryType(int(geometry_type))
        renderer = _load_renderer_from_file(qml_file, qgs_geom_type)
        QgsConfig.set_class_renderer(CLASSES[class_name], geometry_type, renderer)

    # set display priority -> order of layers in layertree
    display_priority = 1
    style_items = generate_default_style_items()
    for i, style_item in enumerate(style_items):
        stored_priority = QgsConfig.layer_priority(style_item.xtype, style_item.geometry_type)
        if stored_priority is None:
            QgsConfig.set_layer_priority(style_item.xtype, style_item.geometry_type, display_priority)
        display_priority += 1


def find_file_based_renderer(xplan_class, geometry_type):
    """ search style file for given xplan type and geometry dimension"""
    default_folder_path = os.path.join(BASE_DIR, 'styles/default/')
    override_folder_path = os.path.join(PERSISTENT_CONFIG_DIR, 'styles/')

    geometry_type_num = GEOMETRY_ORDER[geometry_type]
    # File naming pattern: {xplan_class.__name__}-{geometry_type_num}_{any-text}.qml
    pattern = rf"{xplan_class.__name__}-{geometry_type_num}_.*\.qml"

    # Check if the file exists in the override folder first, then the default folder
    for folder_path in [override_folder_path, default_folder_path]:
        if not os.path.exists(folder_path):
            continue
        for file_name in os.listdir(folder_path):
            if re.match(pattern, file_name):
                file_path = os.path.join(folder_path, file_name)
                return _load_renderer_from_file(file_path, geometry_type)


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
                for geom_type in [QgsWkbTypes.GeometryType.PolygonGeometry, QgsWkbTypes.GeometryType.LineGeometry, QgsWkbTypes.GeometryType.PointGeometry]:
                    items.append(StyleItem(
                        base_type,
                        xplan_class,
                        geom_type,
                        layer_priority=xplan_class.__LAYER_PRIORITY__,
                        is_mixed_geometry=True
                    ))

    return _sort_style_items(items)


def _sort_style_items(style_items: List[StyleItem]) -> List[StyleItem]:

    def sort_key(item: StyleItem):
        has_mixin = issubclass(item.xtype, FlaechenschlussObjekt)
        is_outlined_style = LayerPriorityType.OutlineStyle in item.layer_priority
        return (
            # item.base_xtype.__name__,  # sort by category TODO: does it make more sense to group by category first?
            GEOMETRY_ORDER[item.geometry_type],  # First, sort by geometry type
            not is_outlined_style,  # Second, objects with outlined style should appear above
            has_mixin  # Third, sort by presence of the FlaechenschlussObjekt mixin (False before True)
        )

    return sorted(style_items, key=sort_key)


def _load_renderer_from_file(qml_file: str, geometry_type: GeometryType):
    layer = QgsVectorLayer(geom_type_as_layer_url(geometry_type), "result", "memory")
    layer.loadNamedStyle(qml_file)

    return layer.renderer().clone()
