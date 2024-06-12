import logging
import math
import sys
from typing import Union

from geoalchemy2 import WKTElement
from qgis.PyQt.QtWidgets import QSizePolicy, QCheckBox
from qgis.PyQt import QtWidgets, QtCore
from qgis.gui import QgsMapLayerComboBox, QgsFeaturePickerWidget
from qgis.core import QgsMapLayerProxyModel, QgsGeometry, QgsFeature, QgsDataSourceUri
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import pyqtSlot, QEvent
from qgis.utils import iface

from SAGisXPlanung.GML.geometry import geometry_from_spatial_element, geometry_drop_z
from SAGisXPlanung.Tools.IdentifyFeatureTool import IdentifyFeatureTool

from SAGisXPlanung.gui.widgets import ElideLabel
from SAGisXPlanung.gui.widgets.QXPlanInputElement import XPlanungInputMeta, QXPlanInputElement

FETCH_LIMIT_WEB = 1000

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
        self.set_fetch_limit()
        self.cbFeature.setFetchGeometry(False)  # don't require to fetch geometry
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
            logger.error(e)

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
        self.set_fetch_limit()
        self.cbFeature.setLayer(self.layer)
        self.setInvalid(False)

    def onFeatureChanged(self, feat: QgsFeature):
        self.layer.removeSelection()
        if math.isclose(-sys.maxsize, feat.id()):
            return
        self.layer.select([feat.id()])
        self.featureGeometry = geometry_drop_z(self.layer.getGeometry(feat.id()))
        self.setInvalid(False)
        if self.featureGeometry:
            self.geometry_text.setText(self.featureGeometry.asWkt())

    def validate_widget(self, required):
        if self.geometry and not self.edit_enabled.isChecked():
            return True
        feat_id = self.cbFeature.feature().id()
        if feat_id >= 0 and self.featureGeometry is not None:
            return True
        if self.layer is None:
            self.error_message = 'Kein Layer gewählt...'
        elif not self.featureGeometry:
            self.error_message = f'Gewähltes Objekt konnte nicht geladen werden. '
            source_uri = QgsDataSourceUri(self.layer.source())
            if source_uri.hasParam('url'):
                self.error_message += f'Es können nur {FETCH_LIMIT_WEB} von {self.layer.featureCount()} Geometrien abgerufen werden. '
        self.setInvalid(True)
        return False

    def set_fetch_limit(self):
        if not self.layer:
            return

        source_uri = QgsDataSourceUri(self.layer.source())
        if source_uri.hasParam('url'):
            self.cbFeature.setFetchLimit(FETCH_LIMIT_WEB)  # low fetch limit for layers via web
        else:
            self.cbFeature.setFetchLimit(0)  # no fetch limit for local files, they are loading fast
