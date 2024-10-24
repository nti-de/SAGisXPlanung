import logging
from typing import List
from uuid import uuid4

from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QIcon

from geoalchemy2 import Geometry, WKTElement

from sqlalchemy import Column, String, Date, Integer, Float, Enum, ForeignKey, event, CheckConstraint, Computed
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship

from qgis.core import (QgsCoordinateReferenceSystem, QgsGeometry, QgsVectorLayer, QgsFeatureRequest, edit,
                       QgsSymbolLayerUtils, QgsRuleBasedRenderer)

from .XP_Praesentationsobjekte.feature_types import XP_Nutzungsschablone
from .conversions import XP_Rechtscharakter_EnumType
from .core import XPCol, LayerPriorityType, XPRelationshipProperty
from .enums import XP_BedeutungenBereich, XP_Rechtsstand, XP_Rechtscharakter
from SAGisXPlanung import Base, XPlanVersion
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element, correct_geometry
from SAGisXPlanung.config import export_version
from SAGisXPlanung.core.mixins.mixins import ElementOrderMixin, PolygonGeometry, MapCanvasMixin, RelationshipMixin, RendererMixin
from .types import LargeString, Angle, Length, GeometryType
from ..MapLayerRegistry import MapLayerRegistry

logger = logging.getLogger(__name__)


