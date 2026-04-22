BEGIN;

-- Running upgrade 346f4a91caf3 -> 1983d6b6e2c1

CREATE TYPE xp_zweckbestimmungkennzeichnung AS ENUM ('Naturgewalten', 'Abbauflaeche', 'AeussereEinwirkungen', 'SchadstoffBelastBoden', 'LaermBelastung', 'Bergbau', 'Bodenordnung', 'Vorhabensgebiet', 'AndereGesetzlVorschriften');

CREATE TABLE bp_kennzeichnung (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungkennzeichnung[], 
    "istVerdachtsflaeche" BOOLEAN, 
    nummer VARCHAR, 
    CONSTRAINT pk_bp_kennzeichnung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_kennzeichnung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_versorgung (
    id UUID NOT NULL, 
    "textlicheErgaenzung" VARCHAR, 
    "zugunstenVon" VARCHAR, 
    zweckbestimmung xp_zweckbestimmungverentsorgung[], 
    CONSTRAINT pk_fp_versorgung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_versorgung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_zweckbestimmung_versorgung (
    id UUID NOT NULL, 
    allgemein xp_zweckbestimmungverentsorgung NOT NULL, 
    detail_id UUID, 
    "textlicheErgaenzung" VARCHAR, 
    aufschrift VARCHAR, 
    versorgung_id UUID, 
    CONSTRAINT pk_fp_zweckbestimmung_versorgung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_zweckbestimmung_versorgung_versorgung_id_fp_versorgung FOREIGN KEY(versorgung_id) REFERENCES fp_versorgung (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_zweckversorgung (
    codelist_user_id UUID, 
    codelist_id UUID, 
    CONSTRAINT fk_assoc_detail_zweckversorgung_codelist_id_codelist_values FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_assoc_detail_zweckversorgung_codelist_user_id_fp_zwe_921d FOREIGN KEY(codelist_user_id) REFERENCES fp_zweckbestimmung_versorgung (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='1983d6b6e2c1' WHERE alembic_version.version_num = '346f4a91caf3'; --- # pragma: allowlist secret;

COMMIT;

