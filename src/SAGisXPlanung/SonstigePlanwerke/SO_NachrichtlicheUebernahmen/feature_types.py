from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtGui import QColor
from qgis._core import QgsRuleBasedRenderer, QgsLinePatternFillSymbolLayer, QgsLineSymbol
from qgis.core import (QgsSymbol, QgsSimpleFillSymbolLayer, QgsSimpleLineSymbolLayer, QgsUnitTypes, QgsWkbTypes, Qgis,
                       QgsSingleSymbolRenderer, QgsSymbolLayerUtils, QgsMarkerLineSymbolLayer, QgsMarkerSymbol,
                       QgsSimpleMarkerSymbolLayer, QgsSimpleMarkerSymbolLayerBase, QgsGeometryGeneratorSymbolLayer,
                       QgsMarkerSymbolLayer, QgsProperty, QgsSymbolLayer)

from sqlalchemy import Column, ForeignKey, Enum, String, Boolean, Integer, Float, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Objekt
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen import (SO_KlassifizNachSchienenverkehrsrecht,
                                                                          SO_KlassifizNachDenkmalschutzrecht)
from SAGisXPlanung.SonstigePlanwerke.SO_NachrichtlicheUebernahmen.enums import SO_StrassenEinteilung, \
    SO_KlassifizWasserwirtschaft, SO_KlassifizNachLuftverkehrsrecht, SO_LaermschutzzoneTypen, \
    SO_KlassifizNachSonstigemRecht, SO_KlassifizNachStrassenverkehrsrecht, \
    SO_KlassifizGewaesserv5, SO_KlassifizNachWasserrecht, SO_KlassifizNachBodenschutzrecht, \
    SO_KlassifizBauverbot, SO_RechtlicheGrundlageBauverbot, SO_KlassifizBaubeschraenkung, \
    SO_RechtlicheGrundlageBaubeschraenkung
from SAGisXPlanung.XPlan.core import LayerPriorityType, xp_version
from SAGisXPlanung.XPlan.renderer import fallback_renderer, icon_renderer
from SAGisXPlanung.XPlan.enums import XP_Nutzungsform
from SAGisXPlanung.core.mixins.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, Area, Length, Volume, XPEnum
from SAGisXPlanung.XPlan.enums import XP_EigentumsartWald, XP_ZweckbestimmungWald, XP_WaldbetretungTyp


class SO_Schienenverkehrsrecht(MixedGeometry, SO_Objekt):
    """ Festlegung nach Schienenverkehrsrecht """

    __tablename__ = 'so_schienenverkehr'
    __mapper_args__ = {
        'polymorphic_identity': 'so_schienenverkehr',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(Enum(SO_KlassifizNachSchienenverkehrsrecht))

    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizNachSchienenverkehrsrecht",
                                          back_populates="so_schienenverkehr", foreign_keys=[detailArtDerFestlegung_id],
                                          info={
                                              'form-type': 'inline'
                                          })
    name = Column(String)
    nummer = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#b69ad1'))
        symbol.appendSymbolLayer(fill)

        line = QgsSimpleLineSymbolLayer.create({})
        line.setColor(QColor(0, 0, 0))
        line.setWidth(0.5)
        line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        line.setPenStyle(Qt.PenStyle.SolidLine)
        symbol.appendSymbolLayer(line)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(48, 48))