class XP_Plan(RendererMixin, PolygonGeometry, ElementOrderMixin, RelationshipMixin, MapCanvasMixin, Base):
    """ Abstrakte Oberklasse für alle Klassen raumbezogener Pläne. """

    __tablename__ = 'xp_plan'

    __readonly_columns__ = ['raeumlicherGeltungsbereich']

    __LAYER_PRIORITY__ = LayerPriorityType.Top
    __geometry_column_name__ = 'raeumlicherGeltungsbereich'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String(50))

    name = Column(String, nullable=False, doc='Name')
    nummer = Column(String, doc='Nummer')
    internalId = Column(String, doc='Interner Idenfikator')
    beschreibung = Column(LargeString, doc='Beschreibung')
    kommentar = Column(LargeString, doc='Kommentar')
    technHerstellDatum = Column(Date, doc='Datum der technischen Ausfertigung')
    genehmigungsDatum = Column(Date, doc='Datum der Genehmigung')
    untergangsDatum = Column(Date, doc='Untergangsdatum')

    aendert = relationship("XP_VerbundenerPlan", back_populates="aendert_verbundenerPlan", cascade="all, delete",
                           passive_deletes=True, foreign_keys='XP_VerbundenerPlan.aendert_verbundenerPlan_id')
    wurdeGeaendertVon = relationship("XP_VerbundenerPlan", back_populates="wurdeGeaendertVon_verbundenerPlan",
                                     cascade="all, delete", passive_deletes=True,
                                     foreign_keys='XP_VerbundenerPlan.wurdeGeaendertVon_verbundenerPlan_id')

    erstellungsMassstab = Column(Integer, doc='Erstellungsmaßstab')
    bezugshoehe = Column(Float, doc='Standard Bezugshöhe')
    hoehenbezug = XPCol(String(), doc='Höhenbezug', version=XPlanVersion.SIX)
    technischerPlanersteller = Column(String, doc='Technischer Planersteller')
    raeumlicherGeltungsbereich = Column(Geometry(),
                                        CheckConstraint('st_dimension("raeumlicherGeltungsbereich")) = 2',
                                                        name='check_geometry_type'),
                                        nullable=False, doc='Geltungsbereich')

    verfahrensMerkmale = relationship("XP_VerfahrensMerkmal", back_populates="plan", cascade="all, delete",
                                      passive_deletes=True)
    externeReferenz = relationship("XP_SpezExterneReferenz", back_populates="plan", cascade="all, delete",
                                   passive_deletes=True)

    _sa_search_col = Column(TSVECTOR, Computed("""to_tsvector('german',
            xp_plan.id::text || ' ' ||
            xp_plan.name || ' ' ||
            coalesce(xp_plan.type, '') || ' ' ||
            coalesce(xp_plan.nummer, '') || ' ' ||
            coalesce(xp_plan."internalId", '') || ' ' ||
            coalesce(xp_plan.beschreibung, '') || ' ' ||
            coalesce(xp_plan.kommentar, '') || ' ' ||
            coalesce(immutable_to_char(xp_plan."technHerstellDatum"), '') || ' ' ||
            coalesce(immutable_to_char(xp_plan."genehmigungsDatum"), '') || ' ' ||
            coalesce(immutable_to_char(xp_plan."untergangsDatum"), '') || ' ' ||
            coalesce(xp_plan."erstellungsMassstab"::text, '') || ' ' ||
            coalesce(xp_plan.bezugshoehe::text, '') || ' ' ||
            coalesce(xp_plan."technischerPlanersteller", '')
        )"""))

    __mapper_args__ = {
        "polymorphic_identity": "xp_plan",
        "polymorphic_on": type,
    }

    @classmethod
    def xp_relationship_properties(cls) -> List[XPRelationshipProperty]:
        return [
            XPRelationshipProperty(rel_name='wurdeGeaendertVon', xplan_attribute='wurdeGeaendertVon',
                                   allowed_version=XPlanVersion.FIVE_THREE),
            XPRelationshipProperty(rel_name='aendert', xplan_attribute='aendert',
                                   allowed_version=XPlanVersion.FIVE_THREE),
        ]

    @classmethod
    def avoid_export(cls):
        return ['plangeber_id', '_sa_search_col']

    @classmethod
    def hidden_inputs(cls):
        return ['_sa_search_col']

    def displayName(self):
        return 'Geltungsbereich'

    def srs(self) -> QgsCoordinateReferenceSystem:
        return QgsCoordinateReferenceSystem(f'EPSG:{self.raeumlicherGeltungsbereich.srid}')

    def geometry(self) -> QgsGeometry:
        return geometry_from_spatial_element(self.raeumlicherGeltungsbereich)

    def setGeometry(self, geom: QgsGeometry):
        self.raeumlicherGeltungsbereich = WKTElement(geom.asWkt(), srid=self.raeumlicherGeltungsbereich.srid)

    def toCanvas(self, layer_group, plan_xid=None):
        MapLayerRegistry().remove_canvas_items(str(self.id))

        super(XP_Plan, self).toCanvas(layer_group, plan_xid)

    def enforceFlaechenschluss(self):
        """ Abstrakte Methode zum Erzwingen des Flächenschluss. Muss in jeder konkreten Klasse implementiert werden."""
        raise NotImplementedError()

    @classmethod
    @property
    def bereich(cls):
        raise NotImplementedError()

    def edit_widget(self):
        from SAGisXPlanung.gui.widgets.QXPlanTabWidget import QXPlanTabWidget

        tabs = QXPlanTabWidget(self.__class__)

        def iterate_relations(obj, parent_class=None, page=0):
            for attr in obj.__class__.element_order(version=export_version()):
                attribute_value = getattr(obj, attr)
                if attribute_value is None:
                    continue

                rel = next((obj for obj in obj.relationships() if obj[0] == attr), None)
                if rel is not None:
                    class_type = rel[1].mapper.class_
                    if class_type == parent_class or (
                            parent_class is not None and issubclass(parent_class, class_type)):
                        continue
                    if hasattr(obj.__class__, '__avoidRelation__') and rel[0] in obj.__class__.__avoidRelation__:
                        continue
                    if class_type == XP_Objekt or issubclass(class_type, XP_Objekt):
                        continue
                    if next(iter(rel[1].remote_side)).primary_key or rel[1].secondary is not None:
                        input_element = tabs.widget(page).fields.get(attr, None)
                        if input_element:
                            input_element.setDefault(attribute_value)
                        continue
                    if not rel[1].uselist:
                        attribute_value = [attribute_value]
                    for rel_obj in attribute_value:
                        tabs.setCurrentIndex(page)
                        tabs.createTab(class_type, obj.__class__, parent_attribute=attr, existing_xid=str(rel_obj.id))
                        p = next(index for index in range(tabs.count()) if class_type.__name__ == tabs.tabText(index))
                        iterate_relations(rel_obj, obj.__class__, page=p)
                    continue

                # this can raise KeyError on columns that aren't displayed in forms
                try:
                    input_element = tabs.widget(page).fields[attr]
                    input_element.setDefault(attribute_value)
                except KeyError:
                    pass

        iterate_relations(self)
        tabs.setCurrentIndex(0)
        return tabs


