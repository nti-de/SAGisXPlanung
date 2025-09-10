import logging
from typing import List, Any
from contextlib import contextmanager

from qgis.core import QgsFeatureRequest, QgsEditError

from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlanungItem import XPlanungItem

logger = logging.getLogger(__name__)


def update_field_value(xplan_item: XPlanungItem, field_name: str, new_value: Any):
    update_field_values([xplan_item], {field_name: new_value})


def update_field_values(xplan_items: List[XPlanungItem], update_map: dict[str, Any]):

    layer = MapLayerRegistry().layer_by_orm_id(xplan_items[0].xid)
    if not layer:
        logger.warning(f"QAttributeEdit::update_layer_field_value: layer is None for {xplan_items[0].xtype} {xplan_items[0].xid}")
        return

    feature_ids = []
    xids = [item.xid for item in xplan_items]
    cp = layer.customProperties()
    for feat in layer.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry).setNoAttributes()):
        id_prop = cp.value(f'xplanung/feat-{feat.id()}')
        if id_prop in xids:
            feature_ids.append(feat.id())

    # change update_map from [str, Any] entries to [int, Any] where int is the QGIS field id
    fields = layer.fields()
    field_map = {
        fields.lookupField(attr_name): _coerce_to_table_representation(xplan_items[0].xtype, attr_name, value)
        for attr_name, value in update_map.items()
    }

    # field_map = {
    #     attr_id1: attr_value1,
    #     attr_id2: attr_value2,
    # }

    change_success = True
    with safe_edit(layer):
        for fid in feature_ids:
            was_changed = layer.changeAttributeValues(fid, field_map)
            change_success = change_success and was_changed

    if change_success:
        layer.removeSelection()
        layer.triggerRepaint()
    else:
        logger.error(f'attribute changes not persisted to dataprovider: {field_map}, {layer.commitErrors()}')


def _coerce_to_table_representation(xtype: type, attr: str, value: Any) -> Any:
    """ convert given value to string representation used in the QGIS Attribute Table"""
    _self = xtype()
    setattr(_self, attr, value)
    value = getattr(_self, attr)

    if hasattr(_self, 'layer_fields'):
        legacy_fields = _self.layer_fields()
        if attr in legacy_fields:
            value = legacy_fields[attr]

    if type(value) is list:
        value = ', '.join(str(v) for v in value)

    return str(value) if value else ''


@contextmanager
def safe_edit(layer):
    """
    context manager replacing the default edit() from QGIS (drop-in replacement)
    safe_edit will also work when the layer is already in edit mode, which fails with the default QGIS version
    """
    was_editing = layer.isEditable()

    # If already editing, just yield and keep in edit mode on committing changes
    if was_editing:
        yield layer
        if not layer.commitChanges(False):
            raise QgsEditError(layer.commitErrors())
    else:
        if not layer.startEditing():
            raise QgsEditError("Could not start editing the layer")
        try:
            yield layer
            if not layer.commitChanges():
                raise QgsEditError(layer.commitErrors())
        except Exception as e:
            logger.error(e)
            layer.rollBack()
            raise e
