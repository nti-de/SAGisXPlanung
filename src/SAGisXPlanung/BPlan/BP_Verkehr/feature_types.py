from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSimpleLineSymbolLayer,
                       QgsSymbolLayerUtils, QgsSimpleFillSymbolLayer, QgsUnitTypes, QgsSymbolLayer,
                       QgsLinePatternFillSymbolLayer, QgsLineSymbol, Qgis, QgsSimpleMarkerSymbolLayerBase,
                       QgsMarkerLineSymbolLayer, QgsMarkerSymbol, QgsSimpleMarkerSymbolLayer, QgsProperty)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize

from sqlalchemy import Integer, Column, ForeignKey, Float, Enum, String

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.BPlan.BP_Verkehr.enums import BP_ZweckbestimmungStrassenverkehr, BP_BereichOhneEinAusfahrtTypen, \
    BP_EinfahrtTypen
from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.enums import XP_Nutzungsform
from SAGisXPlanung.XPlan.mixins import PolygonGeometry, LineGeometry, FlaechenschlussObjekt, PointGeometry
from SAGisXPlanung.XPlan.types import Area, Length, Volume, GeometryType, XPEnum


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class BP_StrassenVerkehrsFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Strassenverkehrsfläche (§ 9 Abs. 1 Nr. 11 und Abs. 6 BauGB) """

    __tablename__ = 'bp_strassenverkehr'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_strassenverkehr',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    MaxZahlWohnungen = Column(Integer)
    MinGRWohneinheit = Column(Area)
    Fmin = Column(Area)
    Fmax = Column(Area)
    Bmin = Column(Length)
    Bmax = Column(Length)
    Tmin = Column(Length)
    Tmax = Column(Length)
    GFZmin = Column(Float)
    GFZmax = Column(Float)
    GFZ = Column(Float)
    GFZ_Ausn = Column(Float)
    GFmin = Column(Area)
    GFmax = Column(Area)
    GF = Column(Area)
    GF_Ausn = Column(Area)
    BMZ = Column(Float)
    BMZ_Ausn = Column(Float)
    BM = Column(Volume)
    BM_Ausn = Column(Volume)
    GRZmin = Column(Float)
    GRZmax = Column(Float)
    GRZ = Column(Float)
    GRZ_Ausn = Column(Float)
    GRmin = Column(Area)
    GRmax = Column(Area)
    GR = Column(Area)
    GR_Ausn = Column(Area)
    Zmin = Column(Integer)
    Zmax = Column(Integer)
    Zzwingend = Column(Integer)
    Z = Column(Integer)
    Z_Ausn = Column(Integer)
    Z_Staffel = Column(Integer)
    Z_Dach = Column(Integer)
    ZUmin = Column(Integer)
    ZUmax = Column(Integer)
    ZUzwingend = Column(Integer)
    ZU = Column(Integer)
    ZU_Ausn = Column(Integer)
    nutzungsform = Column(XPEnum(XP_Nutzungsform, include_default=True))
    # begrenzungslinie [0, *] ?

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#fbdd19'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_StrassenbegrenzungsLinie(LineGeometry, BP_Objekt):
    """ Straßenbegrenzungslinie (§ 9 Abs. 1 Nr. 11 und Abs. 6 BauGB) . """

    __tablename__ = 'bp_strassenbegrenzung'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_strassenbegrenzung',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    bautiefe = Column(Length)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
        symbol.deleteSymbolLayer(0)

        colored_strip = QgsSimpleLineSymbolLayer(QColor('#57e158'))
        colored_strip.setWidth(0.7)
        colored_strip.setOffset(0.3)

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.3)

        symbol.appendSymbolLayer(colored_strip)
        symbol.appendSymbolLayer(border)
        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class BP_VerkehrsflaecheBesondererZweckbestimmung(PolygonGeometry, BP_Objekt):
    """ Verkehrsfläche besonderer Zweckbestimmung (§ 9 Abs. 1 Nr. 11 und Abs. 6 BauGB). """

    __tablename__ = 'bp_verkehr_besonders'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_verkehr_besonders',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    MaxZahlWohnungen = Column(Integer)
    MinGRWohneinheit = Column(Area)
    Fmin = Column(Area)
    Fmax = Column(Area)
    Bmin = Column(Length)
    Bmax = Column(Length)
    Tmin = Column(Length)
    Tmax = Column(Length)
    GFZmin = Column(Float)
    GFZmax = Column(Float)
    GFZ = Column(Float)
    GFZ_Ausn = Column(Float)
    GFmin = Column(Area)
    GFmax = Column(Area)
    GF = Column(Area)
    GF_Ausn = Column(Area)
    BMZ = Column(Float)
    BMZ_Ausn = Column(Float)
    BM = Column(Volume)
    BM_Ausn = Column(Volume)
    GRZmin = Column(Float)
    GRZmax = Column(Float)
    GRZ = Column(Float)
    GRZ_Ausn = Column(Float)
    GRmin = Column(Area)
    GRmax = Column(Area)
    GR = Column(Area)
    GR_Ausn = Column(Area)
    Zmin = Column(Integer)
    Zmax = Column(Integer)
    Zzwingend = Column(Integer)
    Z = Column(Integer)
    Z_Ausn = Column(Integer)
    Z_Staffel = Column(Integer)
    Z_Dach = Column(Integer)
    ZUmin = Column(Integer)
    ZUmax = Column(Integer)
    ZUzwingend = Column(Integer)
    ZU = Column(Integer)
    ZU_Ausn = Column(Integer)
    zweckbestimmung = Column(Enum(BP_ZweckbestimmungStrassenverkehr))
    nutzungsform = Column(XPEnum(XP_Nutzungsform, include_default=True))
    # begrenzungslinie [0, *] ?
    zugunstenVon = Column(String)

    __icon_map__ = [
        ('Parkplatz', '"zweckbestimmung" LIKE \'1000\'', 'Parkierungsflaeche.svg'),
        ('Fußgängerbereich', '"zweckbestimmung" LIKE \'1100\'', 'Fussgaengerbereich.svg'),
        ('Verkehrsberuhigte Zone', '"zweckbestimmung" LIKE \'1200\'', 'VerkehrsberuhigterBereich.svg'),
        ('Sonstiges', '', ''),
    ]

    def layer_fields(self):
        return {
            'zweckbestimmung': self.zweckbestimmung.value if self.zweckbestimmung else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
        }

    @classmethod
    def attributes(cls):
        return ['zweckbestimmung', 'skalierung', 'drehwinkel']

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))
        symbol.appendSymbolLayer(fill)

        line_pattern = QgsLinePatternFillSymbolLayer()
        line_pattern_symbol: QgsLineSymbol = QgsLineSymbol.createSimple({})
        line_pattern_symbol.deleteSymbolLayer(0)
        line_pattern_layer = QgsSimpleLineSymbolLayer(QColor('#fbdd19'))
        line_pattern_layer.setWidth(2)
        line_pattern_layer.setWidthUnit(QgsUnitTypes.RenderMapUnits)
        line_pattern_symbol.appendSymbolLayer(line_pattern_layer)
        line_pattern.setDistanceUnit(QgsUnitTypes.RenderMapUnits)
        line_pattern.setSubSymbol(line_pattern_symbol)
        symbol.appendSymbolLayer(line_pattern)

        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        renderer = RuleBasedSymbolRenderer(cls.__icon_map__, cls.symbol(), 'BP_Verkehr')
        return renderer

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_BereichOhneEinAusfahrtLinie(LineGeometry, BP_Objekt):
    """ Bereich ohne Ein- und Ausfahrt (§ 9 Abs. 1 Nr. 11 und Abs. 6 BauGB). """

    __tablename__ = 'bp_keine_ein_ausfahrt'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_keine_ein_ausfahrt',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    typ = Column(XPEnum(BP_BereichOhneEinAusfahrtTypen, include_default=True))

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor('black'))
        line.setWidth(0.1)
        line.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.SemiCircle
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.SemiCircle
        half_dots_symbol_layer = QgsSimpleMarkerSymbolLayer(shape=shape, color=QColor('black'), size=1)
        half_dots_symbol_layer.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)

        marker_line = QgsMarkerLineSymbolLayer(interval=3)
        marker_line.setOutputUnit(QgsUnitTypes.RenderMetersInMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(half_dots_symbol_layer)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(line)
        symbol.appendSymbolLayer(marker_line)
        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


class BP_EinfahrtPunkt(PointGeometry, BP_Objekt):
    """ Punktförmig abgebildete Einfahrt (§9 Abs. 1 Nr. 11 und Abs. 6 BauGB) """

    __tablename__ = 'bp_einfahrtpunkt'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_einfahrtpunkt',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    typ = Column(XPEnum(BP_EinfahrtTypen, include_default=True))

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
        symbol.deleteSymbolLayer(0)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.Triangle
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.Triangle
        triangle_layer = QgsSimpleMarkerSymbolLayer(shape=shape, color=QColor('black'), size=5)
        triangle_layer.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        angle_prop = QgsProperty.fromField("nordwinkel")
        triangle_layer.setDataDefinedProperty(QgsSymbolLayer.Property.PropertyAngle, angle_prop)

        symbol.appendSymbolLayer(triangle_layer)
        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))
