import logging
import os

from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter, QColor
from qgis.PyQt.QtWidgets import QAction, QWidget, QHBoxLayout, QToolButton, QMenu, QMessageBox, QDialog
from qgis.PyQt.QtCore import pyqtSlot, Qt, QSize, QEvent
from qgis.gui import QgsCheckableComboBox
from qgis.utils import iface

from SAGisXPlanung import Session, BASE_DIR
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.gui.widgets.QXPlanInputElement import QComboBoxNoScroll, QXPlanInputElement, XPlanungInputMeta
from SAGisXPlanung.utils import confirmObjectDeletion

logger = logging.getLogger(__name__)


class QAddRelationDropdown(QWidget, QXPlanInputElement, metaclass=XPlanungInputMeta):

    def __init__(self, parent, relation, *args, **kwargs):
        super(QAddRelationDropdown, self).__init__(*args, **kwargs)
        self.relation = relation
        self.cls = self.relation[1].mapper.class_
        self.requires_relation = bool(self.relation[1].secondary is not None)
        self.parent = parent

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.container = QWidget()
        self.container.setObjectName('container')
        self.container.setLayout(QHBoxLayout())
        self.container.layout().setContentsMargins(0, 0, 0, 0)

        if self.requires_relation:
            self.cb = QgsCheckableComboBox()
            # this is not emitted on QGIS 3.16, see https://github.com/qgis/QGIS/pull/43487 for infos,
            self.cb.checkedItemsChanged.connect(lambda items: self.setInvalid(not bool(items)))
            self.cb.view().customContextMenuRequested.disconnect()
        else:
            self.cb = QComboBoxNoScroll()
        self.cb.setFocusPolicy(Qt.StrongFocus)

        self.refreshComboBox()

        self.plus_icon_path = os.path.abspath(os.path.join(BASE_DIR, 'gui/resources/plus.svg'))
        self.b_plus = QToolButton()
        self.b_plus.setIcon(self.loadSvg(self.plus_icon_path))
        self.b_plus.installEventFilter(self)
        self.b_plus.setCursor(Qt.PointingHandCursor)
        self.b_plus.setToolTip('Neues Objekt hinzufügen')
        self.b_plus.clicked.connect(self.addRelation)
        self.b_plus.setStyleSheet('''
            QToolButton {
                background: palette(window); 
                border: 0px; 
            }
            ''')

        self.cb.view().setContextMenuPolicy(Qt.CustomContextMenu)
        self.cb.view().customContextMenuRequested.connect(self.onContextMenuRequested)

        self.container.layout().addWidget(self.cb)
        self.layout.addWidget(self.container)
        self.layout.addWidget(self.b_plus)
        self.setLayout(self.layout)

    def onContextMenuRequested(self, point):
        index = self.cb.view().indexAt(point)
        if not index.isValid():
            return

        data = self.cb.model().data(index, Qt.UserRole)
        if not data:
            return

        menu = QMenu()

        edit_action = QAction(QIcon(':/images/themes/default/mActionMultiEdit.svg'), 'Bearbeiten')
        edit_action.triggered.connect(lambda s, item_data=data: self.onEditObject(item_data))
        menu.addAction(edit_action)

        delete_action = QAction(QIcon(os.path.join(BASE_DIR, 'gui/resources/delete.svg')), 'Löschen')
        delete_action.triggered.connect(lambda s, item_data=data: self.onDeleteObject(item_data))
        menu.addAction(delete_action)

        menu.exec_(self.cb.view().viewport().mapToGlobal(point))

    def onEditObject(self, item_xid):
        from SAGisXPlanung.gui.XPEditObjectDialog import XPEditObjectDialog

        xplan_item = XPlanungItem(xtype=self.cls, xid=item_xid)

        d = XPEditObjectDialog(xplan_item)
        result = d.exec_()
        if result == QDialog.Accepted:
            self.refreshComboBox()

    def onDeleteObject(self, item_xid):
        with Session.begin() as session:
            obj_from_db = session.query(self.cls).get(item_xid)

            if not confirmObjectDeletion(obj_from_db):
                return

            session.delete(obj_from_db)
        self.refreshComboBox()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.HoverEnter:
            obj.setIcon(self.loadSvg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color='#1F2937'))
        elif event.type() == QEvent.HoverLeave:
            obj.setIcon(self.loadSvg(obj.icon().pixmap(obj.icon().actualSize(QSize(32, 32))), color='#6B7280'))
        return False

    def loadSvg(self, svg, color=None):
        img = QPixmap(svg)
        if color:
            qp = QPainter(img)
            qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
            qp.fillRect(img.rect(), QColor(color))
            qp.end()
        return QIcon(img)

    @pyqtSlot()
    def addRelation(self):
        from SAGisXPlanung.gui.XPCreatePlanDialog import XPCreatePlanDialog
        d = XPCreatePlanDialog(iface=iface, cls_type=self.cls, parent_type=self.parent.cls_type)
        d.contentSaved.connect(self.refreshComboBox)
        d.exec_()

    def refreshComboBox(self):
        self.cb.clear()
        if not isinstance(self.cb, QgsCheckableComboBox):
            self.cb.addItem("")
        with Session.begin() as session:
            for r in session.query(self.cls).all():
                self.cb.addItem(str(r), str(r.id))
        self.cb.model().sort(0)

    def validate_widget(self, required):
        if not self.requires_relation:
            return True

        if not self.cb.checkedItems():
            self.setInvalid(True)
            return False

        self.setInvalid(False)
        return True

    def setInvalid(self, is_invalid):
        if not is_invalid:
            self.container.setStyleSheet('')
            self.container.layout().setContentsMargins(0, 0, 0, 0)
            return
        self.container.setAttribute(Qt.WA_StyledBackground, True)
        self.container.layout().setContentsMargins(5, 5, 5, 5)
        self.container.setStyleSheet('#container {background-color: #ffb0b0; border: 1px solid red; border-radius: 3px;}')

    def value(self):
        values = []

        if not isinstance(self.cb, QgsCheckableComboBox):
            with Session.begin() as session:
                return session.get(self.cls, self.cb.currentData())

        user_data = self.cb.checkedItemsData()
        with Session.begin() as session:
            for i, item in enumerate(self.cb.checkedItems()):
                values.append(session.get(self.cls, user_data[i]))

        return values

    def setDefault(self, default):
        if isinstance(self.cb, QgsCheckableComboBox):
            self.cb.setCheckedItems([str(o) for o in default])
        else:
            index = self.cb.findData(str(default.id))
            self.cb.setCurrentIndex(index)
