import datetime

from qgis.core import QgsEditorWidgetSetup, QgsProject, NULL
from qgis.gui import QgsEditorWidgetFactory, QgsEditorWidgetWrapper, QgsCheckableComboBox, QgsEditorConfigWidget
from sqlalchemy import ARRAY, Enum, Date, update

from SAGisXPlanung import Session
from SAGisXPlanung.XPlan.types import XPEnum
from SAGisXPlanung.config import export_version
from SAGisXPlanung.core.helper import find_true_class
from SAGisXPlanung.utils import CLASSES


class CheckableEnumWidgetWrapper(QgsEditorWidgetWrapper):

    def __init__(self, vl, fieldIdx, editor, parent):
        super(CheckableEnumWidgetWrapper, self).__init__(vl, fieldIdx, editor, parent)
        self.combo = editor
        self.attribute = vl.fields().field(fieldIdx).name()

    def value(self):
        if self.combo is None:
            return

        checked_items = self.combo.checkedItems()
        if len(checked_items) > 0:
            return ', '.join(checked_items)
        else:
            return NULL

    def setValue(self, value):
        if self.combo is None:
            return

        if value is None or value == NULL:
            self.combo.setCheckedItems([])
            return

        if isinstance(value, list):
            items = list(map(lambda enum: enum.name, value))
        else:
            items = str(value).split(", ")

        self.combo.setCheckedItems(items)

    def createWidget(self, parent):
        self.combo = QgsCheckableComboBox(parent)

        return self.combo

    def initWidget(self, editor):
        self.combo = editor if isinstance(editor, QgsCheckableComboBox) else editor.findChild(QgsCheckableComboBox)

        cfg = self.config()
        xtype = cfg.get('xtype', None)
        enum_values = cfg.get('enum_values', None)

        self.combo.addItems(enum_values)

    def valid(self):
        return self.combo is not None


class CheckableEnumWidgetWrapperConfig(QgsEditorConfigWidget):
    def __init__(self, layer, idx, parent):
        super().__init__(layer, idx, parent)

        self._xtype = None
        self.enum_values = None

    def config(self):
        return {'xtype': self._xtype, 'enum_values': self.enum_values}

    def setConfig(self, config):
        self._xtype = config.get('xtype')
        self.enum_values = config.get('enum_values')


class CheckableEnumWidgetWrapperFactory(QgsEditorWidgetFactory):
    def __init__(self):
        super().__init__('CheckableEnumWidget')

    def create(self, layer, fieldIdx, editor, parent):
        return CheckableEnumWidgetWrapper(layer, fieldIdx, editor, parent)

    def configWidget(self, layer, idx, parent):
        return CheckableEnumWidgetWrapperConfig(layer, idx, parent)

#############################################################################


def _is_none(field_type):
    return field_type is None


def _is_array_enum(field_type):
    return isinstance(field_type, ARRAY) and hasattr(field_type.item_type, 'enums')


def _is_enum(field_type):
    return isinstance(field_type, (XPEnum, Enum))


def _is_date(field_type):
    return isinstance(field_type, Date)


def _is_array_date(field_type):
    return isinstance(field_type, ARRAY) and isinstance(field_type.item_type, Date)


class EditorWidgetBridge:

    dispatch_map = [
        (_is_none, lambda ft, lyr: FieldType(ft, lyr)),
        (_is_array_enum, lambda ft, lyr: ArrayEnumFieldType(ft, lyr)),
        (_is_enum, lambda ft, lyr: EnumFieldType(ft, lyr)),
        (_is_date, lambda ft, lyr: DateFieldType(ft, lyr)),
        (_is_array_date, lambda ft, lyr: HiddenFieldType(ft, lyr)),
    ]

    @staticmethod
    def create(field_type, layer) -> 'FieldType':
        for condition, handler in EditorWidgetBridge.dispatch_map:
            if condition(field_type):
                return handler(field_type, layer)
        return FieldType(field_type, layer)

    @staticmethod
    def on_attribute_values_changed(layer_id, change_map):
        layer = None
        for map_layer in QgsProject.instance().mapLayers().values():
            if map_layer.id() == layer_id:
                layer = map_layer

        if layer is None:
            raise Exception('no layer with id {0}'.format(layer_id))

        xtype = layer.customProperty('xplanung/type')
        xtype = CLASSES[xtype]

        for feat_id, attr_map in change_map.items():
            id_prop = layer.customProperties().value(f'xplanung/feat-{feat_id}')

            for field_index, new_value in attr_map.items():
                field_name = layer.fields().field(field_index).name()
                true_cls = find_true_class(xtype, field_name)
                field_type = getattr(true_cls, field_name).property.columns[0].type
                widget_config = EditorWidgetBridge.create(field_type, field_name)
                new_value = widget_config.coerce_value(new_value)

                with Session.begin() as session:
                    stmt = update(true_cls.__table__).where(
                        true_cls.__table__.c.id == id_prop
                    ).values({field_name: new_value})
                    session.execute(stmt)


class FieldType:
    def __init__(self, field_type, layer):
        self.layer = layer
        self.field_type = field_type

    def get_editor_widget(self):
        return QgsEditorWidgetSetup('Text', {})

    def coerce_value(self, variant):
        return str(variant)


class HiddenFieldType(FieldType):
    def get_editor_widget(self):
        widget_setup = QgsEditorWidgetSetup('Hidden', {})
        return widget_setup


class DateFieldType(FieldType):
    def get_editor_widget(self):
        config = {'allow_null': True,
                  'calendar_popup': True,
                  'display_format': 'yyyy-MM-dd',
                  'field_format': 'yyyy-MM-dd',
                  'field_iso_format': False}
        widget_setup = QgsEditorWidgetSetup('DateTime', config)
        return widget_setup


class ArrayEnumFieldType(FieldType):
    def get_editor_widget(self):
        if hasattr(self.field_type.item_type.enum_class, 'version'):
            enum_values = [e for e in self.field_type.item_type.enums if
                           self.field_type.item_type.enum_class[e].version in [None, export_version()]]
        else:
            enum_values = self.field_type.item_type.enums

        widget_setup = QgsEditorWidgetSetup('CheckableEnum', {
            'xtype': self.layer.customProperty('xplanung/type'),
            'enum_values': enum_values
        })
        return widget_setup

    def coerce_value(self, variant):
        enum_type = self.field_type.item_type.enum_class
        values = str(variant).split(", ")
        return [enum_type[enum_text] for enum_text in values]


class EnumFieldType(FieldType):
    def get_editor_widget(self):
        should_include_default = isinstance(self.field_type, XPEnum) and self.field_type.include_default
        version = export_version()
        if hasattr(self.field_type.enum_class, 'version'):
            enum_values = [e for e in self.field_type.enums if self.field_type.enum_class[e].version in [None, version]]
        else:
            enum_values = self.field_type.enums
        value_map = {enum_values[i]: enum_values[i] for i in range(len(enum_values))}
        if should_include_default:
            value_map[None] = 'NULL'
        widget_setup = QgsEditorWidgetSetup('ValueMap', {'map': value_map})
        return widget_setup

    def coerce_value(self, variant):
        should_include_default = isinstance(self.field_type, XPEnum) and self.field_type.include_default
        if should_include_default and str(variant) == '':
            return None
        enum_type = self.field_type.enum_class
        return enum_type[variant]