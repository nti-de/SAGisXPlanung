from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSymbolLayerUtils, QgsSimpleFillSymbolLayer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize

from sqlalchemy import Column, ForeignKey, Enum

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.XPlan.core import xp_version, fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungGewaesser
from SAGisXPlanung.XPlan.mixins import PolygonGeometry, FlaechenschlussObjekt
from SAGisXPlanung.XPlan.types import GeometryType


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class BP_GewaesserFlaeche(PolygonGeometry, FlaechenschlussObjekt, BP_Objekt):
    """ Festsetzungen von öffentlichen und privaten Grünflächen (§ 9, Abs. 1, Nr. 15 BauGB)."""

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
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#c1dfea'))
        symbol.appendSymbolLayer(fill)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        renderer = RuleBasedSymbolRenderer(cls.__icon_map__, cls.symbol(), 'BP_Wasser', symbol_size=20)
        return renderer

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))