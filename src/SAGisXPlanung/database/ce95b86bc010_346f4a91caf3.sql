BEGIN;

-- Running upgrade ce95b86bc010 -> 346f4a91caf3

CREATE TYPE bp_zweckbestimmungnebenanlagen AS ENUM ('Stellplaetze', 'Garagen', 'Spielplatz', 'Carport', 'Tiefgarage', 'Nebengebaeude', 'AbfallSammelanlagen', 'EnergieVerteilungsanlagen', 'AbfallWertstoffbehaelter', 'Fahrradstellplaetze', 'Sonstiges');

CREATE TABLE bp_nebenanlage (
    id UUID NOT NULL, 
    zweckbestimmung bp_zweckbestimmungnebenanlagen[], 
    "Zmax" INTEGER, 
    CONSTRAINT pk_bp_nebenanlage PRIMARY KEY (id), 
    CONSTRAINT fk_bp_nebenanlage_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zweckbestimmung_nebenanlagen (
    id UUID NOT NULL, 
    allgemein bp_zweckbestimmungnebenanlagen, 
    "textlicheErgaenzung" VARCHAR, 
    aufschrift VARCHAR, 
    nebenanlage_id UUID, 
    CONSTRAINT pk_bp_zweckbestimmung_nebenanlagen PRIMARY KEY (id), 
    CONSTRAINT fk_bp_zweckbestimmung_nebenanlagen_nebenanlage_id_bp_ne_6d0e FOREIGN KEY(nebenanlage_id) REFERENCES bp_nebenanlage (id) ON DELETE CASCADE
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
    CONSTRAINT pk_so_luftverkehr PRIMARY KEY (id), 
    CONSTRAINT "fk_so_luftverkehr_detailArtDerFestlegung_id_codelist_values" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_luftverkehr_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
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
    CONSTRAINT pk_xp_verbundener_plan PRIMARY KEY (id), 
    CONSTRAINT "fk_xp_verbundener_plan_aendert_verbundenerPlan_id_xp_plan" FOREIGN KEY("aendert_verbundenerPlan_id") REFERENCES xp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT "fk_xp_verbundener_plan_wurdeGeaendertVon_verbundenerPla_1047" FOREIGN KEY("wurdeGeaendertVon_verbundenerPlan_id") REFERENCES xp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT "fk_xp_verbundener_plan_aendertPlan_verbundenerPlan_id_x_3c06" FOREIGN KEY("aendertPlan_verbundenerPlan_id") REFERENCES xp_bereich (id) ON DELETE CASCADE, 
    CONSTRAINT "fk_xp_verbundener_plan_wurdeGeaendertVonPlan_verbundene_adf0" FOREIGN KEY("wurdeGeaendertVonPlan_verbundenerPlan_id") REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE TABLE bp_generisches_objekt (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_generisches_objekt PRIMARY KEY (id), 
    CONSTRAINT fk_bp_generisches_objekt_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_generisches_objekt (
    id UUID NOT NULL, 
    CONSTRAINT pk_fp_generisches_objekt PRIMARY KEY (id), 
    CONSTRAINT fk_fp_generisches_objekt_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
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
    CONSTRAINT pk_bp_immissionsschutz PRIMARY KEY (id), 
    CONSTRAINT fk_bp_immissionsschutz_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_abgrabung (
    id UUID NOT NULL, 
    abbaugut VARCHAR, 
    CONSTRAINT pk_bp_abgrabung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_abgrabung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_aufschuettung (
    id UUID NOT NULL, 
    aufschuettungsmaterial VARCHAR, 
    CONSTRAINT pk_bp_aufschuettung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_aufschuettung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE so_klassifiznachsonstigemrecht AS ENUM ('Bauschutzbereich', 'Berggesetz', 'Richtfunkverbindung', 'Truppenuebungsplatz', 'VermessungsKatasterrecht', 'Rekultivierungsflaeche', 'Renaturierungsflaeche', 'Lärmschutzbereich', 'SchutzzoneLeitungstrasse', 'Sonstiges');

CREATE TABLE so_sonstiges_recht (
    id UUID NOT NULL, 
    nummer VARCHAR, 
    "artDerFestlegung" so_klassifiznachsonstigemrecht, 
    "detailArtDerFestlegung_id" UUID, 
    name VARCHAR, 
    CONSTRAINT pk_so_sonstiges_recht PRIMARY KEY (id), 
    CONSTRAINT "fk_so_sonstiges_recht_detailArtDerFestlegung_id_codelist_values" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_sonstiges_recht_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

DELETE FROM bp_einfahrtpunkt WHERE id NOT IN (SELECT id FROM bp_objekt);

DELETE FROM bp_keine_ein_ausfahrt WHERE id NOT IN (SELECT id FROM bp_objekt);

DELETE FROM bp_nutzungsgrenze WHERE id NOT IN (SELECT id FROM bp_objekt);

ALTER TABLE bp_einfahrtpunkt ADD CONSTRAINT fk_bp_einfahrtpunkt_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE;

ALTER TABLE bp_keine_ein_ausfahrt ADD CONSTRAINT fk_bp_keine_ein_ausfahrt_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE;

ALTER TABLE bp_nutzungsgrenze ADD CONSTRAINT fk_bp_nutzungsgrenze_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE;

ALTER TABLE bp_komplexe_sondernutzung ADD COLUMN detail_id UUID;

ALTER TABLE bp_zweckbestimmung_gruen ADD COLUMN detail_id UUID;

ALTER TABLE lp_plan ALTER COLUMN bundesland SET NOT NULL;

ALTER TABLE lp_plan ALTER COLUMN "rechtlicheAussenwirkung" SET NOT NULL;

ALTER TABLE so_strassenverkehr ALTER COLUMN "hatDarstellungMitBesondZweckbest" SET NOT NULL;

ALTER TABLE xp_objekt ADD CONSTRAINT "fk_xp_objekt_gesetzlicheGrundlage_id_xp_gesetzliche_grundlage" FOREIGN KEY("gesetzlicheGrundlage_id") REFERENCES xp_gesetzliche_grundlage (id);

UPDATE alembic_version SET version_num='346f4a91caf3' WHERE alembic_version.version_num = 'ce95b86bc010'; --- # pragma: allowlist secret;

COMMIT;

