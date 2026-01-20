from typing import List

from qgis._core import QgsAction, Qgis


open_xplan_object_action_text = """
from qgis.utils import active_plugins
from qgis.utils import active_plugins
from qgis.utils import plugins
from SAGisXPlanung.utils import CLASSES
from SAGisXPlanung.XPlanungItem import XPlanungItem

if not 'SAGisXPlanung' in active_plugins:
    iface.messageBar().pushInfo("SAGis XPlanung", "SAGis XPlanung Plugin nicht aktiviert!")
else:
    project = QgsProject.instance()
    layer = QgsProject.instance().mapLayer('[% @layer_id %]')

    plan_xid = layer.customProperty(f'xplanung/plan-xid')
    xtype = layer.customProperty(f'xplanung/type')
    xid = layer.customProperties().value(f'xplanung/feat-{[%@id%]}')
    xplan_item = XPlanungItem(xid=xid, xtype=CLASSES[xtype], plan_xid=plan_xid)

    plugins['SAGisXPlanung'].dockWidget.showObjectAttributes(xplan_item)
"""

def default_actions() -> List[QgsAction]:
    action = QgsAction(
        Qgis.AttributeActionType.GenericPython,
        'SAGis XPlanung: Objekt öffnen',
        open_xplan_object_action_text
    )
    scopes = {'Field', 'Feature'}
    action.setActionScopes(scopes)
    return [action]

