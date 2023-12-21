from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsSymbol, QgsSimpleFillSymbolLayer, QgsSimpleLineSymbolLayer, QgsUnitTypes, QgsWkbTypes, Qgis,
                       QgsSingleSymbolRenderer, QgsSymbolLayerUtils, QgsMarkerLineSymbolLayer, QgsMarkerSymbol,
                       QgsSimpleMarkerSymbolLayer, QgsSimpleMarkerSymbolLayerBase)

from sqlalchemy import Column, ForeignKey, Enum, String, Boolean, Integer, Float, ARRAY
from sqlalchemy.orm import relationship

from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Objekt
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen import (SO_KlassifizNachSchienenverkehrsrecht,
                                                                          SO_KlassifizNachDenkmalschutzrecht)
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen.enums import SO_ZweckbestimmungStrassenverkehr, \
    SO_StrassenEinteilung, SO_KlassifizWasserwirtschaft
from SAGisXPlanung.XPlan.core import XPCol, fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_Nutzungsform
from SAGisXPlanung.XPlan.mixins import PolygonGeometry, MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, Area, Length, Volume, XPEnum


class SO_Schienenverkehrsrecht(PolygonGeometry, SO_Objekt):
    """ Festlegung nach Schienenverkehrsrecht """

    __tablename__ = 'so_schienenverkehr'
    __mapper_args__ = {
        'polymorphic_identity': 'so_schienenverkehr',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(Enum(SO_KlassifizNachSchienenverkehrsrecht))
    name = Column(String)
    nummer = Column(String)

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#b69ad1'))
        symbol.appendSymbolLayer(fill)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.5)
        line.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        line.setPenStyle(Qt.SolidLine)
        symbol.appendSymbolLayer(line)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(48, 48))


class SO_Denkmalschutzrecht(PolygonGeometry, SO_Objekt):
    """ Festlegung nach Denkmalschutzrecht """

    __tablename__ = 'so_denkmalschutz'
    __mapper_args__ = {
        'polymorphic_identity': 'so_denkmalschutz',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(Enum(SO_KlassifizNachDenkmalschutzrecht))
    weltkulturerbe = Column(Boolean)
    name = Column(String)
    nummer = Column(String)

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.Square
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.Square
        symbol_layer = QgsSimpleMarkerSymbolLayer(shape=shape, color=QColor('#ef0000'), size=2)
        symbol_layer.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        marker_line = QgsMarkerLineSymbolLayer(interval=3)
        marker_line.setOffset(0.8)
        marker_line.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(symbol_layer)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(marker_line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(64, 64))


class SO_Strassenverkehr(MixedGeometry, SO_Objekt):
    """
    Verkehrsfläche besonderer Zweckbestimmung (§ 9 Abs. 1 Nr. 11 und Abs. 6 BauGB), Darstellung von Flächen für den
    überörtlichen Verkehr und für die örtlichen Hauptverkehrszüge ( §5, Abs. 2, Nr. 3 BauGB) sowie Festlegung nach
    Straßenverkehrsrecht
    """

    __tablename__ = 'so_strassenverkehr'
    __mapper_args__ = {
        'polymorphic_identity': 'so_strassenverkehr',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

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

    artDerFestlegung = relationship("SO_KomplexeZweckbestStrassenverkehr", back_populates="strassenverkehr",
                                    cascade="all, delete", passive_deletes=True)
    einteilung = Column(XPEnum(SO_StrassenEinteilung, include_default=True))
    name = Column(String)
    nummer = Column(String)
    istOrtsdurchfahrt = Column(Boolean)
    nutzungsform = Column(Enum(XP_Nutzungsform), nullable=False)
    zugunstenVon = Column(String)
    hatDarstellungMitBesondZweckbest = Column(Boolean, nullable=False)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#fbdd19'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(16, 16))


class SO_Gewaesser(MixedGeometry, SO_Objekt):
    """ Planartübergreifende Klasse zur Abbildung von Gewässern."""

    __tablename__ = 'so_gewaesser'
    __mapper_args__ = {
        'polymorphic_identity': 'so_gewaesser',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = relationship("SO_KomplexeFestlegungGewaesser", back_populates="gewaesser",
                                    cascade="all, delete", passive_deletes=True)

    name = Column(String)
    nummer = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#c1dfea'))
        symbol.appendSymbolLayer(fill)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(16, 16))


class SO_Wasserwirtschaft(MixedGeometry, SO_Objekt):
    """
    Flächen für die Wasserwirtschaft, sowie Flächen für Hochwasserschutzanlagen und für die Regelung des
    Wasserabflusses (§9 Abs. 1 Nr. 16a und 16b BauGB, §5 Abs. 2 Nr. 7 BauGB).
    """

    __tablename__ = 'so_wasserwirtschaft'
    __mapper_args__ = {
        'polymorphic_identity': 'so_wasserwirtschaft',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizWasserwirtschaft, include_default=True))

    __icon_map__ = [
        ('Hochwasserrückhaltebecken', '"artDerFestlegung" LIKE \'HochwasserRueckhaltebecken\'', 'Hochwasserrueckhaltebecken.svg'),
        ('Überschwemmungsgebiet', '"artDerFestlegung" LIKE \'Ueberschwemmgebiet\'', 'Ueberschwemmungsgebiet.svg'),
        ('Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ]

    def layer_fields(self):
        return {
            'artDerFestlegung': self.artDerFestlegung.name if self.artDerFestlegung else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
        }

    @classmethod
    def attributes(cls):
        return ['artDerFestlegung', 'skalierung', 'drehwinkel']

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))
        symbol.appendSymbolLayer(fill)

        blue_strip = QgsSimpleLineSymbolLayer(QColor('#45a1d0'))
        blue_strip.setWidth(5)
        blue_strip.setOffset(2.5)
        blue_strip.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        blue_strip.setPenJoinStyle(Qt.MiterJoin)
        symbol.appendSymbolLayer(blue_strip)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return RuleBasedSymbolRenderer(cls.__icon_map__, cls.polygon_symbol(), 'BP_Wasser', symbol_size=20)
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(16, 16))