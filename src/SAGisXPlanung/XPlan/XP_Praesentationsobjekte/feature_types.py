import enum
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Any
from uuid import uuid4

from PyQt5.QtCore import QVariant
from geoalchemy2 import Geometry, WKTElement, WKBElement
from qgis._core import QgsField, QgsNullSymbolRenderer, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsProperty, \
    QgsPropertyCollection, Qgis, QgsFeatureRequest, QgsFeature, QgsFields
from sqlalchemy import Column, ForeignKey, String, Integer, ARRAY, Enum, Float, event, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.event import remove
from sqlalchemy.orm import relationship, object_session

from qgis.core import (QgsGeometry, QgsTextFormat, QgsUnitTypes, QgsTextBackgroundSettings, QgsCoordinateReferenceSystem)

from SAGisXPlanung import Base, BASE_DIR, XPlanVersion
from SAGisXPlanung.config import PPO_CONFIG
from SAGisXPlanung.core.buildingtemplate.template_cells import TableCell
from SAGisXPlanung.core.buildingtemplate.template_item import BuildingTemplateCellDataType, BuildingTemplateRenderer
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.MapLayerRegistry import MapLayerRegistry
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.core.helper import safe_edit
from SAGisXPlanung.core.helper.layer import _coerce_to_table_representation
from SAGisXPlanung.core.helper.xpath import XPathMatcher, ResolvedXPathResult
from SAGisXPlanung.core.mixins.mixins import ElementOrderMixin, RelationshipMixin, MapCanvasMixin, PointGeometry, \
    FeatureType
from SAGisXPlanung.XPlan.types import Angle, GeometryType, XPathField
from SAGisXPlanung.ext.roman import to_roman

logger = logging.getLogger(__name__)

_active_listeners = defaultdict(list)

SCALES = {"BP": 1000, "FP": 5000, "SO": 1000}


def create_attribute_change_listener(cls: type, attr_name: str, target_xid: str, orm_xid: str):
    """Create an attribute change listener for a given ORM class.

    Returns:
        tuple: (listener_function, remove_function) where remove_function is a callable
               that will remove the listener when called.
    """

    @event.listens_for(cls, 'after_update', propagate=True)
    def after_update_listener(mapper, connection, target):
        state = inspect(target)
        attr_state = state.attrs[attr_name]
        if attr_state.history.has_changes() and str(target.id) == target_xid:
            layer = MapLayerRegistry().layer_by_orm_id(str(orm_xid))
            if layer is None:
                return

            session = object_session(target)
            xp_po = session.get(XP_AbstraktesPraesentationsobjekt, orm_xid)

            fr = QgsFeatureRequest().setNoAttributes().setFlags(QgsFeatureRequest.NoGeometry)
            for feat in layer.getFeatures(fr):
                id_prop = layer.customProperties().value(f'xplanung/feat-{feat.id()}')
                if id_prop == str(orm_xid):
                    with safe_edit(layer):
                        xp_po.sync_to_feature(feat, update_listener=False)
                        layer.updateFeature(feat)

    # Create a function to remove this listener
    def remove_listener():
        remove(cls, 'after_update', after_update_listener)

    return after_update_listener, remove_listener



