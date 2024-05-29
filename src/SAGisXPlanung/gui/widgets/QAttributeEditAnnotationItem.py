import logging
import os
from typing import Union

import qasync
from qgis.PyQt import sip
from qgis.PyQt.QtCore import Qt, pyqtSlot
from qgis._core import QgsAnnotationLayer, QgsAnnotationItem
from qgis.core import QgsTextFormat
from sqlalchemy import select
from sqlalchemy.orm import load_only

from SAGisXPlanung import Session, BASE_DIR
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.widgets import SVGSymbolDisplayWidget
from SAGisXPlanung.gui.widgets.QAttributeEdit import QAttributeEdit

logger = logging.getLogger(__name__)


class QAttributeEditAnnotationItem(QAttributeEdit):

    def __init__(self, xplanung_item: XPlanungItem, data, parent=None):
        super(QAttributeEditAnnotationItem, self).__init__(xplanung_item, data, parent)

        self.annotation_type = xplanung_item.xtype.__name__
        self._annotation_item = None

        self.styleGroup.setVisible(True)

        self._annotation_layer = MapLayerRegistry().layerByXid(self._xplanung_item)
        self.annotation_item()

        # set initial form values
        self.set_form_values()
        self.initialize_listeners()

        # setup svg symbol display widget
        if self.annotation_type == 'XP_PPO':
            # don't query database if not required
            if self._annotation_layer and self._annotation_item:
                svg_path = self._annotation_item.format().background().svgFile()
            else:
                with Session.begin() as session:
                    annotation_item = session.get(xplanung_item.xtype, xplanung_item.xid,
                                                  [load_only('id', 'symbol_path')])
                    svg_path = os.path.join(BASE_DIR, annotation_item.symbol_path or '')

            symbol_widget = SVGSymbolDisplayWidget(svg_path)
            symbol_widget.svg_selection_saved.connect(self.onSvgSelected)
            self.layout().addWidget(symbol_widget)

    def annotation_item(self) -> Union[None, QgsAnnotationItem]:
        if not self._annotation_layer or sip.isdeleted(self._annotation_layer):
            self._annotation_layer = MapLayerRegistry().layerByXid(self._xplanung_item)
            if not self._annotation_layer:
                return None

        for item_id, item in self._annotation_layer.items().items():
            id_prop = self._annotation_layer.customProperties().value(f'xplanung/feat-{item_id}')
            if id_prop == self._xplanung_item.xid:
                self._annotation_item = item
                return item

    @qasync.asyncSlot(str)
    async def onSvgSelected(self, path: str):
        self.onAttributeChanged(None, 'symbol_path', path)
        if self.annotation_item():
            text_format: QgsTextFormat = self._annotation_item.format()
            text_format.background().setSvgFile(os.path.join(BASE_DIR, path))
            self._annotation_item.setFormat(text_format)
            self._annotation_layer.triggerRepaint()

    @pyqtSlot(int)
    def onSliderValueChanged(self, value: int):
        scale = (value - 1) / (99 - 1)
        if self.annotation_item():
            text_format: QgsTextFormat = self._annotation_item.format()
            if self.annotation_type == 'XP_PTO':
                text_format.setSize(self.TEXT_DEFAULT_SIZE * scale * 2.0)
            else:
                text_format.setSize(self.ICON_DEFAULT_SIZE * scale * 2.0)
            self._annotation_item.setFormat(text_format)
            self._annotation_layer.triggerRepaint()

        indices = self.model.match(self.model.index(0, 0), Qt.DisplayRole, self.ATTRIBUTE_SIZE, 1, Qt.MatchFixedString)
        if not indices:
            return
        self.model.setData(indices[0].siblingAtColumn(1), f'{scale:.2f}')

    @pyqtSlot(int)
    def onDialValueChanged(self, value: int):
        self.angleEdit.setText(f'{value}°')
        if self.annotation_item():
            self._annotation_item.setAngle(value)
            self._annotation_layer.triggerRepaint()

        indices = self.model.match(self.model.index(0, 0), Qt.DisplayRole, self.ATTRIBUTE_ANGLE, 1, Qt.MatchFixedString)
        if not indices:
            return
        self.model.setData(indices[0].siblingAtColumn(1), value)
