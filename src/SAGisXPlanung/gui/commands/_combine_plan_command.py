import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from qgis.core import QgsGeometry
from sqlalchemy import inspect as sa_inspect, or_, select, and_, func
from sqlalchemy.orm import make_transient, with_polymorphic, ONETOMANY

from SAGisXPlanung import Session, PYQT5
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich, XP_Objekt
from SAGisXPlanung.core.helper import update_geometry
from SAGisXPlanung.gui.commands._undo_commands import snapshot_object
from SAGisXPlanung.utils import BEREICH_BASE_TYPES, OBJECT_BASE_TYPES

if PYQT5:
    from qgis.PyQt.QtWidgets import QUndoCommand
else:
    from qgis.PyQt.QtGui import QUndoCommand

logger = logging.getLogger(__name__)

_RELATIONSHIP_SKIP_COPY = frozenset({
    'planinhalt', 'praesentationsobjekt',
    'gehoertZuBereich', 'gehoertZuPlan',
    'aendertPlan', 'wurdeGeaendertVonPlan',
})

_JOINED_INHERITANCE_PK_FK_RELS = frozenset({
    'gehoertZuBereich',
})


@dataclass
class GeometryUpdate:
    orm_class: type
    xid: str
    old_geom_wkt: str
    new_geom_wkt: str


@dataclass
class CreatedObject:
    orm_class: type
    xid: str


