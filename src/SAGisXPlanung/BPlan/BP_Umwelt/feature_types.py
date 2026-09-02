from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsUnitTypes, Qgis,
                       QgsSimpleMarkerSymbolLayerBase, QgsMarkerLineSymbolLayer, QgsMarkerSymbol,
                       QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer, QgsProperty)
from qgis.PyQt.QtGui import QColor

from sqlalchemy import Column, ForeignKey, String

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.BPlan.BP_Umwelt.enums import BP_Laermpegelbereich, BP_ZweckbestimmungenTMF
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_ImmissionsschutzTypen, XP_TechnVorkehrungenImmissionsschutz
from SAGisXPlanung.core.mixins.mixins import MixedGeometry, PolygonGeometry, UeberlagerungsObjekt
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
    massgeblAussenLaermpegelTag = Column(Sound, info={'xplan_version': XPlanVersion.SIX})
    massgeblAussenLaermpegelNacht = Column(Sound, info={'xplan_version': XPlanVersion.SIX})

    typ = Column(XPEnum(XP_ImmissionsschutzTypen, include_default=True))
    technVorkehrung = Column(XPEnum(XP_TechnVorkehrungenImmissionsschutz, include_default=True))


    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor('black'))
        line.setWidth(0.2)
        line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMetersInMapUnits)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.ArrowHeadFilled
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.Shape.ArrowHeadFilled
        triangle_symbol_layer = QgsSimpleMarkerSymbolLayer(shape=shape, color=QColor('black'), size=2)
        triangle_symbol_layer.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMetersInMapUnits)
        triangle_symbol_layer.setDataDefinedProperty(
            QgsSimpleMarkerSymbolLayer.PropertyAngle,
            QgsProperty.fromExpression('if(@geometry_ring_num > 0, 90, 270)')
        )

        marker_line = QgsMarkerLineSymbolLayer(interval=5)
        marker_line.setOffset(1)
        marker_line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMetersInMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(triangle_symbol_layer)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(marker_line)
        symbol.appendSymbolLayer(line)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


class BP_TechnischeMassnahmenFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Flaeche fuer technische oder bauliche Massnahmen nach § 9 Abs. 1 Nr. 23 BauGB. """

    __tablename__ = 'bp_technische_massnahmen'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_technische_massnahmen',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(XPEnum(BP_ZweckbestimmungenTMF, include_default=True), nullable=False)
    technischeMassnahme = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
