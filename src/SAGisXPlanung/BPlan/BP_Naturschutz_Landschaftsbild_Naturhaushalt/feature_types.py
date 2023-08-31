import os

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSymbolLayerUtils, QgsSimpleLineSymbolLayer,
                       QgsUnitTypes, QgsSimpleFillSymbolLayer, QgsSimpleMarkerSymbolLayerBase,
                       QgsSimpleMarkerSymbolLayer, QgsMarkerLineSymbolLayer, QgsMarkerSymbol)
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtCore import QSize, Qt

from sqlalchemy import Integer, Column, ForeignKey, Enum, String, Boolean
from sqlalchemy.orm import relationship

from SAGisXPlanung import BASE_DIR, XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.RuleBasedSymbolRenderer import RuleBasedSymbolRenderer
from SAGisXPlanung.XPlan.core import XPCol
from SAGisXPlanung.XPlan.enums import XP_ABEMassnahmenTypen, XP_AnpflanzungBindungErhaltungsGegenstand, XP_SPEZiele
from SAGisXPlanung.XPlan.mixins import PointGeometry, PolygonGeometry, MixedGeometry
from SAGisXPlanung.XPlan.types import Length, GeometryType


class BP_AnpflanzungBindungErhaltung(MixedGeometry, BP_Objekt):
    """ Festsetzung des Anpflanzens von Bäumen, Sträuchern und sonstigen Bepflanzungen;
        Festsetzung von Bindungen für Bepflanzungen und für die Erhaltung von Bäumen, Sträuchern und sonstigen
        Bepflanzungen sowie von Gewässern; (§9 Abs. 1 Nr. 25 und Abs. 4 BauGB) """

    __tablename__ = 'bp_pflanzung'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_pflanzung',
    }
    __rule_based_renderers__ = [QgsWkbTypes.PointGeometry]

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    massnahme = Column(Enum(XP_ABEMassnahmenTypen))
    gegenstand = Column(Enum(XP_AnpflanzungBindungErhaltungsGegenstand))
    kronendurchmesser = Column(Length)
    pflanztiefe = Column(Length)
    istAusgleich = Column(Boolean)
    baumArt = XPCol(String, version=XPlanVersion.FIVE_THREE)
    pflanzenArt = XPCol(String, version=XPlanVersion.SIX)
    mindesthoehe = Column(Length)
    anzahl = Column(Integer)

    __icon_map__ = [
        ('Anpflanzen: Bäume', '"gegenstand" LIKE \'1%\' and "massnahme" LIKE \'2000\'', 'Anpflanzen_Baum.svg'),
        ('Anpflanzen: Sträucher/Hecken', '"gegenstand" LIKE \'2%\' and "massnahme" LIKE \'2000\'', 'Anpflanzen_Straeucher.svg'),
        ('Anpflanzen: Sonstiges', '"gegenstand" LIKE \'3%\' and "massnahme" LIKE \'2000\'', 'Anpflanzen_Sonstiges.svg'),
        ('Erhaltung: Bäume', '"gegenstand" LIKE \'1%\' and "massnahme" LIKE \'1000\'', 'Erhaltung_Baum.svg'),
        ('Erhaltung: Sträucher/Hecken', '"gegenstand" LIKE \'2%\' and "massnahme" LIKE \'1000\'', 'Erhaltung_Straeucher.svg'),
        ('Erhaltung: Sonstiges', '"gegenstand" LIKE \'3%\' and "massnahme" LIKE \'1000\'', 'Erhaltung_Sonstiges.svg'),
    ]

    def layer_fields(self):
        return {
            'massnahme': self.massnahme.value if self.massnahme else '',
            'gegenstand': self.gegenstand.value if self.gegenstand else '',
            'skalierung': self.skalierung if self.skalierung else '',
            'drehwinkel': self.drehwinkel if self.drehwinkel else ''
        }

    @classmethod
    def attributes(cls):
        return ['massnahme', 'gegenstand', 'skalierung', 'drehwinkel']

    @classmethod
    def point_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
        return symbol

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        symbol.setClipFeaturesToExtent(False)

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.3)
        border.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        border.setPenJoinStyle(Qt.MiterJoin)

        green_fill = QgsSimpleFillSymbolLayer(QColor('#16ce3c'))

        shape = QgsSimpleMarkerSymbolLayerBase.Circle
        circle_symbol = QgsSimpleMarkerSymbolLayer(shape=shape, color=QColor('#000000'), size=1.5)
        circle_symbol.setFillColor(QColor(Qt.transparent))
        circle_symbol.setStrokeWidth(0.3)
        circle_symbol.setStrokeWidthUnit(QgsUnitTypes.RenderMapUnits)
        circle_symbol.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        marker_line = QgsMarkerLineSymbolLayer(interval=3)
        marker_line.setOffset(1.5)
        marker_line.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(circle_symbol)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(border)
        symbol.appendSymbolLayer(green_fill)
        symbol.appendSymbolLayer(marker_line)
        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        if geom_type == QgsWkbTypes.PointGeometry:
            renderer = RuleBasedSymbolRenderer(cls.__icon_map__, cls.point_symbol(),
                                               'BP_Naturschutz_Landschaftsbild_Naturhaushalt',
                                               geometry_type=QgsWkbTypes.PointGeometry)
            return renderer
        elif geom_type == QgsWkbTypes.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            raise NotImplementedError('Liniengeometrien nicht umgesetzt')

    @classmethod
    def previewIcon(cls):
        return QIcon(os.path.abspath(os.path.join(BASE_DIR, 'symbole/BP_Naturschutz_Landschaftsbild_Naturhaushalt/Anpflanzen_Baum.svg')))


class BP_SchutzPflegeEntwicklungsFlaeche(PolygonGeometry, BP_Objekt):
    """ Umgrenzung von Flächen für Maßnahmen zum Schutz, zur Pflege und zur Entwicklung von Natur und Landschaft
        (§9 Abs. 1 Nr. 20 und Abs. 4 BauGB) """

    __tablename__ = 'bp_schutzflaeche'
    __mapper_args__ = {
        'polymorphic_identity': 'bp_schutzflaeche',
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    ziel = Column(Enum(XP_SPEZiele))
    sonstZiel = Column(String)
    massnahme = relationship("XP_SPEMassnahmenDaten", back_populates="bp_schutzflaeche", cascade="all, delete",
                             passive_deletes=True)
    istAusgleich = Column(Boolean)
    refMassnahmenText = relationship("XP_ExterneReferenz", back_populates="bp_schutzflaeche_massnahme",
                                     cascade="all, delete", passive_deletes=True, uselist=False,
                                     foreign_keys='XP_ExterneReferenz.bp_schutzflaeche_massnahme_id')
    refLandschaftsplan = relationship("XP_ExterneReferenz", back_populates="bp_schutzflaeche_plan",
                                      cascade="all, delete", passive_deletes=True, uselist=False,
                                      foreign_keys='XP_ExterneReferenz.bp_schutzflaeche_plan_id')

    @classmethod
    def symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        symbol.setClipFeaturesToExtent(False)

        border = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        border.setWidth(0.5)
        border.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        border.setPenJoinStyle(Qt.MiterJoin)

        green_strip = QgsSimpleLineSymbolLayer(QColor(22, 206, 60))
        green_strip.setWidth(3)
        green_strip.setOffset(1.75)
        green_strip.setOutputUnit(QgsUnitTypes.RenderMapUnits)
        green_strip.setPenJoinStyle(Qt.MiterJoin)

        symbol.appendSymbolLayer(border)
        symbol.appendSymbolLayer(green_strip)
        return symbol

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(48, 48))