class XP_Bereich(RendererMixin, PolygonGeometry, ElementOrderMixin, RelationshipMixin, MapCanvasMixin, Base):
    """ XP_Bereich

    Abstrakte Oberklasse für die Modellierung von Bereichen.
    Ein Bereich fasst die Inhalte eines Plans nach bestimmten Kriterien zusammen.
    """

    __tablename__ = 'xp_bereich'
    __avoidRelation__ = ['planinhalt', 'praesentationsobjekt', 'simple_geometry']
    __readonly_columns__ = ['geltungsbereich']

    __LAYER_PRIORITY__ = LayerPriorityType.Bottom
    __geometry_column_name__ = 'geltungsbereich'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String(50))

    nummer = Column(Integer, nullable=False, doc='Nummer')
    name = Column(String, doc='Name')
    bedeutung = Column(Enum(XP_BedeutungenBereich), doc='Bedeutung')
    detaillierteBedeutung = Column(LargeString, doc='Erklärung der Bedeutung')
    erstellungsMassstab = Column(Integer, doc='Erstellungsmaßstab')
    geltungsbereich = Column(Geometry(),
                             CheckConstraint('st_dimension("geltungsbereich")) = 2',
                                             name='check_geometry_type'),
                             doc='Geltungsbereich')

    refScan = relationship("XP_ExterneReferenz", back_populates="bereich", cascade="all, delete",
                           passive_deletes=True)
    planinhalt = relationship("XP_Objekt", back_populates="gehoertZuBereich", cascade="all, delete",
                              passive_deletes=True)
    praesentationsobjekt = relationship("XP_AbstraktesPraesentationsobjekt", back_populates="gehoertZuBereich",
                                        cascade="all, delete", passive_deletes=True)
    aendertPlan = relationship("XP_VerbundenerPlan", back_populates="aendertPlan_verbundenerPlan",
                               cascade="all, delete", passive_deletes=True,
                               foreign_keys='XP_VerbundenerPlan.aendertPlan_verbundenerPlan_id')
    wurdeGeaendertVonPlan = relationship("XP_VerbundenerPlan", back_populates="wurdeGeaendertVonPlan_verbundenerPlan",
                                         cascade="all, delete", passive_deletes=True,
                                         foreign_keys='XP_VerbundenerPlan.wurdeGeaendertVonPlan_verbundenerPlan_id')

    # non XPlanung attributes
    simple_geometry = relationship("XP_SimpleGeometry", back_populates="gehoertZuBereich", cascade="all, delete",
                                   passive_deletes=True)

    __mapper_args__ = {
        "polymorphic_identity": "xp_bereich",
        "polymorphic_on": type,
    }

    def displayName(self):
        if not self.name:
            return f'Bereich {self.nummer}'
        return f'Bereich {self.nummer} - {self.name}'

    def srs(self) -> QgsCoordinateReferenceSystem:
        return QgsCoordinateReferenceSystem(f'EPSG:{self.geltungsbereich.srid}')

    def geometry(self) -> QgsGeometry:
        return geometry_from_spatial_element(self.geltungsbereich)

    def setGeometry(self, geom: QgsGeometry):
        self.geltungsbereich = WKTElement(geom.asWkt(), srid=self.geltungsbereich.srid)

    def toCanvas(self, layer_group, plan_xid=None):
        """ Override custom toCanvas behaviour, because each XP_Bereich object should get its own layer
            instead of merging geometries as feautures into one layer"""
        if plan_xid is None:
            raise ValueError("plan_xid cant be None when displaying XP_Bereich")

        try:
            srs = self.srs().postgisSrid()
        except:
            # when srs fails, plan content can't be displayed, therefore return early
            return
        layer = MapLayerRegistry().layer_by_display_name(self.displayName(), str(plan_xid))
        if not layer:
            layer = self.asLayer(srs, plan_xid, name=self.displayName(), geom_type=self.__geometry_type__)

        feat_id = self.addFeatureToLayer(layer, self.asFeature(layer.fields()))
        layer.setCustomProperty(f'xplanung/feat-{feat_id}', str(self.id))
        MapLayerRegistry().addLayer(layer, group=layer_group)

    @classmethod
    def xp_relationship_properties(cls) -> List[XPRelationshipProperty]:
        return [
            XPRelationshipProperty(rel_name='wurdeGeaendertVonPlan', xplan_attribute='wurdeGeaendertVonPlan',
                                   allowed_version=XPlanVersion.SIX),
            XPRelationshipProperty(rel_name='aendertPlan', xplan_attribute='aendertPlan',
                                   allowed_version=XPlanVersion.SIX),
        ]

    @classmethod
    def hidden_inputs(cls):
        return ['praesentationsobjekt', 'simple_geometry']

    @classmethod
    def avoid_export(cls):
        return ['praesentationsobjekt', 'simple_geometry']


