import logging
import os
import uuid
from pathlib import Path

import qasync
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialogButtonBox
from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout, QDialog
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.gui import QgsSvgSelectorWidget
from qgis.utils import iface
from qgis.core import QgsProject, QgsApplication

from geoalchemy2 import WKBElement
from sqlalchemy.orm import load_only

from SAGisXPlanung import BASE_DIR, Session
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_PPO, XP_PTO
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import SVG_CONFIG
from SAGisXPlanung.utils import save_to_db

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/create_annotation.ui'))
logger = logging.getLogger(__name__)


class CreateAnnotateDialog(QDialog, FORM_CLASS):
    """ Dialog zum Annotieren von Planwerken mit Präsentationsobjekten """

    annotationSaved = pyqtSignal(XPlanungItem)

    def __init__(self, parent_item: XPlanungItem, parent=iface.mainWindow()):
        super(CreateAnnotateDialog, self).__init__(parent)
        self.setupUi(self)

        # set svg paths to xplanung symbol library
        self.previous_svg_path = QgsApplication.svgPaths()
        QgsApplication.setSvgPaths([os.path.join(BASE_DIR, 'symbole')])
        QgsApplication.setDefaultSvgPaths([os.path.join(BASE_DIR, 'symbole')])

        self.parent_item = parent_item
        self.selected_name = ''
        self.selected_category = ''
        self.label_name = QLabel(self.selected_name)
        self.label_name.setObjectName('name')
        self.category_name = QLabel(self.selected_category)
        self.category_name.setObjectName('category')

        self._head_layout = QVBoxLayout()
        self._head_layout.addWidget(self.category_name)
        self._head_layout.addWidget(self.label_name)
        self._head_layout.setSpacing(5)
        self.head_layout_shown = False

        self.svg_widget = QgsSvgSelectorWidget()
        self.svg_widget.sourceLineEdit().setVisible(False)
        self.svg_widget.setSvgPath(os.path.join(BASE_DIR, 'symbole'))
        self.svg_widget.svgSelected.connect(self.onSvgSelected)
        self.symbol_tab.layout().addWidget(self.svg_widget)
        self.symbol_tab.layout().setSpacing(20)

        self.save_button = self.buttonBox.button(QDialogButtonBox.Save)
        self.save_button.setEnabled(False)
        self.text_content.textEdited.connect(lambda text: self.save_button.setEnabled(bool(text)))

        self.tabs.tabBar().setCursor(Qt.PointingHandCursor)

        self.setStyleSheet('''
            QToolButton {
                border: 0px;
            }
            #category {
                text-transform: uppercase;
                font-weight: 400;
                color: #374151;
            }
            #name {
                font-size: 1.125rem;
                font-weight: 500;
                color: #1c1917;
            }
            #error_message{
                font-weight: bold; 
                font-size: 7pt; 
                color: #991B1B;
            }
            QTabWidget::pane {
                border: none;
                border-top: 1px solid #e5e7eb;
                position: absolute;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            /* Style the tab using the tab sub-control. Note that
                it reads QTabBar _not_ QTabWidget */
            QTabBar::tab {
                border: none;
                min-width: 20ex;
                padding: 15px;
                color: #4b5563;
                cursor: pointer;
            }
            
            QTabBar::tab:hover {
                background-color: #e5e7eb;
                color: #111827;
            }
            
            QTabBar::tab:selected {
                border-bottom: 2px solid #93C5FD;
                background-color: #eff6ff;
                color: #111827;
            }
            ''')

    def closeEvent(self, e):
        # restore projects svg paths on dialog close
        QgsApplication.setDefaultSvgPaths(self.previous_svg_path)
        QgsApplication.setSvgPaths(self.previous_svg_path)

    @qasync.asyncSlot(str)
    async def onSvgSelected(self, path: str):
        file_name = Path(path).name
        symbol_node = SVG_CONFIG.get(file_name, "")
        if not symbol_node:
            self.error_message.setText('Dieses Symbol gehört nicht zum Symbolkatalog von SAGis XPlanung!')
            self.save_button.setEnabled(False)

            self._head_layout.setParent(None)
            self.category_name.setText('')
            self.label_name.setText('')
            self.head_layout_shown = False
            return

        self.save_button.setEnabled(True)
        self.error_message.clear()

        if not self.head_layout_shown:
            self.symbol_tab.layout().insertLayout(0, self._head_layout)
            self.head_layout_shown = True

        self.category_name.setText(symbol_node['category'])
        self.label_name.setText(symbol_node['name'])

    def accept(self):

        # access parent object and calculate centroid
        with Session.begin() as session:
            parent = session.get(self.parent_item.xtype, self.parent_item.xid,
                                 [load_only('id', 'position', 'gehoertZuBereich_id')])
            centroid = parent.geometry().centroid()
            self.parent_item.bereich_xid = str(parent.gehoertZuBereich_id)

        # create new po object, save to database and draw on canvas
        # case 1: symbol annotation
        if self.tabs.currentIndex() == 0:
            xp_ppo = XP_PPO()
            xp_ppo.id = uuid.uuid4()
            xp_ppo.dientZurDarstellungVon_id = self.parent_item.xid
            xp_ppo.gehoertZuBereich_id = self.parent_item.bereich_xid

            file_name = Path(self.svg_widget.currentSvgPath()).name
            symbol_node = SVG_CONFIG[file_name]
            xp_ppo.symbol_path = os.path.join('symbole', symbol_node['category'], file_name)

            srid = QgsProject().instance().crs().postgisSrid()
            xp_ppo.position = WKBElement(centroid.asWkb(), srid=srid)

            xplan_item = XPlanungItem(
                xid=str(xp_ppo.id),
                xtype=XP_PPO,
                plan_xid=self.parent_item.plan_xid,
                bereich_xid=self.parent_item.bereich_xid,
                parent_xid=self.parent_item.xid,
            )
            po_obj = xp_ppo

        # case 2: text annotation
        else:
            xp_pto = XP_PTO()
            xp_pto.id = uuid.uuid4()
            xp_pto.dientZurDarstellungVon_id = self.parent_item.xid
            xp_pto.gehoertZuBereich_id = self.parent_item.bereich_xid

            srid = QgsProject().instance().crs().postgisSrid()
            xp_pto.position = WKBElement(centroid.asWkb(), srid=srid)

            xp_pto.schriftinhalt = self.text_content.text()

            xplan_item = XPlanungItem(
                xid=str(xp_pto.id),
                xtype=XP_PTO,
                plan_xid=self.parent_item.plan_xid,
                bereich_xid=self.parent_item.bereich_xid,
                parent_xid=self.parent_item.xid,
            )

            po_obj = xp_pto

        save_to_db(po_obj, expire_on_commit=False)
        self.annotationSaved.emit(xplan_item)

        # find parent layer to access plan group
        layer = MapLayerRegistry().layerByXid(self.parent_item)
        root = QgsProject.instance().layerTreeRoot()
        tree_layer = root.findLayer(layer.id())

        # display item on canvas immediately
        po_obj.toCanvas(tree_layer.parent(), xplan_item.plan_xid)

        super(CreateAnnotateDialog, self).accept()