class SO_Bodenschutzrecht(MixedGeometry, SO_Objekt):
    """ Festlegung nach Bodenschutzrecht """

    __tablename__ = 'so_bodenschutz'
    __mapper_args__ = {
        'polymorphic_identity': 'so_bodenschutz',
    }
    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizNachBodenschutzrecht, include_default=True))

    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizNachBodenschutzrecht", back_populates="so_bodenschutz",
                                          foreign_keys=[detailArtDerFestlegung_id], info={
                                              'form-type': 'inline'
                                          })

    istVerdachtsflaeche = Column(Boolean)
    name = Column(String)
    nummer = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.5)
        border.setOffset(0.25)
        border.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        border.setPenJoinStyle(Qt.PenJoinStyle.MiterJoin)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.Cross
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.Shape.Cross

        cross_symbol = QgsSimpleMarkerSymbolLayer(
            shape=shape,
            color=QColor('#000000'),
            strokeColor=QColor('#000000'),
            size=5
        )
        cross_symbol.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMetersInMapUnits)
        cross_symbol.setVerticalAnchorPoint(QgsMarkerSymbolLayer.VerticalAnchorPoint.Bottom)
        cross_symbol.setStrokeWidth(0.5)
        cross_symbol.setAngle(45)

        marker_line = QgsMarkerLineSymbolLayer(interval=10)
        marker_line.setAverageAngleLength(0)
        marker_line.setOffset(2)
        marker_line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMetersInMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(cross_symbol)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(border)
        symbol.appendSymbolLayer(marker_line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


class SO_Denkmalschutzrecht(MixedGeometry, SO_Objekt):
    """ Festlegung nach Denkmalschutzrecht """

    __tablename__ = 'so_denkmalschutz'
    __mapper_args__ = {
        'polymorphic_identity': 'so_denkmalschutz',
    }
    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(Enum(SO_KlassifizNachDenkmalschutzrecht))

    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizNachDenkmalschutzrecht", back_populates="so_denkmalschutz",
                                          foreign_keys=[detailArtDerFestlegung_id], info={
                                              'form-type': 'inline'
                                          })

    weltkulturerbe = Column(Boolean)
    name = Column(String)
    nummer = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.Square
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.Shape.Square
        symbol_layer = QgsSimpleMarkerSymbolLayer(shape=shape, color=QColor('#ef0000'), size=2)
        symbol_layer.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        marker_line = QgsMarkerLineSymbolLayer(interval=3)
        marker_line.setOffset(0.8)
        marker_line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(symbol_layer)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(marker_line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('Denkmalschutz', QgsSymbol.defaultSymbol(geom_type),
                                 'SO_NachrichtlicheUebernahmen', geometry_type=geom_type,
                                 scale_factor=1)
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(64, 64))


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class SO_Strassenverkehrsrecht(MixedGeometry, SO_Objekt):
    """
    Festlegung nach Straßenverkehrsrecht
    """

    __tablename__ = 'so_strassenverkehrsrecht'
    __mapper_args__ = {
        'polymorphic_identity': 'so_strassenverkehrsrecht',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizNachStrassenverkehrsrecht, include_default=True))

    name = Column(String)
    nummer = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#fbdd19'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')


@xp_version(versions=[XPlanVersion.SIX])
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
    nutzungsform = Column(XPEnum(XP_Nutzungsform, include_default=True))
    zugunstenVon = Column(String)
    hatDarstellungMitBesondZweckbest = Column(Boolean, nullable=False)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#fbdd19'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    def besondere_zweckbest_polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))
        symbol.appendSymbolLayer(fill)

        line_pattern = QgsLinePatternFillSymbolLayer()
        line_pattern_symbol: QgsLineSymbol = QgsLineSymbol.createSimple({})
        line_pattern_symbol.deleteSymbolLayer(0)
        line_pattern_layer = QgsSimpleLineSymbolLayer(QColor('#fbdd19'))
        line_pattern_layer.setWidth(2)
        line_pattern_layer.setWidthUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        line_pattern_symbol.appendSymbolLayer(line_pattern_layer)
        line_pattern.setDistanceUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        line_pattern.setSubSymbol(line_pattern_symbol)
        symbol.appendSymbolLayer(line_pattern)

        return symbol


    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            default_symbol = cls.polygon_symbol()
            root_rule = QgsRuleBasedRenderer.Rule(None)
            besondere_zweckbest_rule = QgsRuleBasedRenderer.Rule(cls.besondere_zweckbest_polygon_symbol())
            besondere_zweckbest_rule.setFilterExpression('"hatDarstellungMitBesondZweckbest" = \'True\'')
            besondere_zweckbest_rule.setLabel('Besondere Zweckbestimmung')
            root_rule.appendChild(besondere_zweckbest_rule)

            default_rule = QgsRuleBasedRenderer.Rule(default_symbol)
            default_rule.setIsElse(True)
            default_rule.setLabel('Default')

            root_rule.appendChild(default_rule)
            return QgsRuleBasedRenderer(root_rule)
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

    artDerFestlegung = Column(XPEnum(SO_KlassifizGewaesserv5, include_default=True), info={
        'xplan_version': XPlanVersion.FIVE_THREE,
    })
    rel_artDerFestlegung = relationship("SO_KomplexeFestlegungGewaesser", back_populates="gewaesser",
                                        cascade="all, delete", passive_deletes=True, info={
                                            'xplan_version': XPlanVersion.SIX,
                                            'xplan_attribute': 'artDerFestlegung'
                                        })

    name = Column(String)
    nummer = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#c1dfea'))
        symbol.appendSymbolLayer(fill)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(16, 16))


