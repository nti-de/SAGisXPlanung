import logging
import os
import uuid

import qasync
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel, QIcon
from qgis.PyQt.QtWidgets import QDialog, QMenu, QAction, QAbstractItemView
from qgis.PyQt.QtCore import Qt, pyqtSlot, QPoint, QSortFilterProxyModel, QModelIndex

from SAGisXPlanung import Session, BASE_DIR
from SAGisXPlanung.config import export_version
from SAGisXPlanung.gui.widgets.QXPlanTabWidget import QXPlanTabWidget
from SAGisXPlanung.gui.style import HighlightRowProxyStyle, HighlightRowDelegate
from SAGisXPlanung.utils import PRE_FILLED_CLASSES, save_to_db_async, confirmObjectDeletion

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../ui/prefilled_object_edit.ui'))
logger = logging.getLogger(__name__)

XID_ROLE = Qt.UserRole + 1


class XPEditPreFilledObjectsDialog(QDialog, FORM_CLASS):
    """ Dialog zum Ändern von XPlanung-Objekten, die als Vorauswahl beim Erstellen eines Plans zur Verfügung stehen."""

    def __init__(self, parent=None):
        super(XPEditPreFilledObjectsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.tab_widget = None

        self.model = QStandardItemModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.sort(0)
        self.listView.setModel(self.proxy)
        self.listView.setEnabled(False)
        self.listView.setMouseTracking(True)
        self.listView.setItemDelegate(HighlightRowDelegate())
        self.list_proxy_style = HighlightRowProxyStyle('Fusion')
        self.list_proxy_style.setParent(self)
        self.listView.setStyle(self.list_proxy_style)

        self.cbClass.currentIndexChanged.connect(self.onClassIndexChanged)
        for cls in PRE_FILLED_CLASSES:
            self.cbClass.addItem(cls.__name__, cls)

        self.listView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.listView.doubleClicked.connect(self.onDoubleClicked)
        self.listView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listView.customContextMenuRequested.connect(self.onContextMenuRequested)

        self.newObject.setStyleSheet('''
            QPushButton {
                background: palette(window); 
                border: 1px solid #BFDBFE;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #93C5FD;
                border: none;
            }''')

        self.newObject.clicked.connect(self.onNewObjectClicked)
        self.buttonBox.rejected.connect(self.resetLayout)

    @pyqtSlot(QPoint)
    def onContextMenuRequested(self, pos: QPoint):
        index = self.listView.indexAt(pos)
        index = self.proxy.mapToSource(index)
        if not index.isValid():
            return

        xplan_id = self.model.data(index, XID_ROLE)
        if not xplan_id:
            return

        menu = QMenu()

        edit_action = QAction(QIcon(':/images/themes/default/mActionMultiEdit.svg'), 'Bearbeiten')
        edit_action.triggered.connect(lambda s, xid=xplan_id: self.onEditObject(xid))
        menu.addAction(edit_action)

        delete_action = QAction(QIcon(os.path.join(BASE_DIR, 'gui/resources/delete.svg')), 'Löschen')
        delete_action.triggered.connect(lambda s, xid=xplan_id: self.onDeleteObject(xid))
        menu.addAction(delete_action)

        menu.exec_(self.listView.viewport().mapToGlobal(pos))

    @pyqtSlot(int)
    def onClassIndexChanged(self, index: int):
        self.model.clear()

        cls = self.cbClass.itemData(index)
        with Session.begin() as session:
            objects = session.query(cls).all()

            self.listView.setEnabled(len(objects) > 0)
            for o in objects:
                item = QStandardItem(str(o))
                item.setData(str(o.id), XID_ROLE)
                self.model.appendRow(item)

    @pyqtSlot(bool)
    def onNewObjectClicked(self, checked: bool):
        layout = self.pages.widget(1).layout()

        cls = self.cbClass.itemData(self.cbClass.currentIndex())
        self.tab_widget = QXPlanTabWidget(cls)

        layout.insertWidget(0, self.tab_widget)

        self.buttonBox.accepted.connect(self.newObjectAccepted)
        self.pages.setCurrentIndex(1)

    @pyqtSlot()
    def resetLayout(self):
        layout = self.pages.widget(1).layout()
        layout.removeWidget(self.tab_widget)
        self.tab_widget.deleteLater()
        self.tab_widget = None
        self.buttonBox.accepted.disconnect()
        self.pages.setCurrentIndex(0)

    @qasync.asyncSlot()
    async def newObjectAccepted(self):
        content = self.tab_widget.populateContent()
        if not content:
            return
        content.id = uuid.uuid4()

        self.resetLayout()

        item = QStandardItem(str(content))
        item.setData(str(content.id), XID_ROLE)
        self.model.appendRow(item)

        await save_to_db_async(content)

    def editAccepted(self, xid):
        content = self.tab_widget.populateContent()
        if not content:
            return
        content.id = uuid.uuid4()

        self.resetLayout()

        # update data in database
        with Session.begin() as session:
            obj = session.query(content.__class__).get(xid)

            # copy over attributes
            for attr in obj.element_order(include_base=False, only_columns=True, export=True,
                                          version=export_version()):
                setattr(obj, attr, getattr(content, attr))

        # update data in view
        indices = self.model.match(self.model.index(0, 0), XID_ROLE, xid)
        if indices:
            self.model.setData(indices[0], str(content), Qt.DisplayRole)

    @pyqtSlot(QModelIndex)
    def onDoubleClicked(self, index: QModelIndex):
        index = self.proxy.mapToSource(index)
        if not index.isValid():
            return

        self.onEditObject(index.data(XID_ROLE))

    def onEditObject(self, xid):
        layout = self.pages.widget(1).layout()

        cls = self.cbClass.itemData(self.cbClass.currentIndex())
        self.tab_widget = QXPlanTabWidget(cls)

        layout.insertWidget(0, self.tab_widget)

        with Session.begin() as session:
            obj = session.query(cls).get(xid)
            for label, input_element in self.tab_widget.widget(0).fields.items():
                attribute_value = getattr(obj, label)
                input_element.setDefault(attribute_value)

        self.buttonBox.accepted.connect(lambda x=xid: self.editAccepted(x))
        self.pages.setCurrentIndex(1)

    def onDeleteObject(self, xid):
        cls = self.cbClass.itemData(self.cbClass.currentIndex())
        with Session.begin() as session:
            obj_from_db = session.query(cls).get(xid)

            if not confirmObjectDeletion(obj_from_db):
                return

            session.delete(obj_from_db)

        # remove entry from view
        indices = self.model.match(self.model.index(0, 0), XID_ROLE, xid)
        if indices:
            self.model.removeRow(indices[0].row())
