BEGIN;

-- Running upgrade 315e0f69004f -> 2b1452b49cc5

CREATE TABLE xp_gener_attribut (
    id UUID NOT NULL, 
    name VARCHAR NOT NULL, 
    type VARCHAR, 
    plan_id UUID, 
    xp_objekt_id UUID, 
    CONSTRAINT pk_xp_gener_attribut PRIMARY KEY (id), 
    CONSTRAINT fk_xp_gener_attribut_plan_id_xp_plan FOREIGN KEY(plan_id) REFERENCES xp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_gener_attribut_xp_objekt_id_xp_objekt FOREIGN KEY(xp_objekt_id) REFERENCES xp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE xp_datum_attribut (
    id UUID NOT NULL, 
    wert DATE NOT NULL, 
    CONSTRAINT pk_xp_datum_attribut PRIMARY KEY (id), 
    CONSTRAINT fk_xp_datum_attribut_id_xp_gener_attribut FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE xp_double_attribut (
    id UUID NOT NULL, 
    wert FLOAT NOT NULL, 
    CONSTRAINT pk_xp_double_attribut PRIMARY KEY (id), 
    CONSTRAINT fk_xp_double_attribut_id_xp_gener_attribut FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE xp_integer_attribut (
    id UUID NOT NULL, 
    wert INTEGER NOT NULL, 
    CONSTRAINT pk_xp_integer_attribut PRIMARY KEY (id), 
    CONSTRAINT fk_xp_integer_attribut_id_xp_gener_attribut FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE xp_string_attribut (
    id UUID NOT NULL, 
    wert VARCHAR NOT NULL, 
    CONSTRAINT pk_xp_string_attribut PRIMARY KEY (id), 
    CONSTRAINT fk_xp_string_attribut_id_xp_gener_attribut FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE xp_url_attribut (
    id UUID NOT NULL, 
    wert VARCHAR NOT NULL, 
    CONSTRAINT pk_xp_url_attribut PRIMARY KEY (id), 
    CONSTRAINT fk_xp_url_attribut_id_xp_gener_attribut FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE fp_nutzungsbeschraenkung (
    id UUID NOT NULL, 
    nutzung VARCHAR, 
    typ xp_immissionsschutztypen, 
    "technVorkehrung" xp_technvorkehrungenimmissionsschutz, 
    CONSTRAINT pk_fp_nutzungsbeschraenkung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_nutzungsbeschraenkung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_vorkehrung_immissionschutz (
    codelist_user_id UUID, 
    codelist_id UUID, 
    CONSTRAINT fk_assoc_detail_vorkehrung_immissionschutz_codelist_id__43e1 FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_assoc_detail_vorkehrung_immissionschutz_codelist_use_b6b6 FOREIGN KEY(codelist_user_id) REFERENCES fp_nutzungsbeschraenkung (id) ON DELETE CASCADE
);

CREATE TABLE fp_nutzungsbeschraenkung_flaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_fp_nutzungsbeschraenkung_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_fp_nutzungsbeschraenkung_flaeche_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_wasserwirtschaft (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungwasserwirtschaft, 
    CONSTRAINT pk_bp_wasserwirtschaft PRIMARY KEY (id), 
    CONSTRAINT fk_bp_wasserwirtschaft_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_zweckwasserwirtschaft (
    codelist_user_id UUID, 
    codelist_id UUID, 
    CONSTRAINT fk_assoc_detail_zweckwasserwirtschaft_codelist_id_codel_9acb FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_assoc_detail_zweckwasserwirtschaft_codelist_user_id__175e FOREIGN KEY(codelist_user_id) REFERENCES bp_wasserwirtschaft (id) ON DELETE CASCADE
);

DROP TRIGGER IF EXISTS fp_gruen_sync_attr_zweckbestimmung ON fp_gruen;

DROP TRIGGER IF EXISTS fp_gruen_sync_attr_zweckbestimmung ON fp_zweckbestimmung_gruen;

ALTER TABLE fp_gruen
        ALTER COLUMN "zweckbestimmung"
        TYPE xp_zweckbestimmunggruen[]
        USING CASE
            WHEN zweckbestimmung IS NULL THEN NULL
            ELSE ARRAY[zweckbestimmung::xp_zweckbestimmunggruen]
        END;;

CREATE TABLE fp_flaeche_ohne_darstellung (
    id UUID NOT NULL, 
    CONSTRAINT pk_fp_flaeche_ohne_darstellung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_flaeche_ohne_darstellung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='2b1452b49cc5' WHERE alembic_version.version_num = '315e0f69004f'; --- # pragma: allowlist secret;

COMMIT;

