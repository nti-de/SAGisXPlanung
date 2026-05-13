import asyncio
import functools
import logging
import os
import uuid
from typing import List, Tuple, Union

import qasync

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAbstractItemView, QMenu, QAction, QVBoxLayout, QMessageBox
from qgis.PyQt.QtCore import Qt, pyqtSignal, pyqtSlot, QEvent, QModelIndex
from qgis.core import QgsVectorLayer
from qgis.gui import QgsDockWidget
from qgis.utils import iface
from sqlalchemy import select, exists, inspect as sa_inspect
from sqlalchemy.orm import lazyload, load_only, selectinload, RelationshipProperty, MANYTOMANY

from SAGisXPlanung import Session, BASE_DIR, SessionAsync, compile_ui_file, Base
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Plan
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Plan
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.RPlan.RP_Basisobjekte.feature_types import RP_Plan
from SAGisXPlanung.XPlan.data_types import XP_Gemeinde
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt
from SAGisXPlanung.core.helper import find_true_class
from SAGisXPlanung.core.mixins.mixins import GeometryObject
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import export_version
from SAGisXPlanung.core.canvas_display import plan_to_map
from SAGisXPlanung.ext.spinner import WaitingSpinner, loading_animation
from SAGisXPlanung.gui.commands import (ObjectsDeletedCommand, XPUndoStack, AttributeChangedCommand,
                                        StackChangeType, CommandType)
