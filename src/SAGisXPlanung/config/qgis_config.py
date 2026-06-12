import json
import logging
import typing
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Union

from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsFeatureRenderer, QgsReadWriteContext
from qgis.PyQt.QtCore import QSettings

from SAGisXPlanung.XPlan.types import GeometryType

logger = logging.getLogger(__name__)


def str2bool(v):
  return str(v).lower() in ("true", "1")


def normalize_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


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


@dataclass
class XPlanung24Account:
    name: str
    api_key: str

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return XPlanung24Account(**data)


class QgsConfig:

    STYLES = 'plugins/xplanung/styles'
    CONNECTION = 'plugins/xplanung/connection'
    CORRECT_GEOMETRIES = 'plugins/xplanung/correct_geometries'
    CORRECT_GEOMETRIES_METHOD = 'plugins/xplanung/correct_geometries_method'
    NEXUS_SETTINGS = 'plugins/xplanung/nexus/settings'
    GEOMETRY_VALIDATION_SETTINGS = 'plugins/xplanung/validation/settings'
    LAST_EXPORT_PATH = 'plugins/xplanung/last_export_dir'
    XPLAN_EXPORT_REFERENCE_PATH = 'plugins/xplanung/xplan_export_reference_path'
    LAST_SELECTED_PLAN = 'plugins/xplanung/last_selected_plan'
    XPLAN24_ACCOUNT = 'plugins/xplanung/xplan24_account'
    AUTO_REPLACE_ATTRIBUTE_FORM = 'plugins/xplanung/replace_attribute_form'
    XPLAN_EXPORT_FILE_NAME_SCHEMA = 'plugins/xplanung/xplan_export_filename_schema'

    @staticmethod
    def set_value_if_changed(settings_key: str, value, default=None, normalize=lambda v: v) -> bool:
        qs = QSettings()
        current = qs.value(settings_key, default)
        if normalize(current) == normalize(value):
            return False

        qs.setValue(settings_key, value)
        return True

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

        QgsConfig.set_value_if_changed(
            f"{QgsConfig.STYLES}/{xplan_class}/{geometry_type}/layer_prio",
            layer_priority,
            normalize=normalize_int
        )

    @staticmethod
    def connection_params() -> typing.Dict:
        qs = QSettings()
        conn_name = qs.value(QgsConfig.CONNECTION)
        return {
            "username": qs.value(f"PostgreSQL/connections/{conn_name}/username"),
            "password": qs.value(f"PostgreSQL/connections/{conn_name}/password"),
            "host": qs.value(f"PostgreSQL/connections/{conn_name}/host"),
            "port": qs.value(f"PostgreSQL/connections/{conn_name}/port"),
            "db": qs.value(f"PostgreSQL/connections/{conn_name}/database"),
            "service": qs.value(f"PostgreSQL/connections/{conn_name}/service")
        }

    @staticmethod
    def geometry_validation_config() -> GeometryValidationConfig:
        qs = QSettings()
        return GeometryValidationConfig(
            correct_geometries=bool(int(qs.value(QgsConfig.CORRECT_GEOMETRIES, 1))),
            correct_method=GeometryCorrectionMethod(int(qs.value(QgsConfig.CORRECT_GEOMETRIES_METHOD, 1)))
        )

    @staticmethod
    def set_geometry_validation_config(config: GeometryValidationConfig):
        QgsConfig.set_value_if_changed(
            QgsConfig.CORRECT_GEOMETRIES,
            int(config.correct_geometries),
            normalize=normalize_int
        )
        QgsConfig.set_value_if_changed(
            QgsConfig.CORRECT_GEOMETRIES_METHOD,
            config.correct_method.value,
            normalize=normalize_int
        )

    @staticmethod
    def nexus_settings() -> str:
        qs = QSettings()
        return qs.value(QgsConfig.NEXUS_SETTINGS, None)

    @staticmethod
    def set_nexus_settings(config_json: str):
        QgsConfig.set_value_if_changed(QgsConfig.NEXUS_SETTINGS, config_json)

    @staticmethod
    def geometry_validation_settings() -> str:
        qs = QSettings()
        return qs.value(QgsConfig.GEOMETRY_VALIDATION_SETTINGS, None)

    @staticmethod
    def set_geometry_validation_settings(config_json: str):
        QgsConfig.set_value_if_changed(QgsConfig.GEOMETRY_VALIDATION_SETTINGS, config_json)

    @staticmethod
    def last_export_directory() -> str:
        qs = QSettings()
        return qs.value(QgsConfig.LAST_EXPORT_PATH, "")

    @staticmethod
    def set_last_export_directory(directory: str):
        QgsConfig.set_value_if_changed(QgsConfig.LAST_EXPORT_PATH, directory, normalize=str)

    @staticmethod
    def last_selected_plan() -> str:
        qs = QSettings()
        return qs.value(QgsConfig.LAST_SELECTED_PLAN, "")

    @staticmethod
    def set_last_selected_plan(plan_xid: str):
        QgsConfig.set_value_if_changed(QgsConfig.LAST_SELECTED_PLAN, plan_xid, normalize=str)

    @staticmethod
    def xplan24_accounts() -> typing.List[XPlanung24Account]:
        qs = QSettings()
        raw = qs.value(QgsConfig.XPLAN24_ACCOUNT, "")
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return [XPlanung24Account.from_dict(item) for item in data]
        except Exception as e:
            logger.error(e)
            return []

    @staticmethod
    def set_xplan24_accounts(account_data: typing.List[XPlanung24Account]):
        data = [account.to_dict() for account in account_data]
        QgsConfig.set_value_if_changed(QgsConfig.XPLAN24_ACCOUNT, json.dumps(data), normalize=str)

    @staticmethod
    def auto_replace_attribute_form() -> bool:
        qs = QSettings()
        return str2bool(qs.value(QgsConfig.AUTO_REPLACE_ATTRIBUTE_FORM, False))

    @staticmethod
    def set_auto_replace_attribute_form(replace: bool):
        QgsConfig.set_value_if_changed(
            QgsConfig.AUTO_REPLACE_ATTRIBUTE_FORM,
            replace,
            normalize=str2bool
        )

    @staticmethod
    def xplan_export_reference_path() -> str:
        qs = QSettings()
        return str(qs.value(QgsConfig.XPLAN_EXPORT_REFERENCE_PATH, ""))

    @staticmethod
    def set_xplan_export_reference_path(path: str):
        QgsConfig.set_value_if_changed(QgsConfig.XPLAN_EXPORT_REFERENCE_PATH, path, normalize=str)

    @staticmethod
    def xplan_export_filename_schema() -> str:
        qs = QSettings()
        return str(qs.value(QgsConfig.XPLAN_EXPORT_FILE_NAME_SCHEMA, ""))

    @staticmethod
    def set_xplan_export_filename_schema(path: str):
        QgsConfig.set_value_if_changed(QgsConfig.XPLAN_EXPORT_FILE_NAME_SCHEMA, path, normalize=str)


