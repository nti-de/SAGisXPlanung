from qgis.utils import plugins

from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import QgsConfig
from SAGisXPlanung.utils import CLASSES


def on_sagis_xplan_attribute_form_open(dialog, layer, feature):
    """Python form init function called when the feature form opens."""
    if not QgsConfig.auto_replace_attribute_form():
        return

    try:
        plugin = plugins["SAGisXPlanung"]
    except AttributeError:
        return

    window = dialog.window()
    window.setWindowOpacity(0)
    window.setParent(None)
    window.hide()
    window.deleteLater()

    plan_xid = layer.customProperty(f'xplanung/plan-xid')
    xtype = layer.customProperty(f'xplanung/type')
    xid = layer.customProperties().value(f'xplanung/feat-{feature.id()}')
    xplan_item = XPlanungItem(xid=xid, xtype=CLASSES[xtype], plan_xid=plan_xid)

    plugin.dockWidget.showObjectAttributes(xplan_item)