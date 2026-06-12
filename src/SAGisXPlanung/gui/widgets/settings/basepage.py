from dataclasses import dataclass, field
from typing import Any, Callable, List

from qgis.PyQt.QtGui import QCloseEvent
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QWidget


@dataclass
class SettingBinding:
    name: str
    get_value: Callable[[], Any]
    save_value: Callable[[Any], None]
    normalize: Callable[[Any], Any] = lambda value: value
    dirty: bool = False
    _snapshot: Any = field(default=None, init=False)

    def current_value(self):
        return self.normalize(self.get_value())

    def refresh_snapshot(self):
        self._snapshot = self.current_value()
        self.dirty = False

    def commit(self):
        if not self.dirty:
            return False

        current = self.current_value()
        if current == self._snapshot:
            self.dirty = False
            return False

        self.save_value(current)
        self._snapshot = current
        self.dirty = False
        return True


class SettingsPage(QWidget):

    # signal to notify parent dialog to refresh a settings page of given type
    requestPageRefresh = pyqtSignal(object)  # parameter of type SettingsPage

    def __init__(self, parent=None):
        super(SettingsPage, self).__init__(parent)
        self._setting_bindings: List[SettingBinding] = []
        self._loading_settings = False

    def setup_ui(self, ui):
        raise NotImplementedError('Abstract. Should be implemented in subclass.')

    def setup_data(self):
        raise NotImplementedError('Abstract. Should be implemented in subclass.')

    def load_settings_data(self):
        self._loading_settings = True
        try:
            self.setup_data()
        finally:
            self._loading_settings = False
            self.refresh_settings_snapshot()

    def register_setting(self, binding: SettingBinding, *signals):
        self._setting_bindings.append(binding)
        for signal in signals:
            signal.connect(lambda *args, _binding=binding: self.mark_setting_dirty(_binding))

    def mark_setting_dirty(self, binding: SettingBinding):
        if not self._loading_settings:
            binding.dirty = True

    def refresh_settings_snapshot(self):
        for binding in self._setting_bindings:
            binding.refresh_snapshot()

    def commit_changes(self):
        return [binding.name for binding in self._setting_bindings if binding.commit()]

    def closeEvent(self, event: QCloseEvent):
        pass
