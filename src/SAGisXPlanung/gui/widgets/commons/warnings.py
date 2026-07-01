import os
from dataclasses import dataclass

from qgis.PyQt.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QToolButton

from SAGisXPlanung import BASE_DIR
from SAGisXPlanung.gui.style import load_svg, ApplicationColor
from SAGisXPlanung.gui.widgets.commons.label import ElideLabel


@dataclass
class WarningItem:
    id: str
    message: str


class WarningsWidget(QFrame):
    _style = """
    QFrame {{
        background-color: {_bg_warn};
        border: 1px solid {_warn_color};
        border-radius: 5px;
    }}
    QLabel {{
        color: {_warn_color};
        background: transparent;
        border: none;
    }}
    QToolButton {{
        background: transparent;
        border: none;
        padding: 0px;
    }}
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setStyleSheet(self._style.format(
            _bg_warn=ApplicationColor.WarningBackground,
            _warn_color=ApplicationColor.WarningText,
        ))

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(4)
        self._warnings = []

        self._warning_icon = load_svg(
            os.path.join(BASE_DIR, 'gui/resources/warning.svg'),
            color=ApplicationColor.WarningText
        )

    def set_warnings(self, warnings: list):
        self._warnings = warnings

        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()

        if not warnings:
            self.setVisible(False)
            return

        for warning in warnings:
            row = QHBoxLayout()
            row.setSpacing(6)

            icon = QToolButton(self)
            icon.setIcon(self._warning_icon)
            row.addWidget(icon)

            msg_label = ElideLabel(warning.message)
            row.addWidget(msg_label, 1)

            self._layout.addLayout(row)

        self.setVisible(True)
