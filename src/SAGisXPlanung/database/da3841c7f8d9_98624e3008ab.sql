BEGIN;

-- Running upgrade da3841c7f8d9 -> 98624e3008ab

ALTER TABLE bp_plan ALTER "planArt" type bp_planart[] using ARRAY["planArt"];

ALTER TABLE bp_baugebiet ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_gemeinbedarf ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_wohngebaeude_flaeche ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_besondere_nutzung ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_grundstueck_ueberbaubar ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_dachgestaltung ALTER COLUMN "DNmin" TYPE FLOAT USING "DNmin"::float;;

ALTER TABLE bp_dachgestaltung ALTER COLUMN "DNmax" TYPE FLOAT USING "DNmax"::float;;

ALTER TABLE bp_dachgestaltung ALTER COLUMN "DN" TYPE FLOAT USING "DN"::float;;

ALTER TABLE bp_dachgestaltung ALTER COLUMN "DNZwingend" TYPE FLOAT USING "DNZwingend"::float;;

ALTER TABLE lp_objekt ALTER COLUMN nordwinkel TYPE FLOAT USING nordwinkel::float;;

ALTER TABLE bp_plan ADD CONSTRAINT ck_planart_not_empty_no_nulls CHECK ("planArt" <> '{}' and array_position("planArt", null) is null);;

UPDATE alembic_version SET version_num='98624e3008ab' WHERE alembic_version.version_num = 'da3841c7f8d9'; --- # pragma: allowlist secret;

COMMIT;

