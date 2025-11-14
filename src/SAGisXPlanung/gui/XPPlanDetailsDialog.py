import asyncio
import functools
import inspect
import logging
import os
import uuid
from typing import List, Tuple, Union

import qasync
import yaml

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAbstractItemView, QMenu, QAction
from qgis.PyQt.QtCore import Qt, pyqtSignal, pyqtSlot, QEvent, QModelIndex, QSettings
from qgis.gui import QgsDockWidget
from qgis.core import (Qgis)
from qgis.utils import iface
from sqlalchemy import select, exists
from sqlalchemy.orm import lazyload, load_only, selectinload, class_mapper, RelationshipProperty
from sqlalchemy.orm.exc import UnmappedClassError

from SAGisXPlanung import Session, BASE_DIR, SessionAsync, compile_ui_file, Base
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.BPlan.BP_Bebauung.feature_types import BP_BaugebietsTeilFlaeche
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Plan
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Plan
from SAGisXPlanung.RPlan.RP_Basisobjekte.feature_types import RP_Plan
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_Nutzungsschablone, \
    XP_AbstraktesPraesentationsobjekt
from SAGisXPlanung.XPlan.data_types import XP_Gemeinde
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt
from SAGisXPlanung.core.helper import base_models, find_true_class
from SAGisXPlanung.core.mixins.mixins import GeometryObject
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import export_version
from SAGisXPlanung.core.canvas_display import plan_to_map
from SAGisXPlanung.ext.spinner import WaitingSpinner, loading_animation
from SAGisXPlanung.gui.commands import ObjectsDeletedCommand, XPUndoStack, AttributeChangedCommand
from SAGisXPlanung.gui.style import SVGButtonEventFilter, load_svg
from SAGisXPlanung.gui.widgets.QAttributeEdit import QAttributeEdit, TreeNode
from SAGisXPlanung.core.geometry_validation import VALIDATION_FUNCTIONS
from SAGisXPlanung.gui.widgets.QExplorerView import ClassNode, XID_ROLE
from SAGisXPlanung.gui.widgets.QXPlanTabWidget import QXPlanTabWidget
from SAGisXPlanung.gui.widgets.geometry_validation_view import ValidationState
from SAGisXPlanung.utils import OBJECT_BASE_TYPES, full_version_required_warning

uifile = os.path.join(os.path.dirname(__file__), '../ui/XPlanung_plan_details.ui')
FORM_CLASS = compile_ui_file(uifile)

logger = logging.getLogger(__name__)


