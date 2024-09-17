import os
from uuid import uuid4

from geoalchemy2 import Geometry, WKTElement
from geoalchemy2.shape import to_shape
from sqlalchemy import Column, ForeignKey, String, Integer, Boolean, ARRAY, Enum, Float, event, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from qgis.core import (QgsGeometry, QgsAnnotationPointTextItem, QgsAnnotationLayer, QgsTextFormat, QgsUnitTypes,
                       QgsTextBackgroundSettings, QgsPointXY, QgsCoordinateReferenceSystem, QgsProject)

from SAGisXPlanung import Base, BASE_DIR
from SAGisXPlanung.BuildingTemplateItem import BuildingTemplateCellDataType
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.core.mixins.mixins import ElementOrderMixin, RelationshipMixin, MapCanvasMixin, PointGeometry
from SAGisXPlanung.XPlan.types import Angle


class XP_AbstraktesPraesentationsobjekt(RelationshipMixin, ElementOrderMixin, Base):
    """ Abstrakte Basisklasse für alle Präsentationsobjekt

        Notiz: alle Präsentationsobjektklassen weichen von der vorgegebenen Vererbungshierarchie von XPlanung ab.
        Die vorgegebenen Klassen sind in diesem XPlanung-Modul recht unpassend strukturiert. Viele Attribute werden
        in den Basisklassen nicht verwendet oder sind einfach nicht benötigt. Außerdem sind die Vererbungshierarchien
        zu tief angelegt, was die Struktur der Anwendung verkompliziert. Dadurch entstehen unnötig viele Tabellen in
        der Datenbank. (bspw. durch 4-fache Vererbung: PO -> TPO -> PTO -> Nutzungschablone)"""

    __tablename__ = 'xp_po'

    __LAYER_PRIORITY__ = LayerPriorityType.Top

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    gehoertZuBereich_id = Column(UUID(as_uuid=True), ForeignKey('xp_bereich.id', ondelete='CASCADE'))
    gehoertZuBereich = relationship('XP_Bereich', back_populates='praesentationsobjekt')

    dientZurDarstellungVon_id = Column(UUID(as_uuid=True), ForeignKey('xp_objekt.id', ondelete='CASCADE'))
    dientZurDarstellungVon = relationship('XP_Objekt', back_populates='wirdDargestelltDurch')

    type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'xp_po',
        'polymorphic_on': type
    }
    __readonly_columns__ = ['position', 'skalierung', 'drehwinkel']

    @classmethod
    def avoid_export(cls):
        return ['gehoertZuBereich', 'dientZurDarstellungVon']

    def displayName(self):
        return self.__class__.__name__

    def geometry(self) -> QgsGeometry:
        return geometry_from_spatial_element(self.position)

    def setGeometry(self, geom: QgsGeometry, srid: int = None):
        if srid is None and self.position is None:
            raise Exception('geometry needs a srid')
        self.position = WKTElement(geom.asWkt(), srid=srid or self.position.srid)

    def srs(self):
        return QgsCoordinateReferenceSystem(f'EPSG:{self.position.srid}')

    def remove_from_canvas(self):
        """ Removes this annotation item from canvas if it is currently visible """
        layer: QgsAnnotationLayer = MapLayerRegistry().layerByFeature(str(self.id))
        if not layer:
            return

        for item_id in layer.items().keys():
            id_prop = layer.customProperties().value(f'xplanung/feat-{item_id}')
            if id_prop == str(self.id):
                layer.removeItem(item_id)
                break


@event.listens_for(XP_AbstraktesPraesentationsobjekt, 'after_delete', propagate=True)
def receive_after_delete(mapper, connection, target: XP_AbstraktesPraesentationsobjekt):
    """ Removes annotation item from canvas after deletion """
    target.remove_from_canvas()


class XP_PPO(PointGeometry, MapCanvasMixin, XP_AbstraktesPraesentationsobjekt):
    """ Punktförmiges Präsentationsobjekt """

    __tablename__ = 'xp_ppo'
    __mapper_args__ = {
        'polymorphic_identity': 'xp_ppo',
    }
    __default_size__ = 24

    id = Column(ForeignKey("xp_po.id", ondelete='CASCADE'), primary_key=True)

    position = Column(Geometry(geometry_type='POINT'))
    drehwinkel = Column(Angle, default=0)
    skalierung = Column(Float, default=0.5)

    symbol_path = Column(String)

    def asFeature(self, fields=None):
        shape = to_shape(self.position)
        point = QgsPointXY(shape.x, shape.y)
        item = QgsAnnotationPointTextItem('', point)

        label_format = QgsTextFormat()
        label_format.setSizeUnit(QgsUnitTypes.RenderMapUnits)
        label_format.setSize(self.__default_size__ * self.skalierung * 2.0)

        s = QgsTextBackgroundSettings()
        s.setEnabled(True)
        path = os.path.abspath(os.path.join(BASE_DIR, self.symbol_path))
        s.setSvgFile(path)
        s.setType(QgsTextBackgroundSettings.ShapeSVG)

        label_format.setBackground(s)
        item.setFormat(label_format)
        item.setAngle(self.drehwinkel)
        return item

    @classmethod
    def asLayer(cls, srid, plan_xid, name=None, geom_type=None):
        layer = QgsAnnotationLayer('Symbole', QgsAnnotationLayer.LayerOptions(QgsProject.instance().transformContext()))
        layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{srid}'))
        layer.setCustomProperty("skipMemoryLayersCheck", 1)
        layer.setCustomProperty('xplanung/type', cls.__name__)
        layer.setCustomProperty('xplanung/plan-xid', str(plan_xid))
        # TODO: properties are not persistent, see: https://github.com/qgis/QGIS/issues/47463
        return layer

    @classmethod
    def avoid_export(cls):
        return super(XP_PPO, cls).avoid_export() + ['symbol_path']

    @classmethod
    def hidden_inputs(cls):
        return ['symbol_path']


