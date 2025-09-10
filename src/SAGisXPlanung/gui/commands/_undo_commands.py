import inspect
import logging
from typing import List, Iterable

from qgis.PyQt.QtCore import pyqtSignal, QModelIndex, QObject, Qt
from qgis.PyQt.QtWidgets import QUndoCommand
from sqlalchemy import update, delete, select, inspect as s_inspect
from sqlalchemy.orm import make_transient, selectinload, load_only, RelationshipProperty
from sqlalchemy.orm.attributes import flag_modified

from SAGisXPlanung import Session, Base
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.config import export_version
from SAGisXPlanung.core.callback_registry import CallbackRegistry
from SAGisXPlanung.core.helper import find_true_class
from SAGisXPlanung.gui.widgets.QExplorerView import ClassNode, XID_ROLE


logger = logging.getLogger(__name__)


class SignalProxy(QObject):
    changeApplied = pyqtSignal(QModelIndex, str, object)  # index, attr, value

    deleteReverted = pyqtSignal(ClassNode)
    deleteApplied = pyqtSignal(ClassNode)


class AttributeChangedCommand(QUndoCommand):
    def __init__(self, xplanung_item, attribute, previous_value, new_value, model_index):
        super().__init__(f'Änderung Attribut {attribute} im Objekt {xplanung_item.xtype.__name__}')
        self.xplan_item = xplanung_item
        self.model_index = model_index

        self.attribute = attribute
        self.previous_value = previous_value
        self.new_value = new_value

        self.signal_proxy = SignalProxy()

    def setModelIndex(self, index: QModelIndex):
        self.model_index = index

    def applyValue(self, value):
        with Session.begin() as session:
            session.expire_on_commit = False

            cls = find_true_class(self.xplan_item.xtype, self.attribute)
            if isinstance(mapper_property := getattr(cls, self.attribute).property, RelationshipProperty):
                # if the changed property is a relationship, then write the corresponding id instead of ORM object
                # (only if it does not contain a secondary relation with assoc table)
                update_value = None
                if mapper_property.secondary is not None:
                    o = session.get(self.xplan_item.xtype, self.xplan_item.xid, [
                        load_only('id')
                    ])

                    merged = []
                    for selected_item in value:
                        merged.append(session.merge(selected_item))

                    setattr(o, self.attribute, merged)
                    return
                else:
                    attr = self.attribute + '_id'
                    if value is not None:
                        session.add(value)
                        update_value = value.id
            else:
                attr = self.attribute
                update_value = value

            # this is pretty slow since it emits a SELECT and has to populate the ORM instance
            # but is required to emit mapper-level events after_update/before_update which are used to update visualization
            orm_instance = session.get(cls, self.xplan_item.xid, [load_only('id')])
            setattr(orm_instance, attr, update_value)

            # if hasattr(cls, 'FORCE_ORM_UPDATE') and cls.FORCE_ORM_UPDATE:
            #     orm_instance = session.get(cls, self.xplan_item.xid, [load_only('id')])
            #     setattr(orm_instance, attr, update_value)
            # else:
            #     stmt = update(cls.__table__).where(
            #         cls.__table__.c.id == self.xplan_item.xid
            #     ).values({attr: update_value})
            #     session.execute(stmt)

        CallbackRegistry().run_callbacks(self.xplan_item, attr, update_value)

    def undo(self):
        self.applyValue(self.previous_value)
        self.signal_proxy.changeApplied.emit(self.model_index, self.attribute, self.previous_value)

    def redo(self):
        self.applyValue(self.new_value)
        self.signal_proxy.changeApplied.emit(self.model_index, self.attribute, self.new_value)


class ObjectsDeletedCommand(QUndoCommand):
    def __init__(self, nodes_to_delete: List[ClassNode], parent):
        self.count = len(nodes_to_delete)
        super().__init__(f'Löschen {self.count} Objekt{"e" if self.count > 1 else ""}')

        self.parent = parent

        self.main_items = nodes_to_delete
        self.tracked_deletes = []

        self.signal_proxy = SignalProxy()

    def undo(self):
        with Session.begin() as session:
            for item, obj in self.tracked_deletes:
                make_transient(obj)
                session.add(obj)

            main_item, _ = self.tracked_deletes[-1]
            self.signal_proxy.deleteReverted.emit(main_item)

    def redo(self):
        self.tracked_deletes = []

        def _collect_deletes(item, session):
            # Collect object instances that will be deleted
            # The actual deletion happens via cascaded backrefs on the top-level item to be deleted.
            for i in range(item.childCount()):
                child = item.child(i)
                _collect_deletes(child, session)

            # Fetch and record the object for deletion
            xp_item = item.xplanItem()
            delete_obj = session.get(xp_item.xtype, xp_item.xid)
            self.tracked_deletes.append((item, delete_obj))

        with Session.begin() as session:
            session.expire_on_commit = False

            for main_item in self.main_items:
                _collect_deletes(main_item, session)
                # Delete the top-level object (selected item) after all children are collected
                _, obj = self.tracked_deletes[-1]
                session.delete(obj)
                self.signal_proxy.deleteApplied.emit(main_item)
