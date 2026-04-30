from qgis._core import QgsGeometryGeneratorSymbolLayer
from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsUnitTypes, Qgis,
                       QgsSimpleMarkerSymbolLayerBase, QgsMarkerLineSymbolLayer, QgsMarkerSymbol,
                       QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

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

        jagged_strip = QgsGeometryGeneratorSymbolLayer.create({})
        jagged_strip.setSymbolType(Qgis.SymbolType.Fill)
        jagged_strip.setColor(QColor('black'))
        jagged_strip.setStrokeColor(QColor('black'))
        jagged_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        jagged_strip.setGeometryExpression("difference($geometry, triangular_wave($geometry, 8, 2))")
        sub_symbol = jagged_strip.subSymbol()
        fill_layer = sub_symbol.symbolLayer(0)
        fill_layer.setStrokeWidth(0)
        fill_layer.setStrokeColor(QColor('black'))
        fill_layer.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        symbol.appendSymbolLayer(jagged_strip)

        simple_line = QgsSimpleLineSymbolLayer.create({})
        symbol.appendSymbolLayer(simple_line)

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