@event.listens_for(XP_PPO, 'after_update')
def update_map_display(mapper, connection, xp_ppo: XP_PPO):
    """Update map symbol if attribute 'symbol_path' changes """
    # detect if symbol path changed
    history = inspect(xp_ppo).attrs.symbol_path.history
    if not history.has_changes():
        return

    layer: QgsAnnotationLayer = MapLayerRegistry().layerByFeature(str(xp_ppo.id))
    if not layer:
        return

    for item_id, item in layer.items().items():
        id_prop = layer.customProperties().value(f'xplanung/feat-{item_id}')
        if id_prop == str(xp_ppo.id):
            background_setting = item.format().background()
            path = os.path.abspath(os.path.join(BASE_DIR, xp_ppo.symbol_path))
            background_setting.setSvgFile(path)

            item.format().setBackground(background_setting)

            layer.triggerRepaint()
            break


class XP_PTO(PointGeometry, MapCanvasMixin, XP_AbstraktesPraesentationsobjekt):
    """ Textförmiges Präsentationsobjekt mit punktförmiger Festlegung der Textposition """

    __tablename__ = 'xp_pto'
    __mapper_args__ = {
        'polymorphic_identity': 'xp_pto',
    }
    __default_size__ = 6

    id = Column(ForeignKey("xp_po.id", ondelete='CASCADE'), primary_key=True)

    schriftinhalt = Column(String)

    skalierung = Column(Float, default=0.5)
    position = Column(Geometry(geometry_type='POINT'))
    drehwinkel = Column(Angle, default=0)

    def asFeature(self, fields=None):
        shape = to_shape(self.position)
        point = QgsPointXY(shape.x, shape.y)
        item = QgsAnnotationPointTextItem(self.schriftinhalt, point)

        label_format = QgsTextFormat()
        label_format.setSizeUnit(QgsUnitTypes.RenderMapUnits)
        label_format.setSize(self.__default_size__ * self.skalierung * 2.0)

        item.setFormat(label_format)
        item.setAngle(self.drehwinkel)
        return item

    @classmethod
    def asLayer(cls, srid, plan_xid, name=None, geom_type=None):
        layer = QgsAnnotationLayer('Text', QgsAnnotationLayer.LayerOptions(QgsProject.instance().transformContext()))
        layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{srid}'))
        layer.setCustomProperty("skipMemoryLayersCheck", 1)
        layer.setCustomProperty('xplanung/type', cls.__name__)
        layer.setCustomProperty('xplanung/plan-xid', str(plan_xid))
        # TODO: properties are not persistent, see: https://github.com/qgis/QGIS/issues/47463
        return layer


class XP_Nutzungsschablone(PointGeometry, XP_AbstraktesPraesentationsobjekt):
    """ Modelliert eine Nutzungsschablone. Die darzustellenden Attributwerte werden zeilenweise in die
        Nutzungsschablone geschrieben """

    def __init__(self):
        super(XP_Nutzungsschablone, self).__init__()

        self.hidden = True
        self.data_attributes = BuildingTemplateCellDataType.as_default()

    def set_defaults(self, row_count=3):
        self.data_attributes = BuildingTemplateCellDataType.as_default(row_count)

    __tablename__ = 'xp_nutzungsschablone'
    __mapper_args__ = {
        'polymorphic_identity': 'xp_nutzungsschablone',
    }

    id = Column(ForeignKey("xp_po.id", ondelete='CASCADE'), primary_key=True)

    skalierung = Column(Float, default=0.5)
    position = Column(Geometry(geometry_type='POINT'))
    drehwinkel = Column(Angle, default=0)

    spaltenAnz = Column(Integer, nullable=False, default=2)
    zeilenAnz = Column(Integer, nullable=False, default=3)

    # non xplanung attributes
    hidden = Column(Boolean)
    data_attributes = Column(ARRAY(Enum(BuildingTemplateCellDataType)))

    @classmethod
    def avoid_export(cls):
        return super(XP_Nutzungsschablone, cls).avoid_export() + ['hidden', 'data_attributes']
