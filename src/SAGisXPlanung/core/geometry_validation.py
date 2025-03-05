import logging
from dataclasses import dataclass
from enum import Enum
from typing import List

from sqlalchemy import text

from SAGisXPlanung import Session
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.config import table_name_to_class

logger = logging.getLogger(__name__)


class GeometryIntersectionType(Enum):
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
    intersection_type: GeometryIntersectionType = None
    other_xid: str = None
    other_xtype: type = None

    def __post_init__(self):
        if self.intersection_type is not None:
            self.error_msg = self.intersection_type.value
        elif self.error_msg is None:
            self.error_msg = 'Fehler in der Geometrievalidierung'


def _validate_overlaps(plan_id, short_plan_type: str) -> List[ValidationResult]:
    """ validates if any of the plan contents overlap each other"""
    result = []

    with Session.begin() as session:
        stmt = f"""
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
                ST_AsText(ST_CollectionExtract(ST_Intersection(a.position, b.position))) AS wkt,
                xp_a.id AS a_xid, xp_a.type AS a_type,
                xp_b.id AS b_xid, xp_b.type AS b_type,
                st_within(a.position, b.position) as is_within
            FROM all_objekt_positions a
                CROSS JOIN all_objekt_positions b
                INNER JOIN xp_objekt xp_a ON a.id = xp_a.id
                INNER JOIN xp_objekt xp_b ON b.id = xp_b.id
                INNER JOIN {short_plan_type}_bereich ON xp_a."gehoertZuBereich_id" = {short_plan_type}_bereich.id
                                      AND xp_b."gehoertZuBereich_id" = {short_plan_type}_bereich.id
            WHERE
                a.id < b.id
                AND ST_IsValid(a.position)
                AND ST_IsValid(b.position)
                AND a.flaechenschluss = TRUE
                AND b.flaechenschluss = TRUE
                AND {short_plan_type}_bereich."gehoertZuPlan_id" = '{plan_id}'
                AND (
                    ST_Overlaps(a.position, b.position)
                    OR st_within(a.position, b.position)
                );
        """

        res = session.execute(stmt).all()
        for row in res:
            error_type = GeometryIntersectionType.FullyWithin if row.is_within else GeometryIntersectionType.Planinhalt
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
                not st_within(xp_bereich.geltungsbereich, xp_plan."raeumlicherGeltungsbereich") AND
                not ST_IsEmpty(ST_Difference(xp_bereich.geltungsbereich, xp_plan."raeumlicherGeltungsbereich"));
        """)
        stmt = stmt.bindparams(planid=plan_id)

        res = session.execute(stmt).all()
        for row in res:
            validation_result = ValidationResult(
                xid=str(row.bereich_id),
                xtype=table_name_to_class(row.bereich_type),
                geom_wkt=row.wkt,
                intersection_type=GeometryIntersectionType.Plan,
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
                NOT ST_Within(a.position, xp_bereich.geltungsbereich) AND
                not ST_IsEmpty(ST_Difference(a.position, xp_bereich.geltungsbereich));
        """)
        stmt = stmt.bindparams(planid=plan_id)

        res = session.execute(stmt).all()
        for row in res:
            validation_result = ValidationResult(
                xid=str(row.a_xid),
                xtype=table_name_to_class(row.a_type),
                geom_wkt=row.wkt,
                intersection_type=GeometryIntersectionType.Bereich,
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
                NOT ST_OrderingEquals(geom, ST_RemoveRepeatedPoints(geom)) AS has_duplicate_vertices
            FROM (
                SELECT id, position AS geom, type FROM objects
                UNION ALL
                SELECT id, geltungsbereich AS geom, type FROM bereiche
                UNION ALL
                SELECT id, "raeumlicherGeltungsbereich" AS geom, 'xp_plan' FROM xp_plan
                WHERE xp_plan.id = :planid
            ) AS all_geometries;
        """)
        stmt = stmt.bindparams(planid=plan_id)

        res = session.execute(stmt).all()
        for row in res:
            validation_result = None
            if row.is_valid is False:
                validation_result = ValidationResult(
                    xid=str(row.id),
                    xtype=table_name_to_class(row.type),
                    geom_wkt=row.wkt,
                    error_msg=row.invalid_reason
                )
            if row.has_duplicate_vertices is True:
                validation_result = ValidationResult(
                    xid=str(row.id),
                    xtype=table_name_to_class(row.type),
                    geom_wkt=row.wkt,
                    error_msg='Planinhalt besitzt doppelte Stützpunkte'
                )

            if validation_result is not None:
                result.append(validation_result)

        return result


def _validate_gaps(plan_id, short_plan_type: str) -> List[ValidationResult]:
    # validate that the union of all plan contents is equal to the geltungsbereich => find gaps
    result = []
    with Session.begin() as session:
        stmt = f"""
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
            WHERE xp_plan.id = '{plan_id}';
        """
        res = session.execute(stmt)
        for row in res:
            validation_result = ValidationResult(
                xid=str(row.id),
                xtype=XP_Plan,
                geom_wkt=row.wkt,
                intersection_type=GeometryIntersectionType.NotCovered
            )
            result.append(validation_result)

        return result


VALIDATION_FUNCTIONS = [
    _validate_geometry_valid,
    _validate_within_bounds,
    _validate_overlaps,
    _validate_gaps
]