class XP_AbstraktesPraesentationsobjekt(FeatureType, RelationshipMixin, ElementOrderMixin, MapCanvasMixin, Base):
    """ Abstrakte Basisklasse für alle Präsentationsobjekt """

    __tablename__ = 'xp_po'

    __LAYER_PRIORITY__ = LayerPriorityType.Top

    FORCE_ORM_UPDATE = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    stylesheetId = Column(String)
    darstellungsprioritaet = Column(Integer)
    art = Column(ARRAY(XPathField))
    index = Column(ARRAY(Integer), info={'xplan_version': XPlanVersion.FIVE_THREE})

    gehoertZuBereich_id = Column(UUID(as_uuid=True), ForeignKey('xp_bereich.id', ondelete='CASCADE'))
    gehoertZuBereich = relationship('XP_Bereich', back_populates='praesentationsobjekt', info={
                                        'link': 'xlink-only',
                                        'form-type': 'hidden'
                                    })

    dientZurDarstellungVon_id = Column(UUID(as_uuid=True), ForeignKey('xp_objekt.id', ondelete='CASCADE'))
    dientZurDarstellungVon = relationship('XP_Objekt', back_populates='wirdDargestelltDurch', info={
                                                'link': 'xlink-only',
                                                'form-type': 'hidden'
                                            })

    type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'xp_po',
        'polymorphic_on': type
    }
    __readonly_columns__ = ['position']

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
        """ Removes this presentation object from canvas if it is currently visible """
        layer = MapLayerRegistry().layer_by_orm_id(str(self.id))
        if not layer:
            return

        fr = QgsFeatureRequest().setNoAttributes().setFlags(QgsFeatureRequest.NoGeometry)
        for feature in layer.getFeatures(fr):
            id_prop = layer.customProperties().value(f'xplanung/feat-{feature.id()}')
            if id_prop == str(self.id):
                with safe_edit(layer):
                    res = layer.deleteFeature(feature.id())
                    if not res:
                        logger.warning(f'{self.displayName()}:{self.id} Feature wurde nicht von der Karte entfernt')

                break

    @classmethod
    def text_from_xpath_results(cls, xpath_results: List[ResolvedXPathResult], pattern: str = None) -> str:
        text_contents = []
        for result in xpath_results:
            val = result.value
            if val is None:
                continue
            if isinstance(val, enum.Enum):
                if hasattr(val, 'short_desc'):
                    text_contents.append(val.short_desc())
                else:
                    text_contents.append(val.name)
            else:
                text_contents.append(str(val))
        if pattern:
            text_content = cls.resolve_text_pattern(text_contents, pattern)
        else:
            text_content = ' '.join(map(str, text_contents))
        return text_content

    @classmethod
    def transform_text_content(cls, value, transform_type: str):
        if not transform_type or value is None:
            return str(value) if value is not None else ""

        if transform_type.lower() == 'roman':
            return to_roman(int(value))

        return value

    @classmethod
    def resolve_text_pattern(cls, values: List[Any], pattern: str) -> str:
        """
        Resolve a text pattern that can contain:
        - Static text
        - {xpath} placeholders for dynamic values
        - {xpath|transform} placeholders with transforms

        Example pattern: "Z = {Z|roman}" -> "Z = III"
        """
        if not values or not pattern:
            return ""

        # Find all placeholders in the pattern
        placeholders = re.findall(r'\{([^}]+)\}', pattern)

        result = pattern

        for i, placeholder in enumerate(placeholders):
            parts = placeholder.split('|')
            transform = parts[1].strip() if len(parts) > 1 else None

            value = values[i]
            if transform:
                value = cls.transform_text_content(values[i], transform)

            result = result.replace(f'{{{placeholder}}}', str(value))

        return result

    def _remove_listeners(self):
        if str(self.id) not in _active_listeners:
            return

        for remove_func in _active_listeners[str(self.id)]:
            remove_func()

        del _active_listeners[str(self.id)]

    def _register_listeners(self):
        self._remove_listeners()

        # Create new listeners based on current 'art' value
        for art in self.art:
            xpath_result = XPathMatcher.resolve_xpath_value(self.dientZurDarstellungVon, art)
            if not xpath_result:
                continue

            listener, remove_func = create_attribute_change_listener(
                xpath_result.target_class,
                xpath_result.attribute_name,
                xpath_result.target_xid,
                str(self.id)
            )
            _active_listeners[str(self.id)].append(remove_func)


@event.listens_for(XP_AbstraktesPraesentationsobjekt, 'after_update', propagate=True)
def po_base_changed(mapper, connection, xp_po: XP_AbstraktesPraesentationsobjekt):
    """Update map symbol if attribute 'art' changes """
    # detect if visualisation needs to change
    # only if plan is currently visible
    layer = MapLayerRegistry().layer_by_orm_id(str(xp_po.id))
    if layer is None:
        return

    # and attributes have changed which influence the map visuals
    history = inspect(xp_po).attrs.art.history
    if not history.has_changes():
        return

    # update map display
    fr = QgsFeatureRequest().setNoAttributes().setFlags(QgsFeatureRequest.NoGeometry)
    for feat in layer.getFeatures(fr):
        id_prop = layer.customProperties().value(f'xplanung/feat-{feat.id()}')
        if id_prop == str(xp_po.id):
            with safe_edit(layer):
                feat['art'] = _coerce_to_table_representation(xp_po.__class__, 'art', xp_po.art)
                xp_po.sync_to_feature(feat)
                layer.updateFeature(feat)