@xp_version(versions=[XPlanVersion.SIX])
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

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))
        fill_prop = QgsProperty.fromExpression(f"if (\"flaechenschluss\" = 'True', '#ffffff', 'transparent')")
        fill.setDataDefinedProperty(QgsSymbolLayer.Property.PropertyFillColor, fill_prop)
        symbol.appendSymbolLayer(fill)

        blue_strip = QgsGeometryGeneratorSymbolLayer.create({})
        blue_strip.setSymbolType(Qgis.SymbolType.Fill)
        blue_strip.setColor(QColor('#45a1d0'))
        blue_strip.setStrokeColor(QColor('#45a1d0'))
        blue_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        blue_strip.setGeometryExpression("difference($geometry, buffer(wave($geometry, 20, 1.5), -4))")
        sub_symbol = blue_strip.subSymbol()
        fill_layer = sub_symbol.symbolLayer(0)
        fill_layer.setStrokeColor(QColor('#45a1d0'))
        fill_layer.setStrokeWidth(0)
        symbol.appendSymbolLayer(blue_strip)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('Wasserwirtschaft', QgsSymbol.defaultSymbol(geom_type),
                                 'BP_Wasser', geometry_type=geom_type, scale_factor=4)
        else:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


class SO_Wasserrecht(MixedGeometry, SO_Objekt):
    """
    Festlegung nach Wasserhaushaltsgesetz (WHG).
    """

    __tablename__ = 'so_wasserrecht'
    __mapper_args__ = {
        'polymorphic_identity': 'so_wasserrecht',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizNachWasserrecht, include_default=True))

    istNatuerlichesUberschwemmungsgebiet = Column(Boolean)
    name = Column(String)
    nummer = Column(String)

    @classmethod
    def line_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.LineGeometry)
        symbol.deleteSymbolLayer(0)

        blue_outline = QgsSimpleLineSymbolLayer(QColor('#377ded'))
        symbol.appendSymbolLayer(blue_outline)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.LineGeometry:
            return QgsSingleSymbolRenderer(cls.line_symbol())
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


