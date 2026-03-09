from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSymbolLayerUtils, QgsSimpleFillSymbolLayer, QgsUnitTypes,
                       QgsGeometryGeneratorSymbolLayer, Qgis, QgsSingleSymbolRenderer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize

from sqlalchemy import Column, ForeignKey, Enum
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.BPlan.BP_Wasser.codelists import BP_DetailZweckbestWasserwirtschaftCodelistAssoc
from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGewaesser, XP_ZweckbestimmungWasserwirtschaft
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry, FlaechenschlussObjekt
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class BP_GewaesserFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Festsetzung neuer Wasserflächen nach §9 Abs. 1 Nr. 16a BauGB. """

    __tablename__ = 'bp_gewaesser'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_gewaesser',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(Enum(XP_ZweckbestimmungGewaesser))

    __icon_map__ = [
        ('Hafen/Sportboothafen', '"zweckbestimmung" LIKE \'10%\'', 'Hafen.svg'),
        ('Sonstiges Gewässer', '"zweckbestimmung" LIKE \'\'', ''),
    ]

    def layer_fields(self):
        return {
            'zweckbestimmung': self.zweckbestimmung.value if self.zweckbestimmung else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
        }

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#c1dfea'))
        symbol.appendSymbolLayer(fill)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        renderer = RuleBasedSymbolRenderer(cls.__icon_map__, cls.symbol(), 'BP_Wasser')
        return renderer

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class BP_WasserwirtschaftsFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """
    Flächen für die Wasserwirtschaft (§9 Abs. 1 Nr. 16a BauGB), sowie Flächen für Hochwasserschutz-anlagen und
    für die Regelung des Wasserabflusses (§9 Abs. 1 Nr. 16b BauGB).
    """

    __tablename__ = 'bp_wasserwirtschaft'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_wasserwirtschaft',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(XPEnum(XP_ZweckbestimmungWasserwirtschaft, include_default=True))

    detaillierteZweckbestimmung = relationship(
        'BP_DetailZweckbestWasserwirtschaft',
        back_populates='codelist_user',
        secondary=BP_DetailZweckbestWasserwirtschaftCodelistAssoc,
        info={
            'form-type': 'inline'
        }
    )


    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#ffffff'))
        symbol.appendSymbolLayer(fill)

        blue_strip = QgsGeometryGeneratorSymbolLayer.create({})
        blue_strip.setSymbolType(Qgis.SymbolType.Fill)
        blue_strip.setColor(QColor('#45a1d0'))
        blue_strip.setStrokeColor(QColor('#45a1d0'))
        blue_strip.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        blue_strip.setGeometryExpression("difference($geometry, buffer(wave($geometry, 20, 1.5), -2))")
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
        raise Exception('parameter geometryType should only be PolygonGeometry, but is: ' + str(geom_type))