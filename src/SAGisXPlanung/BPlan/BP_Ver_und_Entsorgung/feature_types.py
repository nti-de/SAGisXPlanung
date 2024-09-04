from typing import List

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSymbolLayerUtils, QgsSimpleFillSymbolLayer, QgsSingleSymbolRenderer)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize

from sqlalchemy import Integer, Column, ForeignKey, Float, Enum, String
from sqlalchemy.orm import relationship, declared_attr

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty, fallback_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungVerEntsorgung
from SAGisXPlanung.core.mixins.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import Area, Length, Volume, GeometryType


class BP_VerEntsorgung(MixedGeometry, BP_Objekt):
    """ Flächen und Leitungen für Versorgungsanlagen, für die Abfallentsorgung und Abwasserbeseitigung sowie für
        Ablagerungen (§9 Abs. 1, Nr. 12, 14 und Abs. 6 BauGB) """

    __tablename__ = 'bp_versorgung'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_versorgung',
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

    @declared_attr
    def zweckbestimmung(cls):
        return XPCol(Enum(XP_ZweckbestimmungVerEntsorgung), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_zweckbestimmung_attr)

    rel_zweckbestimmung = relationship("BP_KomplexeZweckbestVerEntsorgung", back_populates="versorgung",
                                       cascade="all, delete", passive_deletes=True)

    textlicheErgaenzung = XPCol(String, version=XPlanVersion.FIVE_THREE)
    zugunstenVon = Column(String)

    __icon_map__ = [
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
    ]

    def layer_fields(self):
        return {
            'zweckbestimmung': self.zweckbestimmung.value if self.zweckbestimmung else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
        }

    @classmethod
    def import_zweckbestimmung_attr(cls, version):
        if version == XPlanVersion.FIVE_THREE:
            return 'zweckbestimmung'
        else:
            return 'rel_zweckbestimmung'

    @classmethod
    def xp_relationship_properties(cls) -> List[XPRelationshipProperty]:
        return [
            XPRelationshipProperty(rel_name='rel_zweckbestimmung', xplan_attribute='zweckbestimmung',
                                   allowed_version=XPlanVersion.SIX)
        ]

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        fill = QgsSimpleFillSymbolLayer(QColor('#f7ff5a'))

        symbol.appendSymbolLayer(fill)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            renderer = RuleBasedSymbolRenderer(cls.__icon_map__, cls.polygon_symbol(), 'BP_Ver_und_Entsorgung')
            return renderer
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.polygon_symbol(), QSize(16, 16))