from qgis.core import QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSimpleLineSymbolLayer, QgsSymbolLayerUtils
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.core.mixins.mixins import LineGeometry, PointGeometry, PolygonGeometry, UeberlagerungsObjekt
from SAGisXPlanung.XPlan.types import GeometryType, Angle


class BP_RichtungssektorGrenze(LineGeometry, BP_Objekt):
    """ Linienhafte Repräsentation einer Richtungssektor-Grenze. """

    __tablename__ = 'bp_richtungssektorgrenze'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    winkel = Column(Angle)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.LineGeometry)
        symbol.deleteSymbolLayer(0)

        line = QgsSimpleLineSymbolLayer(QColor('#1f1f1f'))
        line.setWidth(0.6)
        symbol.appendSymbolLayer(line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))

    @classmethod
    def avoid_export(cls):
        return []


class BP_ZusatzkontingentLaerm(PointGeometry, BP_Objekt):
    """ Parametrische Spezifikation zusaetzlicher Laermemissionskontingente. """

    __tablename__ = 'bp_zusatzkontingent_laerm'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    bezeichnung = Column(String)
    richtungssektor = relationship('BP_Richtungssektor', back_populates='zusatzkontingent',
                                   cascade='all, delete', passive_deletes=True)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PointGeometry)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))

    @classmethod
    def avoid_export(cls):
        return []


class BP_ZusatzkontingentLaermFlaeche(PolygonGeometry, UeberlagerungsObjekt, BP_Objekt):
    """ Flaechenhafte Spezifikation zusaetzlicher Laermemissionskontingente. """

    __tablename__ = 'bp_zusatzkontingent_laerm_flaeche'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("bp_objekt.id", ondelete='CASCADE'), primary_key=True)

    bezeichnung = Column(String)
    richtungssektor = relationship('BP_Richtungssektor', back_populates='zusatzkontingentFlaeche',
                                   cascade='all, delete', passive_deletes=True, uselist=False)

    @classmethod
    def symbol(cls):
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.GeometryType.PolygonGeometry)
        symbol.deleteSymbolLayer(0)
        line = QgsSimpleLineSymbolLayer(QColor('#1f1f1f'))
        line.setPenStyle(Qt.PenStyle.DashLine)
        symbol.appendSymbolLayer(line)
        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(cls.symbol())

    @classmethod
    def previewIcon(cls):
        return QgsSymbolLayerUtils.symbolPreviewIcon(cls.symbol(), QSize(16, 16))

    @classmethod
    def avoid_export(cls):
        return []
