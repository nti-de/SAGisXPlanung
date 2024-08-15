import logging
from inspect import signature
from typing import Tuple, Union, Any, Iterator, Iterable

from qgis.core import (QgsFields, QgsFeature, QgsVectorLayer, QgsField, QgsEditorWidgetSetup, QgsAnnotationLayer,
                       QgsWkbTypes)
from qgis.PyQt.QtCore import QVariant
from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper, RelationshipProperty

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty
from SAGisXPlanung.GML.geometry import geom_type_as_layer_url
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.XPlanungItem import XPlanungItem

from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.config import xplan_tooltip, export_version, QgsConfig

logger = logging.getLogger(__name__)


class RendererMixin:
    """ Mixin für XPlanung-Klassen, die als Geometrieobjekte auf der Karte visualisiert werden können """

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        # if possible, try to access renderer from saved config
        return QgsConfig.class_renderer(cls, geom_type)


class RelationshipMixin:
    """ Mixin zum Abruf aller Beziehungen eines ORM-Objekts im XPlanung Objektmodell """

    @classmethod
    def relationships(cls):
        return cls.__mapper__.relationships.items()

    def related(self) -> Iterator[Any]:
        """ Iterator über alle abhängigen Objekte"""
        for rel in self.__class__.relationships():
            if next(iter(rel[1].remote_side)).primary_key or rel[1].secondary is not None:
                continue
            if not self.__class__.relation_fits_version(rel[0], export_version()):
                continue
            rel_items = getattr(self, rel[0])
            if rel_items is None:
                continue
            # force iterable, if relation is one-to-one
            if not isinstance(rel_items, Iterable):
                rel_items = [rel_items]

            yield from rel_items

    @classmethod
    def relation_prop_display(cls, rel: Tuple[str, RelationshipProperty]) -> Tuple[str, Union[None, str]]:
        """
        Gibt Displayname und Tooltip für ein gegebenes RelationshipProperty zurück.

        Returns
        -------
        str, str:
            Displayname, Tooltip
        """
        if not hasattr(cls, 'xp_relationship_properties') or not next((p for p in cls.xp_relationship_properties() if p.rel_name == rel[0]), None):
            if rel[1].doc:
                return rel[1].doc, f'XPlanung-Attribut: {rel[0]}'
            else:
                return rel[0], xplan_tooltip(cls, rel[0])

        for relationship_property in cls.xp_relationship_properties():  # type: XPRelationshipProperty
            if relationship_property.rel_name == rel[0]:
                return relationship_property.xplan_attribute, xplan_tooltip(cls, relationship_property.xplan_attribute)

        raise Exception(f'Could not determine display parameters for relation {rel[0]} {rel[1]}')


class GeometryObject:
    """ Abstrakte Oberklasse für XPlanung-Geometrietypen """
    __geometry_type__ = QgsWkbTypes.UnknownGeometry
    __geometry_column_name__ = 'position'


class MixedGeometry(GeometryObject):
    """ Mixin zum Klassifizieren von Klassen mit variablem Raumbezug (Geometrieobjekte im XPlan-Schema) """
    __geometry_type__ = QgsWkbTypes.UnknownGeometry


class PointGeometry(GeometryObject):
    """ Mixin zum Klassifizieren von Klassen als Flächengeometrien"""
    __geometry_type__ = QgsWkbTypes.PointGeometry

    @classmethod
    def hidden_inputs(cls):
        h = super(PointGeometry, cls).hidden_inputs()
        return h + ['flaechenschluss']

    @classmethod
    def avoid_export(cls):
        h = super(PointGeometry, cls).avoid_export()
        return h + ['flaechenschluss']


class PolygonGeometry(GeometryObject):
    """ Mixin zum Klassifizieren von Klassen als Flächengeometrien"""
    __geometry_type__ = QgsWkbTypes.PolygonGeometry


class LineGeometry(GeometryObject):
    """ Mixin zum Klassifizieren von Klassen als Liniengeometrien"""
    __geometry_type__ = QgsWkbTypes.LineGeometry

    @classmethod
    def hidden_inputs(cls):
        h = super(LineGeometry, cls).hidden_inputs()
        return h + ['flaechenschluss']

    @classmethod
    def avoid_export(cls):
        h = super(LineGeometry, cls).avoid_export()
        return h + ['flaechenschluss']


