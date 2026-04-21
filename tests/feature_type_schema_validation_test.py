import datetime
import os
import uuid

import pytest
from geoalchemy2 import Geometry, WKTElement
from lxml import etree
from sqlalchemy import ARRAY
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import RelationshipProperty

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.BPlan.BP_Basisobjekte.enums import BP_PlanArt
from SAGisXPlanung.BPlan.BP_Basisobjekte.feature_types import BP_Plan
from SAGisXPlanung.GML.GMLWriter import GMLWriter
from SAGisXPlanung.core.mixins.mixins import FeatureType
from SAGisXPlanung.core.abstract_types import is_abstract_in_version
from SAGisXPlanung.utils import CLASSES, OBJECT_BASE_TYPES, PLAN_BASE_TYPES, BEREICH_BASE_TYPES


SCHEMA_VERSIONS = ("53", "60")
XPLAN_VERSION_MAP = {
    "53": XPlanVersion.FIVE_THREE,
    "60": XPlanVersion.SIX,
}
MAX_RECURSION_DEPTH = 4


def _minimal_plan() -> BP_Plan:
    plan = BP_Plan()
    plan.name = "feature-schema-validation"
    plan.planArt = [BP_PlanArt.BPlan]
    plan.raeumlicherGeltungsbereich = WKTElement(
        "MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)))",
        srid=4326,
    )
    return plan


def _is_instantiable_xplan_class(model_cls: type) -> bool:
    mapper = sa_inspect(model_cls)
    if mapper.polymorphic_on is not None and mapper.polymorphic_identity is None:
        return False
    return True


def _iter_feature_classes() -> list[type]:
    classes = []
    seen = set()
    excluded = {*OBJECT_BASE_TYPES, *PLAN_BASE_TYPES, *BEREICH_BASE_TYPES}

    for model_cls in CLASSES.values():
        if model_cls in seen:
            continue
        seen.add(model_cls)

        if not isinstance(model_cls, type):
            continue
        if model_cls in excluded:
            continue
        if ".feature_types" not in model_cls.__module__:
            continue
        if not issubclass(model_cls, FeatureType):
            continue
        if not hasattr(model_cls, "element_order"):
            continue
        if not _is_instantiable_xplan_class(model_cls):
            continue

        classes.append(model_cls)

    return sorted(classes, key=lambda cls: f"{cls.__module__}.{cls.__name__}")


FEATURE_CLASSES = _iter_feature_classes()


def _geometry_wkt(geometry_type: str) -> str:
    geometry_type = (geometry_type or "").upper()
    if "LINE" in geometry_type:
        return "LINESTRING (30.5 10.2, 31.0 11.8, 32.25 12.0)"
    if "POINT" in geometry_type:
        return "POINT (7 52)"
    return "MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)))"


def _first_enum_value(enum_type: type, version: XPlanVersion):
    for enum_value in enum_type:
        if enum_value.value is None:
            continue
        if hasattr(enum_value, "version") and enum_value.version not in [None, version]:
            continue
        return enum_value
    return None


def _sample_value(column_type, version: XPlanVersion):
    if isinstance(column_type, Geometry):
        srid = column_type.srid if column_type.srid not in (-1, None) else 4326
        return WKTElement(_geometry_wkt(column_type.geometry_type), srid=srid)

    enum_type = getattr(column_type, "enum_class", None)
    if enum_type is not None:
        return _first_enum_value(enum_type, version)

    if isinstance(column_type, ARRAY):
        item_type = column_type.item_type
        item_enum = getattr(item_type, "enum_class", None)
        if item_enum is not None:
            enum_value = _first_enum_value(item_enum, version)
            return [enum_value] if enum_value is not None else []

        item_python_type = getattr(item_type, "python_type", None)
        if item_python_type is str:
            return ["x"]
        if item_python_type is int:
            return [1]
        if item_python_type is float:
            return [1.0]
        if item_python_type is datetime.date:
            return [datetime.date(2024, 1, 1)]
        return []

    try:
        python_type = column_type.python_type
    except (NotImplementedError, AttributeError):
        return None

    if python_type is str:
        return "x"
    if python_type is bool:
        return True
    if python_type is int:
        return 1
    if python_type is float:
        return 1.0
    if python_type is datetime.date:
        return datetime.date(2024, 1, 1)
    if python_type is datetime.datetime:
        return datetime.datetime(2024, 1, 1, 12, 0, 0)
    if python_type is bytes:
        return b"data"
    if python_type is uuid.UUID:
        return uuid.uuid4()
    return None


