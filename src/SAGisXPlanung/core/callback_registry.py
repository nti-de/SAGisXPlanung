from dataclasses import dataclass
from typing import Callable, Optional

from SAGisXPlanung.XPlanungItem import XPlanungItem


@dataclass
class CallbackEntry:
    callback: Callable
    table_name: Optional[str] = None
    column_name: Optional[str] = None


class CallbackRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensures only one instance of the class is created."""
        if not cls._instance:
            cls._instance = super(CallbackRegistry, cls).__new__(cls)
            cls._instance.callbacks = []
        return cls._instance

    def register_callback(self, callback: Callable, table_name: str = None, column_name: str = None):
        """Registers a callback function with optional table/column filtering."""
        if not callable(callback):
            raise TypeError('callback must be callable')

        entry = CallbackEntry(callback=callback, table_name=table_name, column_name=column_name)
        self.callbacks.append(entry)

    def run_callbacks(self, target_item: XPlanungItem, column, new_value):
        """Executes all registered callbacks with the provided arguments."""
        for entry in self.callbacks:
            # Check if the entry matches the table and column filters
            if (entry.table_name is None or entry.table_name == target_item.xtype.__tablename__) and \
               (entry.column_name is None or entry.column_name == column):
                try:
                    entry.callback(target_item, column, new_value)
                except Exception as e:
                    print(f"Callback {entry.callback.__name__} failed: {e}")