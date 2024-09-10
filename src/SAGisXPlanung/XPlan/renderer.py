import functools

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsSymbol, QgsWkbTypes, QgsUnitTypes, QgsSingleSymbolRenderer

from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.XPlan.types import GeometryType


def fallback_renderer(renderer_function):
    """
    Decorator for `renderer` classmethod in subclassed of :class:`SAGisXPlanung.XPlan.mixins.RendererMixin`.

    Tries to access renderer from QgsConfig, otherwise falls back to using the renderer_function
    """

    @functools.wraps(renderer_function)
    def wrapper(cls, geom_type=None):
        r = super(cls, cls).renderer(geom_type)
        if r is not None:
            return r

        return renderer_function(cls, geom_type)

    return wrapper


def generic_objects_renderer(geom_type: GeometryType):
    if geom_type is None:
        raise Exception('parameter geom_type should not be None')

    symbol = QgsSymbol.defaultSymbol(geom_type)
    if geom_type == QgsWkbTypes.PointGeometry:
        point = symbol.symbolLayer(0)
        point.setColor(QColor('#cbcbcb'))
        point.setSize(4)
        point.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
    elif geom_type == QgsWkbTypes.LineGeometry:
        line = symbol.symbolLayer(0)
        line.setColor(QColor('#cbcbcb'))
        line.setWidth(0.75)
        line.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
    else:
        fill = symbol.symbolLayer(0)
        fill.setFillColor(QColor('#cbcbcb'))
        fill.setBrushStyle(Qt.BDiagPattern)
        fill.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
    return QgsSingleSymbolRenderer(symbol)


_renderer_expressions = {
    'Gemeinbedarf': [
        ('Öffentliche Verwaltung', '"zweckbestimmung" LIKE \'10%\'', 'Oeffentliche_Verwaltung.svg'),
        ('Bildung und Forschung', '"zweckbestimmung" LIKE \'12%\'', 'Bildung_Forschung.svg'),
        ('Kirchliche Einrichtung', '"zweckbestimmung" LIKE \'14%\'', 'Kirchliche_Einrichtung.svg'),
        ('Soziale Einrichtung', '"zweckbestimmung" LIKE \'16%\'', 'Einrichtung_Soziales.svg'),
        ('Gesundheit', '"zweckbestimmung" LIKE \'18%\'', 'Krankenhaus.svg'),
        ('Kulturelle Einrichtung', '"zweckbestimmung" LIKE \'20%\'', 'Einrichtung_Kultur.svg'),
        ('Sicherheit/Ordnung', '"zweckbestimmung" LIKE \'2400\'', 'Polizei.svg'),
        ('Feuerwehr', '"zweckbestimmung" LIKE \'24000\'', 'Feuerwehr.svg'),
        ('Schutzbauwerk', '"zweckbestimmung" LIKE \'24001\'', 'Schutzbauwerk.svg'),
        ('Justiz', '"zweckbestimmung" LIKE \'24002\'', 'Justizvollzug.svg'),
        ('Post', '"zweckbestimmung" LIKE \'26000\'', 'Post.svg'),
        ('Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ],
    'Versorgung': [
        ('Elektrizität', '"zweckbestimmung" LIKE \'10%\'', 'Elektrizitaet.svg'),
        ('Gas', '"zweckbestimmung" LIKE \'12%\'', 'Gas.svg'),
        ('Waermeversorgung', '"zweckbestimmung" LIKE \'14%\'', 'Fernwaerme.svg'),
        ('Wasser', '"zweckbestimmung" LIKE \'16%\'', 'Wasser.svg'),
        ('Abwasser', '"zweckbestimmung" LIKE \'18%\'', 'Abwasser.svg'),
        ('Abfallentsorgung', '"zweckbestimmung" LIKE \'22%\'', 'Abfall.svg'),
        ('Ablagerung', '"zweckbestimmung" LIKE \'24%\'', 'Ablagerung.svg'),
        ('Erneuerbare Energien', '"zweckbestimmung" LIKE \'2800\'', 'Erneuerbare_Energien.svg'),
        ('Kraft-Wärme-Kopplung', '"zweckbestimmung" LIKE \'3000\'', 'Kraft_Waerme_Kopplung.svg'),
        ('Sonstiges', '', ''),
    ],
    'Gruen': [
        ('Parkanlage', '"zweckbestimmung" LIKE \'10%\'', 'Parkanlage.svg'),
        ('Dauerkleingärten', '"zweckbestimmung" LIKE \'12%\'', 'Dauerkleingärten.svg'),
        ('Sportanlage', '"zweckbestimmung" LIKE \'14%\'', 'Sportplatz.svg'),
        ('Spielplatz', '"zweckbestimmung" LIKE \'16%\'', 'Spielplatz.svg'),
        ('Zeltplatz', '"zweckbestimmung" LIKE \'18%\'', 'Zeltplatz.svg'),
        ('Badeplatz', '"zweckbestimmung" LIKE \'20%\'', 'Badeplatz.svg'),
        ('Friedhof', '"zweckbestimmung" LIKE \'26%\'', 'Friedhof.svg'),
        ('Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ]
}


def icon_renderer(renderer_key: str, symbol: QgsSymbol, icon_category: str,  **kwargs):
    icon_map = _renderer_expressions[renderer_key]
    renderer = RuleBasedSymbolRenderer(icon_map, symbol, icon_category, **kwargs)
    return renderer



