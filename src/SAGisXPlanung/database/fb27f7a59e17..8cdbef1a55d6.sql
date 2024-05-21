BEGIN;

-- Running upgrade fb27f7a59e17 -> 8cdbef1a55d6

ALTER TABLE bp_plan ADD COLUMN "versionBauNVO_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
            ALTER TABLE bp_plan ADD COLUMN "versionBauGB_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
            ALTER TABLE bp_plan ADD COLUMN "versionSonstRechtsgrundlage_id" uuid REFERENCES xp_gesetzliche_grundlage(id);;

ALTER TYPE xp_zweckbestimmunggemeinbedarf ADD VALUE IF NOT EXISTS 'SonstigeInfrastruktur';

ALTER TYPE xp_zweckbestimmunggemeinbedarf ADD VALUE IF NOT EXISTS 'SonstigeSicherheitOrdnung';

UPDATE alembic_version SET version_num='8cdbef1a55d6' WHERE alembic_version.version_num = 'fb27f7a59e17';

COMMIT;