class SO_Luftverkehrsrecht(MixedGeometry, SO_Objekt):
    """
    Festlegung nach Luftverkehrsrecht.
    """

    __tablename__ = 'so_luftverkehr'
    __mapper_args__ = {
        'polymorphic_identity': 'so_luftverkehr',
    }

    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizNachLuftverkehrsrecht, include_default=True))

    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizNachLuftverkehrsrecht", back_populates="so_luftverkehr",
                                          foreign_keys=[detailArtDerFestlegung_id], info={
                                              'form-type': 'inline'
                                          })

    name = Column(String)
    nummer = Column(String)
    laermschutzzone = Column(XPEnum(SO_LaermschutzzoneTypen, include_default=True))

    __icon_map__ = [
        ('Flughafen', '"artDerFestlegung" LIKE \'1000\'', 'Flughafen.svg'),
        ('Landeplatz', '"artDerFestlegung" LIKE \'2000\'', 'Landeplatz.svg'),
        ('Segelfluggelände', '"artDerFestlegung" LIKE \'3000\'', 'Segelflugflaeche.svg'),
        ('Hubschrauberlandeplatz', '"artDerFestlegung" LIKE \'4000\'', 'Hubschrauberlandeplatz.svg'),
        ('Sonstiges', '"zweckbestimmung" LIKE \'\'', ''),
    ]

    def layer_fields(self):
        return {
            'artDerFestlegung': self.artDerFestlegung.value if self.artDerFestlegung else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
        }

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))
        symbol.appendSymbolLayer(fill)

        colored_strip = QgsSimpleLineSymbolLayer(QColor('#c052c2'))
        colored_strip.setWidth(5)
        colored_strip.setOffset(2.5)
        colored_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        colored_strip.setPenJoinStyle(Qt.PenJoinStyle.MiterJoin)
        symbol.appendSymbolLayer(colored_strip)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return RuleBasedSymbolRenderer(cls.__icon_map__, cls.polygon_symbol(), 'SO_SonstigeGebiete')
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(16, 16))


class SO_SonstigesRecht(MixedGeometry, SO_Objekt):
    """ Sonstige Festlegung """

    __tablename__ = 'so_sonstiges_recht'
    __mapper_args__ = {
        'polymorphic_identity': 'so_sonstiges_recht',
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    nummer = Column(String)
    artDerFestlegung = Column(XPEnum(SO_KlassifizNachSonstigemRecht, include_default=True))

    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizNachSonstigemRecht", back_populates="so_sonstiges_recht",
                                          foreign_keys=[detailArtDerFestlegung_id], info={
                                              'form-type': 'inline'
                                          })

    name = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class SO_Bauverbotszone(MixedGeometry, SO_Objekt):
    """ Bereich, in denen Verbote/Beschraenkungen fuer bauliche Anlagen bestehen (v5.3). """

    __tablename__ = 'so_bauverbotszone'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizBauverbot, include_default=True))

    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizBauverbot", back_populates="so_bauverbotszone",
                                          foreign_keys=[detailArtDerFestlegung_id], info={
                                              'form-type': 'inline'
                                          })

    rechtlicheGrundlage = Column(XPEnum(SO_RechtlicheGrundlageBauverbot, include_default=True))
    name = Column(String)
    nummer = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


@xp_version(versions=[XPlanVersion.SIX])
class SO_Baubeschraenkung(MixedGeometry, SO_Objekt):
    """ Bereich, in denen Verbote/Beschraenkungen fuer bauliche Anlagen bestehen (v6.0). """

    __tablename__ = 'so_baubeschraenkung'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(SO_KlassifizBaubeschraenkung, include_default=True))

    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizBaubeschraenkung", back_populates="so_baubeschraenkung",
                                          foreign_keys=[detailArtDerFestlegung_id], info={
                                              'form-type': 'inline'
                                          })

    rechtlicheGrundlage = Column(XPEnum(SO_RechtlicheGrundlageBaubeschraenkung, include_default=True))
    name = Column(String)
    nummer = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


class SO_Forstrecht(MixedGeometry, SO_Objekt):
    """ Festlegung nach Forstrecht. """

    __tablename__ = 'so_forstrecht'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("so_objekt.id", ondelete='CASCADE'), primary_key=True)

    artDerFestlegung = Column(XPEnum(XP_EigentumsartWald, include_default=True))

    detailArtDerFestlegung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailArtDerFestlegung = relationship("SO_DetailKlassifizNachForstrecht", back_populates="so_forstrecht",
                                          foreign_keys=[detailArtDerFestlegung_id], info={
                                              'form-type': 'inline'
                                          })

    funktion = Column(ARRAY(Enum(XP_ZweckbestimmungWald)))
    betreten = Column(ARRAY(Enum(XP_WaldbetretungTyp)))

    name = Column(String)
    nummer = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
