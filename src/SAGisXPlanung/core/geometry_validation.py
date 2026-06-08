import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Callable

import requests
from sqlalchemy import text, select, func

from SAGisXPlanung import Session
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Objekt, XP_Bereich
from SAGisXPlanung.config import table_name_to_class
from SAGisXPlanung.core.converter_tasks import export_plan

logger = logging.getLogger(__name__)

GRID_TOLERANCE = 0.001


class GeometryViolationType(Enum):
    """ Gibt an, welcher Grund einen Überschneidungsfehler hevorgerufen hat. """

    Planinhalt = 'Flächenschlussobjekt weist Überschneidung auf'
    Bereich = 'Planinhalt liegt nicht vollständig im Bereich'
    Plan = 'Bereich liegt nicht vollständig im Geltungsbereich des Plans'
    NotCovered = 'Kein Flächenschluss vorliegend'
    FullyWithin = 'Planinhalt wird vollständig überdeckt'


@dataclass
class ValidationResult:
    xid: str
    xtype: type
    error_msg: str = None
    geom_wkt: str = None
    intersection_type: GeometryViolationType = None
    other_xid: str = None
    other_xtype: type = None

    def __post_init__(self):
        if self.intersection_type is not None and self.error_msg is None:
            self.error_msg = self.intersection_type.value
        elif self.error_msg is None:
            self.error_msg = 'Fehler in der Geometrievalidierung'


def _validate_overlaps(plan_id, short_plan_type: str) -> List[ValidationResult]:
    """ validates if any of the plan contents overlap each other"""
    result = []

    with Session.begin() as session:
        stmt = text(f"""
            WITH all_objekt_positions AS (
                SELECT id, flaechenschluss, position FROM bp_objekt
                UNION ALL
                SELECT id, flaechenschluss, position FROM fp_objekt
                UNION ALL
                SELECT id, flaechenschluss, position FROM lp_objekt
                UNION ALL
                SELECT id, flaechenschluss, position FROM so_objekt
            )
            SELECT
                ST_AsText(polygon_geom) AS wkt,
                xp_a.id AS a_xid, xp_a.type AS a_type,
                xp_b.id AS b_xid, xp_b.type AS b_type,
                st_within(a.position, b.position) as is_within
            FROM all_objekt_positions a
                CROSS JOIN all_objekt_positions b
                INNER JOIN xp_objekt xp_a ON a.id = xp_a.id
                INNER JOIN xp_objekt xp_b ON b.id = xp_b.id
                INNER JOIN {short_plan_type}_bereich ON xp_a."gehoertZuBereich_id" = {short_plan_type}_bereich.id
                                      AND xp_b."gehoertZuBereich_id" = {short_plan_type}_bereich.id
                CROSS JOIN LATERAL (
                    SELECT ST_CollectionExtract(
                        ST_Intersection(a.position, b.position, {GRID_TOLERANCE}), 
                        GREATEST(st_dimension(a.position), st_dimension(b.position)) + 1
                    ) AS polygon_geom
                ) AS intersection_geom
            WHERE
                a.id < b.id
                AND ST_IsValid(a.position)
                AND ST_IsValid(b.position)
                AND a.flaechenschluss = TRUE
                AND b.flaechenschluss = TRUE
                AND {short_plan_type}_bereich."gehoertZuPlan_id" = :plan_id
                AND (
                    ST_Overlaps(a.position, b.position)
                    OR st_within(a.position, b.position)
                )
                AND NOT ST_IsEmpty(polygon_geom);
        """) # nosec B608 (only trusted input)

        res = session.execute(stmt, {"plan_id": plan_id}).all()
        for row in res:
            error_type = GeometryViolationType.FullyWithin if row.is_within else GeometryViolationType.Planinhalt
            validation_result = ValidationResult(
                xid=str(row.a_xid),
                xtype=table_name_to_class(row.a_type),
                geom_wkt=row.wkt,
                intersection_type=error_type,
                other_xid=str(row.b_xid),
                other_xtype=table_name_to_class(row.b_type),
            )
            result.append(validation_result)

        return result