def _populate_scalar_attributes(instance, version: XPlanVersion) -> None:
    for attr_name, mapper_property in instance.__class__.element_order(version=version, ret_fmt="sqla"):
        if isinstance(mapper_property, RelationshipProperty):
            continue
        if getattr(instance, attr_name, None) is not None:
            continue

        value = _sample_value(mapper_property.columns[0].type, version)
        if value is not None:
            setattr(instance, attr_name, value)


def _relationship_is_required(relation: RelationshipProperty) -> bool:
    if relation.info.get("nullable") is False:
        return True

    local_columns = [col for col in relation.local_columns if not col.primary_key]
    return bool(local_columns) and any(col.nullable is False for col in local_columns)


def _create_instance(
    model_cls: type,
    version: XPlanVersion,
    depth: int,
    stack: set[type],
):
    instance = model_cls()

    if hasattr(instance, "id") and getattr(instance, "id", None) is None:
        instance.id = uuid.uuid4()

    _populate_scalar_attributes(instance, version)

    if depth >= MAX_RECURSION_DEPTH:
        return instance

    stack.add(model_cls)
    try:
        for attr_name, mapper_property in model_cls.element_order(version=version, ret_fmt="sqla"):
            if not isinstance(mapper_property, RelationshipProperty):
                continue
            if not _relationship_is_required(mapper_property):
                continue

            target_cls = mapper_property.mapper.class_
            if target_cls in stack:
                continue
            if not _is_instantiable_xplan_class(target_cls):
                continue

            related = _create_instance(target_cls, version, depth + 1, stack)
            if mapper_property.uselist:
                current = getattr(instance, attr_name)
                if not current:
                    current.append(related)
            else:
                if getattr(instance, attr_name) is None:
                    setattr(instance, attr_name, related)
    finally:
        stack.remove(model_cls)

    return instance


@pytest.fixture(scope="session")
def xplan_schemas():
    schema_dir = os.path.join(os.path.dirname(__file__), "xsd")
    schemas = {}
    for version in SCHEMA_VERSIONS:
        schema_path = os.path.join(schema_dir, version, "XPlanung-Operationen.xsd")
        schema_root = etree.parse(schema_path)
        schemas[version] = etree.XMLSchema(schema_root)
    return schemas


@pytest.mark.parametrize("schema_version", SCHEMA_VERSIONS)
@pytest.mark.parametrize("model_cls", FEATURE_CLASSES, ids=lambda cls: cls.__name__)
def test_feature_type_export_validates_xsd(model_cls, schema_version, xplan_schemas):
    version = XPLAN_VERSION_MAP[schema_version]

    if hasattr(model_cls, "xp_versions") and version not in model_cls.xp_versions:
        pytest.skip(f"{model_cls.__name__} is not part of schema version {schema_version}")

    if is_abstract_in_version(model_cls, version):
        pytest.skip(f"{model_cls.__name__} is abstract in schema version {schema_version}")

    writer = GMLWriter(_minimal_plan(), version=version)
    feature_instance = _create_instance(model_cls, version, depth=0, stack=set())

    before_count = len(writer.root)
    writer.write_feature(feature_instance)

    for feature_member in writer.root[before_count:]:
        xplan_schemas[schema_version].assertValid(feature_member[0])
