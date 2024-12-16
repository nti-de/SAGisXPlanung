import inspect
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

            stmt = update(cls.__table__).where(
                cls.__table__.c.id == self.xplan_item.xid
            ).values({attr: update_value})
            session.execute(stmt)

        CallbackRegistry().run_callbacks(self.xplan_item, attr, update_value)

    def undo(self):
        self.applyValue(self.previous_value)
        self.signal_proxy.changeApplied.emit(self.model_index, self.attribute, self.previous_value)

    def redo(self):
        self.applyValue(self.new_value)
        self.signal_proxy.changeApplied.emit(self.model_index, self.attribute, self.new_value)


class ObjectsDeletedCommand(QUndoCommand):
    def __init__(self, nodes: List[ClassNode], parent):
        self.count = len(nodes)
        super().__init__(f'Löschen {self.count} Objekt{"e" if self.count > 1 else ""}')

        self.parent = parent

        self.items = nodes
        self.objects = []

        self.signal_proxy = SignalProxy()

    def make_related_objects_transient(self, obj):
        for rel_item in obj.related():
            make_transient(rel_item)
            self.make_related_objects_transient(rel_item)

    def undo(self):
        with Session.begin() as session:
            for item, obj in zip(self.items, self.objects):
                make_transient(obj)
                self.make_related_objects_transient(obj)
                session.add(obj)

                self.signal_proxy.deleteReverted.emit(item)

    def redo(self):
        self.objects = []

        with Session.begin() as session:
            session.expire_on_commit = False
            for item in self.items:
                xp_item = item.xplanItem()
                obj = session.get(xp_item.xtype, xp_item.xid, [selectinload('*')])
                session.delete(obj)

                self.objects.append(obj)
                self.signal_proxy.deleteApplied.emit(item)