class FlaechenschlussObjekt:
    """ Mixin, zum Deklarieren eines Flächenschlussobjekts.
    Alle Objektklassen die von *P_Flaechenobjekt/*P_Flaechenschlussobjekt müssen mit diesem Mixin dekoriert werden,
    damit der schema-konforme Export ins XPlanGML gewährleistet ist.

    Flächenschlussobjekte zeichnen sich dadurch aus, dass das Attribut `flaechenschluss` erforderlich ist."""
    pass


class UeberlagerungsObjekt:
    """ Mixin, zum Deklarieren eines Überlagerungsobjekts.
    Alle Objektklassen die von xplan:*P_Ueberlagerungsobjekt abgeleitet sind, müssen mit diesem Mixin dekoriert werden,
    damit der schema-konforme Export ins XPlanGML gewährleistet ist.

    Überlagerungsobjekte zeichnen sich dadurch aus, dass das Attribut `flaechenschluss` zwingend den Wert `falsch`
    erhält. """
    pass


class ElementOrderDeclarativeInheritanceFixMixin:
    """ Mixin, zum Dekorieren einer sqlalchemy @declarative_base Klasse, damit die `element_order` Methode korrekt
        funktioniert.
        Dieses Mixin muss immmer zuletzt in der Klassensignatur angewendet werden. """
    is_declarative_base = True


class ElementOrderMixin:
    """ Mixin, dass eine Methode zur Auflösung der Reihenfolge der Attribute jedes XPlanung-Objekts bietet.
        Ist das XPlanung-Objekt in eine Vererbungshierarchie eingebunden, muss die XPlanung-Basisklasse in der
        Deklaration aller Basisklassen immer zuerst stehen, damit die Methode element_order korrekt funktioniert. """

    @classmethod
    def element_order(cls, include_base=True, only_columns=False, export=True, version=XPlanVersion.FIVE_THREE):
        if only_columns:
            order = inspect(cls).columns.keys()
            order = [cls.normalize_column_name(x) for x in order if cls.attr_is_treated_as_column(x)]

            # remove duplicates
            order = list(dict.fromkeys(order))
        else:
            order = [key for key, value in cls.__dict__.items() if
                     not (key.startswith('__') or key.startswith('_sa_') or callable(value)
                          or isinstance(value, classmethod))]

        if version is not None:
            order = [x for x in order if cls.attr_fits_version(x, version)]

        if not export and hasattr(cls, 'hidden_inputs'):
            order = [x for x in order if x not in cls.hidden_inputs()]
        elif export and hasattr(cls, 'avoid_export'):
            order = [x for x in order if x not in cls.avoid_export()]

        # remove sqlalchemy utility attributes
        order = [x for x in order if x not in ['type', 'id']]

        try:
            bases = cls.__bases__[-1]
            base_order = bases.element_order(only_columns=only_columns, export=export, version=version)
            if not include_base and not hasattr(cls, 'is_declarative_base'):
                return [x for x in order if x not in base_order]
            # why was this check even introduced?
            # if only_columns:
            #     return order
            return base_order + [x for x in order if x not in base_order]
        except Exception as e:
            return order

    @classmethod
    def attr_fits_version(cls, attr_name: str, version: XPlanVersion) -> bool:
        """ Überprüft, ob ein XPlanung-Attribut zur gegebenen Version des Standards gehört"""
        attr = getattr(cls, attr_name)
        if hasattr(attr, "version") and attr.version != version:
            return False
        if hasattr(cls, 'xp_relationship_properties'):
            for relationship_property in cls.xp_relationship_properties():  # type: XPRelationshipProperty
                if relationship_property.rel_name == attr_name and relationship_property.allowed_version != version:
                    return False
        return True

    @classmethod
    def relation_fits_version(cls, rel_name: str, version: XPlanVersion) -> bool:
        """ Überprüft, ob eine XPlanung-Relation zur gegebenen Version des Standards gehört"""
        if hasattr(cls, 'xp_relationship_properties'):
            for relationship_property in cls.xp_relationship_properties():  # type: XPRelationshipProperty
                if relationship_property.rel_name == rel_name and relationship_property.allowed_version != version:
                    return False
        return True

    @classmethod
    def attr_is_treated_as_column(cls, attr_name: str, consider_suffix=True) -> bool:
        """ Überprüft ob ein gegebenes Attribut, als Column (statt Relationship) gehandhabt wird."""
        attr = getattr(cls, attr_name)
        if hasattr(attr, "version") and hasattr(attr, 'attribute') and attr.attribute is not None:
            return True
        if consider_suffix:
            return not attr_name.endswith('_id')
        return False

    @classmethod
    def normalize_column_name(cls, attr_name: str) -> str:
        """ Gibt den 'echten' XPlanung-Namen züruck, wenn das Python-Attribut nicht korrekt bennant werden kann.
            XPCol muss dafür mit Parameter `attribute` verwendet werden."""
        attr = getattr(cls, attr_name)
        if hasattr(attr, "version") and hasattr(attr, 'attribute'):
            return attr.attribute or attr_name
        return attr_name