def _validate_within_bounds(plan_id, short_plan_type: str) -> List[ValidationResult]:
    """ validate if all geometries of plan contents are within the bounds of the plan """
    result = []

    with Session() as session:
        stmt = text(f"""
            SELECT
                ST_AsText(
                    ST_CollectionExtract(
                        ST_Difference(xp_bereich.geltungsbereich, xp_plan."raeumlicherGeltungsbereich")
                    )
                ) as wkt,
                xp_bereich.id as bereich_id,
                xp_bereich.type as bereich_type,
                xp_plan.id as plan_id,
                xp_plan.type as plan_type
            FROM {short_plan_type}_bereich
            JOIN xp_bereich ON {short_plan_type}_bereich.id = xp_bereich.id
            JOIN xp_plan ON xp_plan.id = {short_plan_type}_bereich."gehoertZuPlan_id"
            WHERE
                xp_plan.id = :planid AND
                ST_IsValid(xp_bereich.geltungsbereich) AND
                NOT st_coveredby(xp_bereich.geltungsbereich, st_buffer(xp_plan."raeumlicherGeltungsbereich", {GRID_TOLERANCE}));
        """) # nosec B608 (only trusted input)
        stmt = stmt.bindparams(planid=plan_id)

        res = session.execute(stmt).all()
        for row in res:
            validation_result = ValidationResult(
                xid=str(row.bereich_id),
                xtype=table_name_to_class(row.bereich_type),
                geom_wkt=row.wkt,
                intersection_type=GeometryViolationType.Plan,
                other_xid=str(row.plan_id),
                other_xtype=table_name_to_class(row.plan_type)
            )
            result.append(validation_result)

        stmt = text(f"""
            WITH all_objekt_positions AS (
                SELECT id, position FROM bp_objekt
                UNION ALL
                SELECT id, position FROM fp_objekt
                UNION ALL
                SELECT id, position FROM lp_objekt
                UNION ALL
                SELECT id, position FROM so_objekt
            )
            SELECT
                ST_AsText(
                    ST_CollectionExtract(
                        ST_Difference(a.position, xp_bereich.geltungsbereich)
                    )
                )  as wkt,
                xp_a.id AS a_xid,
                xp_a.type AS a_type,
                {short_plan_type}_bereich."gehoertZuPlan_id" AS plan_id,
                xp_bereich.id AS bereich_id,
                xp_bereich.type as bereich_type
            FROM all_objekt_positions a
            JOIN xp_objekt xp_a ON a.id = xp_a.id
            JOIN {short_plan_type}_bereich ON {short_plan_type}_bereich.id = xp_a."gehoertZuBereich_id"
            JOIN xp_bereich ON {short_plan_type}_bereich.id = xp_bereich.id
            WHERE
                {short_plan_type}_bereich."gehoertZuPlan_id" = :planid AND
                ST_IsValid(a.position) AND
                NOT st_coveredby(a.position, st_buffer(xp_bereich.geltungsbereich, {GRID_TOLERANCE}));
        """) # nosec B608 (only trusted input)
        stmt = stmt.bindparams(planid=plan_id)

        res = session.execute(stmt).all()
        for row in res:
            validation_result = ValidationResult(
                xid=str(row.a_xid),
                xtype=table_name_to_class(row.a_type),
                geom_wkt=row.wkt,
                intersection_type=GeometryViolationType.Bereich,
                other_xid=str(row.bereich_id),
                other_xtype=table_name_to_class(f'{short_plan_type}_bereich')
            )
            result.append(validation_result)

        return result


