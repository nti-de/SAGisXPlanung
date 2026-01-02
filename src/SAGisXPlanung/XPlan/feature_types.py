import logging
import traceback
from uuid import uuid4

from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QIcon

from geoalchemy2 import Geometry, WKTElement
from qgis.core import QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer, QgsSymbol

from sqlalchemy import Column, String, Date, Integer, Float, Enum, ForeignKey, event, CheckConstraint, Computed, Table
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship

from qgis.core import (QgsCoordinateReferenceSystem, QgsGeometry, QgsVectorLayer, QgsFeatureRequest,
                       QgsSymbolLayerUtils, QgsRuleBasedRenderer)

from .conversions import XP_Rechtscharakter_EnumType
from .core import LayerPriorityType
from .enums import XP_BedeutungenBereich, XP_Rechtsstand, XP_Rechtscharakter
from SAGisXPlanung import Base, XPlanVersion
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element, correct_geometry
from SAGisXPlanung.config import export_version
from SAGisXPlanung.core.mixins.mixins import ElementOrderMixin, PolygonGeometry, MapCanvasMixin, RelationshipMixin, \
    RendererMixin, FeatureType
from .types import LargeString, Angle, Length, GeometryType, XPEnum
from ..MapLayerRegistry import MapLayerRegistry
from ..core.helper import safe_edit

logger = logging.getLogger(__name__)


xp_textabschnitt_assoc = Table(
    "xp_textabschnitt_assoc",
    Base.metadata,
    Column("xp_objekt_id", UUID(as_uuid=True), ForeignKey("xp_objekt.id", ondelete="CASCADE")),
    Column("xp_plan_id", UUID(as_uuid=True), ForeignKey("xp_plan.id", ondelete="CASCADE")),
    Column("xp_bereich_id", UUID(as_uuid=True), ForeignKey("xp_bereich.id", ondelete="CASCADE")),
    Column("textabschnitt_id", UUID(as_uuid=True), ForeignKey("xp_text_abschnitt.id", ondelete="CASCADE")),
)


class XP_Plan(FeatureType, RendererMixin, PolygonGeometry, ElementOrderMixin, RelationshipMixin, MapCanvasMixin, Base):
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
                           passive_deletes=True, foreign_keys='XP_VerbundenerPlan.aendert_verbundenerPlan_id',
                           info={'xplan_version': XPlanVersion.FIVE_THREE})
    wurdeGeaendertVon = relationship("XP_VerbundenerPlan", back_populates="wurdeGeaendertVon_verbundenerPlan",
                                     cascade="all, delete", passive_deletes=True,
                                     foreign_keys='XP_VerbundenerPlan.wurdeGeaendertVon_verbundenerPlan_id',
                                     info={'xplan_version': XPlanVersion.FIVE_THREE})

    erstellungsMassstab = Column(Integer, doc='Erstellungsmaßstab')
    bezugshoehe = Column(Float, doc='Standard Bezugshöhe')
    hoehenbezug = Column(String(), doc='Höhenbezug', info={'xplan_version': XPlanVersion.SIX})
    technischerPlanersteller = Column(String, doc='Technischer Planersteller')
    raeumlicherGeltungsbereich = Column(Geometry(),
                                        CheckConstraint('st_dimension("raeumlicherGeltungsbereich")) = 2',
                                                        name='check_geometry_type'),
                                        nullable=False, doc='Geltungsbereich')

    verfahrensMerkmale = relationship("XP_VerfahrensMerkmal", back_populates="plan", cascade="all, delete",
                                      passive_deletes=True)
    externeReferenz = relationship("XP_SpezExterneReferenz", back_populates="plan", cascade="all, delete",
                                   passive_deletes=True)

    # XP_TextAbschnitt [0..*]
    texte = relationship("XP_TextAbschnitt",
        secondary=xp_textabschnitt_assoc,
        back_populates="xp_plaene",
        cascade="all, delete",
        passive_deletes=True,
        info={'xplan_version': XPlanVersion.FIVE_THREE, 'xplan_attribute': 'texte', 'link-type': 'abstract'})

    texte_v6 = relationship("XP_TextAbschnitt",
        secondary=xp_textabschnitt_assoc,
        back_populates="xp_plaene_v6",
        cascade="all, delete",
        passive_deletes=True,
        info={'xplan_version': XPlanVersion.SIX, 'xplan_attribute': 'texte'})

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
    def avoid_export(cls):
        return ['_sa_search_col']

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


    def enforceFlaechenschluss(self):
        """ Abstrakte Methode zum Erzwingen des Flächenschluss. Muss in jeder konkreten Klasse implementiert werden."""
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


