from qgis.core import QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsSimpleLineSymbolLayer, QgsSymbolLayerUtils
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Objekt
from SAGisXPlanung.XPlan.renderer import fallback_renderer
from SAGisXPlanung.core.mixins.mixins import LineGeometry
from SAGisXPlanung.XPlan.types import GeometryType, Angle


BP_ObjektRichtungssektorGrenzeAssoc = Table(
    'assoc_bp_objekt_richtungssektorgrenze', Base.metadata,
    Column('bp_objekt_id', UUID(as_uuid=True), ForeignKey('bp_objekt.id', ondelete='CASCADE')),
    Column('richtungssektorgrenze_id', UUID(as_uuid=True), ForeignKey('bp_richtungssektorgrenze.id', ondelete='CASCADE'))
)

SO_ObjektRichtungssektorGrenzeAssoc = Table(
    'assoc_so_objekt_richtungssektorgrenze', Base.metadata,
    Column('so_objekt_id', UUID(as_uuid=True), ForeignKey('so_objekt.id', ondelete='CASCADE')),
    Column('richtungssektorgrenze_id', UUID(as_uuid=True), ForeignKey('bp_richtungssektorgrenze.id', ondelete='CASCADE'))
)


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