class XP_Objekt(RendererMixin, RelationshipMixin, ElementOrderMixin, MapCanvasMixin, Base):
    """Abstrakte Oberklasse für alle XPlanung - Fachobjekte """

    __tablename__ = 'xp_objekt'
    __avoidRelation__ = ['wirdDargestelltDurch']

    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder

    hidden = False  # if class should be hidden in GUI forms
    annotation_delete_queue = []  # stores all annotation items that should be removed from canvas after a delete

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String(50))

    uuid = Column(String)
    text = Column(String)
    rechtsstand = Column(Enum(XP_Rechtsstand))

    gesetzlicheGrundlage_id = XPCol(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'),
                                    version=XPlanVersion.SIX, attribute='gesetzlicheGrundlage')
    gesetzlicheGrundlage = relationship("XP_GesetzlicheGrundlage", back_populates="xp_objekts")

    gliederung1 = Column(String)
    gliederung2 = Column(String)
    ebene = Column(Integer)

    hoehenangabe = relationship("XP_Hoehenangabe", back_populates="xp_objekt", cascade="all, delete",
                                passive_deletes=True)

    gehoertZuBereich_id = Column(UUID(as_uuid=True), ForeignKey('xp_bereich.id', ondelete='CASCADE'))
    gehoertZuBereich = relationship('XP_Bereich', back_populates='planinhalt')

    wirdDargestelltDurch = relationship("XP_AbstraktesPraesentationsobjekt", back_populates="dientZurDarstellungVon",
                                        cascade="all, delete", passive_deletes=True)

    aufschrift = Column(String)
    rechtscharakter = XPCol(XP_Rechtscharakter_EnumType(XP_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                            version=XPlanVersion.SIX)

    # non xplanung attributes
    drehwinkel = Column(Angle, default=0)
    skalierung = Column(Length, default=0.5)

    __mapper_args__ = {
        "polymorphic_identity": "xp_objekt",
        "polymorphic_on": type,
    }

    # def __setattr__(self, key, value):
    #     if key == 'rechtscharakter' and export_version() == XPlanVersion.FIVE_THREE:
    #         if not isinstance(value, XP_Rechtscharakter):
    #             logger.debug(f'setattr returns {value.to_xp_rechtscharakter()}')
    #             return super().__setattr__(key, value.to_xp_rechtscharakter())
    #         return super().__setattr__(key, value)
    #     else:
    #         return super().__setattr__(key, value)

    @classmethod
    def hidden_inputs(cls):
        return ['drehwinkel', 'skalierung', 'xp_versions']

    @classmethod
    def avoid_export(cls):
        return ['hidden', 'drehwinkel', 'skalierung', 'gesetzlicheGrundlage_id', 'annotation_delete_queue',
                'xp_versions']

    def displayName(self):
        return self.__class__.__name__

    def toCanvas(self, layer_group, plan_xid=None):

        # display all associated annotation items
        for po in self.wirdDargestelltDurch:
            if isinstance(po, XP_Nutzungsschablone):
                continue
            try:
                po.toCanvas(layer_group, plan_xid)
            except TypeError:
                pass

        super(XP_Objekt, self).toCanvas(layer_group, plan_xid)

    @classmethod
    def preview_icon(cls, geom_type: GeometryType):
        renderer = cls.renderer(geom_type)
        if isinstance(renderer, QgsRuleBasedRenderer):
            symbol = renderer.rootRule().children()[0].symbol()
            if symbol is None:
                child_symbols = renderer.rootRule().children()[0].symbols()
                if child_symbols:
                    symbol = child_symbols[0]
                else:
                    return QIcon()
        else:
            symbol = renderer.symbol()

        icon = QgsSymbolLayerUtils.symbolPreviewIcon(symbol, QSize(16, 16))
        return icon


@event.listens_for(XP_Objekt, 'before_delete', propagate=True)
def receive_before_delete(mapper, connection, target: XP_Objekt):
    """ Removes feature from canvas if it is currently visible """
    # populate the delete queue, the items get consumed in `receive_after_delete` to remove all visible annotations
    target.annotation_delete_queue = target.wirdDargestelltDurch


@event.listens_for(XP_Objekt, 'after_delete', propagate=True)
def receive_after_delete(mapper, connection, target: XP_Objekt):
    """ Removes feature from canvas if it is currently visible """

    layer: QgsVectorLayer = MapLayerRegistry().layerByFeature(str(target.id))
    if not layer:
        return

    fr = QgsFeatureRequest().setNoAttributes().setFlags(QgsFeatureRequest.NoGeometry)
    for feature in layer.getFeatures(fr):
        id_prop = layer.customProperties().value(f'xplanung/feat-{feature.id()}')
        if id_prop == str(target.id):
            with edit(layer):
                res = layer.deleteFeature(feature.id())
                if not res:
                    logger.warning(f'{target.displayName()}:{target.id} Feature wurde nicht von der Karte entfernt')

            while len(target.annotation_delete_queue) > 0:
                po = target.annotation_delete_queue.pop(0)
                po.remove_from_canvas()

            break


@event.listens_for(XP_Objekt, 'before_insert', propagate=True)
@event.listens_for(XP_Objekt, 'before_update', propagate=True)
@event.listens_for(XP_Plan, 'before_insert', propagate=True)
@event.listens_for(XP_Plan, 'before_update', propagate=True)
@event.listens_for(XP_Bereich, 'before_insert', propagate=True)
@event.listens_for(XP_Bereich, 'before_update', propagate=True)
def correct_geometry_trigger(mapper, connection, target):
    geom_element = getattr(target, target.__geometry_column_name__)
    if geom_element is None:
        return

    corrected_geom = correct_geometry(connection, target.geometry(), geom_element)
    if corrected_geom is not None:
        setattr(target, target.__geometry_column_name__, corrected_geom)
