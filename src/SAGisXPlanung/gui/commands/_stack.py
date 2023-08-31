from typing import TypeVar, Type

from qgis.PyQt.QtWidgets import QUndoStack, QUndoCommand


T = TypeVar('T', bound=QUndoCommand)


class XPUndoStack(QUndoStack):
    """ Custom UndoStack with functionality to iterate over the stack contents"""

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
