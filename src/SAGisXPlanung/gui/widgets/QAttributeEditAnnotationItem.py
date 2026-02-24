import logging
from qgis.PyQt.QtCore import Qt, pyqtSlot
from sqlalchemy.orm.attributes import flag_modified

from SAGisXPlanung import Session
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.core.buildingtemplate.template_cells import TableCell
from SAGisXPlanung.core.buildingtemplate.template_item import BuildingTemplateCellDataType
from SAGisXPlanung.core.helper import update_field_value, update_field_values
from SAGisXPlanung.gui.widgets import QBuildingTemplateEdit
from SAGisXPlanung.gui.widgets.QAttributeEdit import QAttributeEdit

logger = logging.getLogger(__name__)


class QAttributeEditAnnotationItem(QAttributeEdit):

    def __init__(self, xplanung_item: XPlanungItem, parent, undo_stack):
        super(QAttributeEditAnnotationItem, self).__init__(xplanung_item, parent, undo_stack)

        self._layer = MapLayerRegistry().layerByXid(self._xplanung_item)
        self.annotation_type = self._xplanung_item.xtype.__name__

        # setup display widget for XP_Nutzungsschablone
        if self.annotation_type == 'XP_Nutzungsschablone':
            with Session.begin() as session:
                template = session.query(xplanung_item.xtype).get(xplanung_item.xid)
                rows = template.zeilenAnz
                if template.data_attributes is None:
                    template.data_attributes = BuildingTemplateCellDataType.as_default(int(rows))
                cells = template.data_attributes

            edit_form = QBuildingTemplateEdit(cells, rows)
            edit_form.cellDataChanged.connect(self.on_template_cell_data_changed)
            edit_form.rowCountChanged.connect(self.on_template_rows_changed)

            self.layout().insertWidget(self.layout().count() - 1, edit_form)

    @pyqtSlot(int)
    def onSliderValueChanged(self, value: int):
        scale = (value - 1) / (99 - 1)

        indices = self.model.match(self.model.index(0, 0), Qt.ItemDataRole.DisplayRole, self.ATTRIBUTE_SIZE, 1, Qt.MatchFlag.MatchFixedString)
        if not indices:
            return
        self.model.setData(indices[0].siblingAtColumn(1), f'{scale:.2f}')
        update_field_value(self._xplanung_item, self.ATTRIBUTE_SIZE, scale) # TODO: very expensive call (cache layer?)

    @pyqtSlot(int)
    def onDialValueChanged(self, value: int):
        self.angleEdit.setText(f'{value}°')

        indices = self.model.match(self.model.index(0, 0), Qt.ItemDataRole.DisplayRole, self.ATTRIBUTE_ANGLE, 1, Qt.MatchFlag.MatchFixedString)
        if not indices:
            return
        self.model.setData(indices[0].siblingAtColumn(1), value)
        update_field_value(self._xplanung_item, self.ATTRIBUTE_ANGLE, value) # TODO: very expensive call (cache layer?)

    @pyqtSlot(BuildingTemplateCellDataType, int)
    def on_template_cell_data_changed(self, cell_type: BuildingTemplateCellDataType, cell_index: int):
        with Session.begin() as session:
            template = session.query(self._xplanung_item.xtype).get(self._xplanung_item.xid)
            template.data_attributes[cell_index] = cell_type
            # workaround for updating array element in database. arrays are not mutable in general
            flag_modified(template, 'data_attributes')

            # update map layer registry immediately if template is currently visible
            if MapLayerRegistry().featureIsShown(self._xplanung_item.xid):
                cell_data = template.dientZurDarstellungVon.template_cell_data(template.data_attributes)
                update_field_value(self._xplanung_item, "cell_content", TableCell.serialize_cells(cell_data))

    @pyqtSlot(int, list)
    def on_template_rows_changed(self, row_count: int, cells: list):
        with Session.begin() as session:
            template = session.query(self._xplanung_item.xtype).get(self._xplanung_item.xid)
            template.data_attributes = cells
            template.zeilenAnz = row_count
            # workaround for updating array element in database. arrays are not mutable in general
            flag_modified(template, 'data_attributes')

            # update map layer registry immediately if template is currently visible
            if MapLayerRegistry().featureIsShown(self._xplanung_item.xid):
                cell_data = template.dientZurDarstellungVon.template_cell_data(template.data_attributes)
                update_field_values([self._xplanung_item],{
                    "zeilenAnz":  row_count,
                    "cell_content": TableCell.serialize_cells(cell_data)
                })