from SAGisXPlanung.gui.style import SVGButtonEventFilter, load_svg
from SAGisXPlanung.gui.widgets.QAttributeEdit import QAttributeEdit
from SAGisXPlanung.gui.widgets.QExplorerView import ClassNode, XID_ROLE
from SAGisXPlanung.gui.widgets.QXPlanTabWidget import QXPlanTabWidget
from SAGisXPlanung.gui.widgets.geometry_validation import ValidationWidget
from SAGisXPlanung.gui.widgets.select_related_widget import SelectRelatedWidget
from SAGisXPlanung.utils import full_version_required_warning, CLASSES

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
        self.setAllowedAreas(self.allowedAreas() | Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setObjectName('xplanung-details')

        self.deleteIcon = QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources/delete.svg')))
        self.bMap.setIcon(QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__), 'resources/map.svg'))))

        self.bMap.clicked.connect(lambda _: plan_to_map(self.plan_xid))
        self.bDelete.setIcon(self.deleteIcon)
        self.bDelete.clicked.connect(self.deletePlanContent)
        self.bEdit.clicked.connect(self.show_attribute_page)
        # self.bEdit.setDisabled(True)
        self.bPrev.clicked.connect(self.prevPage)
        self.bSave = self.bActions.button(QtWidgets.QDialogButtonBox.StandardButton.Save)
        self.bSave.setVisible(False)
        self.lTitle.setElideMode(Qt.TextElideMode.ElideRight)

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

        self.validation_widget = ValidationWidget()
        self.validation_widget.fill_geometric_completed.connect(self.on_fill_geometric_completed)
        self.validation_widget.revertible_action_completed.connect(lambda c: self.undo_stack.push(c))
        validation_group_layout = QVBoxLayout()
        self.validation_group.setLayout(validation_group_layout)
        self.validation_group.layout().addWidget(self.validation_widget)

        self.parishEdit.hide()
        self.parishEdit.parishChanged.connect(self.onParishChanged)
        self.parish.parishEditRequested.connect(self.parishEdit.show)

        # self.objectTree.selectionModel().currentChanged.connect(lambda: self.bEdit.setDisabled(False))
        self.objectTree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.objectTree.customContextMenuRequested.connect(self.showObjectTreeContextMenu)
        self.objectTree.doubleClicked.connect(self.show_attribute_page)
        self.objectTree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.stackedWidget.currentChanged.connect(self.updateButtons)

        self.init_spinner = WaitingSpinner(self, disableParentWhenSpinning=True, radius=5, lines=20,
                                           line_length=5, line_width=1, color=(0, 6, 128))

        self.undo_stack = XPUndoStack()
        self.undo_stack.undoTextChanged.connect(lambda u: self.bUndo.setToolTip(f'Rückgängig: {u}' if u else ''))
        self.undo_stack.redoTextChanged.connect(lambda r: self.bRedo.setToolTip(f'Vorwärts: {r}' if r else ''))
        self.undo_stack.stack_changed.connect(self.on_undo_stack_changed)
        self.bUndo.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/undo.svg'), color='#1F2937'))
        self.bRedo.setIcon(load_svg(os.path.join(BASE_DIR, 'gui/resources/redo.svg'), color='#1F2937'))
        self.bUndo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bRedo.setCursor(Qt.CursorShape.PointingHandCursor)
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

        self._pending_deletion_items = []

        MapLayerRegistry().features_deleted.connect(self._on_features_deleted)
        MapLayerRegistry().committed_features_removed.connect(self._on_committed_features_removed)
        MapLayerRegistry().after_rollback.connect(self._on_after_rollback)

    def changeEvent(self, event: QEvent):
        super(XPPlanDetailsDialog, self).changeEvent(event)
        # widget dock status is changing
        if event.type() == QEvent.Type.ParentChange:
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
                self.undo_stack.clear()
                self.objectTree.clear()

                if not keep_page:
                    self.stackedWidget.setCurrentIndex(0)

                await asyncio.to_thread(_init)

                self.validation_widget.set_plan_info(self.plan_xid, self.plan_type)

                self.objectTree.expandAll()

    @pyqtSlot()
    def updateButtons(self):
        self.bPrev.setEnabled(self.stackedWidget.currentIndex() > 0)
        self.bEdit.setEnabled(self.stackedWidget.currentIndex() == 0)

        current_widget = self.stackedWidget.currentWidget()
        is_new_object_widget = isinstance(current_widget, (SelectRelatedWidget, QXPlanTabWidget))
        self.bSave.setVisible(is_new_object_widget == True)
        self.bUndo.setVisible(not is_new_object_widget)
        self.bRedo.setVisible(not is_new_object_widget)

    @pyqtSlot()
    def prevPage(self):
        widget = self.stackedWidget.currentWidget()
        self.stackedWidget.removeWidget(widget)
        widget.deleteLater()
        self.stackedWidget.setCurrentIndex(0)

    @qasync.asyncSlot(int, StackChangeType)
    async def on_undo_stack_changed(self, idx: int, change_type: StackChangeType):
        self.bUndo.setDisabled(idx == 0)
        self.bRedo.setDisabled(self.undo_stack.count() == 0 or idx == self.undo_stack.count())

        if change_type == StackChangeType.REDO:
            command = self.undo_stack.command(idx - 1)
        else:
            command = self.undo_stack.command(idx)

        if hasattr(command, 'command_type') and command.command_type == CommandType.OBJECT_DELETED:
            if change_type == StackChangeType.REDO:
                for delete_item in command.delete_items:
                    xplan_item = delete_item.xplan_item
                    model = self.objectTree.model
                    index_list = model.match(model.index(0, 0), XID_ROLE, xplan_item.xid, -1,
                                             Qt.MatchFlag.MatchWildcard | Qt.MatchFlag.MatchRecursive)
                    if not index_list:
                        continue
                    index = index_list[0]
                    if not xplan_item.parent_xid:
                        parent = index.parent()
                        if parent.isValid():
                            xplan_item.parent_xid = parent.internalPointer().xplanItem().xid
                            delete_item.explorer_row = index.row()
                    model.removeRows(index.row(), 1, index.parent())

            else:
                for delete_item in command.delete_items:
                    self.onDeleteReverted(delete_item.xplan_item, delete_item.explorer_row)


    @pyqtSlot(bool)
    def onEditMainClicked(self, clicked: bool):
        with Session.begin() as session:
            plan: XP_Plan = session.get(self.plan_type, self.plan_xid, options=[selectinload('*')])

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
                xp_gemeinde = session.get(XP_Gemeinde, parish_id)
                parish_list.append(xp_gemeinde)

            plan = session.get(XP_Plan, self.plan_xid, options=[lazyload('*'), load_only(XP_Plan.id)])
            setattr(plan, 'gemeinde', parish_list)

    def construct_explorer(self, plan):
        xplan_item = XPlanungItem(xid=str(plan.id), xtype=plan.__class__)
        node = ClassNode(xplan_item)

        self.iterateRelation(plan, node)
        self.objectTree.model.addChild(node)

    def addExplorerItem(self, parent_node: ClassNode, xplan_item: XPlanungItem, row=None):
        node = ClassNode(xplan_item, new=True)
        self.objectTree.model.addChild(node, parent_node, row)

        with Session.begin() as session:
            obj = session.get(xplan_item.xtype, xplan_item.xid)
            self.iterateRelation(obj, node)

    def showObjectTreeContextMenu(self, point):

        selected_indices = self.objectTree.selectionModel().selectedIndexes()
        if not selected_indices:
            return

        menu = QtWidgets.QMenu()
        menu.setToolTipsVisible(True)

        if len(selected_indices) > 1:
            self.create_multi_selection_menu(menu, selected_indices)
            menu.exec(self.objectTree.mapToGlobal(point))
            return

        selected_index = selected_indices[0]
        item: ClassNode = selected_index.model().itemAtIndex(selected_index)
        if not item:
            return

        if hasattr(item._data.xtype, 'geometry'):
            flash_action = QtWidgets.QAction(QIcon(':/images/themes/default/mActionScaleHighlightFeature.svg'),
                                             'Planinhalt auf Karte hervorheben')
            flash_action.triggered.connect(self.highlightPlanContent)
            menu.addAction(flash_action)

        if item.parent():
            delete_action = QtWidgets.QAction(QIcon(self.deleteIcon), 'Planinhalt löschen')
            delete_action.triggered.connect(lambda state, del_index=selected_index: self.delete_indices([del_index]))
            menu.addAction(delete_action)

        data_class_menu = QtWidgets.QMenu('Neues Datenobjekt hinzufügen')
        for (attr, mapper_property) in item.xplanItem().xtype.element_order(version=export_version(), ret_fmt='sqla'):
            if not isinstance(mapper_property, RelationshipProperty):
                continue
            rel_class = mapper_property.entity.class_
            if issubclass(rel_class, (XP_Objekt, GeometryObject)) and not issubclass(rel_class, XP_Bereich):
                continue
            form_type = mapper_property.info.get('form-type')
            if form_type == 'inline' or form_type == 'hidden':
                continue

            cls = find_true_class(item.xplanItem().xtype, attr)
            action_name = cls.xplan_attribute_name(attr)

            link_type = mapper_property.info.get('link-type')
            if link_type == 'abstract':
                class_pool = rel_class.__subclasses__()
                # create new sub menu for collection of subclasses from abstract base
                item_option_menu = data_class_menu.addMenu(f'{action_name} ({rel_class.__name__})')
            else:
                class_pool = [rel_class, *rel_class.__subclasses__()]
                item_option_menu = data_class_menu

            for entity_class in class_pool:
                if hasattr(entity_class, 'xp_versions') and export_version() not in entity_class.xp_versions:
                    continue

                data_class_action = QtWidgets.QAction(f'{action_name} ({entity_class.__name__})', self)
                data_class_action.triggered.connect(lambda state, p_item=item, attr=attr, d_class=entity_class:
                                                    self.onCreateDataClass(p_item, d_class, attr))
                if not mapper_property.uselist and item.childCount():
                    for i in range(item.childCount()):
                        child_item = item.child(i)
                        with Session() as session:
                            col = next(iter(mapper_property.remote_side)).description
                            ex = session.query(exists().where(getattr(rel_class, col) == item.id())).scalar()
                        if ex and child_item.xplanItem().xtype == rel_class:
                            data_class_action.setToolTip('Objekt existiert bereits!')
                            data_class_action.setEnabled(False)
                item_option_menu.addAction(data_class_action)

        if not data_class_menu.isEmpty():
            menu.addSeparator()
            menu.addMenu(data_class_menu)

        menu.exec(self.objectTree.viewport().mapToGlobal(point))

    def create_multi_selection_menu(self, menu: QMenu, selected_indices: List[QModelIndex]):
        # edit
        model = selected_indices[0].model()
        xp_items = [model.itemAtIndex(m_idx).xplanItem() for m_idx in selected_indices]

        if all(obj.xtype == xp_items[0].xtype for obj in xp_items):
            multi_edit_action = QAction(QIcon(os.path.join(BASE_DIR, 'gui/resources/edit_note.svg')),
                                        'Gewählte Objekte bearbeiten', menu)
            multi_edit_action.triggered.connect(lambda state, items=xp_items: full_version_required_warning())
            menu.addAction(multi_edit_action)
            menu.addSeparator()

        # delete
        delete_action = QAction(QIcon(self.deleteIcon), 'Markierte Planinhalte löschen', menu)
        delete_action.triggered.connect(lambda state, indices=selected_indices: self.delete_indices(indices))
        menu.addAction(delete_action)

    @pyqtSlot()
    def highlightPlanContent(self):
        item = self.objectTree.selectedItems()[0]
        with Session.begin() as session:
            plan_content = session.get(item._data.xtype, item._data.xid)
            iface.mapCanvas().flashGeometries([plan_content.geometry()], plan_content.srs())

    def onCreateDataClass(self, parent_item: ClassNode, data_class, attribute):
        rel = sa_inspect(parent_item._data.xtype).relationships[attribute]
        if rel.direction == MANYTOMANY:
            widget = SelectRelatedWidget(data_class, parent_item._data, attribute, self.plan_xid)
        else:
            widget = QXPlanTabWidget(data_class, parent_item._data.xtype)

        if self.bSave.receivers(self.bSave.clicked) > 0:
            self.bSave.clicked.disconnect()
        self.bSave.clicked.connect(functools.partial(self.onSaveClicked, parent_item, attribute))
        self.insertWidgetIntoNewPage(widget)

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
        keep_page = False  # flag when error occurred, will make the dialog stay on this page

        try:
            async with SessionAsync.begin() as session:
                tab_widget = self.stackedWidget.widget(self.stackedWidget.currentIndex())

                true_class = find_true_class(parent_item._data.xtype, attribute)
                stmt = select(true_class).filter_by(id=parent_item._data.xid).options(
                    load_only(parent_item._data.xtype.id),
                    selectinload(getattr(true_class, attribute))
                )
                result = await session.execute(stmt)
                parent_obj = result.scalar_one()

                if isinstance(tab_widget, SelectRelatedWidget):
                    if tab_widget.is_create_new():
                        data_obj = tab_widget.data_input_widget.populateContent()
                        # we can append immediately; SelectRelatedWidget is guaranteed to be used with m:n relation
                        getattr(parent_obj, attribute).append(data_obj)
                        return
                    else:
                        selected_ids = tab_widget.get_selected_ids()
                        attach_objects = []
                        for selected_id in selected_ids:
                            o = await session.get(tab_widget.create_type, selected_id, options=[selectinload('*')])
                            attach_objects.append(o)

                        if not attach_objects:
                            getattr(parent_obj, attribute).clear()
                        else:
                            setattr(parent_obj, attribute, attach_objects)

                        return
                else:
                    data_obj = tab_widget.populateContent()

                if not data_obj:
                    keep_page = True
                    return

                data_obj.id = uuid.uuid4()

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

        except Exception as e:
            keep_page = True
            logger.exception(e)
        finally:
            self.init_spinner.stop()
            if not keep_page:
                if self.bSave.receivers(self.bSave.clicked) > 0:
                    self.bSave.clicked.disconnect()
                self.prevPage()


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

        xplanung_item = XPlanungItem(xid=item._data.xid, xtype=item._data.xtype, plan_xid=self.plan_xid)
        attribute_edit_widget = QAttributeEdit.create(xplanung_item, self, self.undo_stack)
        attribute_edit_widget.nameChanged.connect(self.onPlanNameChanged)

        for undo_command in self.undo_stack.iterate(_type=AttributeChangedCommand):
            if undo_command.xplan_item.xid == xplanung_item.xid:
                new_index = attribute_edit_widget.model_index(undo_command.attribute)
                undo_command.setModelIndex(new_index)
                undo_command.signal_proxy.changeApplied.connect(attribute_edit_widget.apply_field_change)

        self.insertWidgetIntoNewPage(attribute_edit_widget)

    @pyqtSlot(XPlanungItem, int)
    def onDeleteReverted(self, xplan_item: XPlanungItem, row: int):
        parent_id = xplan_item.parent_xid or xplan_item.bereich_xid or xplan_item.plan_xid

        # find parent, to add object
        model = self.objectTree.model
        index_list = model.match(model.index(0, 0), XID_ROLE, parent_id, -1, Qt.MatchFlag.MatchWildcard | Qt.MatchFlag.MatchRecursive)

        if not index_list:
            return

        self.addExplorerItem(model.itemAtIndex(index_list[0]), xplan_item, row=row)

    def delete_indices(self, indices: List[QModelIndex]):
        _to_delete = []

        for index in indices:
            item = index.model().itemAtIndex(index)
            parent_xid = item.xplanItem().parent_xid
            if any(d for d in _to_delete if parent_xid in d):
                continue
            _to_delete.append((item.xplanItem(), item.row(), None))

        command = ObjectsDeletedCommand(_to_delete, self)
        self.undo_stack.push(command)

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
                    items_to_delete.append(session.get(cls, xid))
            elif uid is None:
                items_to_delete.append(session.get(XP_Plan, self.plan_xid))
            else:
                items_to_delete.append(session.get(class_type, uid))

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
            ret = msg.exec()
            if ret == QtWidgets.QMessageBox.Cancel:
                return False, []

            for d in items_to_delete:
                session.delete(d)

        if uid is None and delete_map is None:
            self.planDeleted.emit()
        return True, items_to_delete

    @qasync.asyncSlot(list)
    async def on_fill_geometric_completed(self, xplan_items: List[XPlanungItem]):
        for item in xplan_items:
            m = self.objectTree.model
            # find item
            index_list = m.match(m.index(0, 0), XID_ROLE, item.xid, -1, Qt.MatchFlag.MatchWildcard | Qt.MatchFlag.MatchRecursive)
            if index_list:
                index_list[0].internalPointer().flag_new = True
                m.dataChanged.emit(index_list[0], index_list[0])
                continue

            # else find parent and add new item
            index_list = m.match(m.index(0, 0), XID_ROLE, item.parent_xid, -1, Qt.MatchFlag.MatchWildcard | Qt.MatchFlag.MatchRecursive)
            if index_list:
                self.addExplorerItem(index_list[0], item, 0)

    def _collect_children(self, node: ClassNode) -> List[str]:
        xids = []
        for i in range(node.childCount()):
            child = node.child(i)
            xids.append(child.xplanItem().xid)
            xids.extend(self._collect_children(child))
        return xids

    @pyqtSlot(QgsVectorLayer, list)
    def _on_features_deleted(self, layer, deleted_fids: list):
        plan_xid = layer.customProperty(f'xplanung/plan-xid')
        if self.plan_xid != plan_xid:
            return

        model = self.objectTree.model

        for fid in deleted_fids:
            orm_xid = layer.customProperty(f'xplanung/feat-{fid}')
            if not orm_xid:
                continue
            model.mark_for_deletion(orm_xid, layer.id(), True)

    @pyqtSlot(QgsVectorLayer, list)
    def _on_committed_features_removed(self, layer, deleted_fids: list):
        plan_xid = layer.customProperty(f'xplanung/plan-xid')
        if self.plan_xid != plan_xid:
            result = QMessageBox.warning(
                self,
                "XPlan-Objekte löschen",
                f"Die entfernten Objekte gehören zu einem XPlan-Datensatz, der nicht im Arbeitsbereich geöffnet ist.\n\n"
                f"XPlan-Objekte trotzdem unwiderruflich aus der Datenbank löschen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.No:
                return
            delete_map = []
            xtype = layer.customProperty(f'xplanung/type')
            for fid in deleted_fids:
                orm_xid = layer.customProperty(f'xplanung/feat-{fid}')
                if not orm_xid:
                    continue
                delete_map.append((CLASSES[xtype], orm_xid))
                print(delete_map)
            self.deletePlanContent(delete_map=delete_map)
            return

        model = self.objectTree.model
        to_delete = []
        for node in model.get_pending_deletes(layer.id()):
            if node and hasattr(node, 'xplanItem'):
                item = node.xplanItem()
                to_delete.append((item, node.row(), None))
        if to_delete:
            command = ObjectsDeletedCommand(to_delete, self)
            self.undo_stack.push(command)
        model._pending_deletion_items[layer.id()].clear()

    def _on_after_rollback(self):
        self.objectTree.model.discard_pending_deletes()
