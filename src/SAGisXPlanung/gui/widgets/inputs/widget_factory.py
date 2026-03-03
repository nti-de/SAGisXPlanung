from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, String, Date, Boolean, Integer, Float

from SAGisXPlanung.XPlan.types import XPEnum, RefURL, LargeString, XPlanungMeasureType, RegExString, XPathField
from SAGisXPlanung.config import export_version
from SAGisXPlanung.gui.widgets.inputs.input_widgets import QStringInput, QTextListInput, \
    QCheckableComboBoxInput, QComboBoxNoScroll, QMeasureTypeInput, QTextInput, QFileInput, QDateEditNoScroll, \
    QBooleanInput, QIntegerInput, QFloatInput, QDateListInput, QIntegerListInput
from SAGisXPlanung.gui.widgets.inputs.base_input_element import BaseInputElement, WidgetContext

from SAGisXPlanung.gui.widgets.inputs.QFeatureIdentify import QFeatureIdentify
from SAGisXPlanung.gui.widgets.inputs import XPathListWidget


def _get_enum_values(field_type):
    """Helper function to extract filtered enum values based on version."""
    version = export_version()
    if hasattr(field_type.enum_class, 'version'):
        return [e for e in field_type.enums if field_type.enum_class[e].version in [None, version]]
    return field_type.enums


def create_widget(field_type, parent=None, context: Optional[WidgetContext] = None) -> BaseInputElement:
    if field_type is None:
        return QStringInput(parent=parent, context=context)

    if isinstance(field_type, ARRAY):
        if hasattr(field_type.item_type, 'enums'):
            return QCheckableComboBoxInput(
                _get_enum_values(field_type.item_type),
                enum_type=field_type.item_type.enum_class,
                parent=parent,
                context=context
            )
        if isinstance(field_type.item_type, String):
            return QTextListInput(parent=parent, context=context)
        if isinstance(field_type.item_type, Integer):
            return QIntegerListInput(parent=parent, context=context)
        if isinstance(field_type.item_type, Date):
            return QDateListInput(parent=parent, context=context)
        if isinstance(field_type.item_type, XPathField):
            return XPathListWidget(parent=parent, context=context)

    if hasattr(field_type, 'enums'):
        return QComboBoxNoScroll(
            parent,
            items=_get_enum_values(field_type),
            include_default=isinstance(field_type, XPEnum) and field_type.include_default,
            enum_type=field_type.enum_class,
            context=context
        )

    field_mapping = {
        RefURL: lambda ft, p, ctx: QFileInput(parent=p, context=ctx),
        LargeString: lambda ft, p, ctx: QTextInput(parent=p, context=ctx),
        Geometry: lambda ft, p, ctx: QFeatureIdentify(parent=p, context=ctx),
        XPlanungMeasureType: lambda ft, p, ctx: QMeasureTypeInput(ft, parent=p, context=ctx),
        RegExString: lambda ft, p, ctx: QStringInput(ft.expression, ft.error_msg, parent=p, context=ctx),
        Date: lambda ft, p, ctx: QDateEditNoScroll(parent=p, calendarPopup=True, context=ctx),
        Boolean: lambda ft, p, ctx: QBooleanInput(parent=p, context=ctx),
        Integer: lambda ft, p, ctx: QIntegerInput(parent=p, context=ctx),
        Float: lambda ft, p, ctx: QFloatInput(parent=p, context=ctx),
    }

    for field_class, widget_creator in field_mapping.items():
        if isinstance(field_type, field_class):
            return widget_creator(field_type, parent, context)

    # Fallback for unrecognized types
    return QStringInput(parent=parent, context=context)
