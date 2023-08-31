import os

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsCentroidFillSymbolLayer, QgsMarkerSymbol, QgsSvgMarkerSymbolLayer,
                       QgsUnitTypes, QgsMapUnitScale, QgsSymbolLayer, QgsProperty)
from qgis.core import QgsRuleBasedRenderer


class RuleBasedSymbolRenderer(QgsRuleBasedRenderer):

    def __init__(self, icon_map, base_symbology: QgsSymbol, category: str, symbol_size=12,
                 geometry_type=QgsWkbTypes.PolygonGeometry):
        super().__init__(QgsSymbol.defaultSymbol(geometry_type))

        root_rule = self.rootRule()
        self.base_symbology = base_symbology
        self.symbol_size = symbol_size
        self.geometry_type = geometry_type

        for label, expression, svg_file in icon_map:
            rule = root_rule.children()[0].clone()
            rule.setLabel(label)
            symbol = self.base_symbology.clone()
            if svg_file:
                rule.setFilterExpression(expression)

                path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'symbole/{category}/{svg_file}'))
                svg_symbol_layer = QgsSvgMarkerSymbolLayer(path, size=self.symbol_size)
                size_prop = QgsProperty.fromExpression(f'"skalierung" * 2 * {self.symbol_size}')
                angle_prop = QgsProperty.fromField("drehwinkel")
                svg_symbol_layer.setDataDefinedProperty(QgsSymbolLayer.Property.PropertySize, size_prop)
                svg_symbol_layer.setDataDefinedProperty(QgsSymbolLayer.Property.PropertyAngle, angle_prop)
                svg_symbol_layer.setOutputUnit(QgsUnitTypes.RenderMapUnits)
                if self.geometry_type == QgsWkbTypes.PointGeometry:
                    symbol.deleteSymbolLayer(0)
                    symbol.appendSymbolLayer(svg_symbol_layer)
                else:
                    svg_marker = QgsCentroidFillSymbolLayer()
                    svg_marker.setPointOnSurface(True)
                    svg_symbol = QgsMarkerSymbol.createSimple({})
                    svg_symbol.deleteSymbolLayer(0)
                    svg_symbol.appendSymbolLayer(svg_symbol_layer)
                    svg_marker.setSubSymbol(svg_symbol)
                    symbol.appendSymbolLayer(svg_marker)
            else:
                rule.setIsElse(True)

            rule.setSymbol(symbol)
            root_rule.appendChild(rule)

        root_rule.removeChildAt(0)
