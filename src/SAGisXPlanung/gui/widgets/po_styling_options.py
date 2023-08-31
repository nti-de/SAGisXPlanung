
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

        # listeners
        self.angleEdit.editingFinished.connect(self.onAngleTextEdited)
        self.angleDial.valueChanged.connect(self.onDialValueChanged)
        self.sizeSlider.valueChanged.connect(self.onSizeSliderChanged)

    def setSize(self, scale: float):
        self.sizeSlider.setValue(scale * (99 - 1) + 1)

    def setAngle(self, angle: int):
        if angle > 360 or angle < 0:
            raise ValueError('Angle has to be between 0 and 360')
        self.angleEdit.setText(f'{angle}°')
        self.angleDial.setValue(angle)

    @pyqtSlot()
    def onAngleTextEdited(self):
        text = self.angleEdit.text().replace('°', '')
        self.angleDial.setValue(int(text))

    @pyqtSlot(int)
    def onDialValueChanged(self, value: int):
        self.angleEdit.setText(f'{value}°')

        self.styleChanged.emit(self.ATTRIBUTE_ANGLE, value)

    @pyqtSlot(int)
    def onSizeSliderChanged(self, value: int):
        scale = (value - 1) / (99 - 1)
        self.styleChanged.emit(self.ATTRIBUTE_SIZE, scale)



