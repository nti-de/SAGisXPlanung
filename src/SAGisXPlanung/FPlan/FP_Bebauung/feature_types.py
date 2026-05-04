import logging
import os
from typing import List

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSimpleLineSymbolLayer, QgsLimitedRandomColorRamp,
                       QgsRuleBasedRenderer, QgsUnitTypes, QgsSingleSymbolRenderer, Qgis, QgsMarkerLineSymbolLayer,
                       QgsSimpleMarkerSymbolLayer, QgsSimpleMarkerSymbolLayerBase, QgsMarkerSymbol)
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtCore import Qt

from sqlalchemy import Column, ForeignKey, Float, Enum, String, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import BASE_DIR, XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.XPlan.enums import (XP_AllgArtDerBaulNutzung, XP_BesondereArtDerBaulNutzung, XP_Sondernutzungen,
                                       XP_AbweichungBauNVOTypen)
from SAGisXPlanung.core.mixins.mixins import PolygonGeometry, FlaechenschlussObjekt
from SAGisXPlanung.XPlan.types import ConformityException, GeometryType, XPEnum

logger = logging.getLogger(__name__)


class FP_BebauungsFlaeche(PolygonGeometry, FlaechenschlussObjekt, FP_Objekt):
    """ Teil eines Baugebiets mit einheitlicher Art der baulichen Nutzung. """

    __tablename__ = 'fp_baugebiet'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_baugebiet',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    GFZ = Column(Float)
    GFZmin = Column(Float)
    GFZmax = Column(Float)
    GFZdurchschnittlich = Column(Float, info={'xplan_version': XPlanVersion.SIX})
    BMZ = Column(Float)
    GRZ = Column(Float)
    allgArtDerBaulNutzung = Column(Enum(XP_AllgArtDerBaulNutzung))
    besondereArtDerBaulNutzung = Column(XPEnum(XP_BesondereArtDerBaulNutzung, include_default=True))

    sonderNutzung = Column(ARRAY(Enum(XP_Sondernutzungen)), info={'xplan_version': XPlanVersion.FIVE_THREE})

    rel_sondernutzung = relationship("FP_KomplexeSondernutzung", back_populates="baugebiet",
                                     cascade="all, delete", passive_deletes=True, info={
                                           'xplan_version': XPlanVersion.SIX,
                                           'xplan_attribute': 'sondernutzung'
                                       })

    detaillierteArtDerBaulNutzung_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detaillierteArtDerBaulNutzung = relationship("FP_DetailArtDerBaulNutzung", back_populates="fp_baugebiet",
                                                 foreign_keys=[detaillierteArtDerBaulNutzung_id], info={
                                                     'form-type': 'inline'
                                                 })

    nutzungText = Column(String, info={'xplan_version': XPlanVersion.FIVE_THREE})
    abweichungBauNVO = Column(XPEnum(XP_AbweichungBauNVOTypen, include_default=True),
                              info={'xplan_version': XPlanVersion.SIX})

    @classmethod
    def symbol(cls):
        return QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        color_map = [
            (
                'Wohnbaufläche',
                "(\"besondereArtDerBaulNutzung\" IN ('Kleinsiedlungsgebiet', 'ReinesWohngebiet', 'AllgWohngebiet', 'BesonderesWohngebiet') OR \"allgArtDerBaulNutzung\" = 'WohnBauflaeche') AND (\"flaechenschluss\" = 'True' OR \"flaechenschluss\" IS NULL)",
                QColor('#f4c3b4')),
            (
                'Gemischte Baufläche',
                "(\"besondereArtDerBaulNutzung\" IN ('Dorfgebiet', 'DoerflichesWohngebiet', 'Mischgebiet', 'UrbanesGebiet', 'Kerngebiet') OR \"allgArtDerBaulNutzung\" = 'GemischteBauflaeche') AND (\"flaechenschluss\" = 'True' OR \"flaechenschluss\" IS NULL)",
                QColor('#d5a744')),
            (
                'Gewerbliche Baufläche',
                "(\"besondereArtDerBaulNutzung\" IN ('Gewerbegebiet', 'Industriegebiet') OR \"allgArtDerBaulNutzung\" = 'GewerblicheBauflaeche') AND (\"flaechenschluss\" = 'True' OR \"flaechenschluss\" IS NULL)",
                QColor('#a6a596')),
            (
                'Sonderbaufläche',
                "(\"besondereArtDerBaulNutzung\" IN ('SondergebietErholung', 'SondergebietSonst', 'Wochenendhausgebiet', 'Sondergebiet') OR \"allgArtDerBaulNutzung\" = 'SonderBauflaeche') AND (\"flaechenschluss\" = 'True' OR \"flaechenschluss\" IS NULL)",
                QColor('#fbad03')),
            ('keine Nutzungsangabe', '"allgArtDerBaulNutzung" LIKE \'\'', QgsLimitedRandomColorRamp.randomColors(1)[0])
        ]

        renderer = QgsRuleBasedRenderer(cls.symbol())
        root_rule = renderer.rootRule()

        for label, expression, color_name in color_map:
            rule = root_rule.children()[0].clone()
            rule.setLabel(label)
            rule.setFilterExpression(expression)
            rule.symbol().setColor(color_name)
            root_rule.appendChild(rule)

            line = QgsSimpleLineSymbolLayer.create({})
            line.setColor(QColor(0, 0, 0))
            line.setWidth(0.3)
            line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
            line.setPenStyle(Qt.PenStyle.SolidLine)
            rule.symbol().appendSymbolLayer(line)

        root_rule.removeChildAt(0)
        return renderer

    @classmethod
    def previewIcon(cls):
        return QIcon(os.path.join(BASE_DIR, 'symbole/BP_BesondererNutzungszweckFlaeche/Allgemeine_Wohngebiete.svg'))

    def validate(self):
        if (self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Kleinsiedlungsgebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.ReinesWohngebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.AllgWohngebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.BesonderesWohngebiet.name) and (
                self.allgArtDerBaulNutzung != XP_AllgArtDerBaulNutzung.WohnBauflaeche.name):
            raise ConformityException(f'Wenn <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{self.besondereArtDerBaulNutzung}</b> hat, '
                                      f'muss <code>allgArtDerBaulNutzung</code> den Wert <b>'
                                      f'{XP_AllgArtDerBaulNutzung(1000)}</b> haben',
                                      '5.3.1.1', self.__class__.__name__)

        if (self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Dorfgebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Mischgebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.UrbanesGebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Kerngebiet.name) and (
                self.allgArtDerBaulNutzung != XP_AllgArtDerBaulNutzung.GemischteBauflaeche.name):
            raise ConformityException(f'Wenn <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{self.besondereArtDerBaulNutzung}</b> hat, '
                                      f'muss <code>allgArtDerBaulNutzung</code> den Wert <b>'
                                      f'{XP_AllgArtDerBaulNutzung(2000)}</b> haben',
                                      '5.3.1.1', self.__class__.__name__)

        if (self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Gewerbegebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Industriegebiet.name) and (
                self.allgArtDerBaulNutzung != XP_AllgArtDerBaulNutzung.GewerblicheBauflaeche.name):
            raise ConformityException(f'Wenn <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{self.besondereArtDerBaulNutzung}</b> hat, '
                                      f'muss <code>allgArtDerBaulNutzung</code> den Wert <b>'
                                      f'{XP_AllgArtDerBaulNutzung(3000)}</b> haben',
                                      '5.3.1.1', self.__class__.__name__)

        if (self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Sondergebiet.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.SondergebietErholung.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.SondergebietSonst.name or
            self.besondereArtDerBaulNutzung == XP_BesondereArtDerBaulNutzung.Wochenendhausgebiet.name) and (
                self.allgArtDerBaulNutzung != XP_AllgArtDerBaulNutzung.SonderBauflaeche.name):
            raise ConformityException(f'Wenn <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{self.besondereArtDerBaulNutzung}</b> hat, '
                                      f'muss <code>allgArtDerBaulNutzung</code> den Wert <b>'
                                      f'{XP_AllgArtDerBaulNutzung(4000)}</b> haben',
                                      '5.3.1.1', self.__class__.__name__)

        erholung_sondernutzungen = [XP_Sondernutzungen.Wochendhausgebiet.name, XP_Sondernutzungen.Ferienhausgebiet.name,
                                    XP_Sondernutzungen.Campingplatzgebiet.name, XP_Sondernutzungen.Kurgebiet.name,
                                    XP_Sondernutzungen.SonstSondergebietErholung.name]
        if (self.sonderNutzung and not set(self.sonderNutzung).isdisjoint(set(erholung_sondernutzungen))) and \
                self.besondereArtDerBaulNutzung != XP_BesondereArtDerBaulNutzung.SondergebietErholung.name:
            raise ConformityException(f'Wenn <code>sonderNutzung</code> den Wert <b>{self.sonderNutzung}</b> hat, '
                                      f'muss <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{XP_BesondereArtDerBaulNutzung(2000)}</b> haben',
                                      '5.3.1.2', self.__class__.__name__)
        if (self.sonderNutzung and set(self.sonderNutzung).isdisjoint(set(erholung_sondernutzungen))) and \
                self.besondereArtDerBaulNutzung != XP_BesondereArtDerBaulNutzung.SondergebietSonst.name:
            raise ConformityException(f'Wenn <code>sonderNutzung</code> den Wert <b>{self.sonderNutzung}</b> hat, '
                                      f'muss <code>besondereArtDerBaulNutzung</code> den Wert '
                                      f'<b>{XP_BesondereArtDerBaulNutzung(2100)}</b> haben',
                                      '5.3.1.2', self.__class__.__name__)

        if self.GFZ and (self.GFZmax or self.GFZmin):
            raise ConformityException('Die Attribute <code>GFZmin</code>, <code>GFZmax</code> und <code>GFZ</code>'
                                      'dürfen nur in folgenden Kombinationen belegt werden: '
                                      '<ul><li>GFZ</li><li>GFZmin und GFZmax</li></ul>', '5.3.1.4',
                                      self.__class__.__name__)
        if (self.GFZmin and (self.GFZ or not self.GFZmax)) or (self.GFZmax and (self.GFZ or not self.GFZmin)):
            raise ConformityException('Die Attribute <code>GFZmin</code>, <code>GFZmax</code> und <code>GFZ</code>'
                                      'dürfen nur in folgenden Kombinationen belegt werden: '
                                      '<ul><li>GFZ</li><li>GFZmin und GFZmax</li></ul>', '5.3.1.4',
                                      self.__class__.__name__)


