BEGIN;

-- Running upgrade 2cee32cfc646 -> 54455ce1e9f6

CREATE TYPE xp_speziele AS ENUM ('SchutzPflege', 'Entwicklung', 'Anlage', 'SchutzPflegeEntwicklung', 'Sonstiges');

CREATE TABLE bp_schutzflaeche (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    "istAusgleich" BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_spemassnahmentypen AS ENUM ('ArtentreicherGehoelzbestand', 'NaturnaherWald', 'ExtensivesGruenland', 'Feuchtgruenland', 'Obstwiese', 'NaturnaherUferbereich', 'Roehrichtzone', 'Ackerrandstreifen', 'Ackerbrache', 'Gruenlandbrache', 'Sukzessionsflaeche', 'Hochstaudenflur', 'Trockenrasen', 'Heide', 'Sonstiges');

CREATE TABLE xp_spe_daten (
    id UUID NOT NULL, 
    "klassifizMassnahme" xp_spemassnahmentypen, 
    "massnahmeText" VARCHAR, 
    "massnahmeKuerzel" VARCHAR, 
    bp_schutzflaeche_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(bp_schutzflaeche_id) REFERENCES bp_schutzflaeche (id) ON DELETE CASCADE
);

CREATE TYPE bp_wegerechttypen AS ENUM ('Gehrecht', 'Fahrrecht', 'Radfahrrecht', 'Leitungsrecht', 'Sonstiges');

CREATE TABLE bp_wegerecht (
    id UUID NOT NULL, 
    typ bp_wegerechttypen[], 
    "zugunstenVon" VARCHAR, 
    thema VARCHAR, 
    breite FLOAT, 
    "istSchmal" BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_bundeslaender AS ENUM ('BB', 'BE', 'BW', 'BY', 'HB', 'HE', 'HH', 'MV', 'NI', 'NW', 'RP', 'SH', 'SL', 'SN', 'ST', 'TH', 'Bund');

CREATE TYPE rp_art AS ENUM ('Regionalplan', 'SachlicherTeilplanRegionalebene', 'SachlicherTeilplanLandesebene', 'Braunkohlenplan', 'LandesweiterRaumordnungsplan', 'StandortkonzeptBund', 'AWZPlan', 'RaeumlicherTeilplan', 'Sonstiges');

CREATE TYPE rp_rechtsstand AS ENUM ('Aufstellungsbeschluss', 'Entwurf', 'EntwurfGenehmigt', 'EntwurfGeaendert', 'EntwurfAufgegeben', 'EntwurfRuht', 'Plan', 'Inkraftgetreten', 'AllgemeinePlanungsabsicht', 'AusserKraft', 'PlanUngueltig');

CREATE TYPE rp_verfahren AS ENUM ('Aenderung', 'Teilfortschreibung', 'Neuaufstellung', 'Gesamtfortschreibung', 'Aktualisierung', 'Neubekanntmachung');

CREATE TABLE rp_plan (
    id UUID NOT NULL, 
    bundesland xp_bundeslaender, 
    "planArt" rp_art NOT NULL, 
    planungsregion INTEGER, 
    teilabschnitt INTEGER, 
    rechtsstand rp_rechtsstand, 
    "aufstellungsbeschlussDatum" DATE, 
    "auslegungsStartDatum" DATE[], 
    "auslegungsEndDatum" DATE[], 
    "traegerbeteiligungsStartDatum" DATE[], 
    "traegerbeteiligungsEndDatum" DATE[], 
    "aenderungenBisDatum" DATE, 
    "entwurfsbeschlussDatum" DATE, 
    "planbeschlussDatum" DATE, 
    "datumDesInkrafttretens" DATE, 
    verfahren rp_verfahren, 
    "amtlicherSchluessel" VARCHAR, 
    genehmigungsbehoerde VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE rp_bereich (
    id UUID NOT NULL, 
    "versionBROG" DATE, 
    "versionBROGText" VARCHAR, 
    "versionLPLG" DATE, 
    "versionLPLGText" VARCHAR, 
    geltungsmassstab INTEGER, 
    "gehoertZuPlan_id" UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY("gehoertZuPlan_id") REFERENCES rp_plan (id) ON DELETE CASCADE, 
    FOREIGN KEY(id) REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE TYPE lp_planart AS ENUM ('Landschaftsprogramm', 'Landschaftsrahmenplan', 'Landschaftsplan', 'Gruenordnungsplan', 'Sonstiges');

CREATE TYPE lp_rechtsstand AS ENUM ('Aufstellungsbeschluss', 'Entwurf', 'Plan', 'Wirksamkeit', 'Untergegangen');

CREATE TABLE lp_plan (
    id UUID NOT NULL, 
    bundesland xp_bundeslaender, 
    "rechtlicheAussenwirkung" BOOLEAN, 
    "planArt" lp_planart[] NOT NULL, 
    "planungstraegerGKZ" VARCHAR, 
    planungstraeger VARCHAR, 
    rechtsstand lp_rechtsstand, 
    "aufstellungsbeschlussDatum" DATE, 
    "auslegungsDatum" DATE[], 
    "tOeBbeteiligungsDatum" DATE[], 
    "oeffentlichkeitsbeteiligungDatum" DATE[], 
    "aenderungenBisDatum" DATE, 
    "entwurfsbeschlussDatum" DATE, 
    "planbeschlussDatum" DATE, 
    "inkrafttretenDatum" DATE, 
    "sonstVerfahrensDatum" DATE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE lp_bereich (
    id UUID NOT NULL, 
    "gehoertZuPlan_id" UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY("gehoertZuPlan_id") REFERENCES lp_plan (id) ON DELETE CASCADE, 
    FOREIGN KEY(id) REFERENCES xp_bereich (id) ON DELETE CASCADE
);

ALTER TABLE xp_externe_referenz ADD COLUMN bp_schutzflaeche_massnahme_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_schutzflaeche_plan_id UUID;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_schutzflaeche_plan_ref FOREIGN KEY(bp_schutzflaeche_plan_id) REFERENCES bp_schutzflaeche (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_schutzflaeche_massnahme_ref FOREIGN KEY(bp_schutzflaeche_massnahme_id) REFERENCES bp_schutzflaeche (id) ON DELETE CASCADE;

ALTER TABLE xp_tpo ADD COLUMN skalierung FLOAT DEFAULT '0.5';

ALTER TABLE xp_objekt ADD COLUMN skalierung FLOAT DEFAULT '0.5';

ALTER TABLE xp_objekt ADD COLUMN drehwinkel INTEGER DEFAULT '0';

ALTER TABLE bp_plan ADD COLUMN plangeber_id UUID;

ALTER TABLE bp_plan ADD CONSTRAINT fk_plangeber_bp_plan FOREIGN KEY(plangeber_id) REFERENCES xp_plangeber (id);

ALTER TABLE fp_plan ADD COLUMN plangeber_id UUID;

ALTER TABLE fp_plan ADD CONSTRAINT fk_plangeber_fp_plan FOREIGN KEY(plangeber_id) REFERENCES xp_plangeber (id);

UPDATE bp_plan bp SET plangeber_id = xp.plangeber_id FROM xp_plan xp WHERE xp.id = bp.id;;

UPDATE fp_plan fp SET plangeber_id = xp.plangeber_id FROM xp_plan xp WHERE xp.id = fp.id;;

ALTER TABLE xp_plan DROP CONSTRAINT xp_plan_plangeber_id_fkey;

ALTER TABLE xp_plan DROP COLUMN plangeber_id;

ALTER TABLE xp_plan_gemeinde ADD COLUMN bp_plan_id UUID;

ALTER TABLE xp_plan_gemeinde ADD COLUMN fp_plan_id UUID;

ALTER TABLE xp_plan_gemeinde DROP CONSTRAINT xp_plan_gemeinde_plan_id_fkey;

ALTER TABLE xp_plan_gemeinde ADD CONSTRAINT xp_plan_gemeinde_bp_plan_id_fkey FOREIGN KEY(bp_plan_id) REFERENCES bp_plan (id) ON DELETE CASCADE;

ALTER TABLE xp_plan_gemeinde ADD CONSTRAINT xp_plan_gemeinde_fp_plan_id_fkey FOREIGN KEY(fp_plan_id) REFERENCES fp_plan (id) ON DELETE CASCADE;

UPDATE xp_plan_gemeinde g SET bp_plan_id = xp.id FROM xp_plan xp WHERE xp.id = g.plan_id AND xp.type = 'bp_plan';;

UPDATE xp_plan_gemeinde g SET fp_plan_id = xp.id FROM xp_plan xp WHERE xp.id = g.plan_id AND xp.type = 'fp_plan';;

ALTER TABLE xp_plan_gemeinde DROP COLUMN plan_id;

UPDATE alembic_version SET version_num='54455ce1e9f6' WHERE alembic_version.version_num = '2cee32cfc646';

COMMIT;