@event.listens_for(XP_AbstraktesPraesentationsobjekt, 'after_delete', propagate=True)
def receive_after_delete(mapper, connection, target: XP_AbstraktesPraesentationsobjekt):
    """ Removes annotation item from canvas after deletion """
    target.remove_from_canvas()


class PPOType(Enum):
    StaticSVG = 'SVG'
    GeneratedCircle = 'Circle'
    Text = 'Text'

@dataclass
class GeneratedSymbolSettings:
    fill: Optional[str] = 'white'
    stroke: Optional[str] = 'black'
    stroke_width: Optional[float] = 0.1
    text_size: Optional[float] = 3
    symbol_size: Optional[float] = 6

@dataclass
class PPOSettings:
    config_type: PPOType
    symbol_path: Optional[str] = ""
    text_content: Optional[str] = ""
    symbol_settings: Optional[GeneratedSymbolSettings] = field(default_factory=GeneratedSymbolSettings)


class XP_PPO(PointGeometry, XP_AbstraktesPraesentationsobjekt):
    """ Punktförmiges Präsentationsobjekt """

    __tablename__ = 'xp_ppo'
    __mapper_args__ = {
        'polymorphic_identity': 'xp_ppo',
    }

    UTILITY_COLUMNS = ['form', 'text_content', 'text_size', 'symbol_size',
                       'symbol_path', 'symbol_fill', 'symbol_stroke', 'symbol_stroke_width']

    id = Column(ForeignKey("xp_po.id", ondelete='CASCADE'), primary_key=True)

    position = Column(Geometry(geometry_type='POINT'))
    drehwinkel = Column(Angle, default=0)
    skalierung = Column(Float, default=1.0)

    symbol_path = Column(String)

    def sync_to_feature(self, feat: QgsFeature, update_listener=True):
        ppo_settings = self.get_ppo_settings(dict(feat.attributeMap()))

        if not ppo_settings:
            # clear all columns used for PO visualisation
            for col in self.UTILITY_COLUMNS:
                feat[col] = ''

            if update_listener:
                self._remove_listeners()
            return

        class_prefix = self.dientZurDarstellungVon.__class__.__name__.split("_", 1)[0]
        scale_factor = SCALES.get(class_prefix, 1000) / 1000
        feat['form'] = ppo_settings.config_type
        feat['text_content'] = ppo_settings.text_content
        feat['text_size'] = ppo_settings.symbol_settings.text_size * scale_factor
        feat['symbol_size'] = ppo_settings.symbol_settings.symbol_size * scale_factor
        if ppo_settings.config_type == PPOType.StaticSVG:
            feat['symbol_path'] = ppo_settings.symbol_path
        if ppo_settings.config_type == PPOType.GeneratedCircle:
            feat['symbol_fill'] = ppo_settings.symbol_settings.fill
            feat['symbol_stroke'] = ppo_settings.symbol_settings.stroke
            feat['symbol_stroke_width'] = ppo_settings.symbol_settings.stroke_width * scale_factor

        # listeners for attribute changes
        if not update_listener:
            return

        self._register_listeners()

    def get_ppo_settings(self, feat_attributes: dict) -> Optional[PPOSettings]:
        if not self.art:
            return None

        for node_name, entry in PPO_CONFIG.items():
            config_type_node = entry.get('type', {})
            if not isinstance(config_type_node, dict):
                raise Exception(f'PPO Config entry {node_name} has malformed entry "type"')

            attribute_nodes = entry.get('attribute', [])

            for attr_node in attribute_nodes:
                expected_value = attr_node.get('value')
                expected_value_type = attr_node.get('type')
                config_xpath = attr_node.get('xpath')
                match_mode = attr_node.get('match', 'any')  # default to 'any'
                if not config_xpath:
                    continue

                # Check if any of the 'art' values match the config xpath
                xpath_matches = XPathMatcher.xpath_matches_config(self.art, config_xpath, match_mode)
                if not xpath_matches:
                    continue

                # Collect all matching values from the database
                parent_obj = self.dientZurDarstellungVon
                xpath_results = []
                for xpath_option in self.art:
                    result = XPathMatcher.resolve_xpath_value(
                        parent_obj, xpath_option, _index=self.index[0] if self.index else None
                    )
                    if result:
                        xpath_results.append(result)

                if match_mode == 'all' and len(xpath_results) < len(config_xpath):
                    continue  # Not all paths resolved successfully

                # Now check all collected xpath results
                match_found = False
                for result in xpath_results:
                    value = result.value

                    # Type check
                    if expected_value_type:
                        if not type(value).__name__ == expected_value_type:
                            continue

                    compare_value = value
                    if isinstance(value, enum.Enum):
                        compare_value = value.value

                    # Value check
                    if expected_value is not None:
                        if isinstance(expected_value, list):
                            if not compare_value in expected_value:
                                continue
                        elif str(compare_value) != str(expected_value):
                            continue

                    # If we pass checks
                    match_found = True
                    break  # Don't need to check more values

                if not match_found:
                    continue

                if 'svg' in config_type_node:
                    svg_info = config_type_node.get('svg')
                    symbol_path = svg_info.get('path', node_name)
                    if Path(symbol_path).parent == Path('.'):
                        # try access internal svg symbols
                        symbol_category = svg_info.get('category')
                        symbol_path = Path(BASE_DIR, 'symbole', symbol_category, symbol_path).as_posix()

                    return PPOSettings(
                        config_type=PPOType.StaticSVG,
                        symbol_path=symbol_path
                    )

                if 'circle' in config_type_node:
                    symbol_node = config_type_node.get('circle')
                    text_content = symbol_node.get('static-text')
                    pattern = symbol_node.get('pattern')

                    if not text_content:
                        text_content = self.text_from_xpath_results(xpath_results, pattern)

                    return PPOSettings(
                        config_type=PPOType.GeneratedCircle,
                        text_content=text_content,
                        symbol_settings=GeneratedSymbolSettings(
                            fill=symbol_node.get('fill'),
                            stroke=symbol_node.get('stroke'),
                            stroke_width=symbol_node.get('stroke-width'),
                        )
                    )

                if 'text' in config_type_node:
                    text_node = config_type_node.get('text')
                    pattern = text_node.get('pattern')

                    text_content = self.text_from_xpath_results(xpath_results, pattern)

                    return PPOSettings(
                        config_type=PPOType.Text,
                        text_content=text_content
                    )

    def asFeature(self, fields=None):
        feat = super().asFeature(fields)

        self.sync_to_feature(feat)

        return feat

    @classmethod
    def asLayer(cls, srid, plan_xid, name=None, geom_type=None):
        layer = super().asLayer(srid, plan_xid, name, geom_type)

        # add symbol_path field used for label rendering
        with safe_edit(layer):
            for col in cls.UTILITY_COLUMNS:
                layer.addAttribute(QgsField(col, QVariant.String, 'string'))

        form_config = layer.editFormConfig()
        field_index = layer.fields().indexOf('symbol_path')
        form_config.setReadOnly(field_index, True)
        layer.setEditFormConfig(form_config)

        # presentation objects should have no renderer, configure labels instead
        renderer = QgsNullSymbolRenderer()
        layer.setRenderer(renderer)

        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "if(\"form\" = 'SVG', ' ', \"text_content\")"
        label_settings.isExpression = True
        label_settings.drawLabels = True
        label_settings.placement = Qgis.LabelPlacement.OverPoint
        label_settings.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired)

        text_format = QgsTextFormat()
        text_format.setSizeUnit(QgsUnitTypes.RenderMapUnits)
        exp = f"if(\"form\" = 'SVG', \"skalierung\" * \"symbol_size\", \"skalierung\" * \"text_size\")"
        size_prop = QgsProperty.fromExpression(exp)
        angle_prop = QgsProperty.fromField("drehwinkel")
        prop_collection = QgsPropertyCollection()
        prop_collection.setProperty(QgsPalLayerSettings.Size, size_prop)
        prop_collection.setProperty(QgsPalLayerSettings.LabelRotation, angle_prop)

        background = QgsTextBackgroundSettings()
        background.setStrokeWidthUnit(QgsUnitTypes.RenderMapUnits)
        background.setSizeType(QgsTextBackgroundSettings.SizeFixed)
        background.setSizeUnit(QgsUnitTypes.RenderMapUnits)
        background_enable_prop = QgsProperty.fromExpression("\"form\" != 'Text'")
        prop_collection.setProperty(QgsPalLayerSettings.ShapeDraw, background_enable_prop)
        background_form_prop = QgsProperty.fromField("form")
        prop_collection.setProperty(QgsPalLayerSettings.ShapeKind, background_form_prop)
        fill_form_prop = QgsProperty.fromField("symbol_fill")
        prop_collection.setProperty(QgsPalLayerSettings.ShapeFillColor, fill_form_prop)
        stroke_form_prop = QgsProperty.fromField("symbol_stroke")
        prop_collection.setProperty(QgsPalLayerSettings.ShapeStrokeColor, stroke_form_prop)
        strokewidth_form_prop = QgsProperty.fromExpression("\"symbol_stroke_width\" * \"skalierung\"")
        prop_collection.setProperty(QgsPalLayerSettings.ShapeStrokeWidth, strokewidth_form_prop)
        svg_symbol_prop = QgsProperty.fromField("symbol_path")
        prop_collection.setProperty(QgsPalLayerSettings.ShapeSVGFile, svg_symbol_prop)
        shape_size_prop = QgsProperty.fromExpression("\"symbol_size\" * \"skalierung\"")
        prop_collection.setProperty(QgsPalLayerSettings.ShapeSizeX, shape_size_prop)
        prop_collection.setProperty(QgsPalLayerSettings.ShapeSizeY, shape_size_prop)

        # create the labeling configuration and apply it to the layer
        text_format.setBackground(background)
        label_settings.setDataDefinedProperties(prop_collection)
        label_settings.setFormat(text_format)
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabeling(labeling)
        layer.setLabelsEnabled(True)

        return layer

    @classmethod
    def avoid_export(cls):
        return ['symbol_path']

    @classmethod
    def hidden_inputs(cls):
        return ['symbol_path']



