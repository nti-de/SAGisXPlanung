from enum import Enum, auto
from typing import TypeVar, Type

from qgis.PyQt.QtCore import pyqtSignal

from SAGisXPlanung import PYQT5

if PYQT5:
    from qgis.PyQt.QtWidgets import QUndoStack, QUndoCommand
else:
    from qgis.PyQt.QtGui import QUndoStack, QUndoCommand


T = TypeVar('T', bound=QUndoCommand)


class StackChangeType(Enum):
    REDO = auto()
    UNDO = auto()


class XPUndoStack(QUndoStack):
    """ Custom UndoStack with functionality to iterate over the stack contents"""
    stack_changed = pyqtSignal(int, StackChangeType)

    def __init__(self):
        super().__init__()
        self._last_index = self.index()
        self.indexChanged.connect(self._track_change)

    def _track_change(self, new_index):
        if new_index < self._last_index:
            self.stack_changed.emit(new_index, StackChangeType.UNDO)
        elif new_index > self._last_index:
            self.stack_changed.emit(new_index, StackChangeType.REDO)

        self._last_index = new_index

    def iterate(self, _type: Type[T] = None) -> T:
        """ if _type parameter is specified, only filters on the given UndoCommand type"""
        if _type is not None and not issubclass(_type, QUndoCommand):
            raise TypeError('parameter `_type` must be a subclass of `QUndoCommand`')

        for i in range(self.count()):
            command = self.command(i)

            if _type is not None:
                if isinstance(command, _type):
                    yield command
            else:
                yield command
