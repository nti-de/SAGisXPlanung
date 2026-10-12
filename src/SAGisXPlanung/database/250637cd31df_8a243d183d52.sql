BEGIN;

-- Running upgrade 250637cd31df -> 8a243d183d52

CREATE TABLE bp_schutzmassnahme (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    "istAusgleich" BOOLEAN, 
    CONSTRAINT pk_bp_schutzmassnahme PRIMARY KEY (id), 
    CONSTRAINT fk_bp_schutzmassnahme_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE xp_externe_referenz ADD COLUMN bp_schutzmassnahme_massnahme_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_schutzmassnahme_plan_id UUID;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_schutzmassnahme_massnahme_id__7b21 FOREIGN KEY(bp_schutzmassnahme_massnahme_id) REFERENCES bp_schutzmassnahme (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_schutzmassnahme_plan_id_bp_sc_a911 FOREIGN KEY(bp_schutzmassnahme_plan_id) REFERENCES bp_schutzmassnahme (id) ON DELETE CASCADE;

ALTER TABLE xp_spe_daten ADD COLUMN bp_schutzmassnahme_id UUID;

ALTER TABLE xp_spe_daten ADD CONSTRAINT fk_xp_spe_daten_bp_schutzmassnahme_id_bp_schutzmassnahme FOREIGN KEY(bp_schutzmassnahme_id) REFERENCES bp_schutzmassnahme (id) ON DELETE CASCADE;

ALTER TYPE bp_wegerechttypen ADD VALUE IF NOT EXISTS 'GehFahrrecht';

ALTER TYPE bp_wegerechttypen ADD VALUE IF NOT EXISTS 'GehLeitungsrecht';

ALTER TYPE bp_wegerechttypen ADD VALUE IF NOT EXISTS 'FahrLeitungsrecht';

ALTER TYPE bp_wegerechttypen ADD VALUE IF NOT EXISTS 'GehFahrLeitungsrecht';

UPDATE alembic_version SET version_num='8a243d183d52' WHERE alembic_version.version_num = '250637cd31df'; --- # pragma: allowlist secret;

COMMIT;