class XP_PTO(PointGeometry, XP_AbstraktesPraesentationsobjekt):
    """ Textförmiges Präsentationsobjekt mit punktförmiger Festlegung der Textposition """

    __tablename__ = 'xp_pto'
    __mapper_args__ = {
        'polymorphic_identity': 'xp_pto',
    }
    __default_size__ = 3

    id = Column(ForeignKey("xp_po.id", ondelete='CASCADE'), primary_key=True)

    schriftinhalt = Column(String)

    skalierung = Column(Float, default=1.0)
    position = Column(Geometry(geometry_type='POINT'))
    drehwinkel = Column(Angle, default=0)

    def sync_to_feature(self, feat: QgsFeature, update_listener=True):
        class_prefix = self.dientZurDarstellungVon.__class__.__name__.split("_", 1)[0]
        scale_factor = SCALES.get(class_prefix, 1000) / 1000
        feat['text_size'] = self.__default_size__ * scale_factor

        feat['schriftinhalt'] = self.schriftinhalt
        if not self.schriftinhalt:
            # Collect all matching values from the database
            parent_obj = self.dientZurDarstellungVon
            xpath_results = []
            for xpath_option in self.art:
                result = XPathMatcher.resolve_xpath_value(parent_obj, xpath_option)
                if result:
                    xpath_results.append(result)

            if xpath_results:
                text_content = self.text_from_xpath_results(xpath_results)
                feat['schriftinhalt'] = text_content

        # listeners for attribute changes
        if not update_listener:
            return

        self._register_listeners()

    def asFeature(self, fields=None):
        feat = super().asFeature(fields)

        self.sync_to_feature(feat)

        return feat

    @classmethod
    def asLayer(cls, srid, plan_xid, name=None, geom_type=None):
        layer = super().asLayer(srid, plan_xid, name, geom_type)

        with safe_edit(layer):
            layer.addAttribute(QgsField('text_size', QVariant.String, 'string'))

        # presentation objects should have no renderer, configure labels instead
        renderer = QgsNullSymbolRenderer()
        layer.setRenderer(renderer)

        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "schriftinhalt"
        label_settings.drawLabels = True
        label_settings.placement = Qgis.LabelPlacement.OverPoint
        label_settings.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired)

        text_format = QgsTextFormat()
        text_format.setSizeUnit(QgsUnitTypes.RenderMapUnits)
        size_prop = QgsProperty.fromExpression('"skalierung" * "text_size"')
        angle_prop = QgsProperty.fromField("drehwinkel")
        prop_collection = QgsPropertyCollection()
        prop_collection.setProperty(QgsPalLayerSettings.Size, size_prop)
        prop_collection.setProperty(QgsPalLayerSettings.LabelRotation, angle_prop)

        # create the labeling configuration and apply it to the layer
        label_settings.setDataDefinedProperties(prop_collection)
        label_settings.setFormat(text_format)
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabeling(labeling)
        layer.setLabelsEnabled(True)

        return layer