def _validate_geometry_valid(plan_id, short_plan_type: str) -> List[ValidationResult]:
    result = []

    with Session() as session:
        stmt = text(f"""
            WITH all_objekt_positions AS (
                SELECT id, flaechenschluss, position FROM bp_objekt
                UNION ALL
                SELECT id, flaechenschluss, position FROM fp_objekt
                UNION ALL
                SELECT id, flaechenschluss, position FROM lp_objekt
                UNION ALL
                SELECT id, flaechenschluss, position FROM so_objekt
            ),
            bereiche AS (
                SELECT
                    xp_bereich.id,
                    xp_bereich.geltungsbereich,
                    xp_bereich.type
                FROM xp_bereich
                JOIN {short_plan_type}_bereich ON {short_plan_type}_bereich.id = xp_bereich.id
                WHERE {short_plan_type}_bereich."gehoertZuPlan_id" = :planid
            ),
            objects AS (
                SELECT
                    o.id,
                    o.position,
                    xp_objekt.type
                FROM all_objekt_positions o
                JOIN xp_objekt ON o.id = xp_objekt.id
                JOIN bereiche b ON b.id = xp_objekt."gehoertZuBereich_id"
            )
            SELECT
                id,
                ST_AsText(geom) as wkt,
                type,
                ST_IsValid(geom) AS is_valid,
                ST_IsValidReason(geom) AS invalid_reason,
                NOT ST_OrderingEquals(geom, ST_RemoveRepeatedPoints(geom)) AS has_duplicate_vertices,
                ST_IsPolygonCCW(geom) AS is_ccw
            FROM (
                SELECT id, position AS geom, type FROM objects
                UNION ALL
                SELECT id, geltungsbereich AS geom, type FROM bereiche
                UNION ALL
                SELECT id, "raeumlicherGeltungsbereich" AS geom, 'xp_plan' FROM xp_plan
                WHERE xp_plan.id = :planid
            ) AS all_geometries;
        """) # nosec B608 (only trusted input)
        stmt = stmt.bindparams(planid=plan_id)

        res = session.execute(stmt).all()
        for row in res:
            if row.is_valid is False:
                validation_result = ValidationResult(
                    xid=str(row.id),
                    xtype=table_name_to_class(row.type),
                    geom_wkt=row.wkt,
                    error_msg=row.invalid_reason
                )
                result.append(validation_result)
            if row.is_ccw is False:
                validation_result = ValidationResult(
                    xid=str(row.id),
                    xtype=table_name_to_class(row.type),
                    geom_wkt=row.wkt,
                    error_msg='Falscher Polygon-Umlaufsinn'
                )
                result.append(validation_result)
            if row.has_duplicate_vertices is True:
                validation_result = ValidationResult(
                    xid=str(row.id),
                    xtype=table_name_to_class(row.type),
                    geom_wkt=row.wkt,
                    error_msg='Planinhalt besitzt doppelte Stützpunkte'
                )
                result.append(validation_result)

        return result


def _validate_gaps(plan_id, short_plan_type: str) -> List[ValidationResult]:
    # validate that the union of all plan contents is equal to the geltungsbereich => find gaps
    result = []
    with Session.begin() as session:
        stmt = text(f"""
            SELECT 
                ST_AsText((ST_dump(st_difference(xp_plan."raeumlicherGeltungsbereich", plan_contents.united))).geom) as wkt, xp_plan.id
            FROM
                (
                SELECT ST_union(objects.position) as united, {short_plan_type}_bereich."gehoertZuPlan_id" AS plan_id
                FROM
                (
                    SELECT id, flaechenschluss, position FROM bp_objekt
                    UNION ALL
                    SELECT id, flaechenschluss, position FROM fp_objekt
                    UNION ALL
                    SELECT id, flaechenschluss, position FROM lp_objekt
                    UNION ALL
                    SELECT id, flaechenschluss, position FROM so_objekt
                ) objects
                INNER JOIN xp_objekt xp_a ON xp_a.id = objects.id
                INNER JOIN {short_plan_type}_bereich ON xp_a."gehoertZuBereich_id" = {short_plan_type}_bereich.id
                WHERE objects.flaechenschluss = TRUE AND st_isvalid(objects.position)
                GROUP BY {short_plan_type}_bereich."gehoertZuPlan_id"
                ) as plan_contents
            INNER JOIN xp_plan ON plan_contents.plan_id = xp_plan.id
            WHERE xp_plan.id = :plan_id;
        """) # nosec B608 (only trusted input)
        res = session.execute(stmt, {"plan_id": plan_id})
        for row in res:
            validation_result = ValidationResult(
                xid=str(row.id),
                xtype=XP_Plan,
                geom_wkt=row.wkt,
                intersection_type=GeometryViolationType.NotCovered
            )
            result.append(validation_result)

        return result


