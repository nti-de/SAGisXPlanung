from qgis.PyQt.QtWidgets import QProgressBar
from qgis.PyQt.QtCore import Qt

from SAGisXPlanung.gui.style import ApplicationColor


class ProgressBar(QProgressBar):
    def __init__(self,
                 progress_bg_color=ApplicationColor.Grey300,
                 progress_chunk_bg_color=ApplicationColor.Secondary,
                 parent=None):
        super().__init__(parent)

        self._progress_bg_color = progress_bg_color
        self._progress_chunk_bg_color = progress_chunk_bg_color

        self.setTextVisible(False)
        self.setMaximum(100)
        self.setMinimum(0)
        self.setValue(0)
        self.setOrientation(Qt.Orientation.Horizontal)

        self.apply_style()

    def apply_style(self):
        style = f"""
        QProgressBar {{
            background-color: {self._progress_bg_color};
            border: none;
            padding: 0px;
            border-radius: 2px;
            max-height: 4px;
            height: 4px;
            margin: 5px;
        }}
        QProgressBar::chunk {{
            background: {self._progress_chunk_bg_color};
            border-radius: 2px;
            max-height: 4px;
            height: 4px;
            width: 10px;
            margin-right: -2px;
        }}
        """
        self.setStyleSheet(style)

    def set_colors(self, progress_bg_color=None, progress_chunk_bg_color=None):
        if progress_bg_color:
            self._progress_bg_color = progress_bg_color
        if progress_chunk_bg_color:
            self._progress_chunk_bg_color = progress_chunk_bg_color
        self.apply_style()
