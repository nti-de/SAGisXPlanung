import logging
from inspect import signature
from typing import Tuple, Union, Any, Iterator, Iterable

from qgis.core import (QgsFields, QgsFeature, QgsVectorLayer, QgsField, QgsEditorWidgetSetup, QgsAnnotationLayer,
                       QgsWkbTypes)
from qgis.PyQt.QtCore import QVariant
from sqlalchemy.orm import RelationshipProperty, interfaces, ColumnProperty

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.GML.geometry import geom_type_as_layer_url
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.XPlanungItem import XPlanungItem

from SAGisXPlanung.config import xplan_tooltip, export_version, QgsConfig

try:
    from functools import cache
except ImportError:
    from functools import lru_cache as cache

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
            if not self.__class__.attr_fits_version(rel[0], export_version()):
                continue
            rel_items = getattr(self, rel[0])
            if rel_items is None:
                continue
            # force iterable, if relation is one-to-one
            if not isinstance(rel_items, Iterable):
                rel_items = [rel_items]
            # remove classes that don't fit version
            rel_items = [r for r in rel_items
                         if not hasattr(r.__class__, 'xp_versions') or export_version() in r.__class__.xp_versions]

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
        attr_name, rel_property = rel
        xplan_attribute_name = rel_property.info.get('xplan_attribute')
        if xplan_attribute_name is None:
            if rel[1].doc:
                return rel[1].doc, f'XPlanung-Attribut: {rel[0]}'
            else:
                return rel[0], xplan_tooltip(cls, rel[0])

        return xplan_attribute_name, xplan_tooltip(cls, xplan_attribute_name)


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
        return ['flaechenschluss']

    @classmethod
    def avoid_export(cls):
        return ['flaechenschluss']


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
    @cache
    def element_order(cls,
                      include_base=True,
                      only_columns=False,
                      export=True,
                      with_geometry=True,
                      geometry_column_name='',
                      version=XPlanVersion.FIVE_THREE,
                      ret_fmt='',
                      relations='all'):

        order = []
        for supercls in reversed(cls.__mro__[0:-1]):
            if not issubclass(supercls, ElementOrderMixin):
                continue

            for key in supercls.__dict__:
                val = supercls.__dict__[key]
                if (
                    isinstance(val, interfaces.InspectionAttr)
                    and val.is_attribute
                    and val.property.parent.class_.attr_fits_version(val.property.key, version)
                ):
                    mapper_property = val.property
                    # if requested, only show columns (no relations)
                    if only_columns and not isinstance(mapper_property, ColumnProperty):
                        continue

                    # only display relationships per declaration of form-type
                    if isinstance(mapper_property, RelationshipProperty):
                        form_type = mapper_property.info.get('form-type')
                        if hasattr(cls, '__avoidRelation__') and mapper_property.key in cls.__avoidRelation__:
                            continue
                        if relations == 'inline' and form_type != 'inline':
                            continue
                        if not export and form_type == 'hidden':
                            continue

                    order.append(val)

        if not include_base:
            order = [x for x in order if x.property.parent.class_ == cls]

        seen = set()
        exclude = set()
        result_order = []
        for obj in order:
            if obj.key not in seen:
                result_order.append(obj)
                seen.add(obj.key)

                if '_id' in obj.key:  # immediately mark columns for removal, we never want to use _id columns
                    exclude.add(obj.key)

        # remove sqlalchemy utility attributes and geometry column if required
        exclude |= {'type', 'id'}
        if not with_geometry:
            if hasattr(cls, '__geometry_column_name__'):
                geometry_column_name = cls.__geometry_column_name__
            exclude.add(geometry_column_name)

        if not export and hasattr(cls, 'hidden_inputs'):
            if not only_columns and hasattr(cls, '__avoidRelation__'):
                exclude.update(cls.__avoidRelation__)
            exclude.update(cls.hidden_inputs())
        elif export and hasattr(cls, 'avoid_export'):
            exclude.update(cls.avoid_export())

        result_order = [x for x in result_order if x.key not in exclude]

        if ret_fmt == 'sqla':
            return [(ins.key, ins.property) for ins in result_order]
        else:
            return [ins.key for ins in result_order]

    @classmethod
    def attr_fits_version(cls, attr_name: str, version: XPlanVersion) -> bool:
        """ Überprüft, ob ein XPlanung-Attribut zur gegebenen Version des Standards gehört"""
        attr = getattr(cls, attr_name)
        allowed_xplan_version = attr.info.get('xplan_version')
        if allowed_xplan_version is not None and allowed_xplan_version != version:
            return False
        return True

    @classmethod
    def find_attr_class(cls, attr_chain: str) -> tuple[type, str]:
        """ find sqlalchemy model class where an attribute is defined from chained notation,
            e.g. bereich.planinhalt.text -> (XP_Objekt, "text") """
        attributes = attr_chain.split('.')
        current_class = cls
        for attr in attributes:
            relation = getattr(current_class, attr, None)
            if relation is None:
                raise AttributeError(f"Attribute '{attr}' not found in the chain.")
            if not hasattr(relation, 'mapper') or attr == attributes[-1]:
                return current_class, attributes[-1]
            current_class = relation.mapper.class_

        raise ValueError()

    def get_attr(self, attr_name: str) -> tuple[str, list]:
        def _getattr_recursive(current_obj, attr_chain):
            for attr in attr_chain:
                if isinstance(current_obj, list):
                    # If the current object is a list, get the attribute for each item in the list
                    current_obj = [getattr(item, attr) for item in current_obj]
                else:
                    # Otherwise, just get the attribute for the current object
                    current_obj = getattr(current_obj, attr)
            return current_obj

        attributes = attr_name.split('.')
        return attributes[-1], _getattr_recursive(self, attributes)


class MapCanvasMixin:
    """ Mixin, dass Methoden zum Darstellen von Planinhalten auf dem MapCanvas bietet.
        Kann nur in Kombination mit einem GeometryMixin verwendet werden!
        Implementierende Klasse muss über die `geometry()`-Methode verfügen! """

    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder

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

        field_names = cls.element_order(only_columns=True, include_base=True,
                                        with_geometry=False, version=export_version())
        fields = [QgsField(name, QVariant.String, 'string') for name in field_names]
        fields.extend([QgsField('drehwinkel', QVariant.String, 'string'),
                       QgsField('skalierung', QVariant.String, 'string')])

        layer.dataProvider().addAttributes(fields)
        layer.updateFields()

        for i, field_name in enumerate(field_names):
            # exclude relationship columns
            if (rel := next((r for r in cls.relationships() if r[0] == field_name), None)) is not None:
                continue

            widget_setup = QgsEditorWidgetSetup('Hidden', {})
            layer.setEditorWidgetSetup(i, widget_setup)

        return layer
