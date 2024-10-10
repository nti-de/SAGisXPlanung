from qgis.PyQt.QtCore import pyqtSlot, pyqtSignal
from qgis.PyQt.QtWidgets import QAction
from sqlalchemy.orm import load_only, joinedload
from sqlalchemy.orm.attributes import flag_modified

from SAGisXPlanung import Session
from SAGisXPlanung.BuildingTemplateItem import BuildingTemplateCellDataType, BuildingTemplateItem
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_Nutzungsschablone
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.widgets import QBuildingTemplateEdit


class EnableBuldingTemplateAction(QAction):
    """ QAction zur Nutzung im Objektbaum. Kann auf Objekte des Typs BP_BaugebietsTeilFlaeche angewandt werden,
        um deren Nutzungschablone ein- oder auszublenden. Konfiguration wird in der Datenbank gespeichert."""

    def __init__(self, item: XPlanungItem, parent=None):

        self.text = 'Nutzungsschablone anzeigen'
        self.tooltip = 'Soll die Nutzungsschablone dieses Objekts auf der Karte angezeigt werden?'
        self.parent_item = item

        super(EnableBuldingTemplateAction, self).__init__(self.text, parent)

        self.setToolTip(self.tooltip)
        self.setCheckable(True)

        with Session.begin() as session:
            bp_baugebiet = session.query(item.xtype).options(
                load_only('id'),
                # the following should in theory be better as it only emits one sql statement and loads only required columns
                # but in practice it seems that the join query takes longer than two simple selects
                # joinedload(XP_Objekt.wirdDargestelltDurch.of_type(XP_Nutzungsschablone)).load_only('id', 'hidden')
            ).get(item.xid)
            template: XP_Nutzungsschablone = bp_baugebiet.template()
            self.template_id = template.id
            self.setChecked(not template.hidden)

        self.toggled.connect(self.onActionToggled)

    @pyqtSlot(bool)
    def onActionToggled(self, checked: bool):
        with Session.begin() as session:
            template: XP_Nutzungsschablone = session.query(XP_Nutzungsschablone).options(
                load_only('id')).get(self.template_id)
            template.hidden = not checked

        if not checked:
            MapLayerRegistry().remove_canvas_items(self.parent_item.xid)
        elif MapLayerRegistry().featureIsShown(self.parent_item.xid):
            # display template on canvas by reloading layer
            with Session.begin() as session:
                bp_baugebiet = session.query(self.parent_item.xtype).get(self.parent_item.xid)
                # this `toCanvas` call with no parameter only works because we already know that the layer is present
                # on canvas through `featureIsShown` call before
                bp_baugebiet.toCanvas(None)


class EditBuildingTemplateAction(QAction):
    """ QAction zum Generieren eines Widgets, das bearbeiten einer Nuzungsschablone ermöglicht. """

    editFormCreated = pyqtSignal(QBuildingTemplateEdit)

    def __init__(self, item: XPlanungItem, parent=None):

        self.text = 'Nutzungsschablone bearbeiten'
        self.tooltip = 'Die Nutzungsschablone dieser Baugebietsteilfläche bearbeiten'
        self.parent_item = item

        super(EditBuildingTemplateAction, self).__init__(self.text, parent)

        self.setToolTip(self.tooltip)

        with Session.begin() as session:
            bp_baugebiet = session.query(item.xtype).options(
                load_only('id'),
                joinedload('wirdDargestelltDurch').load_only('id')
            ).get(item.xid)
            template: XP_Nutzungsschablone = bp_baugebiet.template()
            self.template_id = template.id

        self.triggered.connect(self.onActionToggled)

    @pyqtSlot(bool)
    def onActionToggled(self, checked: bool):
        with Session.begin() as session:
            template: XP_Nutzungsschablone = session.query(XP_Nutzungsschablone).get(self.template_id)
            rows = template.zeilenAnz
            scale = template.skalierung
            angle = template.drehwinkel
            if template.data_attributes is None:
                template.data_attributes = BuildingTemplateCellDataType.as_default(int(rows))
            cells = template.data_attributes

        # generate widget, send via signal to dialog
        edit_form = QBuildingTemplateEdit(cells, rows, scale=scale, angle=angle)
        edit_form.cellDataChanged.connect(lambda cell, cell_i: self.onTemplateCellDataChanged(cell, cell_i))
        edit_form.rowCountChanged.connect(lambda row_count, cell_types: self.onRowCountChanged(row_count, cell_types))
        edit_form.styleChanged.connect(lambda k, v: self.onStyleChanged(k, v))
        self.editFormCreated.emit(edit_form)

    @pyqtSlot(str, object)
    def onStyleChanged(self, attr: str, value):
        with Session.begin() as session:
            template: XP_Nutzungsschablone = session.query(XP_Nutzungsschablone).get(self.template_id)
            setattr(template, attr, value)

            if not template.hidden and MapLayerRegistry().featureIsShown(self.parent_item.xid):
                canvas_items = MapLayerRegistry().canvas_items_at_feat(self.parent_item.xid)
                template_canvas_item = next(x for x in canvas_items if isinstance(x, BuildingTemplateItem))

                if attr == 'drehwinkel':
                    template_canvas_item.setAngle(value)
                elif attr == 'skalierung':
                    template_canvas_item.setScale(value)

    @pyqtSlot(BuildingTemplateCellDataType, int)
    def onTemplateCellDataChanged(self, cell: BuildingTemplateCellDataType, cell_index: int):
        with Session.begin() as session:
            template: XP_Nutzungsschablone = session.query(XP_Nutzungsschablone).get(self.template_id)
            template.data_attributes[cell_index] = cell
            # workaround for updating array element in database. arrays are not mutable in general
            flag_modified(template, 'data_attributes')

            # update map layer registry immediately if template is currently visible
            if not template.hidden and MapLayerRegistry().featureIsShown(self.parent_item.xid):
                canvas_items = MapLayerRegistry().canvas_items_at_feat(self.parent_item.xid)
                template_canvas_item = next(x for x in canvas_items if isinstance(x, BuildingTemplateItem))

                bp_baugebiet = session.query(self.parent_item.xtype).get(self.parent_item.xid)
                template_canvas_item.setItemData(bp_baugebiet.usageTemplateData(template.data_attributes))
                template_canvas_item.updateCanvas()

    @pyqtSlot(int, list)
    def onRowCountChanged(self, row_count: int, cells: list):
        with Session.begin() as session:
            template: XP_Nutzungsschablone = session.query(XP_Nutzungsschablone).get(self.template_id)
            template.data_attributes = cells
            template.zeilenAnz = row_count
            # workaround for updating array element in database. arrays are not mutable in general
            flag_modified(template, 'data_attributes')

            # update map layer registry immediately if template is currently visible
            if not template.hidden and MapLayerRegistry().featureIsShown(self.parent_item.xid):
                canvas_items = MapLayerRegistry().canvas_items_at_feat(self.parent_item.xid)
                template_canvas_item = next(x for x in canvas_items if isinstance(x, BuildingTemplateItem))

                bp_baugebiet = session.query(self.parent_item.xtype).get(self.parent_item.xid)
                template_canvas_item.setItemData(bp_baugebiet.usageTemplateData(template.data_attributes))
                template_canvas_item.setRowCount(row_count)