class XP_Bereich(FeatureType, RendererMixin, PolygonGeometry, ElementOrderMixin, RelationshipMixin, MapCanvasMixin, Base):
    """ XP_Bereich

    Abstrakte Oberklasse für die Modellierung von Bereichen.
    Ein Bereich fasst die Inhalte eines Plans nach bestimmten Kriterien zusammen.
    """

    __tablename__ = 'xp_bereich'
    __avoidRelation__ = ['praesentationsobjekt', 'simple_geometry']
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
                              passive_deletes=True, info={
                                  'form-type': 'hidden'
                              })
    praesentationsobjekt = relationship("XP_AbstraktesPraesentationsobjekt", back_populates="gehoertZuBereich",
                                        cascade="all, delete", passive_deletes=True, info={
                                            'form-type': 'hidden',
                                            'link': 'xlink-only'
                                        })
    aendertPlan = relationship("XP_VerbundenerPlan", back_populates="aendertPlan_verbundenerPlan",
                               cascade="all, delete", passive_deletes=True,
                               foreign_keys='XP_VerbundenerPlan.aendertPlan_verbundenerPlan_id',
                               info={'xplan_version': XPlanVersion.SIX})
    wurdeGeaendertVonPlan = relationship("XP_VerbundenerPlan", back_populates="wurdeGeaendertVonPlan_verbundenerPlan",
                                         cascade="all, delete", passive_deletes=True,
                                         foreign_keys='XP_VerbundenerPlan.wurdeGeaendertVonPlan_verbundenerPlan_id',
                                         info={'xplan_version': XPlanVersion.SIX})

    # XP_TextAbschnitt [0..*] (v6)
    texte = relationship("XP_TextAbschnitt", back_populates="xp_bereich",
                         secondary=xp_textabschnitt_assoc,
                         cascade="all, delete", passive_deletes=True,
                         info={'xplan_version': XPlanVersion.SIX})

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
            instead of merging geometries as features into one layer"""
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
    def avoid_export(cls):
        return ['praesentationsobjekt', 'simple_geometry']


class XP_Objekt(FeatureType, RendererMixin, RelationshipMixin, ElementOrderMixin, MapCanvasMixin, Base):
    """Abstrakte Oberklasse für alle XPlanung - Fachobjekte """

    __tablename__ = 'xp_objekt'
    __avoidRelation__ = ['wirdDargestelltDurch']

    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder

    hidden = False  # if class should be hidden in GUI forms
    annotation_delete_queue = []  # stores all annotation items that should be removed from canvas after a delete

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String())

    uuid = Column(String)
    text = Column(String)
    rechtsstand = Column(XPEnum(XP_Rechtsstand, include_default=True))

    gesetzlicheGrundlage_id = Column(UUID(as_uuid=True), ForeignKey('xp_gesetzliche_grundlage.id'))
    gesetzlicheGrundlage = relationship("XP_GesetzlicheGrundlage", back_populates="xp_objekts", info={
        'form-type': 'inline',
        'xplan_version': XPlanVersion.SIX
    })

    gliederung1 = Column(String)
    gliederung2 = Column(String)
    ebene = Column(Integer)

    hoehenangabe = relationship("XP_Hoehenangabe", back_populates="xp_objekt", cascade="all, delete",
                                passive_deletes=True)

    gehoertZuBereich_id = Column(UUID(as_uuid=True), ForeignKey('xp_bereich.id', ondelete='CASCADE'))
    gehoertZuBereich = relationship('XP_Bereich', back_populates='planinhalt', info={
        'link': 'xlink-only',
        'form-type': 'hidden'
    })

    wirdDargestelltDurch = relationship("XP_AbstraktesPraesentationsobjekt",
        back_populates="dientZurDarstellungVon",
        cascade="all, delete",
        passive_deletes=True,
        info={
            'link': 'xlink-only',
            'form-type': 'hidden'
        }
    )

    aufschrift = Column(String)
    rechtscharakter = Column(XP_Rechtscharakter_EnumType(XP_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                             info={'xplan_version': XPlanVersion.SIX})

    # XP_TextAbschnitt [0..*] (v6)
    refTextInhalt_v6 = relationship("XP_TextAbschnitt",
        secondary=xp_textabschnitt_assoc,
        back_populates="xp_objekte",
        cascade="all, delete",
        passive_deletes=True,
        info={'xplan_version': XPlanVersion.SIX, 'xplan_attribute': 'refTextInhalt'}
    )

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
        return ['hidden', 'drehwinkel', 'skalierung', 'annotation_delete_queue', 'xp_versions']

    def displayName(self):
        return self.__class__.__name__

    def toCanvas(self, layer_group, plan_xid=None):

        # display all associated annotation items
        for po in self.wirdDargestelltDurch:
            try:
                po.toCanvas(layer_group, plan_xid)
            except TypeError as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())
                pass

        super(XP_Objekt, self).toCanvas(layer_group, plan_xid)

    @classmethod
    def preview_icon(cls, geom_type: GeometryType):
        renderer = cls.renderer(geom_type)
        try:
            if isinstance(renderer, QgsRuleBasedRenderer):
                symbol = renderer.rootRule().children()[0].symbol()
                if symbol is None:
                    child_symbols = renderer.rootRule().children()[0].symbols()
                    if child_symbols:
                        symbol = child_symbols[0]
            elif isinstance(renderer, QgsCategorizedSymbolRenderer):
                symbol = renderer.sourceSymbol()
            else:
                symbol = renderer.symbol()
        except Exception as e:
            logger.exception(f'Error while getting symbol for {cls.__name__}')
            logger.exception(e)
            symbol = None

        if symbol is None:
            return QIcon()

        icon = QgsSymbolLayerUtils.symbolPreviewIcon(symbol, QSize(16, 16))
        return icon


@event.listens_for(XP_Objekt, 'after_delete', propagate=True)
def receive_after_delete(mapper, connection, target: XP_Objekt):
    """ Removes feature from canvas if it is currently visible """

    layer: QgsVectorLayer = MapLayerRegistry().layer_by_orm_id(str(target.id))
    if not layer:
        return

    fr = QgsFeatureRequest().setNoAttributes().setFlags(QgsFeatureRequest.NoGeometry)
    for feature in layer.getFeatures(fr):
        id_prop = layer.customProperties().value(f'xplanung/feat-{feature.id()}')
        if id_prop == str(target.id):
            with safe_edit(layer):
                res = layer.deleteFeature(feature.id())
                if not res:
                    logger.warning(f'{target.displayName()}:{target.id} Feature wurde nicht von der Karte entfernt')

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


class XP_TextAbschnitt(FeatureType, RelationshipMixin, ElementOrderMixin, Base):
    """ Ein Abschnitt der textlich formulierten Inhalte des Plans. """

    __tablename__ = 'xp_text_abschnitt'
    __avoidRelation__ = ['xp_bereich', 'xp_objekt', 'xp_plan', 'bp_objekt', 'fp_objekt', 'bp_baugebiet',
                         'bp_nebenanlagen_ausschluss_flaeche', 'bp_wohngebaeude_flaeche', 'xp_objekte',
                         'xp_plaene', 'xp_plaene_v6']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String())

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        "polymorphic_on": type,
    }

    schluessel = Column(String)
    gesetzlicheGrundlage = Column(String)
    text = Column(LargeString)

    # [0..1]
    refText = relationship("XP_ExterneReferenz", back_populates="xp_text_abschnitt",
                           cascade="all, delete", passive_deletes=True, uselist=False)

    rechtscharakter = Column(XP_Rechtscharakter_EnumType(XP_Rechtscharakter), nullable=False,
                             doc='Rechtscharakter', default='Unbekannt',
                             info={'xplan_version': XPlanVersion.SIX})

    # XP_Bereich [0..*] (v6)
    xp_bereich = relationship("XP_Bereich", secondary=xp_textabschnitt_assoc, back_populates="texte",
                              info={'xplan_version': XPlanVersion.SIX})

    # XP_Objekt [0..*] (v6)
    xp_objekte = relationship("XP_Objekt",
        secondary=xp_textabschnitt_assoc,
        back_populates="refTextInhalt_v6",
        info={'xplan_version': XPlanVersion.SIX}
    )

    # XP_Plan [0..*]
    xp_plaene = relationship("XP_Plan",
        secondary=xp_textabschnitt_assoc,
        back_populates="texte",
        info={'xplan_version': XPlanVersion.FIVE_THREE}
    )
    xp_plaene_v6 = relationship("XP_Plan",
        secondary=xp_textabschnitt_assoc,
        back_populates="texte_v6",
        info={'xplan_version': XPlanVersion.SIX}
    )

    # BP_Objekt [0..*] (v5.3)
    bp_objekt_id = Column(UUID(as_uuid=True), ForeignKey('bp_objekt.id', ondelete='CASCADE'))
    bp_objekt = relationship("BP_Objekt", back_populates="refTextInhalt",
                             foreign_keys=[bp_objekt_id],
                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    # FP_Objekt [0..*] (v5.3)
    fp_objekt_id = Column(UUID(as_uuid=True), ForeignKey('fp_objekt.id', ondelete='CASCADE'))
    fp_objekt = relationship("FP_Objekt", back_populates="refTextInhalt",
                             foreign_keys=[fp_objekt_id],
                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    # BP_BaugebietsTeilFlaeche [0..*] (v6)
    bp_baugebiet_id = Column(UUID(as_uuid=True), ForeignKey('bp_baugebiet.id', ondelete='CASCADE'))
    bp_baugebiet = relationship("BP_BaugebietsTeilFlaeche", back_populates="abweichungText_v6",
                                foreign_keys=[bp_baugebiet_id],
                                info={'xplan_version': XPlanVersion.SIX})

    # BP_NebenanlagenAusschlussFlaeche [0..*] (v6)
    bp_nebenanlagen_ausschluss_flaeche_id = Column(UUID(as_uuid=True),
                                                   ForeignKey('bp_nebenanlagen_ausschluss_flaeche.id',
                                                              ondelete='CASCADE'))
    bp_nebenanlagen_ausschluss_flaeche = relationship("BP_NebenanlagenAusschlussFlaeche",
                                                      back_populates="abweichungText_v6",
                                                      foreign_keys=[bp_nebenanlagen_ausschluss_flaeche_id],
                                                      info={'xplan_version': XPlanVersion.SIX})

    # BP_WohngebaeudeFlaeche [0..*] (v6)
    bp_wohngebaeude_flaeche_id = Column(UUID(as_uuid=True),
                                        ForeignKey('bp_wohngebaeude_flaeche.id', ondelete='CASCADE'))
    bp_wohngebaeude_flaeche = relationship("BP_WohngebaeudeFlaeche", back_populates="abweichungText",
                                           foreign_keys=[bp_wohngebaeude_flaeche_id])

    @classmethod
    def avoid_export(cls):
        return ['xp_plan', 'xp_bereich', 'xp_objekt', 'bp_objekt', 'fp_objekt', 'bp_baugebiet',
                'bp_nebenanlagen_ausschluss_flaeche', 'bp_wohngebaeude_flaeche', 'xp_objekte',
                'xp_plaene', 'xp_plaene_v6']

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
