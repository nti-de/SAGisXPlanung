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
    if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
        point = symbol.symbolLayer(0)
        point.setColor(QColor('#cbcbcb'))
        point.setSize(4)
        point.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMetersInMapUnits)
    elif geom_type == QgsWkbTypes.GeometryType.LineGeometry:
        line = symbol.symbolLayer(0)
        line.setColor(QColor('#cbcbcb'))
        line.setWidth(0.75)
        line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMetersInMapUnits)
    else:
        fill = symbol.symbolLayer(0)
        fill.setFillColor(QColor('#cbcbcb'))
        fill.setBrushStyle(Qt.BrushStyle.BDiagPattern)
        fill.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMetersInMapUnits)
    return QgsSingleSymbolRenderer(symbol)


_renderer_expressions = {
    'Gemeinbedarf': [
        ('Öffentliche Verwaltung', '"zweckbestimmung" LIKE \'10%\'', 'Oeffentliche_Verwaltung.svg'),
        ('Bildung und Forschung', '"zweckbestimmung" LIKE \'12%\'', 'Bildung_Forschung.svg'),
        ('Kirchliche Einrichtung', '"zweckbestimmung" LIKE \'14%\'', 'Kirchliche_Einrichtung.svg'),
        ('Soziale Einrichtung', '"zweckbestimmung" LIKE \'1600\'', 'Einrichtung_Soziales.svg'),
        ('Soziale Einrichtung (Kinder)', '"zweckbestimmung" LIKE \'16000\'', 'Einrichtung_Kinder.svg'),
        ('Soziale Einrichtung (Jugendliche)', '"zweckbestimmung" LIKE \'16001\'', 'Einrichtung_Jugendliche.svg'),
        ('Gesundheit', '"zweckbestimmung" LIKE \'18%\'', 'Gesundheit.svg'),
        ('Kulturelle Einrichtung', '"zweckbestimmung" LIKE \'20%\'', 'Einrichtung_Kultur.svg'),
        ('Sportanlage', '"zweckbestimmung" LIKE \'22%\'', 'Anlage_Sportanlage.svg'),
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
        ('Parkanlage', '"zweckbestimmung" LIKE \'%Parkanlage%\'', 'Parkanlage.svg'),
        ('Dauerkleingärten', '"zweckbestimmung" LIKE \'Dauerkleingaerten\'', 'Dauerkleingärten.svg'),
        ('Sportanlage', '"zweckbestimmung" LIKE \'Sportplatz\'', 'Sportplatz.svg'),
        ('Spielplatz', '"zweckbestimmung" LIKE \'Spielplatz\'', 'Spielplatz.svg'),
        ('Zeltplatz', '"zweckbestimmung" LIKE \'Zeltplatz\' or "zweckbestimmung" LIKE \'Campingplatz\'', 'Zeltplatz.svg'),
        ('Badeplatz/Freibad', '"zweckbestimmung" LIKE \'BadeplatzFreibad\'', 'Freibad.svg'),
        ('Friedhof', '"zweckbestimmung" LIKE \'Friedhof\'', 'Friedhof.svg'),
        ('Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ],
    'SpielSportanlage': [
        ('Sportanlage', '"zweckbestimmung" LIKE \'Sportanlage\'', 'Anlage_Sportanlage.svg'),
        ('Spielanlage', '"zweckbestimmung" LIKE \'Spielanlage\'', 'Anlage_Spielanlage.svg'),
        ('Gemischt/Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ],
    'Denkmalschutz': [
        ('Ensemble', '"artDerFestlegung" = \'DenkmalschutzEnsemble\'', 'Denkmalschutz_Ensemble.svg'),
        ('Einzelanlage', '"artDerFestlegung" = \'DenkmalschutzEinzelanlage\'', 'Denkmalschutz_Einzelanlagen.svg'),
        ('Sonstiges', '"artDerFestlegung" LIKE \'\'', ''),
    ],
    'Kennzeichnung': [
        ('Schadstoffbelasteter Boden', '"zweckbestimmung" = \'SchadstoffBelastBoden\'', 'Kennzeichnung_Schadstoffe.svg'),
        ('Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ],
    'Straßenverkehr': [
        ('Parkplatz', '"zweckbestimmung" LIKE \'Parkplatz\' OR "zweckbestimmung" LIKE \'Parkierungsflaeche\'', 'Parkierungsflaeche.svg'),
        ('Fußgängerbereich', '"zweckbestimmung" LIKE \'Fussgaengerbereich\'', 'Fussgaengerbereich.svg'),
        ('Verkehrsberuhigte Zone', '"zweckbestimmung" LIKE \'VerkehrsberuhigterBereich\'', 'VerkehrsberuhigterBereich.svg'),
        ('Radweg', '"zweckbestimmung" LIKE \'Radweg\'', 'Radweg.svg'),
        ('Fuß- und Radweg', '"zweckbestimmung" LIKE \'RadGehweg\'', 'Fuss_Radweg.svg'),
        ('Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ],
    'Naturschutz': [
        ('Naturschutzgebiet', '"artDerFestlegung" LIKE \'Naturschutzgebiet\'', 'Schutzgebiet_Naturschutzgebiet_SW.svg'),
        ('Nationalpark', '"artDerFestlegung" LIKE \'Nationalpark\'', 'Schutzgebiet_Nationalpark_SW.svg'),
        ('Landschaftsschutzgebiet', '"artDerFestlegung" LIKE \'Landschaftsschutzgebiet\'', 'Schutzgebiet_Landschaftsschutzgebiet_SW.svg'),
        ('Naturpark', '"artDerFestlegung" LIKE \'Naturpark\'', 'Schutzgebiet_Naturpark_SW.svg'),
        ('Naturdenkmal', '"artDerFestlegung" LIKE \'Naturdenkmal\'', 'Schutzgebiet_Naturdenkmal_SW.svg'),
        ('Geschützter Landschaftsbestandteil', '"artDerFestlegung" LIKE \'GeschuetzterLandschaftsbestandteil\'', 'Schutzgebiet_Geschuetzter_Landschaftsbestandteil_SW.svg'),
        ('Sonstiges', '"artDerFestlegung" LIKE \'\'', ''),
    ],
    'Wasserwirtschaft': [
        ('Hochwasser-Rückhaltebecken', '"zweckbestimmung" = \'HochwasserRueckhaltebecken\'', 'Hochwasserrueckhaltebecken.svg'),
        ('Überschwemmungsgebiet', '"zweckbestimmung" = \'Ueberschwemmgebiet\'', 'Ueberschwemmungsgebiet.svg'),
        ('Regen-Rückhaltebecken', '"zweckbestimmung" = \'RegenRueckhaltebecken\'', 'Regenrueckhaltebecken.svg'),
        ('Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ],
}


def icon_renderer(renderer_key: str, symbol: QgsSymbol, icon_category: str,  **kwargs):
    icon_map = _renderer_expressions[renderer_key]
    renderer = RuleBasedSymbolRenderer(icon_map, symbol, icon_category, **kwargs)
    return renderer