class XPlanungEnumMixin:
    def __str__(self):
        return str(self.name)


class MapCanvasMixin:
    """ Mixin, dass Methoden zum Darstellen von Planinhalten auf dem MapCanvas bietet.
        Kann nur in Kombination mit einem GeometryMixin verwendet werden!
        Implementierende Klasse muss über die `geometry()`-Methode verfügen! """

    def toCanvas(self, layer_group, plan_xid=None):
        from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry

        try:
            srs = self.srs().postgisSrid()
        except Exception as e:
            # when srs fails, plan content can't be displayed, therefore return early
            logger.error(f'Fehler beim Abruf des Koordinatebezugssystems. Layer kann nicht dargestellt werden. {e}')
            return

        # check for new geometry API (introduced v1.10.2) or take previously __geometry_type__ attr
        if hasattr(self, 'geomType'):
            geom_type = self.geomType()
        else:
            geom_type = self.__geometry_type__

        plan_id = str(plan_xid) if plan_xid else str(self.id)
        layer = MapLayerRegistry().layerByXid(XPlanungItem(xid=self.id, xtype=self.__class__, plan_xid=plan_id),
                                              geom_type=geom_type)
        if not layer:
            layer = self.asLayer(srs, plan_id, name=self.displayName(), geom_type=geom_type)

        feat_id = None
        if isinstance(layer, QgsVectorLayer):
            feat_id = self.addFeatureToLayer(layer, self.asFeature(layer.fields()))
        elif isinstance(layer, QgsAnnotationLayer):
            feat_id = layer.addItem(self.asFeature())
        layer.setCustomProperty(f'xplanung/feat-{feat_id}', str(self.id))
        MapLayerRegistry().addLayer(layer, group=layer_group)

    def asFeature(self, fields: QgsFields = None) -> QgsFeature:
        feat = QgsFeature()
        feat.setGeometry(self.geometry())
        feat.setFields(fields)

        legacy_fields = None
        if hasattr(self, 'layer_fields'):
            legacy_fields = self.layer_fields()

        for field_name in self.__class__.element_order(only_columns=True, include_base=True, version=export_version()):
            try:
                if legacy_fields and field_name in legacy_fields:
                    value = legacy_fields[field_name]
                else:
                    value = getattr(self, field_name)

                if type(value) is list:
                    value = ', '.join(str(v) for v in value)

                feat[field_name] = str(value) if value is not None else None
            except KeyError as e:
                pass

        return feat

    def addFeatureToLayer(self, layer, feat):
        dp = layer.dataProvider()
        layer.startEditing()
        _, newFeatures = dp.addFeatures([feat])
        layer.commitChanges()

        return newFeatures[0].id()

    @classmethod
    def asLayer(cls, srid, plan_xid, name=None, geom_type=None) -> QgsVectorLayer:
        geom_type = geom_type if geom_type is not None else cls.__geometry_type__
        layer = QgsVectorLayer(f"{geom_type_as_layer_url(geom_type)}?crs=EPSG:{srid}",
                               cls.__name__ if not name else name, "memory")
        layer.setCustomProperty("skipMemoryLayersCheck", 1)
        layer.setCustomProperty('xplanung/type', cls.__name__)
        layer.setCustomProperty('xplanung/plan-xid', str(plan_xid))

        from SAGisXPlanung.XPlan.feature_types import XP_Objekt

        if issubclass(cls, XP_Objekt):
            layer.setReadOnly(True)

        if hasattr(cls, 'renderer'):
            if signature(cls.renderer).parameters.get("geom_type"):
                layer.setRenderer(cls.renderer(geom_type))
            else:
                layer.setRenderer(cls.renderer())

        field_names = cls.element_order(only_columns=True, include_base=True, version=export_version())
        fields = [QgsField(name, QVariant.String, 'string') for name in field_names]
        layer.dataProvider().addAttributes(fields)
        layer.updateFields()

        edit_config = layer.editFormConfig()
        for i in range(len(field_names)):
            edit_config.setReadOnly(i, True)
        layer.setEditFormConfig(edit_config)

        return layer