class XPPlanDetailsDialog(QgsDockWidget, FORM_CLASS):
    """ Dialog zum konfigurieren von vollständig vektoriell zu erfassenden Planinhalten """

    planDeleted = pyqtSignal()
    nameChanged = pyqtSignal(str, str)  # xid, new plan name

    _init_lock = asyncio.Lock()

    def __init__(self, parent=None):
        super(XPPlanDetailsDialog, self).__init__(parent)

        self.plan_xid = None
        self.plan_type = None
        self.setupUi(self)
        self.setAllowedAreas(self.allowedAreas() | Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setObjectName('xplanung-details')

        self.deleteIcon = QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources/delete.svg')))
        self.bMap.setIcon(QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources/map.svg'))))

        self.bMap.clicked.connect(lambda _: plan_to_map(self.plan_xid))
        self.bDelete.setIcon(self.deleteIcon)
        self.bDelete.clicked.connect(self.deletePlanContent)
        self.bEdit.clicked.connect(self.show_attribute_page)
        # self.bEdit.setDisabled(True)
        self.bPrev.clicked.connect(self.prevPage)
        self.bSave = self.bActions.button(QtWidgets.QDialogButtonBox.Save)
        self.bSave.setVisible(False)

        self.bEditMain.setIcon(QIcon(os.path.join(BASE_DIR, 'gui/resources/edit.svg')))
        self.bEditMain.clicked.connect(self.onEditMainClicked)

        self.bSortHierarchy.setIcon(QIcon(os.path.join(BASE_DIR, 'gui/resources/sort_hierarchy.svg')))
        self.bSortCategory.setIcon(QIcon(os.path.join(BASE_DIR, 'gui/resources/category.svg')))
        self.bSortName.setIcon(QIcon(os.path.join(BASE_DIR, 'gui/resources/sort_alpha.svg')))
        self.sortButtons.setId(self.bSortCategory, 2)
        self.sortButtons.setId(self.bSortName, 1)
        self.sortButtons.setId(self.bSortHierarchy, 0)
        self.sortButtons.buttonClicked.connect(lambda: self.objectTree.sort(self.sortButtons.checkedId()))

        self.searchEdit.textChanged.connect(self.objectTree.filter)

        self.bValidate.clicked.connect(self.startValidation)

        self.bFixAreas.clicked.connect(self.fillAreasWithoutUsage)
        self.lFinished.setVisible(False)
        self.reset_label.setVisible(False)
        self.reset_label.mousePressEvent = self.onResetGeometryValidation
        self.lErrorCount.setText('')

        self.parishEdit.hide()
        self.parishEdit.parishChanged.connect(self.onParishChanged)
        self.parish.parishEditRequested.connect(self.parishEdit.show)

        # self.objectTree.selectionModel().currentChanged.connect(lambda: self.bEdit.setDisabled(False))
        self.objectTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.objectTree.customContextMenuRequested.connect(self.showObjectTreeContextMenu)
        self.objectTree.doubleClicked.connect(self.show_attribute_page)
        self.objectTree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.stackedWidget.currentChanged.connect(self.updateButtons)

        self.validation_spinner = WaitingSpinner(self.validation_result_view, disableParentWhenSpinning=True, radius=5, lines=20,
                                                 line_length=5, line_width=1, color=(0, 6, 128))
        self.init_spinner = WaitingSpinner(self, disableParentWhenSpinning=True, radius=5, lines=20,
                                           line_length=5, line_width=1, color=(0, 6, 128))

        self.undo_stack = XPUndoStack()
        self.undo_stack.undoTextChanged.connect(lambda u: self.bUndo.setToolTip(f'Rückgängig: {u}' if u else ''))
        self.undo_stack.redoTextChanged.connect(lambda r: self.bRedo.setToolTip(f'Vorwärts: {r}' if r else ''))
        self.undo_stack.indexChanged.connect(self.onUndoStackChanged)
        self.bUndo.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/undo.svg'), color='#1F2937'))
        self.bRedo.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/redo.svg'), color='#1F2937'))
        self.bUndo.setCursor(Qt.PointingHandCursor)
        self.bRedo.setCursor(Qt.PointingHandCursor)
        self.bUndo.setDisabled(True)
        self.bRedo.setDisabled(True)
        button_styling = '''
            QToolButton {
                border: 0px;
                cursor: pointer;
            }
            QToolButton:hover {
                background: #E5E7EB; 
            }
        '''
        self.bUndo.setStyleSheet(button_styling)
        self.bRedo.setStyleSheet(button_styling)
        self.button_highlight_filter = SVGButtonEventFilter(color='#1F2937', hover_color='black')
        self.bUndo.installEventFilter(self.button_highlight_filter)
        self.bRedo.installEventFilter(self.button_highlight_filter)
        self.bUndo.clicked.connect(self.undo_stack.undo)
        self.bRedo.clicked.connect(self.undo_stack.redo)

    def changeEvent(self, event: QEvent):
        super(XPPlanDetailsDialog, self).changeEvent(event)
        # widget dock status is changing
        if event.type() == QEvent.ParentChange:
            self.updateButtons()

    async def initialize_data(self, xid: str, keep_page=False):
        def _init():
            with Session.begin() as session:
                plan = session.get(XP_Plan, xid)
                self.plan_type = plan.__class__

                self.plan_xid = xid
                self.plan_type = plan.__class__
                self.lTitle.setText(plan.name)
                self.lPlanType.setText(self.plan_type.__name__)
                if isinstance(plan, (BP_Plan, FP_Plan)):
                    self.parish.setText('; '.join(str(g) for g in plan.gemeinde))
                    self.parish.setActive(True)
                    self.parishEdit.setup(plan.gemeinde)
                elif isinstance(plan, (RP_Plan, LP_Plan)):
                    self.parish.setText(f'Bundesland: {plan.bundesland}')
                    self.parish.setActive(False)

                self.construct_explorer(plan)

        async with self._init_lock:
            async with loading_animation(self):
                self.lFinished.setVisible(False)
                self.reset_label.setVisible(False)
                self.lErrorCount.setText('')
                self.undo_stack.clear()
                self.validation_result_view.clear()
                self.objectTree.clear()

                if not keep_page:
                    self.stackedWidget.setCurrentIndex(0)

                await asyncio.to_thread(_init)

                self.objectTree.expandAll()

    @pyqtSlot()
    def updateButtons(self):
        self.bPrev.setEnabled(self.stackedWidget.currentIndex() > 0)
        self.bEdit.setEnabled(self.stackedWidget.currentIndex() == 0)

        self.bSave.setVisible(self.stackedWidget.currentIndex() == 2)
        self.bUndo.setVisible(self.stackedWidget.currentIndex() != 2)
        self.bRedo.setVisible(self.stackedWidget.currentIndex() != 2)

    @pyqtSlot()
    def prevPage(self):
        # self.attributeTree.clear()
        widget = self.stackedWidget.currentWidget()
        self.stackedWidget.removeWidget(widget)
        widget.deleteLater()
        self.stackedWidget.setCurrentIndex(0)

    @qasync.asyncSlot(int)
    async def onUndoStackChanged(self, idx: int):
        self.bUndo.setDisabled(idx == 0)
        self.bRedo.setDisabled(self.undo_stack.count() == 0 or idx == self.undo_stack.count())

    @pyqtSlot(bool)
    def onEditMainClicked(self, clicked: bool):
        with Session.begin() as session:
            plan: XP_Plan = session.get(self.plan_type, self.plan_xid, [selectinload('*')])

            edit_widget = plan.edit_widget()
            self.insertWidgetIntoNewPage(edit_widget)
            self.bSave.setVisible(True)
            self.bSave.clicked.connect(self.onEditSaveClicked)

    @qasync.asyncSlot(dict)
    async def onParishChanged(self, parish: dict):
        self.parish.setText('; '.join(parish.keys()))
        with Session.begin() as session:
            parish_list = []
            for parish_name, parish_id in parish.items():
                xp_gemeinde = session.query(XP_Gemeinde).get(parish_id)
                parish_list.append(xp_gemeinde)

            plan = session.query(XP_Plan).options(lazyload('*'), load_only('id')).get(self.plan_xid)
            setattr(plan, 'gemeinde', parish_list)

    def construct_explorer(self, plan):
        xplan_item = XPlanungItem(xid=str(plan.id), xtype=plan.__class__)
        node = ClassNode(xplan_item)

        self.iterateRelation(plan, node)
        self.objectTree.model.addChild(node)

    async def addExplorerItem(self, parent_node: ClassNode, xplan_item: XPlanungItem, row=None):
        node = ClassNode(xplan_item, new=True)
        self.objectTree.model.addChild(node, parent_node, row)

        with Session.begin() as session:
            obj = session.query(xplan_item.xtype).get(xplan_item.xid)
            self.iterateRelation(obj, node)

    def showObjectTreeContextMenu(self, point):

        selected_indices = self.objectTree.selectionModel().selectedIndexes()
        if not selected_indices:
            return

        menu = QtWidgets.QMenu()
        menu.setToolTipsVisible(True)

        if len(selected_indices) > 1:
            self.create_multi_selection_menu(menu, selected_indices)
            menu.exec_(self.objectTree.mapToGlobal(point))
            return

        item: ClassNode = selected_indices[0].model().itemAtIndex(selected_indices[0])
        if not item:
            return

        if hasattr(item._data.xtype, 'geometry'):
            flash_action = QtWidgets.QAction(QIcon(':/images/themes/default/mActionScaleHighlightFeature.svg'),
                                             'Planinhalt auf Karte hervorheben')
            flash_action.triggered.connect(self.highlightPlanContent)
            menu.addAction(flash_action)

        if item.parent():
            delete_action = QtWidgets.QAction(QIcon(self.deleteIcon), 'Planinhalt löschen')
            delete_action.triggered.connect(lambda state, item_to_delete=item: self.onDeleteClick(item_to_delete))
            menu.addAction(delete_action)

        data_class_menu = QtWidgets.QMenu('Neues Datenobjekt hinzufügen')
        for rel in item._data.xtype.relationships():
            rel_class = rel[1].entity.class_
            if issubclass(rel_class, (XP_Objekt, GeometryObject)) and not issubclass(rel_class, XP_Bereich):
                continue
            if next(iter(rel[1].remote_side)).primary_key or rel[1].secondary is not None:
                continue
            if hasattr(item._data.xtype, '__avoidRelation__') and rel[0] in item._data.xtype.__avoidRelation__:
                continue

            cls = find_true_class(item.xplanItem().xtype, rel[0])
            if cls is None or not cls.attr_fits_version(rel[0], export_version()):
                continue

            action_name = item.xplanItem().xtype.xplan_attribute_name(rel[0])

            for entity_class in [rel_class, *rel_class.__subclasses__()]:
                if hasattr(entity_class, 'xp_versions') and export_version() not in entity_class.xp_versions:
                    continue

                data_class_action = QtWidgets.QAction(f'{action_name} ({entity_class.__name__})', self)
                data_class_action.triggered.connect(lambda state, p_item=item, attr=rel[0], d_class=entity_class:
                                                    self.onCreateDataClass(p_item, d_class, attr))
                data_class_action.setEnabled(not issubclass(item._data.xtype, XP_Objekt))
                if not rel[1].uselist and item.childCount():
                    for i in range(item.childCount()):
                        child_item = item.child(i)
                        with Session() as session:
                            col = next(iter(rel[1].remote_side)).description
                            ex = session.query(exists().where(getattr(rel_class, col) == item.id())).scalar()
                        if ex and child_item.xplanItem().xtype == rel_class:
                            data_class_action.setToolTip('Objekt existiert bereits!')
                            data_class_action.setEnabled(False)
                data_class_menu.addAction(data_class_action)

        if not data_class_menu.isEmpty():
            menu.addSeparator()
            menu.addMenu(data_class_menu)

        menu.exec_(self.objectTree.viewport().mapToGlobal(point))

    def create_multi_selection_menu(self, menu: QMenu, selected_indices: List[QModelIndex]):
        # edit
        # not in community-edition

        # delete
        delete_action = QAction(QIcon(self.deleteIcon), 'Markierte Planinhalte löschen', menu)
        delete_action.triggered.connect(lambda state, indices=selected_indices: self.delete_indices(indices))
        menu.addAction(delete_action)

    @pyqtSlot()
    def highlightPlanContent(self):
        item = self.objectTree.selectedItems()[0]
        with Session.begin() as session:
            plan_content = session.query(item._data.xtype).get(item._data.xid)
            iface.mapCanvas().flashGeometries([plan_content.geometry()], plan_content.srs())

    def onCreateDataClass(self, parent_item: ClassNode, data_class, attribute):
        if issubclass(parent_item._data.xtype, XP_Objekt):
            full_version_required_warning()
            return
        tab_widget = QXPlanTabWidget(data_class, parent_item._data.xtype)

        if self.bSave.receivers(self.bSave.clicked) > 0:
            self.bSave.clicked.disconnect()
        self.bSave.clicked.connect(functools.partial(self.onSaveClicked, parent_item, attribute))
        self.stackedWidget.insertWidget(2, tab_widget)
        self.stackedWidget.setCurrentIndex(2)

    @pyqtSlot(QtWidgets.QWidget)
    def insertWidgetIntoNewPage(self, widget):
        page_index = self.stackedWidget.currentIndex()
        self.stackedWidget.insertWidget(page_index + 1, widget)
        self.stackedWidget.setCurrentIndex(page_index + 1)

    @qasync.asyncSlot(bool)
    async def onEditSaveClicked(self, checked: bool):
        self.init_spinner.start()

        try:
            async with SessionAsync.begin() as session:
                tab_widget = self.stackedWidget.widget(self.stackedWidget.currentIndex())
                edited_object = tab_widget.populateContent()
                if not edited_object:
                    return
                edited_object.id = self.plan_xid

                plan = await session.merge(edited_object)

            await self.initialize_data(self.plan_xid, keep_page=True)

            self.prevPage()
            self.bSave.clicked.disconnect()

        except Exception as e:
            logger.exception(e)
        finally:
            self.init_spinner.stop()

    @qasync.asyncSlot(object, object, bool)
    async def onSaveClicked(self, parent_item: ClassNode, attribute, checked: bool):

        self.init_spinner.start()

        try:
            async with SessionAsync.begin() as session:
                tab_widget = self.stackedWidget.widget(self.stackedWidget.currentIndex())
                data_obj = tab_widget.populateContent()
                if not data_obj:
                    return

                data_obj.id = uuid.uuid4()

                true_class = find_true_class(parent_item._data.xtype, attribute)
                stmt = select(true_class).filter_by(id=parent_item._data.xid).options(
                    load_only(parent_item._data.xtype.id),
                    selectinload(getattr(true_class, attribute))
                )
                result = await session.execute(stmt)
                parent_obj = result.scalar_one()

                try:
                    getattr(parent_obj, attribute).append(data_obj)
                except AttributeError:
                    setattr(parent_obj, attribute, data_obj)
                await session.flush()

                data_obj = await session.get(data_obj.__class__, data_obj.id,
                                             options=[selectinload('*')], populate_existing=True)

                xplan_item = XPlanungItem(xid=str(data_obj.id), xtype=data_obj.__class__)
                node = ClassNode(xplan_item, new=True)
                self.objectTree.model.addChild(node, parent_item)
                self.iterateRelation(data_obj, node)

            self.prevPage()
            self.bSave.clicked.disconnect()

        except Exception as e:
            logger.exception(e)
        finally:
            self.init_spinner.stop()

    def iterateRelation(self, obj, root_node):
        try:
            for rel_item in obj.related():
                xplan_item = XPlanungItem(
                    xid=str(rel_item.id),
                    xtype=rel_item.__class__,
                    parent_xid=root_node.xplanItem().xid
                )
                node = ClassNode(xplan_item, new=root_node.flag_new)
                root_node.addChild(node)

                self.iterateRelation(rel_item, node)
        except Exception as e:
            logger.exception(f"Exception on filling object explorer: {e}")

    @pyqtSlot()
    def show_attribute_page(self):
        """ Zeigt ein QTreeWidget mit den Attributen und Werten des aktuell im Objektbaum gewählten Objekts an """
        item = self.objectTree.selectedItems()[0]
        attribute_config = yaml.safe_load(QSettings().value(f"plugins/xplanung/attribute_config", '')) or {}

        with Session() as session:
            session.expire_on_commit = False
            plan_content = session.query(item._data.xtype).get(item._data.xid)

            xtype = item._data.xtype
            plan_content = session.query(xtype).get(item._data.xid)
            base_classes = base_models(xtype)

            def skip_column():
                for mro_member in base_classes:
                    if attr in attribute_config.get(mro_member.__name__, []):
                        return True
                return False

            root_node = TreeNode("root", node_type="root")
            for (attr, mapper_property) in xtype.element_order(version=export_version(), ret_fmt='sqla'):

                if skip_column():
                    continue

                value = getattr(plan_content, attr)
                xplan_attribute_name = xtype.xplan_attribute_name(attr)

                if isinstance(mapper_property, RelationshipProperty):
                    form_type = mapper_property.info.get('form-type')
                    if form_type == 'inline':
                        root_node.add_child(TreeNode(xplan_attribute_name, value, node_type="attribute"))
                    elif value is not None and isinstance(value, list):
                        root_node.add_child(TreeNode.create_section(
                            xplan_attribute_name,
                            value
                        ))
                    else:
                        root_node.add_child(TreeNode(xplan_attribute_name, value, node_type="relation"))
                else:
                    root_node.add_child(TreeNode(xplan_attribute_name, value, node_type="attribute"))

            if isinstance(plan_content, GeometryObject):
                if hasattr(plan_content, 'geomType'):
                    geom_type = plan_content.geomType()
                else:
                    geom_type = plan_content.__geometry_type__
            else:
                geom_type = None

            xplanung_item = XPlanungItem(xid=item._data.xid, xtype=xtype, plan_xid=self.plan_xid, geom_type=geom_type)
            attribute_edit_widget = QAttributeEdit.create(xplanung_item, root_node, self)
            attribute_edit_widget.nameChanged.connect(self.onPlanNameChanged)

            for undo_command in self.undo_stack.iterate(_type=AttributeChangedCommand):
                if undo_command.xplan_item.xid == xplanung_item.xid:
                    new_index = attribute_edit_widget.model_index(undo_command.attribute)
                    undo_command.setModelIndex(new_index)
                    undo_command.signal_proxy.changeApplied.connect(attribute_edit_widget.apply_field_change)

            self.insertWidgetIntoNewPage(attribute_edit_widget)

    @qasync.asyncSlot(ClassNode)
    async def onDeleteReverted(self, node: ClassNode):
        xplan_item = node.xplanItem()
        parent_id = xplan_item.parent_xid or xplan_item.bereich_xid or xplan_item.plan_xid

        # find parent, to add object
        model = self.objectTree.model
        index_list = model.match(model.index(0, 0), XID_ROLE, parent_id, -1, Qt.MatchWildcard | Qt.MatchRecursive)

        if not index_list:
            return

        await self.addExplorerItem(model.itemAtIndex(index_list[0]), xplan_item, row=node.row())

    @qasync.asyncSlot(ClassNode)
    async def onDeleteApplied(self, node: ClassNode):
        # find node to delete
        model = self.objectTree.model
        index_list = model.match(model.index(0, 0), XID_ROLE, node.xplanItem().xid, -1,
                                 Qt.MatchWildcard | Qt.MatchRecursive)

        if not index_list:
            return
        model.removeRows(index_list[0].row(), 1, index_list[0].parent())

    def onDeleteClick(self, item: ClassNode):
        command = ObjectsDeletedCommand([item], self)
        command.signal_proxy.deleteReverted.connect(self.onDeleteReverted)
        command.signal_proxy.deleteApplied.connect(self.onDeleteApplied)
        self.undo_stack.push(command)

    def delete_indices(self, indices: List[QModelIndex]):
        _to_delete = []
        items = []
        for index in indices:
            item = index.model().itemAtIndex(index)
            parent_xid = item.xplanItem().parent_xid
            if any(d for d in _to_delete if parent_xid in d):
                continue
            _to_delete.append((item.xplanItem().xtype, item.xplanItem().xid))
            items.append(item)

        deleted, _ = self.deletePlanContent(delete_map=_to_delete)
        if deleted:
            for i in items:
                self.objectTree.removeItem(i)

    @pyqtSlot(str)
    def onPlanNameChanged(self, updated_name: str):
        self.lTitle.setText(updated_name)
        self.nameChanged.emit(self.plan_xid, updated_name)

    @pyqtSlot()
    def deletePlanContent(self,
                          class_type=None,
                          uid=None,
                          delete_map: Union[None, List[Tuple[type, str]]] = None) -> Tuple[bool, List[object]]:
        """
        Löscht einen oder mehrere Planinhalte aus der Datenbank.
        """
        with Session.begin() as session:
            session.expire_on_commit = False

            items_to_delete = []
            if delete_map is not None:
                for cls, xid in delete_map:
                    items_to_delete.append(session.query(cls).get(xid))
            elif uid is None:
                items_to_delete.append(session.query(XP_Plan).get(self.plan_xid))
            else:
                items_to_delete.append(session.query(class_type).get(uid))

            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle("Löschvorgang bestätigen")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)

            if len(items_to_delete) <= 1:
                msg.setText(f"Wollen Sie den Planinhalt unwiderruflich löschen? (id: {items_to_delete[0].id})")
            else:
                t = f"Wollen Sie die Planinhalte unwiderruflich löschen? <ul>"
                for item in items_to_delete:
                    t += f'<li>{item.__class__.__name__}: {item.id}</li>'
                t += '</ul>'
                msg.setText(t)
            ret = msg.exec_()
            if ret == QtWidgets.QMessageBox.Cancel:
                return False, []

            for d in items_to_delete:
                session.delete(d)

        if uid is None and delete_map is None:
            self.planDeleted.emit()
        return True, items_to_delete

    @qasync.asyncSlot()
    async def fillAreasWithoutUsage(self):
        self.bFixAreas.setEnabled(False)
        with Session.begin() as session:
            plan: XP_Plan = session.query(XP_Plan).get(self.plan_xid)
            loop = asyncio.get_running_loop()
            xplan_items = await loop.run_in_executor(None, plan.enforceFlaechenschluss)

            for item in xplan_items:
                m = self.objectTree.model
                # find item
                index_list = m.match(m.index(0, 0), XID_ROLE, item.xid, -1, Qt.MatchWildcard | Qt.MatchRecursive)
                if index_list:
                    index_list[0].internalPointer().flag_new = True
                    m.dataChanged.emit(index_list[0], index_list[0])
                    continue

                # else find parent and add new item
                index_list = m.match(m.index(0, 0), XID_ROLE, item.parent_xid, -1, Qt.MatchWildcard | Qt.MatchRecursive)
                if index_list:
                    await self.addExplorerItem(index_list[0], item, 0)

        self.bFixAreas.setEnabled(True)
        iface.messageBar().pushMessage("XPlanung", "Bilden des Flaechenschluss abgeschlossen", level=Qgis.Info)

    @qasync.asyncSlot()
    async def startValidation(self):
        self.validation_spinner.start()

        self.bValidate.setEnabled(False)
        self.lFinished.setVisible(False)
        self.reset_label.setVisible(False)
        self.lErrorCount.setText('')
        self.validation_result_view.clear()

        internal_error = False

        try:
            await asyncio.to_thread(self.validate_plan_geometric)
        except Exception as e:
            internal_error = True
            logger.error(e)
        finally:
            error_count = self.validation_result_view.item_count()
            if internal_error:
                self.validation_result_view.clear()
                self.validation_result_view.set_validation_state(ValidationState.ERROR)
            elif error_count == 0:
                self.validation_result_view.set_validation_state(ValidationState.SUCCESS)
            else:
                self.validation_result_view.set_validation_state(ValidationState.UNKNOWN)

            self.lErrorCount.setText(f'{error_count} Fehler gefunden' if error_count else 'Keine Fehler gefunden')
            if error_count:
                self.reset_label.setVisible(True)

            self.lFinished.setVisible(True)
            self.bValidate.setEnabled(True)
            self.validation_spinner.stop()

    def validate_plan_geometric(self):
        """
        Validate geometric correctness of the opened plan
        Tests for:
        -   All geometries are valid
        -   All geometries are within bounds of the plan
        -   There are no gaps/overlaps between geometries
        """
        short_plan_type = str(self.plan_type.__name__[:2]).lower()

        for func in VALIDATION_FUNCTIONS:
            validation_results = func(self.plan_xid, short_plan_type)
            self.validation_result_view.add_result_items(validation_results)

    def onResetGeometryValidation(self, event):
        self.validation_result_view.clear()

        self.lFinished.setVisible(False)
        self.reset_label.setVisible(False)
        self.lErrorCount.setText('')


def _is_mapped(obj):
    try:
        class_mapper(obj)
    except UnmappedClassError:
        return False
    return True