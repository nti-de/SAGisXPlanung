import logging
from typing import List, Any

from qgis.core import QgsFeatureRequest

from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlanungItem import XPlanungItem

logger = logging.getLogger(__name__)


def update_field_value(xplan_item: XPlanungItem, field_name: str, new_value: Any):
    update_field_values([xplan_item], {field_name: new_value})


def update_field_values(xplan_items: List[XPlanungItem], update_map: dict[str, Any]):
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

        return str(value)

    layer = MapLayerRegistry().layerByXid(xplan_items[0])
    if not layer:
        logger.warning(f"QAttributeEdit::update_layer_field_value: layer is None")
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

    # { feat_id1: {
    #     attr_id1: attr_value1,
    #     attr_id2: attr_value2},
    # }, feat_id2: {
    #     attr_id1: attr_value1,
    #     attr_id2: attr_value2},
    # }}

    qgis_changed_attr_map = {fid: field_map for fid in feature_ids}

    success = layer.dataProvider().changeAttributeValues(qgis_changed_attr_map)
    if success:
        layer.removeSelection()
        layer.triggerRepaint()
    else:
        logger.warning('attribute changes not persisted to dataprovider')

