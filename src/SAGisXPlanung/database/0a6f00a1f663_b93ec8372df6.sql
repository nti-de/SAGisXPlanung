BEGIN;

-- Running upgrade 0a6f00a1f663 -> b93ec8372df6

ALTER TABLE xp_plan ALTER COLUMN "raeumlicherGeltungsbereich" type geometry(Geometry);;

ALTER TABLE xp_plan ADD CONSTRAINT check_geometry_type CHECK (st_dimension("raeumlicherGeltungsbereich") = 2);;

ALTER TABLE xp_bereich ALTER COLUMN "geltungsbereich" type geometry(Geometry);;

ALTER TABLE xp_bereich ADD CONSTRAINT check_geometry_type CHECK (st_dimension("geltungsbereich") = 2);;

UPDATE alembic_version SET version_num='b93ec8372df6' WHERE alembic_version.version_num = '0a6f00a1f663';

COMMIT;

