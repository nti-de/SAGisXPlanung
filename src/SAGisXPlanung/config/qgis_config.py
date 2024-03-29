from typing import Union

from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsFeatureRenderer, QgsReadWriteContext
from qgis.PyQt.QtCore import QSettings

from SAGisXPlanung.XPlan.types import GeometryType


class ConfigSaveException(Exception):
    """Exception for cases, where values could not be written to the config entry"""
    pass


class QgsConfig:

    STYLES = 'plugins/xplanung/styles'

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
