import logging
import os
from typing import List

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSimpleLineSymbolLayer, QgsLimitedRandomColorRamp, QgsRuleBasedRenderer,
                       QgsUnitTypes)
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtCore import Qt

from sqlalchemy import Column, ForeignKey, Float, Enum, String, ARRAY
from sqlalchemy.orm import declared_attr, relationship

from SAGisXPlanung import BASE_DIR, XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty, fallback_renderer
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
    GFZdurchschnittlich = XPCol(Float, version=XPlanVersion.SIX)
    BMZ = Column(Float)
    GRZ = Column(Float)
    allgArtDerBaulNutzung = Column(Enum(XP_AllgArtDerBaulNutzung))
    besondereArtDerBaulNutzung = Column(XPEnum(XP_BesondereArtDerBaulNutzung, include_default=True))

    @declared_attr
    def sonderNutzung(cls):
        return XPCol(ARRAY(Enum(XP_Sondernutzungen)), version=XPlanVersion.FIVE_THREE,
                     import_attr=cls.import_sondernutzung_attr)

    rel_sondernutzung = relationship("FP_KomplexeSondernutzung", back_populates="baugebiet",
                                     cascade="all, delete", passive_deletes=True)

    nutzungText = XPCol(String, version=XPlanVersion.FIVE_THREE)
    abweichungBauNVO = XPCol(XPEnum(XP_AbweichungBauNVOTypen, include_default=True), version=XPlanVersion.SIX)

    @classmethod
    def import_sondernutzung_attr(cls, version):
        if version == XPlanVersion.FIVE_THREE:
            return 'sonderNutzung'
        else:
            return 'rel_sondernutzung'

    @classmethod
    def xp_relationship_properties(cls) -> List[XPRelationshipProperty]:
        return [
            XPRelationshipProperty(rel_name='rel_sondernutzung', xplan_attribute='sondernutzung',
                                   allowed_version=XPlanVersion.SIX)
        ]

    @classmethod
    def symbol(cls):
        return QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        color_map = [
            ('Wohngebiet', '"allgArtDerBaulNutzung" LIKE \'WohnBauflaeche\'', QColor('#fb6868')),
            ('Gemischtes Gebiet', '"allgArtDerBaulNutzung" LIKE \'GemischteBauflaeche\'', QColor('#e48700')),
            ('Gewerbliches Gebiet', '"allgArtDerBaulNutzung" LIKE \'GewerblicheBauflaeche\'', QColor('#cfcbcb')),
            ('Sondergebiet', '"allgArtDerBaulNutzung" LIKE \'SonderBauflaeche\'', QColor('#f8c85c')),
            ('keine Nutzung', '"allgArtDerBaulNutzung" LIKE \'\'', QgsLimitedRandomColorRamp.randomColors(1)[0])
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
            line.setOutputUnit(QgsUnitTypes.RenderMapUnits)
            line.setPenStyle(Qt.SolidLine)
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