class FP_KeineZentrAbwasserBeseitigungFlaeche(PolygonGeometry, FP_Objekt):
    """ Bauflaeche ohne vorgesehene zentrale Abwasserbeseitigung (§ 5 Abs. 2 Nr. 1 BauGB). """

    __tablename__ = 'fp_keine_zentr_abwasser_beseitigung'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)

        line_layer = QgsSimpleLineSymbolLayer()
        line_layer.setColor(QColor('black'))
        line_layer.setWidth(0.5)
        line_layer.setOutputUnit(QgsUnitTypes.RenderMapUnits)

        if Qgis.versionInt() >= 32400:
            shape = Qgis.MarkerShape.Square
        else:
            shape = QgsSimpleMarkerSymbolLayerBase.Shape.Square
        triangle_symbol_layer = QgsSimpleMarkerSymbolLayer(shape=shape, color=QColor('#fbfd82'), size=8)
        triangle_symbol_layer.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)

        marker_line = QgsMarkerLineSymbolLayer(interval=20)
        marker_line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        marker_line.setOffset(4)
        marker_symbol = QgsMarkerSymbol()
        marker_symbol.deleteSymbolLayer(0)
        marker_symbol.appendSymbolLayer(triangle_symbol_layer)
        marker_line.setSubSymbol(marker_symbol)

        symbol.appendSymbolLayer(line_layer)
        symbol.appendSymbolLayer(marker_line)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        else:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
