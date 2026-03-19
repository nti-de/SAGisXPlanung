BEGIN;

-- Running upgrade 315e0f69004f -> 2b1452b49cc5

CREATE TABLE xp_gener_attribut (
    id UUID NOT NULL, 
    name VARCHAR NOT NULL, 
    type VARCHAR, 
    plan_id UUID, 
    xp_objekt_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(plan_id) REFERENCES xp_plan (id) ON DELETE CASCADE, 
    FOREIGN KEY(xp_objekt_id) REFERENCES xp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE xp_datum_attribut (
    id UUID NOT NULL, 
    wert DATE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE xp_double_attribut (
    id UUID NOT NULL, 
    wert FLOAT NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE xp_integer_attribut (
    id UUID NOT NULL, 
    wert INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE xp_string_attribut (
    id UUID NOT NULL, 
    wert VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE xp_url_attribut (
    id UUID NOT NULL, 
    wert VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_gener_attribut (id)
);

CREATE TABLE fp_nutzungsbeschraenkung (
    id UUID NOT NULL, 
    nutzung VARCHAR, 
    typ xp_immissionsschutztypen, 
    "technVorkehrung" xp_technvorkehrungenimmissionsschutz, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_vorkehrung_immissionschutz (
    codelist_user_id UUID, 
    codelist_id UUID, 
    FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    FOREIGN KEY(codelist_user_id) REFERENCES fp_nutzungsbeschraenkung (id) ON DELETE CASCADE
);

CREATE TABLE fp_nutzungsbeschraenkung_flaeche (
    id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_wasserwirtschaft (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungwasserwirtschaft, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_zweckwasserwirtschaft (
    codelist_user_id UUID, 
    codelist_id UUID, 
    FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    FOREIGN KEY(codelist_user_id) REFERENCES bp_wasserwirtschaft (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='2b1452b49cc5' WHERE alembic_version.version_num = '315e0f69004f';

COMMIT;

