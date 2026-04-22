BEGIN;

-- Running upgrade 98624e3008ab -> 315e0f69004f

CREATE TABLE xp_textabschnitt_assoc (
    xp_objekt_id UUID, 
    xp_plan_id UUID, 
    xp_bereich_id UUID, 
    textabschnitt_id UUID NOT NULL, 
    CONSTRAINT fk_xp_textabschnitt_assoc_textabschnitt_id_xp_text_abschnitt FOREIGN KEY(textabschnitt_id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_textabschnitt_assoc_xp_objekt_id_xp_objekt FOREIGN KEY(xp_objekt_id) REFERENCES xp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_textabschnitt_assoc_xp_plan_id_xp_plan FOREIGN KEY(xp_plan_id) REFERENCES xp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_textabschnitt_assoc_xp_bereich_id_xp_bereich FOREIGN KEY(xp_bereich_id) REFERENCES xp_bereich (id) ON DELETE CASCADE
);

INSERT INTO xp_textabschnitt_assoc (xp_objekt_id, xp_plan_id, xp_bereich_id, textabschnitt_id)
        SELECT xp_objekt_id, xp_plan_id, xp_bereich_id, id
        FROM xp_text_abschnitt
        WHERE xp_objekt_id IS NOT NULL OR xp_plan_id IS NOT NULL OR xp_bereich_id IS NOT NULL;;

ALTER TABLE xp_text_abschnitt DROP COLUMN xp_objekt_id;

ALTER TABLE xp_text_abschnitt DROP COLUMN xp_plan_id;

ALTER TABLE xp_text_abschnitt DROP COLUMN xp_bereich_id;

CREATE TABLE xp_rasterdarstellung (
    id UUID NOT NULL, 
    bereich_id UUID, 
    CONSTRAINT pk_xp_rasterdarstellung PRIMARY KEY (id), 
    CONSTRAINT fk_xp_rasterdarstellung_bereich_id_xp_bereich FOREIGN KEY(bereich_id) REFERENCES xp_bereich (id) ON DELETE CASCADE
);

ALTER TABLE xp_externe_referenz ADD COLUMN xp_rasterdarstellung_scan_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN xp_rasterdarstellung_text_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN xp_rasterdarstellung_legende_id UUID;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_xp_rasterdarstellung_legende_id__5c0c FOREIGN KEY(xp_rasterdarstellung_legende_id) REFERENCES xp_rasterdarstellung (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_xp_rasterdarstellung_text_id_xp__c43e FOREIGN KEY(xp_rasterdarstellung_text_id) REFERENCES xp_rasterdarstellung (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_xp_rasterdarstellung_scan_id_xp__cc66 FOREIGN KEY(xp_rasterdarstellung_scan_id) REFERENCES xp_rasterdarstellung (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD COLUMN georef_file BYTEA;

ALTER TABLE xp_externe_referenz ADD COLUMN "referenzMimeType_id" uuid REFERENCES codelist_values(id);;

UPDATE alembic_version SET version_num='315e0f69004f' WHERE alembic_version.version_num = '98624e3008ab'; --- # pragma: allowlist secret;

COMMIT;

