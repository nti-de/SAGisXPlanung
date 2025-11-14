
from qgis.PyQt.QtWidgets import (QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QSizePolicy,
                                 QSpacerItem, QLineEdit, QDial)
from qgis.PyQt.QtCore import Qt, pyqtSlot, pyqtSignal


class QCommonStylingOptions(QWidget):

    ATTRIBUTE_SIZE = 'skalierung'
    ATTRIBUTE_ANGLE = 'drehwinkel'

    styleChanged = pyqtSignal(str, object)  # style attribute, value

    def __init__(self, parent=None):
        super(QCommonStylingOptions, self).__init__(parent)

        self._layout = QGridLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._layout.addWidget(QLabel('Größe'), 0, 0)
        self._layout.addWidget(QLabel('Drehwinkel'), 1, 0)

        vbox = QVBoxLayout()
        self.sizeSlider = QSlider(Qt.Horizontal, self)
        self.sizeSlider.setRange(1, 99)
        self.sizeSlider.setSliderPosition(50)
        self.sizeSlider.setSingleStep(1)
        vbox.addWidget(self.sizeSlider)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('Klein'))
        hbox.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        hbox.addWidget(QLabel('Mittel'))
        hbox.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        hbox.addWidget(QLabel('Groß'))
        vbox.addLayout(hbox)
        self._layout.addLayout(vbox, 0, 1)

        hbox = QHBoxLayout()
        self.angleEdit = QLineEdit()
        self.angleDial = QDial()
        self.angleDial.setRange(0, 359)
        self.angleDial.setMaximumWidth(40)
        self.angleDial.setMaximumHeight(40)
        hbox.addWidget(self.angleEdit)
        hbox.addWidget(self.angleDial)
        self._layout.addLayout(hbox, 1, 1)

        self.setLayout(self._layout)