class XP_Nutzungsschablone(PointGeometry, XP_AbstraktesPraesentationsobjekt):
    """ Modelliert eine Nutzungsschablone. Die darzustellenden Attributwerte werden zeilenweise in die
        Nutzungsschablone geschrieben """

    def __init__(self):
        super(XP_Nutzungsschablone, self).__init__()
        self.data_attributes = BuildingTemplateCellDataType.as_default()

    def set_defaults(self, row_count=3):
        self.data_attributes = BuildingTemplateCellDataType.as_default(row_count)

    __tablename__ = 'xp_nutzungsschablone'
    __mapper_args__ = {
        'polymorphic_identity': 'xp_nutzungsschablone',
    }
    __readonly_columns__ = ['position', 'spaltenAnz', 'zeilenAnz']

    id = Column(ForeignKey("xp_po.id", ondelete='CASCADE'), primary_key=True)

    skalierung = Column(Float, default=1.0)
    position = Column(Geometry(geometry_type='POINT'))
    drehwinkel = Column(Angle, default=0)

    spaltenAnz = Column(Integer, nullable=False, default=2)
    zeilenAnz = Column(Integer, nullable=False, default=3)

    # non xplanung attributes
    data_attributes = Column(ARRAY(Enum(BuildingTemplateCellDataType)))

    @classmethod
    def renderer(cls, geom_type: GeometryType = None):
        return BuildingTemplateRenderer('sagisxplanung.buildingtemplate')

    @classmethod
    def asLayer(cls, srid, plan_xid, name=None, geom_type=None):
        layer = super().asLayer(srid, plan_xid, name, geom_type)
        with safe_edit(layer):
            layer.addAttribute(QgsField("id", QVariant.String, 'string'))
            layer.addAttribute(QgsField("cell_content", QVariant.String, 'string'))
        return layer

    def asFeature(self, fields: QgsFields = None):
        feat = super().asFeature(fields)
        feat['id'] = str(self.id)

        if hasattr(self.dientZurDarstellungVon, 'template_cell_data'):
            cell_data = self.dientZurDarstellungVon.template_cell_data(self.data_attributes)
            feat['cell_content'] = TableCell.serialize_cells(cell_data)
        return feat

    def toCanvas(self, layer_group, plan_xid=None):

        if not self.position:
            geom = self.dientZurDarstellungVon.geometry().centroid()
            self.position = WKBElement(geom.asWkb(), srid=self.dientZurDarstellungVon.position.srid)

        super().toCanvas(layer_group, plan_xid)

    @classmethod
    def avoid_export(cls):
        return ['hidden', 'data_attributes']