class CombinePlanCommand(QUndoCommand):
    """Undo command that merges a source plan's contents into a target plan.

    Redo: creates new Bereich(s) in the target plan with all source objects,
          cuts existing target objects where the source Geltungsbereich overlaps,
          expands the target Geltungsbereich if the source extends beyond it.
    Undo: deletes created Bereich(s) and their copied objects,
          restores modified target object geometries and the target Geltungsbereich.
    """

    def __init__(self, source_plan_xid: str, target_plan_xid: str):
        super().__init__('Plan zusammenführen')
        self._source_plan_xid = source_plan_xid
        self._target_plan_xid = target_plan_xid

        self._geometry_updates: list[GeometryUpdate] = []
        self._created_objects: list[CreatedObject] = []
        self._old_target_geltungsbereich_wkt: Optional[str] = None
        self._geltungsbereich_changed: bool = False
        self._id_mapping: dict[str, str] = {}
        self._executed: bool = False

    def redo(self):
        self._reset_state()

        with Session.begin() as session:
            source_plan = session.get(XP_Plan, self._source_plan_xid)
            target_plan = session.get(XP_Plan, self._target_plan_xid)

            if source_plan is None or target_plan is None:
                raise ValueError('Quell- oder Zielplan nicht gefunden')

            source_geom = source_plan.geometry()
            self._cut_target_objects(session, source_geom, source_plan, target_plan)

            for source_bereich in source_plan.bereich:
                self._insert_bereich(session, source_bereich, target_plan)
            #
            # self._update_target_geltungsbereich(session, target_plan, source_geom)

        self._apply_canvas_updates()
        self._executed = True


    def undo(self):
        if not self._executed:
            return

        with Session.begin() as session:
            for created in reversed(self._created_objects):
                obj = session.get(created.orm_class, created.xid)
                if obj is not None:
                    session.delete(obj)

            for update in self._geometry_updates:
                orm_obj = session.get(update.orm_class, update.xid)
                if orm_obj is not None:
                    geom = QgsGeometry.fromWkt(update.old_geom_wkt)
                    orm_obj.setGeometry(geom)

            if self._geltungsbereich_changed and self._old_target_geltungsbereich_wkt:
                target_plan = session.get(XP_Plan, self._target_plan_xid)
                geom = QgsGeometry.fromWkt(self._old_target_geltungsbereich_wkt)
                target_plan.setGeometry(geom)

        self._apply_canvas_updates(restore=True)

    def _reset_state(self):
        self._geometry_updates.clear()
        self._created_objects.clear()
        self._id_mapping.clear()
        self._old_target_geltungsbereich_wkt = None
        self._geltungsbereich_changed = False

    def _apply_canvas_updates(self, restore: bool = False):
        for update in self._geometry_updates:
            wkt = update.old_geom_wkt if restore else update.new_geom_wkt
            geom = QgsGeometry.fromWkt(wkt)
            update_geometry(update.xid, geom)

    # -- Geometry helpers --

    def _plan_geometry(self, session, plan_xid: str) -> QgsGeometry:
        stmt = select(XP_Plan.raeumlicherGeltungsbereich).where(XP_Plan.id == plan_xid)
        result = session.execute(stmt).scalar()
        if result is None:
            return QgsGeometry()
        from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
        return geometry_from_spatial_element(result)


    def _collect_plan_objects(self, session, bereiche, geometry_query: str) -> list:
        bereich_ids = [b.id for b in bereiche]

        objects = []
        for obj_base in OBJECT_BASE_TYPES:
            stmt = select(obj_base).where(
                and_(
                    obj_base.gehoertZuBereich_id.in_(bereich_ids),
                    func.ST_Intersects(
                        obj_base.position, func.ST_GeomFromText(geometry_query, func.ST_SRID(obj_base.position))
                    )
                )
            )
            objects.extend(session.execute(stmt).scalars().all())

        return objects

    def _cut_target_objects(self, session, source_geom: QgsGeometry, source_plan, target_plan):
        if source_geom.isNull() or source_geom.isEmpty():
            return

        target_objects = self._collect_plan_objects(session, target_plan.bereich, source_geom.asWkt())
        target_objects.extend(target_plan.bereich)
        print('found targets objects', len(target_objects))

        for obj in target_objects:
            print(obj)

            try:
                obj_geom = obj.geometry()
            except Exception:
                obj_geom = source_plan.geometry()

            if obj_geom.isNull() or obj_geom.isEmpty():
                continue

            diff = obj_geom.difference(source_geom)

            if diff.isNull() or diff.isEmpty():
                continue

            if diff.equals(obj_geom):
                continue

            corrected_geom = diff.simplify(0)
            old_geom_wkt = obj_geom.asWkt()
            new_geom_wkt = corrected_geom.asWkt()

            obj.setGeometry(corrected_geom)

            self._geometry_updates.append(GeometryUpdate(
                orm_class=type(obj),
                xid=str(obj.id),
                old_geom_wkt=old_geom_wkt,
                new_geom_wkt=new_geom_wkt,
            ))

    def _insert_bereich(self, session, source_bereich, target_plan):
        bereich_snapshot = snapshot_object(source_bereich)

        obj = source_bereich.__class__()
        for key, value in bereich_snapshot.items():
            setattr(obj, key, value)
        obj.id = uuid.uuid4()
        obj.gehoertZuPlan_id = target_plan.id

        # for rel in sa_inspect(source_bereich.__class__).relationships.values():
        #     if rel.direction == ONETOMANY:
        #         rel_value = getattr(source_bereich, rel.key, [])
        #         children = [rel_value] if rel_value is not None and not isinstance(rel_value, list) else (rel_value or [])
        #         for child in children:
        #             _recurse(child)

        # TODO: where does the new bereich go? its nowhere to be found, check db
        session.add(obj)

        created = CreatedObject(orm_class=obj.__class__, xid=str(obj.id))
        self._created_objects.append(created)


    def _copy_bereich(self, session, source_bereich, target_plan):
        orm_class = type(source_bereich)
        snapshot = snapshot_object(source_bereich)

        new_bereich = orm_class()
        for key, value in snapshot.items():
            if key == 'id':
                continue
            if key == 'gehoertZuPlan_id':
                continue
            setattr(new_bereich, key, value)

        new_id = uuid.uuid4()
        new_bereich.id = new_id
        new_bereich.gehoertZuPlan = target_plan

        make_transient(new_bereich)
        session.add(new_bereich)
        session.flush()

        self._created_objects.append(CreatedObject(
            orm_class=orm_class, xid=str(new_id), is_bereich=True
        ))

        self._copy_bereich_children(session, source_bereich, new_bereich)

        return new_bereich

    def _copy_bereich_children(self, session, source_bereich, new_bereich):
        mapper = sa_inspect(type(source_bereich))
        for rel in mapper.relationships:
            if rel.direction != ONETOMANY:
                continue
            if rel.key in ('planinhalt', 'praesentationsobjekt'):
                continue
            if rel.key in ('aendertPlan', 'wurdeGeaendertVonPlan'):
                continue

            children = getattr(source_bereich, rel.key)
            if not children:
                continue

            if isinstance(children, list):
                for child in children:
                    self._deep_copy_generic(session, child, parent_rel_key=rel.key, parent_obj=new_bereich)
            else:
                self._deep_copy_generic(session, children, parent_rel_key=rel.key, parent_obj=new_bereich)

    # -- Generic object copying --

    def _deep_copy_objekt(self, session, source_obj, target_bereich):
        new_obj = self._copy_object_columns(session, source_obj)
        new_obj.gehoertZuBereich = target_bereich
        session.flush()

        self._id_mapping[str(source_obj.id)] = str(new_obj.id)
        self._created_objects.append(CreatedObject(
            orm_class=type(source_obj), xid=str(new_obj.id)
        ))

        self._copy_objekt_children(session, source_obj, new_obj)

    def _copy_objekt_children(self, session, source_obj, new_obj):
        mapper = sa_inspect(type(source_obj))
        for rel in mapper.relationships:
            if rel.direction != ONETOMANY:
                continue
            if rel.key in ('wirdDargestelltDurch',):
                continue

            children = getattr(source_obj, rel.key)
            if not children:
                continue

            if isinstance(children, list):
                for child in children:
                    self._deep_copy_generic(session, child, parent_rel_key=rel.key, parent_obj=new_obj)
            else:
                self._deep_copy_generic(session, children, parent_rel_key=rel.key, parent_obj=new_obj)

    def _deep_copy_presentation_object(self, session, source_po, target_bereich):
        new_po = self._copy_object_columns(session, source_po)
        new_po.gehoertZuBereich = target_bereich

        if source_po.dientZurDarstellungVon_id is not None:
            source_obj_xid = str(source_po.dientZurDarstellungVon_id)
            target_obj_xid = self._id_mapping.get(source_obj_xid)
            if target_obj_xid is not None:
                target_obj = session.get(XP_Objekt, uuid.UUID(target_obj_xid))
                if target_obj is not None:
                    new_po.dientZurDarstellungVon = target_obj

        session.flush()

        self._created_objects.append(CreatedObject(
            orm_class=type(source_po), xid=str(new_po.id)
        ))

    def _deep_copy_generic(self, session, source_obj, parent_rel_key: str, parent_obj):
        orm_class = type(source_obj)
        snapshot = snapshot_object(source_obj)

        new_obj = orm_class()
        for key, value in snapshot.items():
            if key == 'id':
                continue
            if key in ('xp_objekt_id', 'plan_id', 'gehoertZuBereich_id', 'dientZurDarstellungVon_id'):
                continue
            setattr(new_obj, key, value)

        new_id = uuid.uuid4()
        new_obj.id = new_id

        if hasattr(new_obj, 'xp_objekt_id') and hasattr(parent_obj, '__tablename__'):
            parent_table = parent_obj.__tablename__
            if parent_table in ('xp_objekt', 'bp_objekt', 'fp_objekt', 'lp_objekt', 'so_objekt'):
                new_obj.xp_objekt = parent_obj

        if hasattr(new_obj, 'gehoertZuBereich_id') and isinstance(parent_obj, XP_Bereich):
            new_obj.gehoertZuBereich = parent_obj

        make_transient(new_obj)
        session.add(new_obj)
        session.flush()

        self._created_objects.append(CreatedObject(orm_class=orm_class, xid=str(new_id)))

        child_mapper = sa_inspect(orm_class)
        for child_rel in child_mapper.relationships:
            if child_rel.direction != ONETOMANY:
                continue

            grandchildren = getattr(source_obj, child_rel.key)
            if not grandchildren:
                continue

            if isinstance(grandchildren, list):
                for grandchild in grandchildren:
                    self._deep_copy_generic(session, grandchild, parent_rel_key=child_rel.key, parent_obj=new_obj)
            else:
                self._deep_copy_generic(session, grandchildren, parent_rel_key=child_rel.key, parent_obj=new_obj)

    def _copy_object_columns(self, session, source_obj):
        orm_class = type(source_obj)
        snapshot = snapshot_object(source_obj)

        new_obj = orm_class()
        for key, value in snapshot.items():
            if key == 'id':
                continue
            if key in ('gehoertZuBereich_id', 'gehoertZuPlan_id', 'dientZurDarstellungVon_id'):
                continue
            setattr(new_obj, key, value)

        new_obj.id = uuid.uuid4()

        make_transient(new_obj)
        session.add(new_obj)
        session.flush()

        return new_obj

    # -- Step 3: Update target Geltungsbereich --

    def _update_target_geltungsbereich(self, session, target_plan, source_geom: QgsGeometry):
        if source_geom.isNull() or source_geom.isEmpty():
            return

        target_geom = self._plan_geometry(session, self._target_plan_xid)
        if target_geom.isNull() or target_geom.isEmpty():
            return

        if target_geom.contains(source_geom):
            return

        self._old_target_geltungsbereich_wkt = target_geom.asWkt()
        self._geltungsbereich_changed = True

        combined = target_geom.combine(source_geom)
        target_plan.setGeometry(combined)