FULLY_WITHIN_RE = re.compile(
    r"gml id (?P<obj1>GML_[^\s]+).*gml id (?P<obj2>GML_[^\s]+) vollständig",
    re.IGNORECASE,
)

NOT_IN_PLAN_RE = re.compile(
    r"Objekt mit der gml id (?P<obj>GML_[^\s]+) liegt nicht vollständig im Geltungsbereich "
    r"des Plans mit der gml id (?P<plan>GML_[^\s]+)",
    re.IGNORECASE,
)

POINT_RE = re.compile(
    r"\((?P<x>-?\d+(?:\.\d+)?)\s*,\s*(?P<y>-?\d+(?:\.\d+)?)\)"
)

FLAECHENSCHLUSS_RE = re.compile(
    r"Flächenschlussobjekt mit der gml id (?P<obj>GML_[^\s]+)",
    re.IGNORECASE,
)

GML_ID_RE = re.compile(r"GML_([A-Za-z0-9\-]+)")


class XPlanValidationError(Exception):
    pass


def collect_xids(messages: list[str]) -> set[str]:
    xids: set[str] = set()

    for message in messages:
        xids.update(GML_ID_RE.findall(message))

    return xids


def _strip_gml_prefix(value: str | None) -> str | None:
    if value is None:
        return None

    return value[4:] if value.startswith("GML_") else value


def _points_to_wkt(message: str) -> str | None:
    matches = list(POINT_RE.finditer(message))

    if not matches:
        return None

    points = [(match.group("x"),match.group("y")) for match in matches]

    if len(points) == 1:
        x, y = points[0]
        return f"POINT({x} {y})"

    multipoint = ",".join(f"({x} {y})" for x, y in points)
    return f"MULTIPOINT({multipoint})"


def _collect_xids(messages: list[str]) -> set[str]:
    xids: set[str] = set()

    for message in messages:
        xids.update(GML_ID_RE.findall(message))

    return xids


def _resolve_type(type_lookup: dict[str, type], xid: str | None) -> type | None:
    if xid is None:
        return None

    return type_lookup.get(xid)


