import logging
from typing import Union

from geoalchemy2 import WKTElement
from qgis.PyQt.QtWidgets import QSizePolicy, QLabel, QCheckBox
from qgis.PyQt import QtWidgets, QtCore
from qgis.gui import QgsMapLayerComboBox, QgsFeaturePickerWidget
from qgis.core import QgsMapLayerProxyModel, QgsGeometry, QgsFeature
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import pyqtSlot, QEvent
from qgis.utils import iface

from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.Tools.IdentifyFeatureTool import IdentifyFeatureTool
from shapely.geometry import MultiPolygon
from shapely.wkt import loads

from SAGisXPlanung.gui.widgets import ElideLabel
from SAGisXPlanung.gui.widgets.QXPlanInputElement import XPlanungInputMeta, QXPlanInputElement

logger = logging.getLogger(__name__)


class QFeatureIdentify(QXPlanInputElement, QtWidgets.QWidget, metaclass=XPlanungInputMeta):
    """
    Widget zum Auswählen von Features eines Polygon-VektorLayers durch Klick auf den Karten-Canvas
    """
    def __init__(self, geometry=None, *args, **kwargs):
        super(QFeatureIdentify, self).__init__(*args, **kwargs)
        self.geometry = geometry

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setSpacing(20)

        self.reconfigure_layout = QtWidgets.QHBoxLayout(self)
        self.geometry_text = ElideLabel()
        self.geometry_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.geometry_text.setStyleSheet('color: #4b5563')
        self.edit_enabled = QCheckBox('Geometrie anpassen')
        self.reconfigure_layout.addWidget(self.geometry_text)
        self.reconfigure_layout.addWidget(self.edit_enabled)
        if self.geometry:
            geom = geometry_from_spatial_element(self.geometry)
            self.geometry_text.setText(geom.asWkt())
            self.verticalLayout.addLayout(self.reconfigure_layout)

        self.geometry_layout = QtWidgets.QVBoxLayout(self)
        self.mMapLayerComboBox = QgsMapLayerComboBox(self)
        self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.geometry_layout.addWidget(self.mMapLayerComboBox)

        self.layer = self.mMapLayerComboBox.currentLayer()
        self.featureGeometry: Union[QgsGeometry, None] = None

        self.horizontalLayout.addItem(QtWidgets.QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.label = QtWidgets.QLabel("Feature:")
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.horizontalLayout.addWidget(self.label)
        self.cbFeature = QgsFeaturePickerWidget(self)
        self.cbFeature.setMaximumWidth(self.cbFeature.sizeHint().width() + 40)
        self.cbFeature.setLayer(self.layer)
        self.cbFeature.featureChanged.connect(self.onFeatureChanged)
        self.cbFeature.setAllowNull(True)
        self.horizontalLayout.addWidget(self.cbFeature)

        self.bIdentify = QtWidgets.QPushButton(self)
        self.bIdentify.setText("")
        self.bIdentify.setToolTip("Geltungsbereich auf Karte wählen")
        self.bIdentify.setIcon(QIcon(':/images/themes/default/mActionIdentifyByPolygon.svg'))
        self.bIdentify.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.bIdentify.clicked.connect(self.identifyFeature)
        self.horizontalLayout.addWidget(self.bIdentify)

        self.geometry_layout.addLayout(self.horizontalLayout)
        self.verticalLayout.addLayout(self.geometry_layout)

        self.mapTool = IdentifyFeatureTool(iface.mapCanvas())
        self.mapTool.setLayer(self.layer)
        self.mapTool.featureIdentified.connect(self.onFeatureIdentified)
        self.mapTool.noFeatureSelected.connect(self.noFeatureSelected)
        self.mMapLayerComboBox.layerChanged.connect(self.onLayerChanged)

        self.bIdentify.setEnabled(self.mMapLayerComboBox.count() != 0)
        self.cbFeature.setEnabled(self.mMapLayerComboBox.count() != 0)
        self.edit_enabled.stateChanged.connect(self.onEditEnabledCheck)

        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """ Wird benötigt, damit der QgsFeaturePicker nicht größer wächst als das Fenster.
            Führt zu leichtem flickern, wenn sich die Größe des Fensters verändert, daher keine optimale Lösung.

            Korrekte Lösung wäre die Nutzung von SizePolicy's der zugrundeliegenden ComboBox, diese ist aber als
            privates Attribut `mComboBox` der Klasse `QgsFeaturePickerWidget` versteckt."""
        if event.type() == QEvent.Resize:
            self.cbFeature.setMaximumWidth(self.mMapLayerComboBox.width() / 2)
            return True
        return False

    @pyqtSlot(int)
    def onEditEnabledCheck(self, state: int):
        self.mMapLayerComboBox.setEnabled(state)
        self.label.setEnabled(state)
        self.bIdentify.setEnabled(state and self.mMapLayerComboBox.count() != 0)
        self.cbFeature.setEnabled(state and self.mMapLayerComboBox.count() != 0)
        if state == 0:
            geom = geometry_from_spatial_element(self.geometry)
            self.geometry_text.setText(geom.asWkt())
        else:
            self.geometry_text.setText(self.featureGeometry.asWkt())

    def value(self):
        try:
            if not self.edit_enabled.isChecked() and self.geometry:
                return self.geometry
            wkt = WKTElement(self.geom().asWkt(), srid=self.srid)
            return wkt
        except AttributeError as e:
            logger.warning(e)

    def setDefault(self, default):
        self.geometry = default
        geom = geometry_from_spatial_element(self.geometry)
        self.geometry_text.setText(geom.asWkt())
        self.verticalLayout.insertLayout(0, self.reconfigure_layout)
        self.onEditEnabledCheck(0)

    @property
    def srid(self) -> int:
        srid = self.layer.crs().postgisSrid()
        return srid

    def geom(self):
        self.layer.removeSelection()
        return self.featureGeometry

    def onFeatureIdentified(self, feature):
        self.cbFeature.setFeature(feature.id())
        self.setInvalid(False)

    def noFeatureSelected(self):
        null_index = self.cbFeature.nullIndex()
        self.cbFeature.setFeature(None)
        # self.cbFeature.mComboBox.setCurrentIndex(null_index) # TODO: return combobox index to null value ?

    @pyqtSlot()
    def identifyFeature(self):
        iface.mapCanvas().setMapTool(self.mapTool)

    @pyqtSlot()
    def onLayerChanged(self):
        self.bIdentify.setEnabled(self.mMapLayerComboBox.count() != 0)
        self.cbFeature.setEnabled(self.mMapLayerComboBox.count() != 0)

        self.layer.removeSelection() if self.layer is not None else 0
        self.layer = self.mMapLayerComboBox.currentLayer()
        self.mapTool.setLayer(self.layer)
        self.cbFeature.setLayer(self.layer)
        self.setInvalid(False)

    def onFeatureChanged(self, feat: QgsFeature):
        self.layer.removeSelection()
        self.layer.select([feat.id()])
        self.featureGeometry = feat.geometry()
        self.setInvalid(False)
        if self.featureGeometry:
            self.geometry_text.setText(self.featureGeometry.asWkt())

    def validate_widget(self, required):
        if self.geometry and not self.edit_enabled.isChecked():
            return True
        feat_id = self.cbFeature.feature().id()
        if feat_id >= 0:
            return True
        self.setInvalid(True)
        return False

    def setInvalid(self, is_invalid):
        if not is_invalid:
            self.setStyleSheet('')
            self.verticalLayout.setContentsMargins(0, 0, 0, 0)
            return
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.setStyleSheet('QFeatureIdentify {background-color: #ffb0b0; border: 1px solid red; border-radius:5px;}')


def load_geometry(feat):
    """
    Konvertiert Geometrie eines QGIS Polygon-Vektorlayer Features in eine entsprechende shapely-Geometrie.

    Parameters
    ----------
    feat: qgis.core.QgsFeature
        Polygon-Vektorlayer
    Returns
    -------
    shapely.geometry.MultiPolygon
    """
    if not feat.geometry():
        return
    geom = feat.geometry()
    geom.convertToStraightSegment()
    feature = loads(geom.asWkt())
    if feature.geom_type == 'MultiPolygon':
        return feature
    return MultiPolygon([feature])
