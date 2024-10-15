import functools

from sqlalchemy.orm import load_only

from .template_item import BuildingTemplateCellDataType, BuildingTemplateItem, TableCellFactory
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche

from SAGisXPlanung.utils import CLASSES  # dont remove: requires loading all model classed before registering listeners
from SAGisXPlanung.core.callback_registry import CallbackRegistry
from SAGisXPlanung import Session
from SAGisXPlanung.BPlan.BP_Bebauung.data_types import BP_Dachgestaltung
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.data_types import XP_Hoehenangabe
from SAGisXPlanung.XPlanungItem import XPlanungItem


def register_update_listeners():
    for cell_type in BuildingTemplateCellDataType:
        cell_class = cell_type.value
        for affected_col in cell_class.affected_columns:
            cls, attr_name = BP_BaugebietsTeilFlaeche.find_attr_class(affected_col)

            CallbackRegistry().register_callback(
                functools.partial(refresh_template, cell_type),
                table_name=cls.__tablename__,
                column_name=attr_name
            )


def refresh_template(cell_type, target: XPlanungItem, column_name: str, new_value):
    with Session.begin() as session:
        if target.xtype is BP_Dachgestaltung:
            dachgestaltung = session.query(BP_Dachgestaltung).options(load_only('id')).get(target.xid)
            bp_baugebiet = dachgestaltung.baugebiet
        elif target.xtype is XP_Hoehenangabe:
            try:
                hoehenangabe = session.query(XP_Hoehenangabe).options(load_only('id')).get(target.xid)
                bp_baugebiet = session.query(BP_BaugebietsTeilFlaeche).options(
                    load_only('id')
                ).get(hoehenangabe.xp_objekt_id)
            except:
                # might fail when hohenangabe is used in a different relation than with BP_BaugebietsTeilFlaeche
                return
        else:
            bp_baugebiet = session.query(BP_BaugebietsTeilFlaeche).options(load_only('id')).get(target.xid)

        template = bp_baugebiet.template()
        # update map layer registry immediately if template is currently visible
        if not template.hidden and MapLayerRegistry().featureIsShown(str(bp_baugebiet.id)):
            canvas_items = MapLayerRegistry().canvas_items_at_feat(str(bp_baugebiet.id))
            template_canvas_item = next(x for x in canvas_items if isinstance(x, BuildingTemplateItem))

            new_cell = TableCellFactory.create_cell(cell_type, bp_baugebiet)
            template_canvas_item.replace_cells_of_type(new_cell)
            template_canvas_item.updateCanvas()


register_update_listeners()
