BEGIN;

-- Running upgrade 346f4a91caf3 -> 1983d6b6e2c1

CREATE TYPE xp_zweckbestimmungkennzeichnung AS ENUM ('Naturgewalten', 'Abbauflaeche', 'AeussereEinwirkungen', 'SchadstoffBelastBoden', 'LaermBelastung', 'Bergbau', 'Bodenordnung', 'Vorhabensgebiet', 'AndereGesetzlVorschriften');

CREATE TABLE bp_kennzeichnung (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungkennzeichnung[], 
    "istVerdachtsflaeche" BOOLEAN, 
    nummer VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_versorgung (
    id UUID NOT NULL, 
    "textlicheErgaenzung" VARCHAR, 
    "zugunstenVon" VARCHAR, 
    zweckbestimmung xp_zweckbestimmungverentsorgung[], 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_zweckbestimmung_versorgung (
    id UUID NOT NULL, 
    allgemein xp_zweckbestimmungverentsorgung NOT NULL, 
    detail_id UUID, 
    "textlicheErgaenzung" VARCHAR, 
    aufschrift VARCHAR, 
    versorgung_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(versorgung_id) REFERENCES fp_versorgung (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_zweckversorgung (
    codelist_user_id UUID, 
    codelist_id UUID, 
    FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    FOREIGN KEY(codelist_user_id) REFERENCES fp_zweckbestimmung_versorgung (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='1983d6b6e2c1' WHERE alembic_version.version_num = '346f4a91caf3';

COMMIT;

