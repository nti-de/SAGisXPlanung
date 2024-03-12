from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsUnitTypes, Qgis,
                       QgsSimpleMarkerSymbolLayerBase, QgsMarkerLineSymbolLayer, QgsMarkerSymbol,
                       QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

from sqlalchemy import Column, ForeignKey, String

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.BPlan.BP_Umwelt.enums import BP_Laermpegelbereich
from SAGisXPlanung.XPlan.core import fallback_renderer, XPCol
from SAGisXPlanung.XPlan.enums import XP_ImmissionsschutzTypen, XP_TechnVorkehrungenImmissionsschutz
from SAGisXPlanung.XPlan.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum, Sound


class BP_Immissionsschutz(MixedGeometry, BP_Objekt):
    """ Festsetzung einer von der Bebauung freizuhaltenden Schutzfläche und ihre Nutzung, sowie einer Fläche für
    besondere Anlagen und Vorkehrungen zum Schutz vor schädlichen Umwelteinwirkungen und sonstigen Gefahren im Sinne des
    Bundes-Immissionsschutzgesetzes sowie die zum Schutz vor solchen Einwirkungen oder zur Vermeidung oder Minderung
    solcher Einwirkungen zu treffenden baulichen und sonstigen technischen Vorkehrungen (§9, Abs. 1, Nr. 24 BauGB).
    Die Klasse wird innbesondere benutzt, um 5 db Lärmpegelbereiche gemäß DIN-4109:2016-1, oder alternativ Maßgebliche
    (1 db) Außenlärmpegelbereiche gemäß DIN 4109-1: 2018-01 festzusetzen """

    __tablename__ = 'bp_immissionsschutz'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_immissionsschutz',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    nutzung = Column(String)
    laermpegelbereich = Column(XPEnum(BP_Laermpegelbereich, include_default=True))
    massgeblAussenLaermpegelTag = XPCol(Sound, version=XPlanVersion.SIX)
    massgeblAussenLaermpegelNacht = XPCol(Sound, version=XPlanVersion.SIX)

    typ = Column(XPEnum(XP_ImmissionsschutzTypen, include_default=True))
    technVorkehrung = Column(XPEnum(XP_TechnVorkehrungenImmissionsschutz, include_default=True))


    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.5)
        border.setOffset(0.25)
        border.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        border.setPenJoinStyle(Qt.MiterJoin)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.ArrowHeadFilled
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.ArrowHeadFilled
        arrowhead_symbol = QgsSimpleMarkerSymbolLayer(shape=shape, color=QColor('#000000'), size=6)
        arrowhead_symbol.setAngle(270)
        arrowhead_symbol.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)

        marker_line = QgsMarkerLineSymbolLayer(interval=10)
        marker_line.setAverageAngleLength(0)
        marker_line.setOffset(3.5)
        marker_line.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.setAngle(270)
        marker_symbol.appendSymbolLayer(arrowhead_symbol)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(border)
        symbol.appendSymbolLayer(marker_line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
