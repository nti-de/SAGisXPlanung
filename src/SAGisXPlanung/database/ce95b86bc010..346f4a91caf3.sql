BEGIN;

-- Running upgrade ce95b86bc010 -> 346f4a91caf3

CREATE TYPE bp_zweckbestimmungnebenanlagen AS ENUM ('Stellplaetze', 'Garagen', 'Spielplatz', 'Carport', 'Tiefgarage', 'Nebengebaeude', 'AbfallSammelanlagen', 'EnergieVerteilungsanlagen', 'AbfallWertstoffbehaelter', 'Fahrradstellplaetze', 'Sonstiges');

CREATE TABLE bp_nebenanlage (
    id UUID NOT NULL, 
    zweckbestimmung bp_zweckbestimmungnebenanlagen[], 
    "Zmax" INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zweckbestimmung_nebenanlagen (
    id UUID NOT NULL, 
    allgemein bp_zweckbestimmungnebenanlagen, 
    "textlicheErgaenzung" VARCHAR, 
    aufschrift VARCHAR, 
    nebenanlage_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(nebenanlage_id) REFERENCES bp_nebenanlage (id) ON DELETE CASCADE
);

CREATE TYPE so_klassifiznachluftverkehrsrecht AS ENUM ('Flughafen', 'Landeplatz', 'Segelfluggelaende', 'HubschrauberLandeplatz', 'Ballonstartplatz', 'Haengegleiter', 'Gleitsegler', 'Laermschutzbereich', 'Baubeschraenkungsbereich', 'Sonstiges');

CREATE TYPE so_laermschutzzonetypen AS ENUM ('TagZone1', 'TagZone2', 'Nacht');

CREATE TABLE so_luftverkehr (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachluftverkehrsrecht, 
    "detailArtDerFestlegung_id" UUID, 
    name VARCHAR, 
    nummer VARCHAR, 
    laermschutzzone so_laermschutzzonetypen, 
    PRIMARY KEY (id), 
    FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_rechtscharakterplanaenderung AS ENUM ('Aenderung', 'Ergaenzung', 'Aufhebung', 'Aufhebungsverfahren', 'Ueberplanung');

CREATE TYPE xp_aenderungsarten AS ENUM ('Änderung', 'Ersetzung', 'Ergänzung', 'Streichung', 'Aufhebung', 'Überplanung');

CREATE TABLE xp_verbundener_plan (
    id UUID NOT NULL, 
    "planName" VARCHAR, 
    rechtscharakter xp_rechtscharakterplanaenderung, 
    "aenderungsArt" xp_aenderungsarten, 
    nummer VARCHAR, 
    aenderungsdatum DATE, 
    "aendert_verbundenerPlan_id" UUID, 
    "wurdeGeaendertVon_verbundenerPlan_id" UUID, 
    "aendertPlan_verbundenerPlan_id" UUID, 
    "wurdeGeaendertVonPlan_verbundenerPlan_id" UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY("aendert_verbundenerPlan_id") REFERENCES xp_plan (id) ON DELETE CASCADE, 
    FOREIGN KEY("wurdeGeaendertVon_verbundenerPlan_id") REFERENCES xp_plan (id) ON DELETE CASCADE, 
    FOREIGN KEY("aendertPlan_verbundenerPlan_id") REFERENCES xp_bereich (id) ON DELETE CASCADE, 
    FOREIGN KEY("wurdeGeaendertVonPlan_verbundenerPlan_id") REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE TABLE bp_generisches_objekt (
    id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_generisches_objekt (
    id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE bp_laermpegelbereich AS ENUM ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'SpezifizierungBereich');

CREATE TYPE xp_immissionsschutztypen AS ENUM ('Schutzflaeche', 'BesondereAnlagenVorkehrungen');

CREATE TYPE xp_technvorkehrungenimmissionsschutz AS ENUM ('Laermschutzvorkehrung', 'FassadenMitSchallschutzmassnahmen', 'Laermschutzwand', 'Laermschutzwall', 'SonstigeVorkehrung');

CREATE TABLE bp_immissionsschutz (
    id UUID NOT NULL, 
    nutzung VARCHAR, 
    laermpegelbereich bp_laermpegelbereich, 
    "massgeblAussenLaermpegelTag" FLOAT, 
    "massgeblAussenLaermpegelNacht" FLOAT, 
    typ xp_immissionsschutztypen, 
    "technVorkehrung" xp_technvorkehrungenimmissionsschutz, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_abgrabung (
    id UUID NOT NULL, 
    abbaugut VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_aufschuettung (
    id UUID NOT NULL, 
    aufschuettungsmaterial VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE so_klassifiznachsonstigemrecht AS ENUM ('Bauschutzbereich', 'Berggesetz', 'Richtfunkverbindung', 'Truppenuebungsplatz', 'VermessungsKatasterrecht', 'Rekultivierungsflaeche', 'Renaturierungsflaeche', 'Lärmschutzbereich', 'SchutzzoneLeitungstrasse', 'Sonstiges');

CREATE TABLE so_sonstiges_recht (
    id UUID NOT NULL, 
    nummer VARCHAR, 
    "artDerFestlegung" so_klassifiznachsonstigemrecht, 
    "detailArtDerFestlegung_id" UUID, 
    name VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

ALTER TABLE bp_einfahrtpunkt ADD FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE;

ALTER TABLE bp_keine_ein_ausfahrt ADD FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE;

ALTER TABLE bp_nutzungsgrenze ADD FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE;

ALTER TABLE bp_komplexe_sondernutzung ADD COLUMN detail_id UUID;

ALTER TABLE bp_zweckbestimmung_gruen ADD COLUMN detail_id UUID;

ALTER TABLE lp_plan ALTER COLUMN bundesland SET NOT NULL;

ALTER TABLE lp_plan ALTER COLUMN "rechtlicheAussenwirkung" SET NOT NULL;

ALTER TABLE so_strassenverkehr ALTER COLUMN "hatDarstellungMitBesondZweckbest" SET NOT NULL;

ALTER TABLE xp_objekt ADD FOREIGN KEY("gesetzlicheGrundlage_id") REFERENCES xp_gesetzliche_grundlage (id);

UPDATE alembic_version SET version_num='346f4a91caf3' WHERE alembic_version.version_num = 'ce95b86bc010';

COMMIT;

