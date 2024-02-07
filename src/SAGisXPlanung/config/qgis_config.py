import typing
from dataclasses import dataclass
from enum import Enum
from typing import Union

from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsFeatureRenderer, QgsReadWriteContext
from qgis.PyQt.QtCore import QSettings

from SAGisXPlanung.XPlan.types import GeometryType


class ConfigSaveException(Exception):
    """Exception for cases, where values could not be written to the config entry"""
    pass


class GeometryCorrectionMethod(Enum):
    PreserveTopology = 1
    RigorousRemoval = 2


@dataclass
class GeometryValidationConfig:
    correct_geometries: bool
    correct_method: GeometryCorrectionMethod


class QgsConfig:

    STYLES = 'plugins/xplanung/styles'
    CONNECTION = 'plugins/xplanung/connection'
    CORRECT_GEOMETRIES = 'plugins/xplanung/correct_geometries'
    CORRECT_GEOMETRIES_METHOD = 'plugins/xplanung/correct_geometries_method'

    @staticmethod
    def remove_section(settings_key: str):
        qs = QSettings()
        qs.remove(f'{settings_key}/')

    @staticmethod
    def class_renderer(xplan_class: type, geometry_type: GeometryType) -> Union[None, QgsFeatureRenderer]:
        if geometry_type is None:
            return

        qs = QSettings()
        xml = qs.value(f"{QgsConfig.STYLES}/{xplan_class.__name__}/{geometry_type}/renderer", None)

        if xml is None:
            return

        doc = QDomDocument()
        success, error_message, error_line, error_column = doc.setContent(xml)

        if success:
            return QgsFeatureRenderer.load(doc.firstChild().toElement(), QgsReadWriteContext())

    @staticmethod
    def set_class_renderer(xplan_class: type, geometry_type: GeometryType, renderer: QgsFeatureRenderer):
        qs = QSettings()

        doc = QDomDocument()
        elem = renderer.save(doc, QgsReadWriteContext())
        doc.appendChild(elem)

        if doc.isNull():
            raise ConfigSaveException('Document is empty. Renderer failed to save.')

        qs.setValue(f"{QgsConfig.STYLES}/{xplan_class.__name__}/{geometry_type}/renderer", doc.toString())

    @staticmethod
    def layer_priority(xplan_class: Union[type, str], geometry_type: GeometryType) -> Union[None, int]:
        if geometry_type is None:
            return

        if not isinstance(xplan_class, str):
            xplan_class = xplan_class.__name__

        qs = QSettings()
        prio = qs.value(f"{QgsConfig.STYLES}/{xplan_class}/{geometry_type}/layer_prio", None)

        if prio is None:
            return

        return prio

    @staticmethod
    def set_layer_priority(xplan_class: Union[type, str], geometry_type: GeometryType, layer_priority: int):
        if not isinstance(xplan_class, str):
            xplan_class = xplan_class.__name__

        qs = QSettings()
        qs.setValue(f"{QgsConfig.STYLES}/{xplan_class}/{geometry_type}/layer_prio", layer_priority)

    @staticmethod
    def connection_params() -> typing.Dict:
        qs = QSettings()
        conn_name = qs.value(QgsConfig.CONNECTION)
        return {
            "username": qs.value(f"PostgreSQL/connections/{conn_name}/username"),
            "password": qs.value(f"PostgreSQL/connections/{conn_name}/password"),
            "host": qs.value(f"PostgreSQL/connections/{conn_name}/host"),
            "port": qs.value(f"PostgreSQL/connections/{conn_name}/port"),
            "db": qs.value(f"PostgreSQL/connections/{conn_name}/database")
        }

    @staticmethod
    def geometry_validation_config() -> GeometryValidationConfig:
        qs = QSettings()
        return GeometryValidationConfig(
            correct_geometries=qs.value(QgsConfig.CORRECT_GEOMETRIES),
            correct_method=GeometryCorrectionMethod(int(qs.value(QgsConfig.CORRECT_GEOMETRIES_METHOD)))
        )

    @staticmethod
    def set_geometry_validation_config(config: GeometryValidationConfig):
        qs = QSettings()
        qs.setValue(QgsConfig.CORRECT_GEOMETRIES, config.correct_geometries)
        qs.setValue(QgsConfig.CORRECT_GEOMETRIES_METHOD, config.correct_method.value)