def _parse_geometric_message(message: str, type_lookup: dict[str, type]) -> ValidationResult:
    match = FULLY_WITHIN_RE.search(message)
    if match:
        xid = _strip_gml_prefix(match.group("obj1"))
        other_xid = _strip_gml_prefix(match.group("obj2"))
        other_xtype = _resolve_type(type_lookup, other_xid)
        stmt = select(func.ST_AsText(getattr(other_xtype, other_xtype.__geometry_column_name__))).filter_by(id=other_xid)
        with Session() as session:
            covered_wkt = session.execute(stmt).scalar_one()
        return ValidationResult(
            xid=xid,
            xtype=_resolve_type(type_lookup, xid),
            other_xid=other_xid,
            other_xtype=other_xtype,
            intersection_type=GeometryViolationType.FullyWithin,
            geom_wkt=covered_wkt,
            error_msg=message,
        )

    match = NOT_IN_PLAN_RE.search(message)
    if match:
        xid = _strip_gml_prefix(match.group("obj"))
        other_xid = _strip_gml_prefix(match.group("plan"))
        return ValidationResult(
            xid=xid,
            xtype=_resolve_type(type_lookup, xid),
            other_xid=other_xid,
            other_xtype=_resolve_type(type_lookup, other_xid),
            intersection_type=GeometryViolationType.Bereich,
            geom_wkt=_points_to_wkt(message),
            error_msg=message,
        )

    if "Lücke" in message:
        match = FLAECHENSCHLUSS_RE.search(message)

        xid = _strip_gml_prefix(match.group("obj")) if match else None

        return ValidationResult(
            xid=xid,
            xtype=_resolve_type(type_lookup, xid),
            intersection_type=GeometryViolationType.NotCovered,
            geom_wkt=_points_to_wkt(message),
            error_msg=message,
        )

    if "Flächenschlussbedingung" in message:
        match = FLAECHENSCHLUSS_RE.search(message)

        xid = _strip_gml_prefix(match.group("obj")) if match else None

        return ValidationResult(
            xid=xid,
            xtype=_resolve_type(type_lookup, xid),
            intersection_type=GeometryViolationType.Planinhalt,
            geom_wkt=_points_to_wkt(message),
            error_msg=message,
        )

    unknown_xid = None

    ids = GML_ID_RE.findall(message)
    if ids:
        unknown_xid = ids[0]

    return ValidationResult(
        xid=unknown_xid,
        xtype=_resolve_type(type_lookup, unknown_xid),
        error_msg=message,
    )


def _build_type_lookup(session, xids: set[str]) -> dict[str, type]:
    lookup: dict[str, type] = {}

    for obj in session.scalars(select(XP_Objekt).where(XP_Objekt.id.in_(xids))):
        lookup[str(obj.id)] = type(obj)

    for bereich in session.scalars(select(XP_Bereich).where(XP_Bereich.id.in_(xids))):
        lookup[str(bereich.id)] = type(bereich)

    for plan in session.scalars(select(XP_Plan).where(XP_Plan.id.in_(xids))):
        lookup[str(plan.id)] = type(plan)

    return lookup


def validate_geometric_xplan_validator(plan_id, set_status: Callable) -> List[ValidationResult]:
    set_status('XPlanGML erstellen...')
    gml_data = export_plan(out_file_format="gml", plan_xid=plan_id)

    headers = {"X-Filename": 'xplan.gml', 'Content-Type': 'application/gml+xml'}
    query_params = {
        "name": 'validation',
        "skipSemantisch": 'true',
        "skipGeometrisch": 'false',
        "skipFlaechenschluss": 'false',
        "skipGeltungsbereich": 'false',
        "skipLaufrichtung": 'false',
        "profiles": ''
    }

    set_status('XPlanGML hochladen und validieren...')
    upload_url = "https://www.xplanungsplattform.de/xplan-api-validator/xvalidator/api/v1/validate"
    r = requests.post(upload_url, headers=headers, data=gml_data.decode('utf-8'), params=query_params, timeout=10)
    r.raise_for_status()

    result_json = r.json()
    syntactic = result_json.get("validationResult", {}).get("syntaktisch", {})

    if not syntactic.get("valid", True):
        messages = syntactic.get("messages", [])
        raise XPlanValidationError("XPlan validator reported syntactic errors:\n"+ "\n".join(messages))

    geometric = result_json.get("validationResult", {}).get("geometrisch", {})

    messages = [
        *geometric.get("errors", []),
        *geometric.get("warnings", []),
    ]

    xids = _collect_xids(messages)

    with Session() as session:
        type_lookup = _build_type_lookup(session=session, xids=xids)

    missing = xids - set(type_lookup.keys())
    if missing:
        logger.debug(f"Unknown XPlan object ids returned by validator {missing}")

    return [_parse_geometric_message(message, type_lookup) for message in messages]



INTERNAL_VALIDATION_FUNCTIONS = [
    _validate_geometry_valid,
    _validate_within_bounds,
    _validate_overlaps,
    _validate_gaps
]
