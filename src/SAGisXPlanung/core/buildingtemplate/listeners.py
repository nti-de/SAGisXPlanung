import functools

from sqlalchemy.orm import load_only

from .template_cells import TableCell
from .template_item import BuildingTemplateCellDataType, BuildingTemplateItem, TableCellFactory

from SAGisXPlanung.utils import CLASSES  # dont remove: requires loading all model classed before registering listeners
from SAGisXPlanung.core.callback_registry import CallbackRegistry
from SAGisXPlanung import Session
from SAGisXPlanung.BPlan.BP_Bebauung.data_types import BP_Dachgestaltung
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.data_types import XP_Hoehenangabe
from SAGisXPlanung.XPlanungItem import XPlanungItem
from ..helper import update_field_value
from ...XPlan.XP_Praesentationsobjekte.feature_types import XP_Nutzungsschablone


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
        load_opt = load_only(getattr(target.xtype, 'id'))
        if target.xtype is BP_Dachgestaltung:
            dachgestaltung = session.query(BP_Dachgestaltung).options(load_opt).get(target.xid)
            bp_baugebiet = dachgestaltung.baugebiet
        elif target.xtype is XP_Hoehenangabe:
            try:
                hoehenangabe = session.query(XP_Hoehenangabe).options(load_opt).get(target.xid)
                bp_baugebiet = session.query(BP_BaugebietsTeilFlaeche).options(
                    load_only(BP_BaugebietsTeilFlaeche.id)
                ).get(hoehenangabe.xp_objekt_id)
            except:
                # might fail when hohenangabe is used in a different relation than with BP_BaugebietsTeilFlaeche
                return
        else:
            bp_baugebiet = session.query(BP_BaugebietsTeilFlaeche).options(load_opt).get(target.xid)

        if not bp_baugebiet:
            return

        template = next((x for x in bp_baugebiet.wirdDargestelltDurch if isinstance(x, XP_Nutzungsschablone)), None)
        if not template:
            return

        # update map layer registry immediately if template is currently visible
        if MapLayerRegistry().featureIsShown(str(template.id)):
            cell_data = template.dientZurDarstellungVon.template_cell_data(template.data_attributes)
            update_field_value(
                XPlanungItem(xtype=template.__class__, xid=str(template.id)),
      "cell_content",
                TableCell.serialize_cells(cell_data)
            )


register_update_listeners()
