import logging

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSimpleFillSymbolLayer, QgsSymbolLayerUtils,
                       QgsSvgMarkerSymbolLayer, QgsMarkerLineSymbolLayer, QgsMarkerSymbol, QgsUnitTypes,
                       QgsSimpleLineSymbolLayer, QgsSimpleMarkerSymbolLayer, Qgis, QgsSimpleMarkerSymbolLayerBase)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt, QSize
from sqlalchemy import Column, ForeignKey, Boolean, String, Enum, ARRAY

from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.BPlan.BP_Sonstiges.enums import BP_WegerechtTypen, BP_AbgrenzungenTypen
from SAGisXPlanung.XPlan.core import fallback_renderer, generic_objects_renderer
from SAGisXPlanung.XPlan.mixins import PolygonGeometry, FlaechenschlussObjekt, LineGeometry, MixedGeometry, \
    UeberlagerungsObjekt
from SAGisXPlanung.XPlan.types import Length, GeometryType, XPEnum

logger = logging.getLogger(__name__)


class BP_FlaecheOhneFestsetzung(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Fläche, für die keine geplante Nutzung angegeben werden kann """

    __tablename__ = 'bp_flaeche_ohne_festsetzung'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_flaeche_ohne_festsetzung',
    }

    hidden = True

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer.create({})
        fill.setFillColor(QColor(0, 0, 0))
        fill.setBrushStyle(Qt.BDiagPattern)

        symbol.appendSymbolLayer(fill)
        symbol.setOpacity(0.2)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_Wegerecht(MixedGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Festsetzung von Flächen, die mit Geh-, Fahr-, und Leitungsrechten zugunsten der Allgemeinheit, eines
        Erschließungsträgers, oder eines beschränkten Personenkreises belastet sind (§ 9 Abs. 1 Nr. 21 und Abs. 6
        BauGB). """

    __readonly_columns__ = ['position', 'flaechenschluss']

    __tablename__ = 'bp_wegerecht'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_wegerecht',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    typ = Column(ARRAY(Enum(BP_WegerechtTypen)))
    zugunstenVon = Column(String)
    thema = Column(String)
    breite = Column(Length)
    istSchmal = Column(Boolean)

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        white_marker = QgsSimpleLineSymbolLayer(QColor('#ffffff'))
        white_marker.setWidth(1)
        white_marker.setOffset(0.5)
        white_marker.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        white_marker.setUseCustomDashPattern(True)
        white_marker.setCustomDashVector([3, 1.5])

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.2)
        border.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        symbol.appendSymbolLayer(white_marker)
        symbol.appendSymbolLayer(border)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(48, 48))

    @classmethod
    def hidden_inputs(cls):
        h = super(BP_Wegerecht, cls).hidden_inputs()
        return h + ['flaechenschluss']


class BP_NutzungsartenGrenze(LineGeometry, BP_Objekt):
    """ Festsetzung einer Baulinie (§9 Abs. 1 Nr. 2 BauGB, §22 und 23 BauNVO). """

    __tablename__ = 'bp_nutzungsgrenze'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_nutzungsgrenze',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    typ = Column(XPEnum(BP_AbgrenzungenTypen, include_default=True))

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor('black'))
        line.setWidth(0.1)
        line.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.Circle
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.Circle
        dots_symbol_layer = QgsSimpleMarkerSymbolLayer(shape=shape, color=QColor('black'), size=1)
        dots_symbol_layer.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)

        marker_line = QgsMarkerLineSymbolLayer(interval=3)
        marker_line.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(dots_symbol_layer)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(line)
        symbol.appendSymbolLayer(marker_line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(64, 64))


class BP_GenerischesObjekt(MixedGeometry, BP_Objekt):
    """ Klasse zur Modellierung aller Inhalte des Bebauungsplans,die durch keine andere spezifische XPlanung Klasse
        repräsentiert werden können """

    __tablename__ = 'bp_generisches_objekt'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_generisches_objekt',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return generic_objects_renderer(geom_type)
