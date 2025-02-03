from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, String, Date, Boolean, Integer, Float

from SAGisXPlanung.XPlan.types import XPEnum, RefURL, LargeString, XPlanungMeasureType, RegExString
from SAGisXPlanung.config import export_version
from SAGisXPlanung.gui.widgets.inputs.input_widgets import QStringInput, QTextListInput, \
    QCheckableComboBoxInput, QComboBoxNoScroll, QMeasureTypeInput, QTextInput, QFileInput, QDateEditNoScroll, \
    QBooleanInput, QIntegerInput, QFloatInput, QDateListInput
from SAGisXPlanung.gui.widgets.inputs.base_input_element import BaseInputElement

from SAGisXPlanung.gui.widgets.inputs.QFeatureIdentify import QFeatureIdentify


def _get_enum_values(field_type):
    """Helper function to extract filtered enum values based on version."""
    version = export_version()
    if hasattr(field_type.enum_class, 'version'):
        return [e for e in field_type.enums if field_type.enum_class[e].version in [None, version]]
    return field_type.enums


def create_widget(field_type, parent=None) -> BaseInputElement:
    if field_type is None:
        return QStringInput()

    if isinstance(field_type, ARRAY):
        if isinstance(field_type.item_type, String):
            return QTextListInput()
        if isinstance(field_type.item_type, Date):
            return QDateListInput()
        if hasattr(field_type.item_type, 'enums'):
            return QCheckableComboBoxInput(
                _get_enum_values(field_type.item_type),
                enum_type=field_type.item_type.enum_class
            )

    if hasattr(field_type, 'enums'):
        return QComboBoxNoScroll(
            parent,
            items=_get_enum_values(field_type),
            include_default=isinstance(field_type, XPEnum) and field_type.include_default,
            enum_type=field_type.enum_class
        )

    field_mapping = {
        RefURL: lambda _: QFileInput(),
        LargeString: lambda _: QTextInput(),
        Geometry: lambda _: QFeatureIdentify(),
        XPlanungMeasureType: lambda ft: QMeasureTypeInput(field_type),
        RegExString: lambda ft: QStringInput(ft.expression, ft.error_msg),
        Date: lambda _: QDateEditNoScroll(parent, calendarPopup=True),
        Boolean: lambda _: QBooleanInput(),
        Integer: lambda _: QIntegerInput(),
        Float: lambda _: QFloatInput(),
    }

    return field_mapping.get(field_type.__class__, lambda _: QStringInput())(field_type)
