BEGIN;

-- Running upgrade 812b33dce3d1 -> 0a6f00a1f663

UPDATE xp_po SET type='xp_pto' WHERE type='xp_tpo';;

ALTER INDEX idx_xp_tpo_position RENAME TO idx_xp_pto_position;;

ALTER TABLE xp_tpo RENAME CONSTRAINT xp_tpo_id_fkey TO xp_pto_id_fkey;;

ALTER TABLE xp_tpo RENAME CONSTRAINT xp_tpo_pkey TO xp_pto_pkey;;

ALTER TABLE xp_tpo RENAME TO xp_pto;;

ALTER TABLE xp_ppo ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;;

ALTER TABLE xp_pto ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;;

ALTER TABLE xp_nutzungsschablone ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;;

ALTER TABLE xp_objekt ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;;

INSERT INTO xp_externe_referenz (id, datum, "referenzMimeType", art, "referenzName", beschreibung, file, "georefURL", "referenzURL") SELECT id, datum, "referenzMimeType", art, "referenzName", beschreibung, file, "georefURL", "referenzURL" FROM xp_spez_externe_referenz;

ALTER TABLE xp_spez_externe_referenz ADD CONSTRAINT xp_spez_externe_referenz_id_fkey FOREIGN KEY(id) REFERENCES xp_externe_referenz (id) ON DELETE CASCADE;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN datum;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN "referenzMimeType";

ALTER TABLE xp_spez_externe_referenz DROP COLUMN art;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN "referenzName";

ALTER TABLE xp_spez_externe_referenz DROP COLUMN beschreibung;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN file;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN "georefURL";

ALTER TABLE xp_spez_externe_referenz DROP COLUMN "referenzURL";

ALTER TABLE xp_externe_referenz ADD COLUMN type VARCHAR(50);

UPDATE xp_externe_referenz SET type='xp_spez_externe_referenz' WHERE id in (SELECT id FROM xp_spez_externe_referenz);;

UPDATE xp_externe_referenz SET type='xp_externe_referenz' WHERE type IS NULL;

UPDATE alembic_version SET version_num='0a6f00a1f663' WHERE alembic_version.version_num = '812b33dce3d1';

COMMIT;

