import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Union

from qgis.PyQt.QtCore import pyqtSignal, QModelIndex, QObject
from sqlalchemy.orm import make_transient, load_only, RelationshipProperty, ONETOMANY
from sqlalchemy import inspect as sa_inspect

from SAGisXPlanung import Session, Base, PYQT5
from SAGisXPlanung.XPlanungItem import XPlanungItem
from SAGisXPlanung.core.callback_registry import CallbackRegistry
from SAGisXPlanung.core.helper import find_true_class

if PYQT5:
    from qgis.PyQt.QtWidgets import QUndoCommand
else:
    from qgis.PyQt.QtGui import QUndoCommand


logger = logging.getLogger(__name__)


class CommandType(Enum):
    ATTRIBUTE_CHANGED = auto()
    OBJECT_DELETED = auto()
    RELATION_UNLINKED = auto()


class SignalProxy(QObject):
    changeApplied = pyqtSignal(QModelIndex, str, object)  # index, attr, value


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
            load_opts = [load_only(getattr(self.xplan_item.xtype, 'id'))]
            if isinstance(mapper_property := getattr(cls, self.attribute).property, RelationshipProperty):
                # if the changed property is a relationship, then write the corresponding id instead of ORM object
                # (only if it does not contain a secondary relation with assoc table)
                update_value = None
                if mapper_property.secondary is not None:
                    o = session.get(self.xplan_item.xtype, self.xplan_item.xid, options=load_opts)

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
            orm_instance = session.get(cls, self.xplan_item.xid, options=load_opts)
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
    command_type = CommandType.OBJECT_DELETED

    @dataclass
    class DeleteItem:
        xplan_item: XPlanungItem
        explorer_row: int = None
        attribute_view_index: QModelIndex = None
        attribute_name: str = None

    def __init__(self,
                 delete_items: list[tuple[XPlanungItem, Union[int, None], Union[QModelIndex, None]]],
                 parent=None):
        self.count = len(delete_items)
        super().__init__(f'Löschen {self.count} Objekt{"e" if self.count > 1 else ""}')

        self.parent = parent
        self.delete_items = []
        for item, explorer_row, attribute_view_index in delete_items:
            if attribute_view_index is None:
                self.delete_items.append(self.DeleteItem(item, explorer_row))
                continue

            parent_index = attribute_view_index.parent()
            if parent_index.isValid():
                attribute_name = parent_index.internalPointer().name
            else:
                attribute_name = attribute_view_index.internalPointer().name
            self.delete_items.append(self.DeleteItem(
                item,
                explorer_row,
                attribute_view_index,
                attribute_name=attribute_name
            ))

        self._snapshots: list[tuple[type, dict]] = []

    def redo(self):
        self._snapshots = []

        with Session.begin() as session:
            session.expire_on_commit = False

            for delete_item in self.delete_items:
                xplan_item = delete_item.xplan_item
                root_obj = session.get(xplan_item.xtype, xplan_item.xid)
                if root_obj is None:
                    continue

                # collect full tree state before delete
                self._snapshots.extend(collect_tree(root_obj))

                session.delete(root_obj)  # cascade handles children in DB

    def undo(self):
        if not self._snapshots:
            return

        with Session.begin() as session:
            for orm_class, state in self._snapshots:
                obj = orm_class()
                for key, value in state.items():
                    setattr(obj, key, value)
                make_transient(obj)
                session.add(obj)


def snapshot_object(obj) -> dict:
    """Capture all column values of an ORM object as a plain dict."""
    insp = sa_inspect(obj.__class__)
    return {col.key: getattr(obj, col.key) for col in insp.mapper.column_attrs}


def collect_tree(obj) -> list[tuple[type, dict]]:
    """
    DFS collection of an object and all cascade-deleted children.
    Returns list of (ORM class, state dict) in parent-first order.
    """
    result = []

    def _recurse(o):
        result.append((o.__class__, snapshot_object(o)))

        for rel in sa_inspect(o.__class__).relationships.values():
            if rel.direction == ONETOMANY:
                rel_value = getattr(o, rel.key, [])
                children = [rel_value] if rel_value is not None and not isinstance(rel_value, list) else (rel_value or [])
                for child in children:
                    _recurse(child)

    _recurse(obj)
    return result
