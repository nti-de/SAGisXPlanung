BEGIN;

-- Running upgrade 5b93f2301608 -> e9b38a472653

CREATE TABLE assoc_detail_zweckgemeinbedarf (
    codelist_user_id UUID, 
    codelist_user_v6_id UUID, 
    codelist_id UUID, 
    FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    FOREIGN KEY(codelist_user_id) REFERENCES fp_gemeinbedarf (id) ON DELETE CASCADE, 
    FOREIGN KEY(codelist_user_v6_id) REFERENCES fp_zweckbestimmung_gemeinbedarf (id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS civil_line;

DROP TABLE IF EXISTS civil_point;

DROP TABLE IF EXISTS civil_area;

DROP TABLE IF EXISTS civil_plan;

DROP TABLE IF EXISTS civil_gemeinde;

ALTER TABLE bp_komplexe_sondernutzung ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE bp_komplexe_sondernutzung DROP COLUMN detail_id;

ALTER TABLE bp_veraenderungssperre_daten ALTER COLUMN verlaengerung SET NOT NULL;

ALTER TABLE bp_zweckbestimmung_gemeinbedarf ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE bp_zweckbestimmung_gruen ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE bp_zweckbestimmung_gruen DROP COLUMN detail_id;

ALTER TABLE bp_zweckbestimmung_landwirtschaft ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE bp_zweckbestimmung_nebenanlagen ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE bp_zweckbestimmung_sport ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE bp_zweckbestimmung_versorgung ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE bp_zweckbestimmung_wald ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE fp_komplexe_sondernutzung ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE fp_zweckbestimmung_gemeinbedarf ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE fp_zweckbestimmung_gruen ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE fp_zweckbestimmung_landwirtschaft ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE fp_zweckbestimmung_sport ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE fp_zweckbestimmung_versorgung DROP COLUMN detail_id;

ALTER TABLE fp_zweckbestimmung_wald ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE so_festlegung_gewaesser ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE so_zweckbestimmung_strassenverkehr ALTER COLUMN allgemein SET NOT NULL;

ALTER TABLE xp_objekt ALTER COLUMN rechtscharakter SET NOT NULL;

ALTER TABLE xp_plan ALTER COLUMN "raeumlicherGeltungsbereich" SET NOT NULL;

UPDATE alembic_version SET version_num='e9b38a472653' WHERE alembic_version.version_num = '5b93f2301608';

COMMIT;

