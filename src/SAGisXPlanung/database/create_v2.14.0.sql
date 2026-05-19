BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> cfbf4d3b2a9d

CREATE EXTENSION IF NOT EXISTS postgis;;

CREATE TYPE xp_bedeutungenbereich AS ENUM ('Teilbereich', 'Kompensationsbereich', 'Sonstiges');

CREATE TABLE xp_bereich (
    id UUID NOT NULL, 
    type VARCHAR(50), 
    srs VARCHAR(20), 
    nummer INTEGER NOT NULL, 
    name VARCHAR, 
    bedeutung xp_bedeutungenbereich, 
    "detaillierteBedeutung" VARCHAR, 
    "erstellungsMassstab" INTEGER, 
    geltungsbereich geometry(MULTIPOLYGON,-1), 
    CONSTRAINT pk_xp_bereich PRIMARY KEY (id)
);

CREATE INDEX idx_xp_bereich_geltungsbereich ON xp_bereich USING gist (geltungsbereich);

CREATE TABLE xp_gemeinde (
    id UUID NOT NULL, 
    ags VARCHAR, 
    rs VARCHAR, 
    "gemeindeName" VARCHAR NOT NULL, 
    "ortsteilName" VARCHAR, 
    CONSTRAINT pk_xp_gemeinde PRIMARY KEY (id)
);

CREATE TABLE xp_plangeber (
    id UUID NOT NULL, 
    name VARCHAR NOT NULL, 
    kennziffer VARCHAR, 
    CONSTRAINT pk_xp_plangeber PRIMARY KEY (id)
);

CREATE TYPE xp_rechtsstand AS ENUM ('Geplant', 'Bestehend', 'Fortfallend');

CREATE TYPE xp_gesetzliche_grundlage AS ENUM ('');

CREATE TABLE xp_objekt (
    id UUID NOT NULL, 
    type VARCHAR(50), 
    uuid VARCHAR, 
    text VARCHAR, 
    rechtsstand xp_rechtsstand, 
    "gesetzlicheGrundlage" xp_gesetzliche_grundlage, 
    gliederung1 VARCHAR, 
    gliederung2 VARCHAR, 
    ebene INTEGER, 
    "gehoertZuBereich_id" UUID, 
    aufschrift VARCHAR, 
    CONSTRAINT pk_xp_objekt PRIMARY KEY (id), 
    CONSTRAINT "fk_xp_objekt_gehoertZuBereich_id_xp_bereich" FOREIGN KEY("gehoertZuBereich_id") REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE TABLE xp_plan (
    id UUID NOT NULL, 
    type VARCHAR(50), 
    srs VARCHAR(20), 
    name VARCHAR NOT NULL, 
    nummer VARCHAR, 
    "internalId" VARCHAR, 
    beschreibung VARCHAR, 
    kommentar VARCHAR, 
    "technHerstellDatum" DATE, 
    "genehmigungsDatum" DATE, 
    "untergangsDatum" DATE, 
    "erstellungsMassstab" INTEGER, 
    bezugshoehe FLOAT, 
    "technischerPlanersteller" VARCHAR, 
    "raeumlicherGeltungsbereich" geometry(MULTIPOLYGON,-1), 
    plangeber_id UUID, 
    CONSTRAINT pk_xp_plan PRIMARY KEY (id), 
    CONSTRAINT fk_xp_plan_plangeber_id_xp_plangeber FOREIGN KEY(plangeber_id) REFERENCES xp_plangeber (id)
);

CREATE INDEX "idx_xp_plan_raeumlicherGeltungsbereich" ON xp_plan USING gist ("raeumlicherGeltungsbereich");

CREATE TABLE xp_po (
    id UUID NOT NULL, 
    "gehoertZuBereich_id" UUID, 
    type VARCHAR, 
    CONSTRAINT pk_xp_po PRIMARY KEY (id), 
    CONSTRAINT "fk_xp_po_gehoertZuBereich_id_xp_bereich" FOREIGN KEY("gehoertZuBereich_id") REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE TABLE xp_simple_geometry (
    id UUID NOT NULL, 
    name VARCHAR, 
    xplanung_type VARCHAR, 
    position geometry(GEOMETRY,-1), 
    "gehoertZuBereich_id" UUID, 
    CONSTRAINT pk_xp_simple_geometry PRIMARY KEY (id), 
    CONSTRAINT "fk_xp_simple_geometry_gehoertZuBereich_id_xp_bereich" FOREIGN KEY("gehoertZuBereich_id") REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE INDEX idx_xp_simple_geometry_position ON xp_simple_geometry USING gist (position);

CREATE TYPE bp_rechtscharakter AS ENUM ('Festsetzung', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk', 'Kennzeichnung', 'Unbekannt');

CREATE TABLE bp_objekt (
    id UUID NOT NULL, 
    rechtscharakter bp_rechtscharakter, 
    position geometry(GEOMETRY,-1), 
    flaechenschluss BOOLEAN, 
    CONSTRAINT pk_bp_objekt PRIMARY KEY (id), 
    CONSTRAINT fk_bp_objekt_id_xp_objekt FOREIGN KEY(id) REFERENCES xp_objekt (id) ON DELETE CASCADE
);

CREATE INDEX idx_bp_objekt_position ON bp_objekt USING gist (position);

CREATE TYPE bp_planart AS ENUM ('BPlan', 'EinfacherBPlan', 'QualifizierterBPlan', 'VorhabenbezogenerBPlan', 'VorhabenUndErschliessungsplan', 'InnenbereichsSatzung', 'KlarstellungsSatzung', 'EntwicklungsSatzung', 'ErgaenzungsSatzung', 'AussenbereichsSatzung', 'OertlicheBauvorschrift', 'Sonstiges');

CREATE TYPE bp_verfahren AS ENUM ('Normal', 'Parag13', 'Parag13a', 'Parag13b');

CREATE TYPE bp_rechtsstand AS ENUM ('Aufstellungsbeschluss', 'Entwurf', 'FruehzeitigeBehoerdenBeteiligung', 'FruehzeitigeOeffentlichkeitsBeteiligung', 'BehoerdenBeteiligung', 'OeffentlicheAuslegung', 'Satzung', 'InkraftGetreten', 'TeilweiseUntergegangen', 'Untergegangen', 'Aufgehoben', 'AusserKraft');

CREATE TYPE xp_verlaengerungveraenderungssperre AS ENUM ('Keine', 'ErsteVerlaengerung', 'ZweiteVerlaengerung');

CREATE TABLE bp_plan (
    id UUID NOT NULL, 
    "planArt" bp_planart NOT NULL, 
    verfahren bp_verfahren, 
    rechtsstand bp_rechtsstand, 
    hoehenbezug VARCHAR, 
    "aenderungenBisDatum" DATE, 
    "aufstellungsbeschlussDatum" DATE, 
    "veraenderungssperreBeschlussDatum" DATE, 
    "veraenderungssperreDatum" DATE, 
    "veraenderungssperreEndDatum" DATE, 
    "verlaengerungVeraenderungssperre" xp_verlaengerungveraenderungssperre, 
    "auslegungsStartDatum" DATE[], 
    "auslegungsEndDatum" DATE[], 
    "traegerbeteiligungsStartDatum" DATE[], 
    "traegerbeteiligungsEndDatum" DATE[], 
    "satzungsbeschlussDatum" DATE, 
    "rechtsverordnungsDatum" DATE, 
    "inkrafttretensDatum" DATE, 
    "ausfertigungsDatum" DATE, 
    veraenderungssperre BOOLEAN, 
    "staedtebaulicherVertrag" BOOLEAN, 
    "erschliessungsVertrag" BOOLEAN, 
    "durchfuehrungsVertrag" BOOLEAN, 
    gruenordnungsplan BOOLEAN, 
    "versionBauNVODatum" DATE, 
    "versionBauNVOText" VARCHAR, 
    "versionBauGBDatum" DATE, 
    "versionBauGBText" VARCHAR, 
    "versionSonstRechtsgrundlageDatum" DATE, 
    "versionSonstRechtsgrundlageText" VARCHAR, 
    CONSTRAINT pk_bp_plan PRIMARY KEY (id), 
    CONSTRAINT fk_bp_plan_id_xp_plan FOREIGN KEY(id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TYPE fp_planart AS ENUM ('FPlan', 'GemeinsamerFPlan', 'RegFPlan', 'FPlanRegPlan', 'SachlicherTeilplan', 'Sonstiges');

CREATE TYPE fp_verfahren AS ENUM ('Normal', 'Parag13');

CREATE TYPE fp_rechtsstand AS ENUM ('Aufstellungsbeschluss', 'Entwurf', 'FruehzeitigeBehoerdenBeteiligung', 'FruehzeitigeOeffentlichkeitsBeteiligung', 'BehoerdenBeteiligung', 'OeffentlicheAuslegung', 'Plan', 'Wirksamkeit', 'Untergegangen', 'Aufgehoben', 'AusserKraft');

CREATE TABLE fp_plan (
    id UUID NOT NULL, 
    "planArt" fp_planart NOT NULL, 
    sachgebiet VARCHAR, 
    verfahren fp_verfahren, 
    rechtsstand fp_rechtsstand, 
    "aufstellungsbeschlussDatum" DATE, 
    "auslegungsStartDatum" DATE[], 
    "auslegungsEndDatum" DATE[], 
    "traegerbeteiligungsStartDatum" DATE[], 
    "traegerbeteiligungsEndDatum" DATE[], 
    "aenderungenBisDatum" DATE, 
    "entwurfsbeschlussDatum" DATE, 
    "planbeschlussDatum" DATE, 
    "wirksamkeitsDatum" DATE, 
    "versionBauNVODatum" DATE, 
    "versionBauNVOText" VARCHAR, 
    "versionBauGBDatum" DATE, 
    "versionBauGBText" VARCHAR, 
    "versionSonstRechtsgrundlageDatum" DATE, 
    "versionSonstRechtsgrundlageText" VARCHAR, 
    CONSTRAINT pk_fp_plan PRIMARY KEY (id), 
    CONSTRAINT fk_fp_plan_id_xp_plan FOREIGN KEY(id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE xp_plan_gemeinde (
    plan_id UUID, 
    gemeinde_id UUID, 
    CONSTRAINT fk_xp_plan_gemeinde_gemeinde_id_xp_gemeinde FOREIGN KEY(gemeinde_id) REFERENCES xp_gemeinde (id), 
    CONSTRAINT fk_xp_plan_gemeinde_plan_id_xp_plan FOREIGN KEY(plan_id) REFERENCES xp_plan (id)
);

CREATE TABLE xp_ppo (
    id UUID NOT NULL, 
    position geometry(POINT,-1), 
    drehwinkel INTEGER, 
    skalierung FLOAT, 
    symbol_path VARCHAR, 
    CONSTRAINT pk_xp_ppo PRIMARY KEY (id), 
    CONSTRAINT fk_xp_ppo_id_xp_po FOREIGN KEY(id) REFERENCES xp_po (id) ON DELETE CASCADE
);

CREATE INDEX idx_xp_ppo_position ON xp_ppo USING gist (position);

CREATE TYPE xp_externereferenzart AS ENUM ('Dokument', 'PlanMitGeoreferenz');

CREATE TYPE xp_mime_types AS ENUM ('application/pdf', 'application/zip', 'application/xml', 'application/msword', 'application/msexcel', 'application/vnd.ogc.sld+xml', 'application/vnd.ogc.wms_xml', 'application/vnd.ogc.gml', 'application/vnd.shp', 'application/vnd.dbf', 'application/vnd.shx', 'application/octet-stream', 'image/vnd.dxf', 'image/vnd.dwg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp', 'image/ecw', 'image/svg+xml', 'text/html', 'text/plain');

CREATE TYPE xp_externereferenztyp AS ENUM ('Beschreibung', 'Begruendung', 'Legende', 'Rechtsplan', 'Plangrundlage', 'Umweltbericht', 'Satzung', 'Verordnung', 'Karte', 'Erlaeuterung', 'ZusammenfassendeErklaerung', 'Koordinatenliste', 'Grundstuecksverzeichnis', 'Pflanzliste', 'Gruenordnungsplan', 'Erschliessungsvertrag', 'Durchfuehrungsvertrag', 'StaedtebaulicherVertrag', 'UmweltbezogeneStellungnahmen', 'Beschluss', 'VorhabenUndErschliessungsplan', 'MetadatenPlan', 'Genehmigung', 'Bekanntmachung', 'Rechtsverbindlich', 'Informell');

CREATE TABLE xp_spez_externe_referenz (
    id UUID NOT NULL, 
    "georefURL" VARCHAR, 
    art xp_externereferenzart, 
    "referenzName" VARCHAR, 
    "referenzURL" VARCHAR, 
    "referenzMimeType" xp_mime_types, 
    beschreibung VARCHAR, 
    datum DATE, 
    file BYTEA, 
    typ xp_externereferenztyp, 
    plan_id UUID, 
    CONSTRAINT pk_xp_spez_externe_referenz PRIMARY KEY (id), 
    CONSTRAINT ck_xp_spez_externe_referenz_referenz_name_or_url_not_null CHECK (NOT("referenzName" IS NULL AND "referenzURL" IS NULL)), 
    CONSTRAINT fk_xp_spez_externe_referenz_plan_id_xp_plan FOREIGN KEY(plan_id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE xp_tpo (
    id UUID NOT NULL, 
    position geometry(POINT,-1), 
    drehwinkel INTEGER, 
    schriftinhalt VARCHAR, 
    CONSTRAINT pk_xp_tpo PRIMARY KEY (id), 
    CONSTRAINT fk_xp_tpo_id_xp_po FOREIGN KEY(id) REFERENCES xp_po (id) ON DELETE CASCADE
);

CREATE INDEX idx_xp_tpo_position ON xp_tpo USING gist (position);

CREATE TABLE xp_verfahrens_merkmal (
    id UUID NOT NULL, 
    plan_id UUID, 
    vermerk VARCHAR NOT NULL, 
    datum DATE NOT NULL, 
    signatur VARCHAR NOT NULL, 
    signiert BOOLEAN NOT NULL, 
    CONSTRAINT pk_xp_verfahrens_merkmal PRIMARY KEY (id), 
    CONSTRAINT fk_xp_verfahrens_merkmal_plan_id_xp_plan FOREIGN KEY(plan_id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TYPE bp_zulaessigkeit AS ENUM ('Zulaessig', 'NichtZulaessig', 'AusnahmsweiseZulaessig');

CREATE TYPE xp_allgartderbaulnutzung AS ENUM ('WohnBauflaeche', 'GemischteBauflaeche', 'GewerblicheBauflaeche', 'SonderBauflaeche', 'Sonstiges');

CREATE TYPE xp_besondereartderbaulnutzung AS ENUM ('Kleinsiedlungsgebiet', 'ReinesWohngebiet', 'AllgWohngebiet', 'BesonderesWohngebiet', 'Dorfgebiet', 'Mischgebiet', 'UrbanesGebiet', 'Kerngebiet', 'Gewerbegebiet', 'Industriegebiet', 'SondergebietErholung', 'SondergebietSonst', 'Wochenendhausgebiet', 'Sondergebiet', 'SonstigesGebiet');

CREATE TYPE xp_sondernutzungen AS ENUM ('KeineSondernutzung', 'Wochendhausgebiet', 'Ferienhausgebiet', 'Campingplatzgebiet', 'Kurgebiet', 'SonstSondergebietErholung', 'Einzelhandelsgebiet', 'GrossflaechigerEinzelhandel', 'Ladengebiet', 'Einkaufszentrum', 'SonstGrossflEinzelhandel', 'Verkehrsuebungsplatz', 'Hafengebiet', 'SondergebietErneuerbareEnergie', 'SondergebietMilitaer', 'SondergebietLandwirtschaft', 'SondergebietSport', 'SondergebietGesundheitSoziales', 'Klinikgebiet', 'Golfplatz', 'SondergebietKultur', 'SondergebietTourismus', 'SondergebietBueroUndVerwaltung', 'SondergebietJustiz', 'SondergebietHochschuleForschung', 'SondergebietMesse', 'SondergebietAndereNutzungen');

CREATE TYPE xp_abweichungbaunvotypen AS ENUM ('KeineAbweichung', 'EinschraenkungNutzung', 'AusschlussNutzung', 'AusweitungNutzung', 'SonstAbweichung');

CREATE TYPE bp_bauweise AS ENUM ('KeineAngabe', 'OffeneBauweise', 'GeschlosseneBauweise', 'AbweichendeBauweise');

CREATE TYPE bp_bebauungsart AS ENUM ('Einzelhaeuser', 'Doppelhaeuser', 'Hausgruppen', 'EinzelDoppelhaeuser', 'EinzelhaeuserHausgruppen', 'DoppelhaeuserHausgruppen', 'Reihenhaeuser', 'EinzelhaeuserDoppelhaeuserHausgruppen');

CREATE TYPE bp_grenzbebauung AS ENUM ('KeineAngabe', 'Verboten', 'Erlaubt', 'Erzwungen');

CREATE TABLE bp_baugebiet (
    id UUID NOT NULL, 
    "FR" INTEGER, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    "wohnnutzungEGStrasse" bp_zulaessigkeit, 
    "ZWohn" INTEGER, 
    "GFAntWohnen" INTEGER, 
    "GFWohnen" FLOAT, 
    "GFAntGewerbe" INTEGER, 
    "GFGewerbe" FLOAT, 
    "VF" FLOAT, 
    "allgArtDerBaulNutzung" xp_allgartderbaulnutzung, 
    "besondereArtDerBaulNutzung" xp_besondereartderbaulnutzung, 
    sondernutzung xp_sondernutzungen, 
    "nutzungText" VARCHAR, 
    "abweichungBauNVO" xp_abweichungbaunvotypen, 
    bauweise bp_bauweise, 
    "vertikaleDifferenzierung" BOOLEAN, 
    "bebauungsArt" bp_bebauungsart, 
    "bebauungVordereGrenze" bp_grenzbebauung, 
    "bebauungRueckwaertigeGrenze" bp_grenzbebauung, 
    "bebauungSeitlicheGrenze" bp_grenzbebauung, 
    "zugunstenVon" VARCHAR, 
    CONSTRAINT pk_bp_baugebiet PRIMARY KEY (id), 
    CONSTRAINT fk_bp_baugebiet_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_baugrenze (
    id UUID NOT NULL, 
    bautiefe FLOAT, 
    "geschossMin" INTEGER, 
    "geschossMax" INTEGER, 
    CONSTRAINT pk_bp_baugrenze PRIMARY KEY (id), 
    CONSTRAINT fk_bp_baugrenze_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_bereich (
    id UUID NOT NULL, 
    "versionBauGBDatum" DATE, 
    "versionBauGBText" VARCHAR, 
    "versionSonstRechtsgrundlageDatum" DATE, 
    "versionSonstRechtsgrundlageText" VARCHAR, 
    "gehoertZuPlan_id" UUID, 
    CONSTRAINT pk_bp_bereich PRIMARY KEY (id), 
    CONSTRAINT "fk_bp_bereich_gehoertZuPlan_id_bp_plan" FOREIGN KEY("gehoertZuPlan_id") REFERENCES bp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_bereich_id_xp_bereich FOREIGN KEY(id) REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE TABLE fp_bereich (
    id UUID NOT NULL, 
    "gehoertZuPlan_id" UUID, 
    CONSTRAINT pk_fp_bereich PRIMARY KEY (id), 
    CONSTRAINT "fk_fp_bereich_gehoertZuPlan_id_fp_plan" FOREIGN KEY("gehoertZuPlan_id") REFERENCES fp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_fp_bereich_id_xp_bereich FOREIGN KEY(id) REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE TYPE bp_dachform AS ENUM ('Flachdach', 'Pultdach', 'VersetztesPultdach', 'GeneigtesDach', 'Satteldach', 'Walmdach', 'KrueppelWalmdach', 'Mansarddach', 'Zeltdach', 'Kegeldach', 'Kuppeldach', 'Sheddach', 'Bogendach', 'Turmdach', 'Tonnendach', 'Mischform', 'Sonstiges');

CREATE TABLE bp_dachgestaltung (
    id UUID NOT NULL, 
    "DNmin" INTEGER, 
    "DNmax" INTEGER, 
    "DN" INTEGER, 
    "DNZwingend" INTEGER, 
    dachform bp_dachform, 
    baugebiet_id UUID, 
    CONSTRAINT pk_bp_dachgestaltung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_dachgestaltung_baugebiet_id_bp_baugebiet FOREIGN KEY(baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE
);

CREATE TABLE xp_externe_referenz (
    id UUID NOT NULL, 
    "georefURL" VARCHAR, 
    art xp_externereferenzart, 
    "referenzName" VARCHAR, 
    "referenzURL" VARCHAR, 
    "referenzMimeType" xp_mime_types, 
    beschreibung VARCHAR, 
    datum DATE, 
    file BYTEA, 
    bereich_id UUID, 
    baugebiet_id UUID, 
    CONSTRAINT pk_xp_externe_referenz PRIMARY KEY (id), 
    CONSTRAINT ck_xp_spez_externe_referenz_referenz_name_or_url_not_null CHECK (NOT("referenzName" IS NULL AND "referenzURL" IS NULL)), 
    CONSTRAINT fk_xp_externe_referenz_baugebiet_id_bp_baugebiet FOREIGN KEY(baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_externe_referenz_bereich_id_xp_bereich FOREIGN KEY(bereich_id) REFERENCES xp_bereich (id) ON DELETE CASCADE
);

INSERT INTO alembic_version (version_num) VALUES ('cfbf4d3b2a9d') RETURNING alembic_version.version_num;

-- Running upgrade cfbf4d3b2a9d -> 20c50b38b0af

CREATE TABLE bp_flaeche_ohne_festsetzung (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_flaeche_ohne_festsetzung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_flaeche_ohne_festsetzung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE bp_objekt ALTER COLUMN rechtscharakter SET NOT NULL;

ALTER TABLE xp_bereich DROP COLUMN srs;

ALTER TABLE xp_plan DROP COLUMN srs;

UPDATE alembic_version SET version_num='20c50b38b0af' WHERE alembic_version.version_num = 'cfbf4d3b2a9d'; --- # pragma: allowlist secret;

-- Running upgrade 20c50b38b0af -> 2cee32cfc646

CREATE TABLE bp_baulinie (
    id UUID NOT NULL, 
    bautiefe FLOAT, 
    "geschossMin" INTEGER, 
    "geschossMax" INTEGER, 
    CONSTRAINT pk_bp_baulinie PRIMARY KEY (id), 
    CONSTRAINT fk_bp_baulinie_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_besondere_nutzung (
    id UUID NOT NULL, 
    "FR" FLOAT, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    zweckbestimmung VARCHAR, 
    bauweise bp_bauweise, 
    "bebauungsArt" bp_bebauungsart, 
    CONSTRAINT pk_bp_besondere_nutzung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_besondere_nutzung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmunggemeinbedarf AS ENUM ('OeffentlicheVerwaltung', 'KommunaleEinrichtung', 'BetriebOeffentlZweckbestimmung', 'AnlageBundLand', 'BildungForschung', 'Schule', 'Hochschule', 'BerufsbildendeSchule', 'Forschungseinrichtung', 'Kirche', 'Sakralgebaeude', 'KirchlicheVerwaltung', 'Kirchengemeinde', 'Sozial', 'EinrichtungKinder', 'EinrichtungJugendliche', 'EinrichtungFamilienErwachsene', 'EinrichtungSenioren', 'SonstigeSozialeEinrichtung', 'EinrichtungBehinderte', 'Gesundheit', 'Krankenhaus', 'Kultur', 'MusikTheater', 'Bildung', 'Sport', 'Bad', 'SportplatzSporthalle', 'SicherheitOrdnung', 'Feuerwehr', 'Schutzbauwerk', 'Justiz', 'Infrastruktur', 'Post', 'Sonstiges');

CREATE TABLE bp_gemeinbedarf (
    id UUID NOT NULL, 
    "FR" INTEGER, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    zweckbestimmung xp_zweckbestimmunggemeinbedarf, 
    bauweise bp_bauweise, 
    "bebauungsArt" bp_bebauungsart, 
    "zugunstenVon" VARCHAR, 
    CONSTRAINT pk_bp_gemeinbedarf PRIMARY KEY (id), 
    CONSTRAINT fk_bp_gemeinbedarf_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmunggewaesser AS ENUM ('Hafen', 'Sportboothafen', 'Wasserflaeche', 'Fliessgewaesser', 'Sonstiges');

CREATE TABLE bp_gewaesser (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunggewaesser, 
    CONSTRAINT pk_bp_gewaesser PRIMARY KEY (id), 
    CONSTRAINT fk_bp_gewaesser_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmunggruen AS ENUM ('Parkanlage', 'ParkanlageHistorisch', 'ParkanlageNaturnah', 'ParkanlageWaldcharakter', 'NaturnaheUferParkanlage', 'Dauerkleingarten', 'ErholungsGaerten', 'Sportplatz', 'Reitsportanlage', 'Hundesportanlage', 'Wassersportanlage', 'Schiessstand', 'Golfplatz', 'Skisport', 'Tennisanlage', 'Spielplatz', 'Bolzplatz', 'Abenteuerspielplatz', 'Zeltplatz', 'Campingplatz', 'Badeplatz', 'FreizeitErholung', 'Kleintierhaltung', 'Festplatz', 'SpezGruenflaeche', 'StrassenbegleitGruen', 'BoeschungsFlaeche', 'FeldWaldWiese', 'Uferschutzstreifen', 'Abschirmgruen', 'UmweltbildungsparkSchaugatter', 'RuhenderVerkehr', 'Friedhof', 'Sonstiges', 'Gaertnerei');

CREATE TYPE xp_nutzungsform AS ENUM ('Privat', 'Oeffentlich');

CREATE TABLE bp_gruenflaeche (
    id UUID NOT NULL, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    zweckbestimmung xp_zweckbestimmunggruen, 
    nutzungsform xp_nutzungsform, 
    "zugunstenVon" VARCHAR, 
    CONSTRAINT pk_bp_gruenflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_gruenflaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmunglandwirtschaft AS ENUM ('LandwirtschaftAllgemein', 'Ackerbau', 'WiesenWeidewirtschaft', 'GartenbaulicheErzeugung', 'Obstbau', 'Weinbau', 'Imkerei', 'Binnenfischerei', 'Sonstiges');

CREATE TABLE bp_landwirtschaft (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunglandwirtschaft, 
    CONSTRAINT pk_bp_landwirtschaft PRIMARY KEY (id), 
    CONSTRAINT fk_bp_landwirtschaft_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_abemassnahmentypen AS ENUM ('BindungErhaltung', 'Anpflanzung');

CREATE TYPE xp_anpflanzungbindungerhaltungsgegenstand AS ENUM ('Baeume', 'Kopfbaeume', 'Baumreihe', 'Straeucher', 'BaeumeUndStraeucher', 'Hecke', 'Knick', 'SonstBepflanzung', 'Gewaesser', 'Fassadenbegruenung', 'Dachbegruenung');

CREATE TABLE bp_pflanzung (
    id UUID NOT NULL, 
    massnahme xp_abemassnahmentypen, 
    gegenstand xp_anpflanzungbindungerhaltungsgegenstand, 
    kronendurchmesser FLOAT, 
    pflanztiefe FLOAT, 
    "istAusgleich" BOOLEAN, 
    "baumArt" VARCHAR, 
    mindesthoehe FLOAT, 
    anzahl INTEGER, 
    CONSTRAINT pk_bp_pflanzung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_pflanzung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmungspielsportanlage AS ENUM ('Sportanlage', 'Spielanlage', 'SpielSportanlage', 'Sonstiges');

CREATE TABLE bp_spiel_sportanlage (
    id UUID NOT NULL, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    zweckbestimmung xp_zweckbestimmungspielsportanlage, 
    "zugunstenVon" VARCHAR, 
    CONSTRAINT pk_bp_spiel_sportanlage PRIMARY KEY (id), 
    CONSTRAINT fk_bp_spiel_sportanlage_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_strassenbegrenzung (
    id UUID NOT NULL, 
    bautiefe FLOAT, 
    CONSTRAINT pk_bp_strassenbegrenzung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_strassenbegrenzung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_strassenverkehr (
    id UUID NOT NULL, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    nutzungsform xp_nutzungsform, 
    CONSTRAINT pk_bp_strassenverkehr PRIMARY KEY (id), 
    CONSTRAINT fk_bp_strassenverkehr_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE bp_zweckbestimmungstrassenverkehr AS ENUM ('Parkierungsflaeche', 'Fussgaengerbereich', 'VerkehrsberuhigterBereich', 'RadGehweg', 'Radweg', 'Gehweg', 'Wanderweg', 'ReitKutschweg', 'Wirtschaftsweg', 'FahrradAbstellplatz', 'UeberfuehrenderVerkehrsweg', 'UnterfuehrenderVerkehrsweg', 'P_RAnlage', 'Platz', 'Anschlussflaeche', 'LandwirtschaftlicherVerkehr', 'Verkehrsgruen', 'Rastanlage', 'Busbahnhof', 'CarSharing', 'BikeSharing', 'B_RAnlage', 'Parkhaus', 'Mischverkehrsflaeche', 'Ladestation', 'Sonstiges');

CREATE TABLE bp_verkehr_besonders (
    id UUID NOT NULL, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    zweckbestimmung bp_zweckbestimmungstrassenverkehr, 
    nutzungsform xp_nutzungsform, 
    "zugunstenVon" VARCHAR, 
    CONSTRAINT pk_bp_verkehr_besonders PRIMARY KEY (id), 
    CONSTRAINT fk_bp_verkehr_besonders_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmungverentsorgung AS ENUM ('Elektrizitaet', 'Hochspannungsleitung', 'TrafostationUmspannwerk', 'Solarkraftwerk', 'Windkraftwerk', 'Geothermiekraftwerk', 'Elektrizitaetswerk', 'Wasserkraftwerk', 'BiomasseKraftwerk', 'Kabelleitung', 'Niederspannungsleitung', 'Leitungsmast', 'Kernkraftwerk', 'Kohlekraftwerk', 'Gaskraftwerk', 'Gas', 'Ferngasleitung', 'Gaswerk', 'Gasbehaelter', 'Gasdruckregler', 'Gasstation', 'Gasleitung', 'Erdoel', 'Erdoelleitung', 'Bohrstelle', 'Erdoelpumpstation', 'Oeltank', 'Waermeversorgung', 'Blockheizkraftwerk', 'Fernwaermeleitung', 'Fernheizwerk', 'Wasser', 'Wasserwerk', 'Wasserleitung', 'Wasserspeicher', 'Brunnen', 'Pumpwerk', 'Quelle', 'Abwasser', 'Abwasserleitung', 'Abwasserrueckhaltebecken', 'Abwasserpumpwerk', 'Klaeranlage', 'AnlageKlaerschlamm', 'SonstigeAbwasserBehandlungsanlage', 'SalzOderSoleleitungen', 'Regenwasser', 'RegenwasserRueckhaltebecken', 'Niederschlagswasserleitung', 'Abfallentsorgung', 'Muellumladestation', 'Muellbeseitigungsanlage', 'Muellsortieranlage', 'Recyclinghof', 'Ablagerung', 'Erdaushubdeponie', 'Bauschuttdeponie', 'Hausmuelldeponie', 'Sondermuelldeponie', 'StillgelegteDeponie', 'RekultivierteDeponie', 'Telekommunikation', 'Fernmeldeanlage', 'Mobilfunkanlage', 'Fernmeldekabel', 'ErneuerbareEnergien', 'KraftWaermeKopplung', 'Sonstiges', 'Produktenleitung');

CREATE TABLE bp_versorgung (
    id UUID NOT NULL, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    zweckbestimmung xp_zweckbestimmungverentsorgung, 
    "textlicheErgaenzung" VARCHAR, 
    "zugunstenVon" VARCHAR, 
    CONSTRAINT pk_bp_versorgung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_versorgung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmungwald AS ENUM ('Naturwald', 'Waldschutzgebiet', 'Nutzwald', 'Erholungswald', 'Schutzwald', 'Bodenschutzwald', 'Biotopschutzwald', 'NaturnaherWald', 'SchutzwaldSchaedlicheUmwelteinwirkungen', 'Schonwald', 'Bannwald', 'FlaecheForstwirtschaft', 'ImmissionsgeschaedigterWald', 'Sonstiges');

CREATE TYPE xp_eigentumsartwald AS ENUM ('OeffentlicherWald', 'Staatswald', 'Koerperschaftswald', 'Kommunalwald', 'Stiftungswald', 'Privatwald', 'Gemeinschaftswald', 'Genossenschaftswald', 'Kirchenwald', 'Sonstiges');

CREATE TYPE xp_waldbetretungtyp AS ENUM ('KeineZusaetzlicheBetretung', 'Radfahren', 'Reiten', 'Fahren', 'Hundesport', 'Sonstiges');

CREATE TABLE bp_wald (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungwald, 
    eigentumsart xp_eigentumsartwald, 
    betreten xp_waldbetretungtyp, 
    CONSTRAINT pk_bp_wald PRIMARY KEY (id), 
    CONSTRAINT fk_bp_wald_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE bp_dachgestaltung ADD COLUMN besondere_nutzung_id UUID;

ALTER TABLE bp_dachgestaltung ADD COLUMN gemeinbedarf_id UUID;

ALTER TABLE bp_dachgestaltung ADD CONSTRAINT fk_dachgestaltung_gemeinbedarf FOREIGN KEY(gemeinbedarf_id) REFERENCES bp_gemeinbedarf (id) ON DELETE CASCADE;

ALTER TABLE bp_dachgestaltung ADD CONSTRAINT fk_dachgestaltung_besondere_nutzung FOREIGN KEY(besondere_nutzung_id) REFERENCES bp_besondere_nutzung (id) ON DELETE CASCADE;

UPDATE alembic_version SET version_num='2cee32cfc646' WHERE alembic_version.version_num = '20c50b38b0af'; --- # pragma: allowlist secret;

-- Running upgrade 2cee32cfc646 -> 54455ce1e9f6

CREATE TYPE xp_speziele AS ENUM ('SchutzPflege', 'Entwicklung', 'Anlage', 'SchutzPflegeEntwicklung', 'Sonstiges');

CREATE TABLE bp_schutzflaeche (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    "istAusgleich" BOOLEAN, 
    CONSTRAINT pk_bp_schutzflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_schutzflaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_spemassnahmentypen AS ENUM ('ArtentreicherGehoelzbestand', 'NaturnaherWald', 'ExtensivesGruenland', 'Feuchtgruenland', 'Obstwiese', 'NaturnaherUferbereich', 'Roehrichtzone', 'Ackerrandstreifen', 'Ackerbrache', 'Gruenlandbrache', 'Sukzessionsflaeche', 'Hochstaudenflur', 'Trockenrasen', 'Heide', 'Sonstiges');

CREATE TABLE xp_spe_daten (
    id UUID NOT NULL, 
    "klassifizMassnahme" xp_spemassnahmentypen, 
    "massnahmeText" VARCHAR, 
    "massnahmeKuerzel" VARCHAR, 
    bp_schutzflaeche_id UUID, 
    CONSTRAINT pk_xp_spe_daten PRIMARY KEY (id), 
    CONSTRAINT fk_xp_spe_daten_bp_schutzflaeche_id_bp_schutzflaeche FOREIGN KEY(bp_schutzflaeche_id) REFERENCES bp_schutzflaeche (id) ON DELETE CASCADE
);

CREATE TYPE bp_wegerechttypen AS ENUM ('Gehrecht', 'Fahrrecht', 'Radfahrrecht', 'Leitungsrecht', 'Sonstiges');

CREATE TABLE bp_wegerecht (
    id UUID NOT NULL, 
    typ bp_wegerechttypen[], 
    "zugunstenVon" VARCHAR, 
    thema VARCHAR, 
    breite FLOAT, 
    "istSchmal" BOOLEAN, 
    CONSTRAINT pk_bp_wegerecht PRIMARY KEY (id), 
    CONSTRAINT fk_bp_wegerecht_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
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
    CONSTRAINT pk_rp_plan PRIMARY KEY (id), 
    CONSTRAINT fk_rp_plan_id_xp_plan FOREIGN KEY(id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE rp_bereich (
    id UUID NOT NULL, 
    "versionBROG" DATE, 
    "versionBROGText" VARCHAR, 
    "versionLPLG" DATE, 
    "versionLPLGText" VARCHAR, 
    geltungsmassstab INTEGER, 
    "gehoertZuPlan_id" UUID, 
    CONSTRAINT pk_rp_bereich PRIMARY KEY (id), 
    CONSTRAINT "fk_rp_bereich_gehoertZuPlan_id_rp_plan" FOREIGN KEY("gehoertZuPlan_id") REFERENCES rp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_rp_bereich_id_xp_bereich FOREIGN KEY(id) REFERENCES xp_bereich (id) ON DELETE CASCADE
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
    CONSTRAINT pk_lp_plan PRIMARY KEY (id), 
    CONSTRAINT fk_lp_plan_id_xp_plan FOREIGN KEY(id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE lp_bereich (
    id UUID NOT NULL, 
    "gehoertZuPlan_id" UUID, 
    CONSTRAINT pk_lp_bereich PRIMARY KEY (id), 
    CONSTRAINT "fk_lp_bereich_gehoertZuPlan_id_lp_plan" FOREIGN KEY("gehoertZuPlan_id") REFERENCES lp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_lp_bereich_id_xp_bereich FOREIGN KEY(id) REFERENCES xp_bereich (id) ON DELETE CASCADE
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

ALTER TABLE xp_plan DROP COLUMN plangeber_id;

ALTER TABLE xp_plan_gemeinde ADD COLUMN bp_plan_id UUID;

ALTER TABLE xp_plan_gemeinde ADD COLUMN fp_plan_id UUID;

ALTER TABLE xp_plan_gemeinde DROP CONSTRAINT fk_xp_plan_gemeinde_plan_id_xp_plan;

ALTER TABLE xp_plan_gemeinde ADD CONSTRAINT xp_plan_gemeinde_bp_plan_id_fkey FOREIGN KEY(bp_plan_id) REFERENCES bp_plan (id) ON DELETE CASCADE;

ALTER TABLE xp_plan_gemeinde ADD CONSTRAINT xp_plan_gemeinde_fp_plan_id_fkey FOREIGN KEY(fp_plan_id) REFERENCES fp_plan (id) ON DELETE CASCADE;

UPDATE xp_plan_gemeinde g SET bp_plan_id = xp.id FROM xp_plan xp WHERE xp.id = g.plan_id AND xp.type = 'bp_plan';;

UPDATE xp_plan_gemeinde g SET fp_plan_id = xp.id FROM xp_plan xp WHERE xp.id = g.plan_id AND xp.type = 'fp_plan';;

ALTER TABLE xp_plan_gemeinde DROP COLUMN plan_id;

UPDATE alembic_version SET version_num='54455ce1e9f6' WHERE alembic_version.version_num = '2cee32cfc646'; --- # pragma: allowlist secret;

-- Running upgrade 54455ce1e9f6 -> 873e18b73036

CREATE TYPE buildingtemplatecelldatatype AS ENUM ('ArtDerBaulNutzung', 'ZahlVollgeschosse', 'GRZ', 'GFZ', 'BebauungsArt', 'Bauweise', 'Dachneigung', 'Dachform');

CREATE TABLE xp_nutzungsschablone (
    id UUID NOT NULL, 
    position geometry(POINT,-1), 
    drehwinkel INTEGER, 
    skalierung FLOAT, 
    "spaltenAnz" INTEGER NOT NULL, 
    "zeilenAnz" INTEGER NOT NULL, 
    hidden BOOLEAN, 
    data_attributes buildingtemplatecelldatatype[], 
    CONSTRAINT pk_xp_nutzungsschablone PRIMARY KEY (id), 
    CONSTRAINT fk_xp_nutzungsschablone_id_xp_po FOREIGN KEY(id) REFERENCES xp_po (id) ON DELETE CASCADE
);

CREATE INDEX idx_xp_nutzungsschablone_position ON xp_nutzungsschablone USING gist (position);

ALTER TABLE xp_po ADD COLUMN "dientZurDarstellungVon_id" UUID;

ALTER TABLE xp_po ADD CONSTRAINT fk_po_xp_object FOREIGN KEY("dientZurDarstellungVon_id") REFERENCES xp_objekt (id) ON DELETE CASCADE;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";;

INSERT INTO xp_po(id, type, "dientZurDarstellungVon_id") SELECT uuid_generate_v4(), 'xp_nutzungsschablone', bp_baugebiet.id FROM bp_baugebiet;

INSERT INTO xp_nutzungsschablone(id, drehwinkel, skalierung, "spaltenAnz", "zeilenAnz", hidden) SELECT xp_po.id, 0, 0.5, 2, 3, TRUE FROM xp_po WHERE xp_po.type = 'xp_nutzungsschablone';

create table civil_gemeinde
        (
            id             uuid       not null
                primary key,
            ags            varchar(8) not null,
            rs             varchar(12),
            "gemeindeName" varchar    not null,
            "ortsteilName" varchar
        );

        create table civil_plan
        (
            id          uuid                                   not null
                primary key,
            art         bp_planart default 'BPlan'::bp_planart not null,
            gemeinde_id uuid
                constraint plan_gemeinde_fkey
                    references civil_gemeinde,
            name        varchar(255)                           not null
        );

        create table civil_area
        (
            id              uuid                   not null
                constraint bp_area_pkey
                    primary key,
            layer           varchar(255)           not null,
            rechtscharakter bp_rechtscharakter default 'Unbekannt'::bp_rechtscharakter,
            geom            geometry(MultiPolygon) not null,
            plan_id         uuid
                constraint area_plan_fkey
                    references civil_plan
        );

        create table civil_point
        (
            id              uuid not null
                constraint bp_point_pkey
                    primary key,
            layer           varchar(255),
            rechtscharakter bp_rechtscharakter default 'Unbekannt'::bp_rechtscharakter,
            geom            geometry(Point),
            plan_id         uuid
                constraint point_plan_fkey
                    references civil_plan
        );

        create table civil_line
        (
            id              uuid not null
                constraint bp_line_pkey
                    primary key,
            layer           varchar(255),
            rechtscharakter bp_rechtscharakter default 'Unbekannt'::bp_rechtscharakter,
            geom            geometry(MultiLineString),
            plan_id         uuid
                constraint line_plan_fkey
                    references civil_plan
        );;

UPDATE alembic_version SET version_num='873e18b73036' WHERE alembic_version.version_num = '54455ce1e9f6'; --- # pragma: allowlist secret;

-- Running upgrade 873e18b73036 -> 1a015621a38f

CREATE TYPE fp_rechtscharakter AS ENUM ('Darstellung', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk', 'Kennzeichnung', 'Unbekannt');

CREATE TABLE fp_objekt (
    id UUID NOT NULL, 
    rechtscharakter fp_rechtscharakter NOT NULL, 
    "vonGenehmigungAusgenommen" BOOLEAN, 
    position geometry(GEOMETRY,-1), 
    flaechenschluss BOOLEAN, 
    CONSTRAINT pk_fp_objekt PRIMARY KEY (id), 
    CONSTRAINT fk_fp_objekt_id_xp_objekt FOREIGN KEY(id) REFERENCES xp_objekt (id) ON DELETE CASCADE
);

CREATE INDEX idx_fp_objekt_position ON fp_objekt USING gist (position);

CREATE TABLE fp_baugebiet (
    id UUID NOT NULL, 
    "GFZ" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "BMZ" FLOAT, 
    "GRZ" FLOAT, 
    "allgArtDerBaulNutzung" xp_allgartderbaulnutzung, 
    "besondereArtDerBaulNutzung" xp_besondereartderbaulnutzung, 
    "sonderNutzung" xp_sondernutzungen[], 
    "nutzungText" VARCHAR, 
    CONSTRAINT pk_fp_baugebiet PRIMARY KEY (id), 
    CONSTRAINT fk_fp_baugebiet_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_gemeinbedarf (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunggemeinbedarf, 
    CONSTRAINT pk_fp_gemeinbedarf PRIMARY KEY (id), 
    CONSTRAINT fk_fp_gemeinbedarf_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_gewaesser (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunggewaesser, 
    CONSTRAINT pk_fp_gewaesser PRIMARY KEY (id), 
    CONSTRAINT fk_fp_gewaesser_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_gruen (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunggruen, 
    nutzungsform xp_nutzungsform, 
    CONSTRAINT pk_fp_gruen PRIMARY KEY (id), 
    CONSTRAINT fk_fp_gruen_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_landwirtschaft (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunglandwirtschaft, 
    CONSTRAINT pk_fp_landwirtschaft PRIMARY KEY (id), 
    CONSTRAINT fk_fp_landwirtschaft_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_spiel_sportanlage (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungspielsportanlage, 
    CONSTRAINT pk_fp_spiel_sportanlage PRIMARY KEY (id), 
    CONSTRAINT fk_fp_spiel_sportanlage_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE fp_zweckbestimmungstrassenverkehr AS ENUM ('Autobahn', 'Hauptverkehrsstrasse', 'Ortsdurchfahrt', 'SonstigerVerkehrswegAnlage', 'VerkehrsberuhigterBereich', 'Platz', 'Fussgaengerbereich', 'RadGehweg', 'Radweg', 'Gehweg', 'Wanderweg', 'ReitKutschweg', 'Rastanlage', 'Busbahnhof', 'UeberfuehrenderVerkehrsweg', 'UnterfuehrenderVerkehrsweg', 'Wirtschaftsweg', 'LandwirtschaftlicherVerkehr', 'RuhenderVerkehr', 'Parkplatz', 'FahrradAbstellplatz', 'P_RAnlage', 'CarSharing', 'BikeSharing', 'B_RAnlage', 'Parkhaus', 'Mischverkehrsflaeche', 'Ladestation', 'Sonstiges');

CREATE TABLE fp_strassenverkehr (
    id UUID NOT NULL, 
    zweckbestimmung fp_zweckbestimmungstrassenverkehr, 
    nutzungsform xp_nutzungsform, 
    CONSTRAINT pk_fp_strassenverkehr PRIMARY KEY (id), 
    CONSTRAINT fk_fp_strassenverkehr_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_wald (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungwald, 
    eigentumsart xp_eigentumsartwald, 
    betreten xp_waldbetretungtyp[], 
    CONSTRAINT pk_fp_wald PRIMARY KEY (id), 
    CONSTRAINT fk_fp_wald_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='1a015621a38f' WHERE alembic_version.version_num = '873e18b73036'; --- # pragma: allowlist secret;

-- Running upgrade 1a015621a38f -> 812b33dce3d1

CREATE TYPE so_rechtscharakter AS ENUM ('FestsetzungBPlan', 'DarstellungFPlan', 'InhaltLPlan', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk', 'Kennzeichnung', 'Unbekannt', 'Sonstiges');

CREATE TABLE so_objekt (
    id UUID NOT NULL, 
    rechtscharakter so_rechtscharakter NOT NULL, 
    position geometry(GEOMETRY,-1), 
    flaechenschluss BOOLEAN, 
    flussrichtung BOOLEAN, 
    nordwinkel INTEGER, 
    CONSTRAINT pk_so_objekt PRIMARY KEY (id), 
    CONSTRAINT fk_so_objekt_id_xp_objekt FOREIGN KEY(id) REFERENCES xp_objekt (id) ON DELETE CASCADE
);

CREATE INDEX idx_so_objekt_position ON so_objekt USING gist (position);

CREATE TYPE so_klassifiznachdenkmalschutzrecht AS ENUM ('DenkmalschutzEnsemble', 'DenkmalschutzEinzelanlage', 'Grabungsschutzgebiet', 'PufferzoneWeltkulturerbeEnger', 'PufferzoneWeltkulturerbeWeiter', 'ArcheologischesDenkmal', 'Bodendenkmal', 'Sonstiges');

CREATE TABLE so_denkmalschutz (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachdenkmalschutzrecht, 
    weltkulturerbe BOOLEAN, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_denkmalschutz PRIMARY KEY (id), 
    CONSTRAINT fk_so_denkmalschutz_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TYPE so_klassifiznachschienenverkehrsrecht AS ENUM ('Bahnanlage', 'DB_Bahnanlage', 'Personenbahnhof', 'Fernbahnhof', 'Gueterbahnhof', 'Bahnlinie', 'Personenbahnlinie', 'Regionalbahn', 'Kleinbahn', 'Gueterbahnlinie', 'WerksHafenbahn', 'Seilbahn', 'OEPNV', 'Strassenbahn', 'UBahn', 'SBahn', 'OEPNV_Haltestelle', 'Sonstiges');

CREATE TABLE so_schienenverkehr (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachschienenverkehrsrecht, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_schienenverkehr PRIMARY KEY (id), 
    CONSTRAINT fk_so_schienenverkehr_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TYPE so_klassifizschutzgebietwasserrecht AS ENUM ('Wasserschutzgebiet', 'QuellGrundwasserSchutzgebiet', 'OberflaechengewaesserSchutzgebiet', 'Heilquellenschutzgebiet', 'Sonstiges');

CREATE TYPE so_schutzzonenwasserrecht AS ENUM ('Zone_1', 'Zone_2', 'Zone_3', 'Zone_3a', 'Zone_3b', 'Zone_4');

CREATE TABLE so_wasserschutz (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizschutzgebietwasserrecht, 
    zone so_schutzzonenwasserrecht, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_wasserschutz PRIMARY KEY (id), 
    CONSTRAINT fk_so_wasserschutz_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

UPDATE bp_baugebiet SET sondernutzung=NULL WHERE sondernutzung='KeineSondernutzung'::xp_sondernutzungen;;

ALTER TABLE bp_baugebiet ALTER sondernutzung DROP DEFAULT, ALTER sondernutzung type xp_sondernutzungen[] using NULLIF(ARRAY[sondernutzung], '{null}'), alter sondernutzung set default '{}';;

UPDATE xp_ppo SET symbol_path = replace(symbol_path, 'BP_Naturschutz_Landschaft', 'BP_Naturschutz_Landschaftsbild_Naturhaushalt');;

UPDATE xp_ppo SET symbol_path = replace(symbol_path, 'BP_GruenFlaeche', 'BP_Landwirtschaft_Wald_und_Gruenflaechen');;

UPDATE xp_ppo SET symbol_path = replace(symbol_path, 'BP_WaldFlaeche', 'BP_Landwirtschaft_Wald_und_Gruenflaechen');;

UPDATE xp_ppo SET symbol_path = replace(symbol_path, 'BP_GemeinbedarfsFlaeche', 'BP_Gemeinbedarf_Spiel_und_Sportanlagen');;

UPDATE xp_ppo SET symbol_path = replace(symbol_path, 'BP_Erhaltungssatzung_und_Denkmalschutz', 'SO_SonstigeGebiete');;

UPDATE xp_ppo SET symbol_path = replace(symbol_path, 'BP_VerEntsorgung', 'BP_Ver_und_Entsorgung');;

UPDATE xp_ppo SET symbol_path = replace(symbol_path, 'BP_SpielSportanlagenFlaeche', 'BP_Gemeinbedarf_Spiel_und_Sportanlagen');;

UPDATE alembic_version SET version_num='812b33dce3d1' WHERE alembic_version.version_num = '1a015621a38f'; --- # pragma: allowlist secret;

-- Running upgrade 812b33dce3d1 -> 0a6f00a1f663

UPDATE xp_po SET type='xp_pto' WHERE type='xp_tpo';;

ALTER INDEX idx_xp_tpo_position RENAME TO idx_xp_pto_position;;

ALTER TABLE xp_tpo RENAME CONSTRAINT fk_xp_tpo_id_xp_po TO fk_xp_pto_id_xp_po;;

ALTER TABLE xp_tpo RENAME CONSTRAINT pk_xp_tpo TO pk_xp_pto;;

ALTER TABLE xp_tpo RENAME TO xp_pto;;

ALTER TABLE xp_ppo ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;;

ALTER TABLE xp_pto ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;;

ALTER TABLE xp_nutzungsschablone ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;;

ALTER TABLE xp_objekt ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;;

INSERT INTO xp_externe_referenz (id, datum, "referenzMimeType", art, "referenzName", beschreibung, file, "georefURL", "referenzURL") SELECT id, datum, "referenzMimeType", art, "referenzName", beschreibung, file, "georefURL", "referenzURL" FROM xp_spez_externe_referenz;

ALTER TABLE xp_spez_externe_referenz ADD CONSTRAINT xp_spez_externe_referenz_id_fkey FOREIGN KEY(id) REFERENCES xp_externe_referenz (id) ON DELETE CASCADE;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN datum;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN "referenzMimeType";

ALTER TABLE xp_spez_externe_referenz DROP COLUMN art;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN "referenzName";

ALTER TABLE xp_spez_externe_referenz DROP COLUMN beschreibung;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN file;

ALTER TABLE xp_spez_externe_referenz DROP COLUMN "georefURL";

ALTER TABLE xp_spez_externe_referenz DROP COLUMN "referenzURL";

ALTER TABLE xp_externe_referenz ADD COLUMN type VARCHAR(50);

UPDATE xp_externe_referenz SET type='xp_spez_externe_referenz' WHERE id in (SELECT id FROM xp_spez_externe_referenz);;

UPDATE xp_externe_referenz SET type='xp_externe_referenz' WHERE type IS NULL;

UPDATE alembic_version SET version_num='0a6f00a1f663' WHERE alembic_version.version_num = '812b33dce3d1'; --- # pragma: allowlist secret;

-- Running upgrade 0a6f00a1f663 -> b93ec8372df6

ALTER TABLE xp_plan ALTER COLUMN "raeumlicherGeltungsbereich" type geometry(Geometry);;

ALTER TABLE xp_plan ADD CONSTRAINT check_geometry_type CHECK (st_dimension("raeumlicherGeltungsbereich") = 2);;

ALTER TABLE xp_bereich ALTER COLUMN "geltungsbereich" type geometry(Geometry);;

ALTER TABLE xp_bereich ADD CONSTRAINT check_geometry_type CHECK (st_dimension("geltungsbereich") = 2);;

UPDATE alembic_version SET version_num='b93ec8372df6' WHERE alembic_version.version_num = '0a6f00a1f663'; --- # pragma: allowlist secret;

-- Running upgrade b93ec8372df6 -> fb27f7a59e17

ALTER TABLE xp_plan ADD COLUMN hoehenbezug VARCHAR;;

create or replace function xp_plan_sync_attr_hoehenbezug()
        returns trigger language plpgsql as $$
        begin
            UPDATE xp_plan
            SET hoehenbezug = COALESCE(NEW.hoehenbezug, hoehenbezug)
            where xp_plan.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger xp_plan_sync_attr_hoehenbezug
        after insert or update on bp_plan
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure xp_plan_sync_attr_hoehenbezug();
        
        create or replace function bp_plan_sync_attr_hoehenbezug()
        returns trigger language plpgsql as $$
        begin
            UPDATE bp_plan
            SET hoehenbezug = COALESCE(NEW.hoehenbezug, hoehenbezug)
            where bp_plan.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_plan_sync_attr_hoehenbezug
        after insert or update on xp_plan
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_plan_sync_attr_hoehenbezug();;

ALTER TABLE xp_objekt DROP COLUMN "gesetzlicheGrundlage";

DROP TYPE xp_gesetzliche_grundlage CASCADE;

ALTER TABLE xp_objekt ADD COLUMN "gesetzlicheGrundlage_id" UUID;

CREATE TABLE xp_gesetzliche_grundlage (
    id UUID NOT NULL, 
    name VARCHAR, 
    datum DATE, 
    detail VARCHAR, 
    CONSTRAINT pk_xp_gesetzliche_grundlage PRIMARY KEY (id)
);

ALTER TYPE xp_externereferenztyp ADD VALUE IF NOT EXISTS 'Schutzgebietsverordnung';;

CREATE TYPE xp_traegerschaft AS ENUM('EinrichtungBund','EinrichtungLand', 'EinrichtungKreis', 'KommunaleEinrichtung', 'ReligioeserTraeger', 'SonstTraeger');;

ALTER TABLE bp_gemeinbedarf ADD COLUMN traeger xp_traegerschaft;;

UPDATE xp_externe_referenz SET "referenzName"='Unbekannt' WHERE "referenzName" is NULL;;

UPDATE xp_externe_referenz SET "referenzURL"="referenzURL" WHERE "referenzURL" is NULL;;

ALTER TYPE xp_sondernutzungen ADD VALUE IF NOT EXISTS 'SondergebietGrosshandel';;

ALTER TYPE xp_spemassnahmentypen ADD VALUE IF NOT EXISTS 'ArtenreicherGehoelzbestand';;

ALTER TYPE xp_spemassnahmentypen ADD VALUE IF NOT EXISTS 'Moor';;

ALTER TYPE "public"."xp_spemassnahmentypen" RENAME TO "xp_spemassnahmentypen_old";

CREATE TYPE "public"."xp_spemassnahmentypen" AS ENUM('ArtenreicherGehoelzbestand', 'NaturnaherWald', 'ExtensivesGruenland', 'Feuchtgruenland', 'Obstwiese', 'NaturnaherUferbereich', 'Roehrichtzone', 'Ackerrandstreifen', 'Ackerbrache', 'Gruenlandbrache', 'Sukzessionsflaeche', 'Hochstaudenflur', 'Trockenrasen', 'Heide', 'Sonstiges');

CREATE FUNCTION new_old_not_equals(
                new_enum_val "public"."xp_spemassnahmentypen", old_enum_val "public"."xp_spemassnahmentypen_old"
            )
            RETURNS boolean AS $$
                SELECT new_enum_val::text != CASE
                    WHEN old_enum_val::text = 'ArtentreicherGehoelzbestand' THEN 'ArtenreicherGehoelzbestand'

                    ELSE old_enum_val::text
                END;
            $$ LANGUAGE SQL IMMUTABLE;

CREATE OPERATOR != (
            leftarg = "public"."xp_spemassnahmentypen",
            rightarg = "public"."xp_spemassnahmentypen_old",
            procedure = new_old_not_equals
        );

CREATE FUNCTION new_old_equals(
                new_enum_val "public"."xp_spemassnahmentypen", old_enum_val "public"."xp_spemassnahmentypen_old"
            )
            RETURNS boolean AS $$
                SELECT new_enum_val::text = CASE
                    WHEN old_enum_val::text = 'ArtentreicherGehoelzbestand' THEN 'ArtenreicherGehoelzbestand'

                    ELSE old_enum_val::text
                END;
            $$ LANGUAGE SQL IMMUTABLE;

CREATE OPERATOR = (
            leftarg = "public"."xp_spemassnahmentypen",
            rightarg = "public"."xp_spemassnahmentypen_old",
            procedure = new_old_equals
        );

ALTER TABLE "public"."xp_spe_daten" 
                ALTER COLUMN "klassifizMassnahme" TYPE "public"."xp_spemassnahmentypen" 
                USING CASE 
                WHEN "klassifizMassnahme"::text = 'ArtentreicherGehoelzbestand' THEN 'ArtenreicherGehoelzbestand'::"public"."xp_spemassnahmentypen"

                ELSE "klassifizMassnahme"::text::"public"."xp_spemassnahmentypen"
                END;

DROP OPERATOR IF EXISTS != (
                "public"."xp_spemassnahmentypen",
                "public"."xp_spemassnahmentypen_old"
            );

DROP FUNCTION new_old_not_equals(
            new_enum_val "public"."xp_spemassnahmentypen", old_enum_val "public"."xp_spemassnahmentypen_old"
        );

DROP OPERATOR IF EXISTS = (
                "public"."xp_spemassnahmentypen",
                "public"."xp_spemassnahmentypen_old"
            );

DROP FUNCTION new_old_equals(
            new_enum_val "public"."xp_spemassnahmentypen", old_enum_val "public"."xp_spemassnahmentypen_old"
        );

DROP TYPE "public"."xp_spemassnahmentypen_old";

ALTER TABLE bp_bereich ADD COLUMN verfahren bp_verfahren;;

UPDATE bp_bereich SET verfahren = bp_plan.verfahren FROM bp_plan WHERE "gehoertZuPlan_id" = bp_plan.id;;

create or replace function bp_bereich_sync_attr_verfahren()
        returns trigger language plpgsql as $$
        begin
            UPDATE bp_bereich
            SET verfahren = COALESCE(NEW.verfahren, bp_bereich.verfahren)
            where bp_bereich.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_bereich_sync_attr_verfahren
        after insert or update on bp_plan
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_bereich_sync_attr_verfahren();
        
        create or replace function bp_plan_sync_attr_verfahren()
        returns trigger language plpgsql as $$
        begin
            UPDATE bp_plan
            SET verfahren = COALESCE(NEW.verfahren, verfahren)
            where bp_plan.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_plan_sync_attr_verfahren
        after insert or update on bp_bereich
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_plan_sync_attr_verfahren();;

DROP TYPE IF EXISTS xp_rechtscharakter;
        CREATE TYPE xp_rechtscharakter AS ENUM (
        'FestsetzungBPlan',
        'NachrichtlicheUebernahme',
        'DarstellungFPlan',
        'ZielDerRaumordnung',
        'GrundsatzDerRaumordnung',
        'NachrichtlicheUebernahmeZiel',
        'NachrichtlicheUebernahmeGrundsatz',
        'NurInformationsgehaltRPlan',
        'TextlichesZielRaumordnung',
        'ZielUndGrundsatzRaumordnung',
        'VorschlagRaumordnung',
        'FestsetzungImLP',
        'GeplanteFestsetzungImLP',
        'DarstellungKennzeichnungImLP',
        'LandschaftsplanungsInhaltZurBeruecksichtigung',
        'Hinweis',
        'Kennzeichnung',
        'Vermerk',
        'Unbekannt',
        'Sonstiges');
    
        ALTER TABLE xp_objekt ADD COLUMN rechtscharakter xp_rechtscharakter;
        -- bp_objekt
        UPDATE xp_objekt SET rechtscharakter = (
                CASE
                    WHEN bp_objekt.rechtscharakter = 'Festsetzung'::bp_rechtscharakter
                        THEN 'FestsetzungBPlan'::xp_rechtscharakter
                    ELSE bp_objekt.rechtscharakter::text::xp_rechtscharakter
                END)
        FROM bp_objekt WHERE xp_objekt.id = bp_objekt.id;
        
        create or replace function xp_objekt_sync_attr_rechtscharakter()
        returns trigger language plpgsql as $$
        begin
            UPDATE xp_objekt
            SET rechtscharakter = (
                CASE
                    WHEN NEW.rechtscharakter = 'Festsetzung'::bp_rechtscharakter
                        THEN 'FestsetzungBPlan'::xp_rechtscharakter
                    ELSE COALESCE(NEW.rechtscharakter::text::xp_rechtscharakter, rechtscharakter)
                END)
            where xp_objekt.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger xp_objekt_sync_attr_rechtscharakter
        after insert or update on bp_objekt
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure xp_objekt_sync_attr_rechtscharakter();
        
        create or replace function bp_objekt_sync_attr_rechtscharakter()
        returns trigger language plpgsql as $$
        begin
            IF new.type != 'bp_objekt'
                THEN RETURN NEW;
            END IF;
            UPDATE bp_objekt
            SET rechtscharakter = (
                CASE
                    WHEN NEW.rechtscharakter = 'FestsetzungBPlan'::xp_rechtscharakter
                        THEN 'Festsetzung'::bp_rechtscharakter
                    WHEN NEW.rechtscharakter in ('NachrichtlicheUebernahme'::xp_rechtscharakter,
                                                'Hinweis'::xp_rechtscharakter,
                                                'Vermerk'::xp_rechtscharakter,
                                                'Kennzeichnung'::xp_rechtscharakter,
                                                'Unbekannt'::xp_rechtscharakter)
                        THEN NEW.rechtscharakter::text::bp_rechtscharakter
                    ELSE rechtscharakter
                END)
            where bp_objekt.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_objekt_sync_attr_rechtscharakter
        after insert or update on xp_objekt
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_objekt_sync_attr_rechtscharakter();
        
        
        -- fp_objekt
        UPDATE xp_objekt SET rechtscharakter = (
                CASE
                    WHEN fp_objekt.rechtscharakter = 'Darstellung'::fp_rechtscharakter
                        THEN 'DarstellungFPlan'::xp_rechtscharakter
                    ELSE fp_objekt.rechtscharakter::text::xp_rechtscharakter
                END)
        FROM fp_objekt WHERE xp_objekt.id = fp_objekt.id;
        
        create or replace function xp_objekt_sync_attr_rechtscharakter_from_fp()
        returns trigger language plpgsql as $$
        begin
            UPDATE xp_objekt
            SET rechtscharakter = (
                CASE
                    WHEN NEW.rechtscharakter = 'Darstellung'::fp_rechtscharakter
                        THEN 'DarstellungFPlan'::xp_rechtscharakter
                    ELSE COALESCE(NEW.rechtscharakter::text::xp_rechtscharakter, rechtscharakter)
                END)
            where xp_objekt.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger xp_objekt_sync_attr_rechtscharakter_from_fp
        after insert or update on fp_objekt
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure xp_objekt_sync_attr_rechtscharakter_from_fp();
        
        create or replace function fp_objekt_sync_attr_rechtscharakter()
        returns trigger language plpgsql as $$
        begin
            IF new.type != 'fp_objekt'
                THEN RETURN NEW;
            END IF;
            UPDATE fp_objekt
            SET rechtscharakter = (
                CASE
                    WHEN NEW.rechtscharakter = 'DarstellungFPlan'::xp_rechtscharakter
                        THEN 'Darstellung'::fp_rechtscharakter
                    WHEN NEW.rechtscharakter in ('NachrichtlicheUebernahme'::xp_rechtscharakter,
                                                'Hinweis'::xp_rechtscharakter,
                                                'Vermerk'::xp_rechtscharakter,
                                                'Kennzeichnung'::xp_rechtscharakter,
                                                'Unbekannt'::xp_rechtscharakter)
                        THEN NEW.rechtscharakter::text::fp_rechtscharakter
                    ELSE rechtscharakter
                END)
            where fp_objekt.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger fp_objekt_sync_attr_rechtscharakter
        after insert or update on xp_objekt
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_objekt_sync_attr_rechtscharakter();
        
        
        -- so_objekt
        UPDATE xp_objekt SET rechtscharakter = (
                CASE
                    WHEN so_objekt.rechtscharakter = 'InhaltLPlan'::so_rechtscharakter
                        THEN 'FestsetzungImLP'::xp_rechtscharakter
                    ELSE so_objekt.rechtscharakter::text::xp_rechtscharakter
                END)
        FROM so_objekt WHERE xp_objekt.id = so_objekt.id;
        
        create or replace function xp_objekt_sync_attr_rechtscharakter_from_so()
        returns trigger language plpgsql as $$
        begin
            UPDATE xp_objekt
            SET rechtscharakter = (
                CASE
                    WHEN NEW.rechtscharakter = 'InhaltLPlan'::so_rechtscharakter
                        THEN 'FestsetzungImLP'::xp_rechtscharakter
                    ELSE COALESCE(NEW.rechtscharakter::text::xp_rechtscharakter, rechtscharakter)
                END)
            where xp_objekt.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger xp_objekt_sync_attr_rechtscharakter_from_so
        after insert or update on so_objekt
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure xp_objekt_sync_attr_rechtscharakter_from_so();
        
        create or replace function so_objekt_sync_attr_rechtscharakter()
        returns trigger language plpgsql as $$
        begin
            IF new.type != 'so_objekt'
                THEN RETURN NEW;
            END IF;
            UPDATE so_objekt
            SET rechtscharakter = (
                CASE
                    WHEN NEW.rechtscharakter = 'FestsetzungImLP'::xp_rechtscharakter
                        THEN 'InhaltLPlan'::so_rechtscharakter
                    WHEN NEW.rechtscharakter in ('NachrichtlicheUebernahme'::xp_rechtscharakter,
                                                'Hinweis'::xp_rechtscharakter,
                                                'Vermerk'::xp_rechtscharakter,
                                                'Kennzeichnung'::xp_rechtscharakter,
                                                'Unbekannt'::xp_rechtscharakter,
                                                'Sonstiges'::xp_rechtscharakter)
                        THEN NEW.rechtscharakter::text::so_rechtscharakter
                    ELSE rechtscharakter
                END)
            where so_objekt.id = new.id;
            RETURN NEW;
        end $$;
        
        create constraint trigger so_objekt_sync_attr_rechtscharakter
        after insert or update on xp_objekt
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure so_objekt_sync_attr_rechtscharakter();;

ALTER TYPE bp_planart ADD VALUE IF NOT EXISTS 'BebauungsplanZurWohnraumversorgung';;

ALTER TYPE xp_zweckbestimmunggruen ADD VALUE IF NOT EXISTS 'Naturerfahrungsraum';;

ALTER TYPE xp_besondereartderbaulnutzung ADD VALUE IF NOT EXISTS 'DoerflichesWohngebiet';;

CREATE TABLE bp_zweckbestimmung_gruen (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmunggruen,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            gruenflaeche_id UUID,
            FOREIGN KEY(gruenflaeche_id) REFERENCES bp_gruenflaeche (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM bp_gruenflaeche g
        )
        INSERT INTO bp_zweckbestimmung_gruen (id, allgemein, gruenflaeche_id)
        SELECT * FROM upd;
        
        create or replace function bp_gruenflaeche_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE bp_zweckbestimmung_gruen
                SET allgemein = NEW.zweckbestimmung
                WHERE gruenflaeche_id = NEW.id;
            ELSE
                UPDATE bp_gruenflaeche SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.gruenflaeche_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_gruenflaeche_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on bp_gruenflaeche
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_gruenflaeche_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger bp_gruenflaeche_sync_attr_zweckbestimmung
        after insert or update of allgemein on bp_zweckbestimmung_gruen
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_gruenflaeche_sync_attr_zweckbestimmung('gruenflaeche_id');;

CREATE TABLE bp_komplexe_sondernutzung (
            id UUID NOT NULL,
            allgemein xp_sondernutzungen,
            "nutzungText" VARCHAR,
            aufschrift VARCHAR,
            baugebiet_id UUID,
            FOREIGN KEY(baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        INSERT INTO bp_komplexe_sondernutzung (id, baugebiet_id, allgemein)
        SELECT uuid_generate_v4(), bp_baugebiet.id, t.sondernutzung_unnested
        FROM bp_baugebiet
        CROSS JOIN unnest(bp_baugebiet.sondernutzung) as t(sondernutzung_unnested);
        
        create or replace function bp_baugebiet_sync_attr_sondernutzung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'sondernutzung' THEN
                DELETE FROM bp_komplexe_sondernutzung WHERE baugebiet_id = NEW.id;
        
                INSERT INTO bp_komplexe_sondernutzung (id, baugebiet_id, allgemein)
                SELECT uuid_generate_v4(), bp_baugebiet.id, t.sondernutzung_unnested
                FROM bp_baugebiet
                CROSS JOIN unnest(bp_baugebiet.sondernutzung) as t(sondernutzung_unnested);
            ELSE
                -- make sure no duplicates are inserted by selecting distinct from unnested array
                UPDATE bp_baugebiet SET sondernutzung = ARRAY(SELECT DISTINCT UNNEST(sondernutzung || ARRAY[NEW.allgemein]))
                WHERE id = NEW.baugebiet_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_baugebiet_sync_attr_sondernutzung
        after insert or update of sondernutzung on bp_baugebiet
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_baugebiet_sync_attr_sondernutzung('sondernutzung');
        
        create constraint trigger bp_baugebiet_sync_attr_sondernutzung
        after insert or update of allgemein on bp_komplexe_sondernutzung
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_baugebiet_sync_attr_sondernutzung('baugebiet_id');
        
        create or replace function bp_baugebiet_sync_attr_sondernutzung_on_delete()
        returns trigger language plpgsql as $$
        begin
            -- make sure no duplicates are inserted by selecting distinct from unnested array
            UPDATE bp_baugebiet SET sondernutzung = array_remove(sondernutzung, OLD.allgemein)
            WHERE id = OLD.baugebiet_id;
            RETURN NULL;
        end $$;
        
        create constraint trigger bp_baugebiet_sync_attr_sondernutzung_on_delete
        after delete on bp_komplexe_sondernutzung
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_baugebiet_sync_attr_sondernutzung_on_delete();;

CREATE TYPE so_zweckbestimmungstrassenverkehr AS ENUM (
            'AutobahnUndAehnlich',
            'Hauptverkehrsstrasse',
            'SonstigerVerkehrswegAnlage',
            'VerkehrsberuhigterBereich',
            'Platz',
            'Fussgaengerbereich',
            'RadGehweg',
            'Radweg',
            'Gehweg',
            'Wanderweg',
            'ReitKutschweg',
            'Rastanlage',
            'Busbahnhof',
            'UeberfuehrenderVerkehrsweg',
            'UnterfuehrenderVerkehrsweg',
            'Wirtschaftsweg',
            'LandwirtschaftlicherVerkehr',
            'Anschlussflaeche',
            'Verkehrsgruen',
            'RuhenderVerkehr',
            'Parkplatz',
            'FahrradAbstellplatz',
            'P_RAnlage',
            'B_RAnlage',
            'Parkhaus',
            'CarSharing',
            'BikeSharing',
            'Mischverkehrsflaeche',
            'Ladestation',
            'Sonstiges');
        
        CREATE TYPE so_strasseneinteilung AS ENUM (
            'Bundesautobahn',
            'Bundesstrasse',
            'LandesStaatsstrasse',
            'Kreisstrasse',
            'Gemeindestrasse',
            'SonstOeffentlStrasse');
        
        
        CREATE TABLE so_strassenverkehr (
            id UUID NOT NULL,
            "MaxZahlWohnungen" INTEGER,
            "MinGRWohneinheit" FLOAT,
            "Fmin" FLOAT,
            "Fmax" FLOAT,
            "Bmin" FLOAT,
            "Bmax" FLOAT,
            "Tmin" FLOAT,
            "Tmax" FLOAT,
            "GFZmin" FLOAT,
            "GFZmax" FLOAT,
            "GFZ" FLOAT,
            "GFZ_Ausn" FLOAT,
            "GFmin" FLOAT,
            "GFmax" FLOAT,
            "GF" FLOAT,
            "GF_Ausn" FLOAT,
            "BMZ" FLOAT,
            "BMZ_Ausn" FLOAT,
            "BM" FLOAT,
            "BM_Ausn" FLOAT,
            "GRZmin" FLOAT,
            "GRZmax" FLOAT,
            "GRZ" FLOAT,
            "GRZ_Ausn" FLOAT,
            "GRmin" FLOAT,
            "GRmax" FLOAT,
            "GR" FLOAT,
            "GR_Ausn" FLOAT,
            "Zmin" INTEGER,
            "Zmax" INTEGER,
            "Zzwingend" INTEGER,
            "Z" INTEGER,
            "Z_Ausn" INTEGER,
            "Z_Staffel" INTEGER,
            "Z_Dach" INTEGER,
            "ZUmin" INTEGER,
            "ZUmax" INTEGER,
            "ZUzwingend" INTEGER,
            "ZU" INTEGER,
            "ZU_Ausn" INTEGER,
        
            einteilung so_strasseneinteilung,
            name VARCHAR,
            nummer VARCHAR,
            "istOrtsdurchfahrt" BOOLEAN,
            nutzungsform xp_nutzungsform not null,
            "zugunstenVon" VARCHAR,
            "hatDarstellungMitBesondZweckbest" BOOLEAN,
        
            PRIMARY KEY (id),
            FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
        );
        
        CREATE TABLE so_zweckbestimmung_strassenverkehr (
            id UUID NOT NULL,
            allgemein so_zweckbestimmungstrassenverkehr,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            strassenverkehr_id UUID,
            FOREIGN KEY(strassenverkehr_id) REFERENCES so_strassenverkehr (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );;

ALTER TABLE so_objekt ALTER COLUMN nordwinkel TYPE FLOAT USING nordwinkel::float;;

ALTER TABLE fp_gemeinbedarf ALTER zweckbestimmung DROP DEFAULT, ALTER zweckbestimmung type xp_zweckbestimmunggemeinbedarf[] using NULLIF(ARRAY[zweckbestimmung], '{null}'), alter zweckbestimmung set default '{}';;

ALTER TYPE bp_rechtsstand ADD VALUE IF NOT EXISTS 'Entwurfsbeschluss';
        ALTER TYPE bp_rechtsstand ADD VALUE IF NOT EXISTS 'TeilweiseAufgehoben';
        ALTER TYPE bp_rechtsstand ADD VALUE IF NOT EXISTS 'TeilweiseAusserKraft';
        
        ALTER TYPE rp_rechtsstand ADD VALUE IF NOT EXISTS 'TeilweiseAusserKraft';
        ALTER TYPE fp_rechtsstand ADD VALUE IF NOT EXISTS 'Entwurfsbeschluss';;

CREATE TABLE bp_zweckbestimmung_sport (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmungspielsportanlage,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            spiel_sportanlage_id UUID,
            FOREIGN KEY(spiel_sportanlage_id) REFERENCES bp_spiel_sportanlage (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM bp_spiel_sportanlage g
        )
        INSERT INTO bp_zweckbestimmung_sport (id, allgemein, spiel_sportanlage_id)
        SELECT * FROM upd;
        
        create or replace function bp_spiel_sportanlage_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE bp_zweckbestimmung_sport
                SET allgemein = NEW.zweckbestimmung
                WHERE spiel_sportanlage_id = NEW.id;
            ELSE
                UPDATE bp_spiel_sportanlage SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.spiel_sportanlage_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_spiel_sportanlage_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on bp_spiel_sportanlage
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_spiel_sportanlage_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger bp_spiel_sportanlage_sync_attr_zweckbestimmung
        after insert or update of allgemein on bp_zweckbestimmung_sport
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_spiel_sportanlage_sync_attr_zweckbestimmung('spiel_sportanlage_id');;

CREATE TABLE bp_zweckbestimmung_gemeinbedarf (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmunggemeinbedarf,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            gemeinbedarf_id UUID,
            FOREIGN KEY(gemeinbedarf_id) REFERENCES bp_gemeinbedarf (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM bp_gemeinbedarf g
        )
        INSERT INTO bp_zweckbestimmung_gemeinbedarf (id, allgemein, gemeinbedarf_id)
        SELECT * FROM upd;
        
        create or replace function bp_gemeinbedarf_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE bp_zweckbestimmung_gemeinbedarf
                SET allgemein = NEW.zweckbestimmung
                WHERE gemeinbedarf_id = NEW.id;
            ELSE
                UPDATE bp_gemeinbedarf SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.gemeinbedarf_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_gemeinbedarf_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on bp_gemeinbedarf
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_gemeinbedarf_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger bp_gemeinbedarf_sync_attr_zweckbestimmung
        after insert or update of allgemein on bp_zweckbestimmung_gemeinbedarf
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_gemeinbedarf_sync_attr_zweckbestimmung('gemeinbedarf_id');;

CREATE TABLE bp_zweckbestimmung_landwirtschaft (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmunglandwirtschaft,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            landwirtschaft_id UUID,
            FOREIGN KEY(landwirtschaft_id) REFERENCES bp_landwirtschaft (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM bp_landwirtschaft g
        )
        INSERT INTO bp_zweckbestimmung_landwirtschaft (id, allgemein, landwirtschaft_id)
        SELECT * FROM upd;
        
        create or replace function bp_landwirtschaft_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE bp_zweckbestimmung_landwirtschaft
                SET allgemein = NEW.zweckbestimmung
                WHERE landwirtschaft_id = NEW.id;
            ELSE
                UPDATE bp_landwirtschaft SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.landwirtschaft_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_landwirtschaft_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on bp_landwirtschaft
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_landwirtschaft_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger bp_landwirtschaft_sync_attr_zweckbestimmung
        after insert or update of allgemein on bp_zweckbestimmung_landwirtschaft
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_landwirtschaft_sync_attr_zweckbestimmung('landwirtschaft_id');;

CREATE TABLE bp_zweckbestimmung_wald (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmungwald,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            waldflaeche_id UUID,
            FOREIGN KEY(waldflaeche_id) REFERENCES bp_wald (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM bp_wald g
        )
        INSERT INTO bp_zweckbestimmung_wald (id, allgemein, waldflaeche_id)
        SELECT * FROM upd;
        
        create or replace function bp_wald_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE bp_zweckbestimmung_wald
                SET allgemein = NEW.zweckbestimmung
                WHERE waldflaeche_id = NEW.id;
            ELSE
                UPDATE bp_wald SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.waldflaeche_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_wald_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on bp_wald
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_wald_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger bp_wald_sync_attr_zweckbestimmung
        after insert or update of allgemein on bp_zweckbestimmung_wald
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_wald_sync_attr_zweckbestimmung('waldflaeche_id');;

ALTER TABLE bp_pflanzung ADD COLUMN "pflanzenArt" VARCHAR;

CREATE TABLE bp_zweckbestimmung_versorgung (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmungverentsorgung,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            versorgung_id UUID,
            FOREIGN KEY(versorgung_id) REFERENCES bp_versorgung (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM bp_versorgung g
        )
        INSERT INTO bp_zweckbestimmung_versorgung (id, allgemein, versorgung_id)
        SELECT * FROM upd;
        
        create or replace function bp_versorgung_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE bp_zweckbestimmung_versorgung
                SET allgemein = NEW.zweckbestimmung
                WHERE versorgung_id = NEW.id;
            ELSE
                UPDATE bp_versorgung SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.versorgung_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger bp_versorgung_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on bp_versorgung
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_versorgung_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger bp_versorgung_sync_attr_zweckbestimmung
        after insert or update of allgemein on bp_zweckbestimmung_versorgung
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure bp_versorgung_sync_attr_zweckbestimmung('versorgung_id');;

CREATE TYPE bp_verlaengerungveraenderungssperre AS ENUM ('Keine', 'ErsteVerlaengerung', 'ZweiteVerlaengerung');

        CREATE TABLE bp_veraenderungssperre_daten (
            id UUID NOT NULL,
            "startDatum" DATE not null,
            "endDatum" DATE not null,
            verlaengerung bp_verlaengerungveraenderungssperre,
            "beschlussDatum" DATE,
        
            plan_id UUID,
            FOREIGN KEY(plan_id) REFERENCES bp_plan (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        ALTER TABLE xp_externe_referenz ADD COLUMN veraenderungssperre_id UUID REFERENCES bp_veraenderungssperre_daten(id);
            
        WITH upd AS (
           SELECT uuid_generate_v4(), "veraenderungssperreDatum",
                  "veraenderungssperreEndDatum", "verlaengerungVeraenderungssperre"::text::bp_verlaengerungveraenderungssperre AS verl,
                  "veraenderungssperreBeschlussDatum", id FROM bp_plan p
        )
        INSERT INTO bp_veraenderungssperre_daten (id, "startDatum", "endDatum", verlaengerung, "beschlussDatum", plan_id)
        SELECT * FROM upd
        WHERE upd."veraenderungssperreEndDatum" is not NULL AND "veraenderungssperreDatum" is not NULL AND upd.verl is not NULL;;

CREATE TYPE so_klassifizgewaesser AS ENUM (
            'Gewaesser',
            'Fliessgewaesser',
            'Gewaesser1Ordnung',
            'Gewaesser2Ordnung',
            'Gewaesser3Ordnung',
            'StehendesGewaesser',
            'Hafen',
            'Sportboothafen',
            'Wasserstrasse',
            'Kanal',
            'Sonstiges');
        
        CREATE TABLE so_gewaesser (
            id UUID NOT NULL,
            name VARCHAR,
            nummer VARCHAR,
        
            PRIMARY KEY (id),
            FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
        );
        
        CREATE TABLE so_festlegung_gewaesser (
            id UUID NOT NULL,
            allgemein so_klassifizgewaesser,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            gewaesser_id UUID,
            FOREIGN KEY(gewaesser_id) REFERENCES so_gewaesser (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );;

CREATE TYPE so_klassifizwasserwirtschaft AS ENUM (
            'HochwasserRueckhaltebecken',
            'Ueberschwemmgebiet',
            'Versickerungsflaeche',
            'Entwaesserungsgraben',
            'Deich',
            'RegenRueckhaltebecken',
            'Sonstiges');
        
        CREATE TABLE so_wasserwirtschaft (
            id UUID NOT NULL,
        
            "artDerFestlegung" so_klassifizwasserwirtschaft,
        
            PRIMARY KEY (id),
            FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
        );;

ALTER TABLE fp_plan ADD COLUMN "versionBauNVO_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
        ALTER TABLE fp_plan ADD COLUMN "versionBauGB_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
        ALTER TABLE fp_plan ADD COLUMN "versionSonstRechtsgrundlage_id" uuid REFERENCES xp_gesetzliche_grundlage(id);;

ALTER TABLE fp_baugebiet ADD COLUMN "GFZdurchschnittlich" FLOAT;
        ALTER TABLE fp_baugebiet ADD COLUMN "abweichungBauNVO" xp_abweichungbaunvotypen;;

CREATE TABLE fp_komplexe_sondernutzung (
            id UUID NOT NULL,
            allgemein xp_sondernutzungen,
            "nutzungText" VARCHAR,
            aufschrift VARCHAR,
            baugebiet_id UUID,
            FOREIGN KEY(baugebiet_id) REFERENCES fp_baugebiet (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        INSERT INTO fp_komplexe_sondernutzung (id, baugebiet_id, allgemein)
        SELECT uuid_generate_v4(), fp_baugebiet.id, t.sondernutzung_unnested
        FROM fp_baugebiet
        CROSS JOIN unnest(fp_baugebiet."sonderNutzung") as t(sondernutzung_unnested);
        
        create or replace function fp_baugebiet_sync_attr_sondernutzung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'sondernutzung' THEN
                DELETE FROM fp_komplexe_sondernutzung WHERE baugebiet_id = NEW.id;
        
                INSERT INTO fp_komplexe_sondernutzung (id, baugebiet_id, allgemein)
                SELECT uuid_generate_v4(), fp_baugebiet.id, t.sondernutzung_unnested
                FROM fp_baugebiet
                CROSS JOIN unnest(fp_baugebiet."sonderNutzung") as t(sondernutzung_unnested);
            ELSE
                -- make sure no duplicates are inserted by selecting distinct from unnested array
                UPDATE fp_baugebiet SET "sonderNutzung" = ARRAY(SELECT DISTINCT UNNEST("sonderNutzung" || ARRAY[NEW.allgemein]))
                WHERE id = NEW.baugebiet_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger fp_baugebiet_sync_attr_sondernutzung
        after insert or update of "sonderNutzung" on fp_baugebiet
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_baugebiet_sync_attr_sondernutzung('sondernutzung');
        
        create constraint trigger fp_baugebiet_sync_attr_sondernutzung
        after insert or update of allgemein on fp_komplexe_sondernutzung
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_baugebiet_sync_attr_sondernutzung('baugebiet_id');
        
        create or replace function fp_baugebiet_sync_attr_sondernutzung_on_delete()
        returns trigger language plpgsql as $$
        begin
            -- make sure no duplicates are inserted by selecting distinct from unnested array
            UPDATE fp_baugebiet SET "sonderNutzung" = array_remove("sonderNutzung", OLD.allgemein)
            WHERE id = OLD.baugebiet_id;
            RETURN NULL;
        end $$;
        
        create constraint trigger fp_baugebiet_sync_attr_sondernutzung_on_delete
        after delete on fp_komplexe_sondernutzung
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_baugebiet_sync_attr_sondernutzung_on_delete();;

CREATE TABLE fp_zweckbestimmung_gemeinbedarf (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmunggemeinbedarf,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            gemeinbedarf_id UUID,
            FOREIGN KEY(gemeinbedarf_id) REFERENCES fp_gemeinbedarf (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        ALTER TABLE fp_gemeinbedarf ADD COLUMN traeger xp_traegerschaft;
        ALTER TABLE fp_gemeinbedarf ADD COLUMN "zugunstenVon" VARCHAR;
        
        INSERT INTO fp_zweckbestimmung_gemeinbedarf (id, gemeinbedarf_id, allgemein)
        SELECT uuid_generate_v4(), fp_gemeinbedarf.id, t.zweckbestimmung_unnested
        FROM fp_gemeinbedarf
        CROSS JOIN unnest(fp_gemeinbedarf."zweckbestimmung") as t(zweckbestimmung_unnested);
        
        create or replace function fp_gemeinbedarf_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmung' THEN
                DELETE FROM fp_zweckbestimmung_gemeinbedarf WHERE gemeinbedarf_id = NEW.id;
        
                INSERT INTO fp_zweckbestimmung_gemeinbedarf (id, gemeinbedarf_id, allgemein)
                SELECT uuid_generate_v4(), fp_gemeinbedarf.id, t.zweckbestimmung_unnested
                FROM fp_gemeinbedarf
                CROSS JOIN unnest(fp_gemeinbedarf."zweckbestimmung") as t(zweckbestimmung_unnested);
            ELSE
                UPDATE fp_gemeinbedarf SET zweckbestimmung = array_remove(zweckbestimmung, OLD.allgemein) WHERE id = OLD.gemeinbedarf_id;
        
                -- make sure no duplicates are inserted by selecting distinct from unnested array
                UPDATE fp_gemeinbedarf SET zweckbestimmung = ARRAY(SELECT DISTINCT UNNEST(zweckbestimmung || ARRAY[NEW.allgemein]))
                WHERE id = NEW.gemeinbedarf_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger fp_gemeinbedarf_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on fp_gemeinbedarf
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_gemeinbedarf_sync_attr_zweckbestimmung('zweckbestimmung');
        
        create constraint trigger fp_gemeinbedarf_sync_attr_zweckbestimmung
        after insert or update of allgemein on fp_zweckbestimmung_gemeinbedarf
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_gemeinbedarf_sync_attr_zweckbestimmung('gemeinbedarf_id');
        
        create or replace function fp_gemeinbedarf_sync_attr_zweckbestimmung_on_delete()
        returns trigger language plpgsql as $$
        begin
            UPDATE fp_gemeinbedarf SET zweckbestimmung = array_remove(zweckbestimmung, OLD.allgemein)
            WHERE id = OLD.gemeinbedarf_id;
            RETURN NULL;
        end $$;
        
        create constraint trigger fp_gemeinbedarf_sync_attr_zweckbestimmung_on_delete
        after delete on fp_zweckbestimmung_gemeinbedarf
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_gemeinbedarf_sync_attr_zweckbestimmung_on_delete();;

CREATE TABLE fp_zweckbestimmung_sport (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmungspielsportanlage,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            sportanlage_id UUID,
            FOREIGN KEY(sportanlage_id) REFERENCES fp_spiel_sportanlage (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        ALTER TABLE fp_spiel_sportanlage ADD COLUMN "zugunstenVon" VARCHAR;
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM fp_spiel_sportanlage g
        )
        INSERT INTO fp_zweckbestimmung_sport (id, allgemein, sportanlage_id)
        SELECT * FROM upd;
        
        create or replace function fp_sport_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE fp_zweckbestimmung_sport
                SET allgemein = NEW.zweckbestimmung
                WHERE sportanlage_id = NEW.id;
            ELSE
                UPDATE fp_spiel_sportanlage SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.sportanlage_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger fp_sport_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on fp_spiel_sportanlage
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_sport_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger fp_sport_sync_attr_zweckbestimmung
        after insert or update of allgemein on fp_zweckbestimmung_sport
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_sport_sync_attr_zweckbestimmung('sportanlage_id');;

CREATE TABLE fp_zweckbestimmung_gruen (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmunggruen,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            gruenflaeche_id UUID,
            FOREIGN KEY(gruenflaeche_id) REFERENCES fp_gruen (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        ALTER TABLE fp_gruen ADD COLUMN "zugunstenVon" VARCHAR;
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM fp_gruen g
        )
        INSERT INTO fp_zweckbestimmung_gruen (id, allgemein, gruenflaeche_id)
        SELECT * FROM upd;
        
        create or replace function fp_gruen_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE fp_zweckbestimmung_gruen
                SET allgemein = NEW.zweckbestimmung
                WHERE gruenflaeche_id = NEW.id;
            ELSE
                UPDATE fp_gruen SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.gruenflaeche_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger fp_gruen_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on fp_gruen
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_gruen_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger fp_gruen_sync_attr_zweckbestimmung
        after insert or update of allgemein on fp_zweckbestimmung_gruen
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_gruen_sync_attr_zweckbestimmung('gruenflaeche_id');;

CREATE TABLE fp_zweckbestimmung_landwirtschaft (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmunglandwirtschaft,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            landwirtschaft_id UUID,
            FOREIGN KEY(landwirtschaft_id) REFERENCES fp_landwirtschaft (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM fp_landwirtschaft g
        )
        INSERT INTO fp_zweckbestimmung_landwirtschaft (id, allgemein, landwirtschaft_id)
        SELECT * FROM upd;
        
        create or replace function fp_landwirtschaft_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE fp_zweckbestimmung_landwirtschaft
                SET allgemein = NEW.zweckbestimmung
                WHERE landwirtschaft_id = NEW.id;
            ELSE
                UPDATE fp_landwirtschaft SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.landwirtschaft_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger fp_landwirtschaft_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on fp_landwirtschaft
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_landwirtschaft_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger fp_landwirtschaft_sync_attr_zweckbestimmung
        after insert or update of allgemein on fp_zweckbestimmung_landwirtschaft
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_landwirtschaft_sync_attr_zweckbestimmung('landwirtschaft_id');;

CREATE TABLE fp_zweckbestimmung_wald (
            id UUID NOT NULL,
            allgemein xp_zweckbestimmungwald,
            "textlicheErgaenzung" VARCHAR,
            aufschrift VARCHAR,
            waldflaeche_id UUID,
            FOREIGN KEY(waldflaeche_id) REFERENCES fp_wald (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        WITH upd AS (
           SELECT uuid_generate_v4(), zweckbestimmung, id FROM fp_wald g
        )
        INSERT INTO fp_zweckbestimmung_wald (id, allgemein, waldflaeche_id)
        SELECT * FROM upd;
        
        create or replace function fp_wald_sync_attr_zweckbestimmung()
        returns trigger language plpgsql as $$
        begin
            IF TG_ARGV[0]  = 'zweckbestimmmung' THEN
                UPDATE fp_zweckbestimmung_wald
                SET allgemein = NEW.zweckbestimmung
                WHERE waldflaeche_id = NEW.id;
            ELSE
                UPDATE fp_wald SET zweckbestimmung = NEW.allgemein
                WHERE id = NEW.waldflaeche_id;
            END IF;
            RETURN NEW;
        end $$;
        
        create constraint trigger fp_wald_sync_attr_zweckbestimmung
        after insert or update of zweckbestimmung on fp_wald
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_wald_sync_attr_zweckbestimmung('zweckbestimmmung');
        
        create constraint trigger fp_wald_sync_attr_zweckbestimmung
        after insert or update of allgemein on fp_zweckbestimmung_wald
        DEFERRABLE
        for each row when (pg_trigger_depth() = 0)
        execute procedure fp_wald_sync_attr_zweckbestimmung('waldflaeche_id');;

ALTER TABLE xp_plan_gemeinde ADD COLUMN lp_plan_id uuid REFERENCES lp_plan(id) ON DELETE CASCADE;
        ALTER TABLE lp_plan ADD COLUMN plangeber_id uuid REFERENCES xp_plangeber(id);
        
        ALTER TABLE lp_plan ADD COLUMN "auslegungsStartDatum" DATE[];
        ALTER TABLE lp_plan ADD COLUMN "auslegungsEndDatum" DATE[];
        ALTER TABLE lp_plan ADD COLUMN "tOeBbeteiligungsStartDatum" DATE[];
        ALTER TABLE lp_plan ADD COLUMN "tOeBbeteiligungsEndDatum" DATE[];
        ALTER TABLE lp_plan ADD COLUMN "oeffentlichkeitsBetStartDatum" DATE[];
        ALTER TABLE lp_plan ADD COLUMN "oeffentlichkeitsBetEndDatum" DATE[];
        
        ALTER TABLE lp_plan ADD COLUMN "veroeffentlichungsDatum" DATE;
        
        ALTER TABLE lp_plan ADD COLUMN "sonstVerfahrensText" VARCHAR;
        ALTER TABLE lp_plan ADD COLUMN "startBedingungen" VARCHAR;
        ALTER TABLE lp_plan ADD COLUMN "endeBedingungen" VARCHAR;;

UPDATE alembic_version SET version_num='fb27f7a59e17' WHERE alembic_version.version_num = 'b93ec8372df6'; --- # pragma: allowlist secret;

-- Running upgrade fb27f7a59e17 -> 8cdbef1a55d6

ALTER TABLE bp_plan ADD COLUMN "versionBauNVO_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
            ALTER TABLE bp_plan ADD COLUMN "versionBauGB_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
            ALTER TABLE bp_plan ADD COLUMN "versionSonstRechtsgrundlage_id" uuid REFERENCES xp_gesetzliche_grundlage(id);;

ALTER TYPE xp_zweckbestimmunggemeinbedarf ADD VALUE IF NOT EXISTS 'SonstigeInfrastruktur';

ALTER TYPE xp_zweckbestimmunggemeinbedarf ADD VALUE IF NOT EXISTS 'SonstigeSicherheitOrdnung';

UPDATE alembic_version SET version_num='8cdbef1a55d6' WHERE alembic_version.version_num = 'fb27f7a59e17'; --- # pragma: allowlist secret;

-- Running upgrade 8cdbef1a55d6 -> ce95b86bc010

CREATE TABLE codelist (
            id UUID NOT NULL,
            name VARCHAR,
            uri VARCHAR,
            description VARCHAR,
        
            PRIMARY KEY (id)
        );
        
        CREATE TABLE codelist_values (
            id UUID NOT NULL,
            value VARCHAR,
            uri VARCHAR,
            definition VARCHAR,
            type VARCHAR,
        
            "codelist_id" UUID,
            FOREIGN KEY("codelist_id") REFERENCES codelist (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );
        
        ALTER TABLE bp_plan ADD COLUMN "sonstPlanArt_id" uuid REFERENCES codelist_values(id);
        ALTER TABLE bp_plan ADD COLUMN "status_id" uuid REFERENCES codelist_values(id);
        ALTER TABLE bp_baugebiet ADD COLUMN "detaillierteArtDerBaulNutzung_id" uuid REFERENCES codelist_values(id);
        ALTER TABLE bp_dachgestaltung ADD COLUMN "detaillierteDachform_id" uuid REFERENCES codelist_values(id);
        
        ALTER TABLE fp_plan ADD COLUMN "sonstPlanArt_id" uuid REFERENCES codelist_values(id);
        ALTER TABLE fp_plan ADD COLUMN "status_id" uuid REFERENCES codelist_values(id);
        ALTER TABLE fp_baugebiet ADD COLUMN "detaillierteArtDerBaulNutzung_id" uuid REFERENCES codelist_values(id);
        
        ALTER TABLE so_schienenverkehr ADD COLUMN "detailArtDerFestlegung_id" uuid REFERENCES codelist_values(id);
        ALTER TABLE so_denkmalschutz ADD COLUMN "detailArtDerFestlegung_id" uuid REFERENCES codelist_values(id);;

CREATE TABLE assoc_detail_sondernutzung (
            "codelist_id" UUID,
            "codelist_user_id" UUID,
        
            FOREIGN KEY("codelist_user_id") REFERENCES bp_komplexe_sondernutzung (id) ON DELETE CASCADE,
            FOREIGN KEY("codelist_id") REFERENCES codelist_values (id),
            PRIMARY KEY (codelist_id, codelist_user_id)
        );
        
        CREATE TABLE assoc_detail_zweckgruen (
            "codelist_id" UUID,
            "codelist_user_id" UUID,
        
            FOREIGN KEY("codelist_user_id") REFERENCES bp_zweckbestimmung_gruen (id) ON DELETE CASCADE,
            FOREIGN KEY("codelist_id") REFERENCES codelist_values (id),
            PRIMARY KEY (codelist_id, codelist_user_id)
        );;

CREATE TYPE xp_arthoehenbezug AS ENUM (
            'absolutNHN',
            'absolutNN',
            'absolutDHHN',
            'relativGelaendeoberkante',
            'relativGehwegOberkante',
            'relativBezugshoehe',
            'relativStrasse',
            'relativEFH'
        );
        
        CREATE TYPE xp_arthoehenbezugspunkt AS ENUM (
            'TH',
            'FH',
            'OK',
            'LH',
            'SH',
            'EFH',
            'HBA',
            'UK',
            'GBH',
            'WH',
            'GOK'
        );
        
        CREATE TABLE xp_hoehenangabe (
            id UUID NOT NULL,
            "abweichenderHoehenbezug" VARCHAR,
            hoehenbezug xp_arthoehenbezug,
            "abweichenderBezugspunkt" VARCHAR,
            bezugspunkt xp_arthoehenbezugspunkt,
            "hMin" FLOAT,
            "hMax" FLOAT,
            "hZwingend" FLOAT,
            "h" FLOAT,
        
            "xp_objekt_id" UUID,
            "dachgestaltung_id" UUID,
            FOREIGN KEY("xp_objekt_id") REFERENCES xp_objekt (id) ON DELETE CASCADE,
            FOREIGN KEY("dachgestaltung_id") REFERENCES bp_dachgestaltung (id) ON DELETE CASCADE,
            PRIMARY KEY (id)
        );;

CREATE TYPE bp_abgrenzungentypen AS ENUM (
            'Nutzungsartengrenze',
            'UnterschiedlicheHoehen',
            'SonstigeAbgrenzung'
            );
        
        CREATE TABLE bp_nutzungsgrenze (
            id UUID NOT NULL,
            typ bp_abgrenzungentypen,
        
            PRIMARY KEY (id)
        );;

CREATE TYPE bp_bereichohneeinausfahrttypen  AS ENUM (
            'KeineEinfahrt',
            'KeineAusfahrt',
            'KeineEinAusfahrt'
            );
        
        CREATE TABLE bp_keine_ein_ausfahrt (
            id UUID NOT NULL,
            typ bp_bereichohneeinausfahrttypen,
        
            PRIMARY KEY (id)
        );;

CREATE TYPE bp_einfahrttypen AS ENUM (
            'Einfahrt',
            'Ausfahrt',
            'EinAusfahrt'
            );
        
        CREATE TABLE bp_einfahrtpunkt (
            id UUID NOT NULL,
            typ bp_einfahrttypen,
        
            PRIMARY KEY (id)
        );;

UPDATE alembic_version SET version_num='ce95b86bc010' WHERE alembic_version.version_num = '8cdbef1a55d6'; --- # pragma: allowlist secret;

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

-- Running upgrade 1983d6b6e2c1 -> 20238c1f2cf8

CREATE OR REPLACE FUNCTION immutable_date_to_char(date) RETURNS text AS
        $$ select extract(year from $1)::text || '-' ||
                    lpad(extract(week from $1)::text, 2, '0') || '-' ||
                    lpad(extract(day from $1)::text, 2, '0'); $$
        LANGUAGE sql immutable;;

ALTER TABLE xp_plan
        ADD COLUMN _sa_search_col tsvector
        GENERATED ALWAYS AS (to_tsvector('german',
            xp_plan.id::text || ' ' ||
            xp_plan.name || ' ' ||
            coalesce(xp_plan.type, '') || ' ' ||
            coalesce(xp_plan.nummer, '') || ' ' ||
            coalesce(xp_plan."internalId", '') || ' ' ||
            coalesce(xp_plan.beschreibung, '') || ' ' ||
            coalesce(xp_plan.kommentar, '') || ' ' ||
            coalesce(immutable_date_to_char(xp_plan."technHerstellDatum"), '') || ' ' ||
            coalesce(immutable_date_to_char(xp_plan."genehmigungsDatum"), '') || ' ' ||
            coalesce(immutable_date_to_char(xp_plan."untergangsDatum"), '') || ' ' ||
            coalesce(xp_plan."erstellungsMassstab"::text, '') || ' ' ||
            coalesce(xp_plan.bezugshoehe::text, '') || ' ' ||
            coalesce(xp_plan."technischerPlanersteller", '')
        )) STORED;;

CREATE INDEX textsearch_idx ON xp_plan USING GIN (_sa_search_col);;

CREATE TABLE bp_grundstueck_ueberbaubar (
    id UUID NOT NULL, 
    "FR" INTEGER, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    "wohnnutzungEGStrasse" bp_zulaessigkeit, 
    "ZWohn" INTEGER, 
    "GFAntWohnen" INTEGER, 
    "GFWohnen" FLOAT, 
    "GFAntGewerbe" INTEGER, 
    "GFGewerbe" FLOAT, 
    "VF" FLOAT, 
    bauweise bp_bauweise, 
    "vertikaleDifferenzierung" BOOLEAN, 
    "bebauungsArt" bp_bebauungsart, 
    "bebauungVordereGrenze" bp_grenzbebauung, 
    "bebauungRueckwaertigeGrenze" bp_grenzbebauung, 
    "bebauungSeitlicheGrenze" bp_grenzbebauung, 
    "geschossMin" INTEGER, 
    "geschossMax" INTEGER, 
    CONSTRAINT pk_bp_grundstueck_ueberbaubar PRIMARY KEY (id), 
    CONSTRAINT fk_bp_grundstueck_ueberbaubar_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE bp_dachgestaltung ADD COLUMN grundstueck_ueberbaubar_id UUID;

ALTER TABLE bp_dachgestaltung ADD CONSTRAINT fk_bp_dachgestaltung_grundstueck_ueberbaubar_id_bp_grun_7341 FOREIGN KEY(grundstueck_ueberbaubar_id) REFERENCES bp_grundstueck_ueberbaubar (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD COLUMN grundstueck_ueberbaubar_id UUID;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_grundstueck_ueberbaubar_id_bp_gr_1813 FOREIGN KEY(grundstueck_ueberbaubar_id) REFERENCES bp_grundstueck_ueberbaubar (id) ON DELETE CASCADE;

UPDATE alembic_version SET version_num='20238c1f2cf8' WHERE alembic_version.version_num = '1983d6b6e2c1'; --- # pragma: allowlist secret;

-- Running upgrade 20238c1f2cf8 -> 151ba21532e3

create or replace function fp_baugebiet_sync_attr_sondernutzung() returns trigger
            language plpgsql
        as
        $$
        DECLARE
            sn_enum_value text;
        begin
            IF TG_ARGV[0]  = 'sondernutzung' THEN
                DELETE FROM fp_komplexe_sondernutzung WHERE baugebiet_id = NEW.id;

                IF NEW."sonderNutzung" IS NOT NULL THEN
                    FOREACH sn_enum_value IN ARRAY NEW."sonderNutzung"
                    LOOP
                        -- Insert a new row into fp_komplexe_sondernutzung
                        INSERT INTO fp_komplexe_sondernutzung (id, baugebiet_id, allgemein)
                        VALUES (uuid_generate_v4(), NEW.id, sn_enum_value::xp_sondernutzungen);
                    END LOOP;
                END IF;
            ELSE
                -- make sure no duplicates are inserted by selecting distinct from unnested array
                UPDATE fp_baugebiet SET "sonderNutzung" = ARRAY(SELECT DISTINCT UNNEST("sonderNutzung" || ARRAY[NEW.allgemein]))
                WHERE id = NEW.baugebiet_id;
            END IF;
            RETURN NEW;
        end $$;;

create or replace function fp_gemeinbedarf_sync_attr_zweckbestimmung() returns trigger
            language plpgsql
        as
        $$
        DECLARE
            zb_enum_value text;
        begin
            IF TG_ARGV[0]  = 'zweckbestimmung' THEN
                DELETE FROM fp_zweckbestimmung_gemeinbedarf WHERE gemeinbedarf_id = NEW.id;
        
                IF NEW."zweckbestimmung" IS NOT NULL THEN
                    FOREACH zb_enum_value IN ARRAY NEW."zweckbestimmung"
                    LOOP
                        -- Insert a new row into fp_komplexe_sondernutzung
                        INSERT INTO fp_zweckbestimmung_gemeinbedarf (id, gemeinbedarf_id, allgemein)
                        VALUES (uuid_generate_v4(), NEW.id, zb_enum_value::xp_zweckbestimmunggemeinbedarf);
                    END LOOP;
                END IF;
            ELSE
                UPDATE fp_gemeinbedarf SET zweckbestimmung = array_remove(zweckbestimmung, OLD.allgemein) WHERE id = OLD.gemeinbedarf_id;
        
                -- make sure no duplicates are inserted by selecting distinct from unnested array
                UPDATE fp_gemeinbedarf SET zweckbestimmung = ARRAY(SELECT DISTINCT UNNEST(zweckbestimmung || ARRAY[NEW.allgemein]))
                WHERE id = NEW.gemeinbedarf_id;
            END IF;
            RETURN NEW;
        end $$;;

create or replace function bp_baugebiet_sync_attr_sondernutzung() returns trigger
            language plpgsql
        as
        $$
        DECLARE
            sn_enum_value text;
        begin
            IF TG_ARGV[0]  = 'sondernutzung' THEN
                DELETE FROM bp_komplexe_sondernutzung WHERE baugebiet_id = NEW.id;

                IF NEW."sondernutzung" IS NOT NULL THEN
                    FOREACH sn_enum_value IN ARRAY NEW."sondernutzung"
                    LOOP
                        -- Insert a new row into bp_komplexe_sondernutzung
                        INSERT INTO bp_komplexe_sondernutzung (id, baugebiet_id, allgemein)
                        VALUES (uuid_generate_v4(), NEW.id, sn_enum_value::xp_sondernutzungen);
                    END LOOP;
                END IF;
            ELSE
                -- make sure no duplicates are inserted by selecting distinct from unnested array
                UPDATE bp_baugebiet SET sondernutzung = ARRAY(SELECT DISTINCT UNNEST(sondernutzung || ARRAY[NEW.allgemein]))
                WHERE id = NEW.baugebiet_id;
            END IF;
            RETURN NEW;
        end $$;;

CREATE TABLE fp_abgrabung (
    id UUID NOT NULL, 
    abbaugut VARCHAR, 
    CONSTRAINT pk_fp_abgrabung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_abgrabung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_aufschuettung (
    id UUID NOT NULL, 
    aufschuettungsmaterial VARCHAR, 
    CONSTRAINT pk_fp_aufschuettung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_aufschuettung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_schutzflaeche (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    "istAusgleich" BOOLEAN, 
    CONSTRAINT pk_fp_schutzflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_fp_schutzflaeche_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE xp_spe_daten ADD COLUMN fp_schutzflaeche_id UUID;

ALTER TABLE xp_spe_daten ADD CONSTRAINT fk_spe_daten_schutzflaeche FOREIGN KEY(fp_schutzflaeche_id) REFERENCES fp_schutzflaeche (id) ON DELETE CASCADE;

CREATE TABLE fp_kennzeichnung (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungkennzeichnung[], 
    "istVerdachtsflaeche" BOOLEAN, 
    nummer VARCHAR, 
    CONSTRAINT pk_fp_kennzeichnung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_kennzeichnung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='151ba21532e3' WHERE alembic_version.version_num = '20238c1f2cf8'; --- # pragma: allowlist secret;

-- Running upgrade 151ba21532e3 -> 5b93f2301608

ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'BauHoehe';;

ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'BauMasse';;

ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'GrundGeschossflaeche';;

ALTER TABLE so_strassenverkehr ALTER COLUMN nutzungsform DROP NOT NULL;;

UPDATE alembic_version SET version_num='5b93f2301608' WHERE alembic_version.version_num = '151ba21532e3'; --- # pragma: allowlist secret;

-- Running upgrade 5b93f2301608 -> e9b38a472653

CREATE TABLE assoc_detail_zweckgemeinbedarf (
    codelist_user_id UUID, 
    codelist_user_v6_id UUID, 
    codelist_id UUID, 
    CONSTRAINT fk_assoc_detail_zweckgemeinbedarf_codelist_id_codelist_values FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_assoc_detail_zweckgemeinbedarf_codelist_user_id_fp_g_d4b9 FOREIGN KEY(codelist_user_id) REFERENCES fp_gemeinbedarf (id) ON DELETE CASCADE, 
    CONSTRAINT fk_assoc_detail_zweckgemeinbedarf_codelist_user_v6_id_f_6dd0 FOREIGN KEY(codelist_user_v6_id) REFERENCES fp_zweckbestimmung_gemeinbedarf (id) ON DELETE CASCADE
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

DELETE FROM xp_objekt 
        WHERE id IN (
            SELECT id FROM bp_objekt WHERE GeometryType(position) IN ('GEOMETRYCOLLECTION')
        );

        DELETE FROM bp_objekt WHERE GeometryType(position) IN ('GEOMETRYCOLLECTION');

        DELETE FROM xp_objekt 
        WHERE id IN (
            SELECT id FROM fp_objekt WHERE GeometryType(position) IN ('GEOMETRYCOLLECTION')
        );

        DELETE FROM fp_objekt WHERE GeometryType(position) IN ('GEOMETRYCOLLECTION');

        DELETE FROM xp_objekt 
        WHERE id IN (
            SELECT id FROM so_objekt WHERE GeometryType(position) IN ('GEOMETRYCOLLECTION')
        );

        DELETE FROM so_objekt WHERE GeometryType(position) IN ('GEOMETRYCOLLECTION');;

ALTER TABLE bp_objekt ADD CONSTRAINT "ck_bp_objekt_`prevent_geometry_collection`" CHECK (GeometryType(position) NOT IN ('GEOMETRYCOLLECTION'));

ALTER TABLE fp_objekt ADD CONSTRAINT "ck_fp_objekt_`prevent_geometry_collection`" CHECK (GeometryType(position) NOT IN ('GEOMETRYCOLLECTION'));

ALTER TABLE so_objekt ADD CONSTRAINT "ck_so_objekt_`prevent_geometry_collection`" CHECK (GeometryType(position) NOT IN ('GEOMETRYCOLLECTION'));

CREATE TYPE so_klassifiznachstrassenverkehrsrecht AS ENUM ('Bundesautobahn', 'Bundesstrasse', 'LandesStaatsstrasse', 'Kreisstrasse', 'SonstOeffentlStrasse');

CREATE TABLE so_strassenverkehrsrecht (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachstrassenverkehrsrecht, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_strassenverkehrsrecht PRIMARY KEY (id), 
    CONSTRAINT fk_so_strassenverkehrsrecht_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE OR REPLACE FUNCTION temp_convert(v_input text)
        RETURNS so_klassifiznachstrassenverkehrsrecht AS $$
        DECLARE ret so_klassifiznachstrassenverkehrsrecht DEFAULT NULL;
        BEGIN
            BEGIN
                ret := v_input::so_klassifiznachstrassenverkehrsrecht;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Invalid so_klassifiznachstrassenverkehrsrecht value: "%".  Returning Default.', v_input;
                RETURN 'SonstOeffentlStrasse'::so_klassifiznachstrassenverkehrsrecht;
            END;
        RETURN ret;
        END;
        $$ LANGUAGE plpgsql;

        WITH old_and_new_ids AS (
            SELECT 
                uuid_generate_v4() AS new_id, -- new id to be inserted
                'so_strassenverkehrsrecht' AS type,
                xp.rechtscharakter,
                str.id AS old_id -- capturing old id, needed later for merging data
            FROM so_strassenverkehr str
            JOIN xp_objekt xp ON xp.id = str.id
        ),
        -- Step 2: insert into xo_objekt
        new_xp_objekt AS (
            INSERT INTO xp_objekt (id, type, rechtscharakter, uuid, text, rechtsstand, gliederung1, gliederung2, ebene, "gehoertZuBereich_id", aufschrift, "gesetzlicheGrundlage_id", skalierung, drehwinkel)
            SELECT 
                new_id,
                oani.type,
                oani.rechtscharakter,
                uuid, text, rechtsstand, gliederung1, gliederung2, ebene, "gehoertZuBereich_id", aufschrift, "gesetzlicheGrundlage_id", skalierung, drehwinkel
            FROM old_and_new_ids oani
            JOIN xp_objekt xp ON oani.old_id=xp.id
            RETURNING id, type, rechtscharakter
        ),
        -- Step 2: insert into so_objekt
        new_so_objekt AS (
            INSERT INTO so_objekt (id, rechtscharakter, position, flaechenschluss, flussrichtung, nordwinkel)
            SELECT 
                new.id as id, 
                so.rechtscharakter as rechtscharakter,
                position, flaechenschluss, flussrichtung, nordwinkel
            FROM new_xp_objekt new
            JOIN old_and_new_ids oani ON new.id = oani.new_id
            JOIN so_objekt so ON oani.old_id=so.id
            RETURNING id, rechtscharakter
        )
        
        -- Step 3: insert into so_strassenverkehrsrecht
        INSERT INTO so_strassenverkehrsrecht (id, name, nummer, "artDerFestlegung")
          SELECT
            oani.new_id AS id, 
            s.name, s.nummer, 
            temp_convert(s.einteilung::text) AS "artDerFestlegung"
        FROM so_strassenverkehr s
        JOIN old_and_new_ids oani ON s.id = oani.old_id;
        
        DROP function temp_convert(v_input text);;

CREATE TYPE so_klassifizgewaesserv5 AS ENUM ('Gewaesser', 'Fliessgewaesser', 'Gewaesser1Ordnung', 'Gewaesser2Ordnung', 'Gewaesser3Ordnung', 'StehendesGewaesser', 'Hafen', 'Sonstiges');

ALTER TABLE so_gewaesser ADD COLUMN "artDerFestlegung" so_klassifizgewaesserv5;

CREATE TYPE so_klassifiznachwasserrecht AS ENUM ('Ueberschwemmungsgebiet', 'FestgesetztesUeberschwemmungsgebiet', 'NochNichtFestgesetztesUeberschwemmungsgebiet', 'UeberschwemmGefaehrdetesGebiet', 'Risikogebiet', 'RisikogebietAusserhUeberschwemmgebiet', 'Hochwasserentstehungsgebiet', 'Sonstiges');

CREATE TABLE so_wasserrecht (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachwasserrecht, 
    "istNatuerlichesUberschwemmungsgebiet" BOOLEAN, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_wasserrecht PRIMARY KEY (id), 
    CONSTRAINT fk_so_wasserrecht_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_klassifizschutzgebietnaturschutzrecht AS ENUM ('Naturschutzgebiet', 'Nationalpark', 'Biosphaerenreservat', 'Landschaftsschutzgebiet', 'Naturpark', 'Naturdenkmal', 'GeschuetzterLandschaftsBestandteil', 'GesetzlichGeschuetztesBiotop', 'Natura2000', 'GebietGemeinschaftlicherBedeutung', 'EuropaeischesVogelschutzgebiet', 'NationalesNaturmonument', 'Sonstiges');

CREATE TYPE so_schutzzonennaturschutzrecht AS ENUM ('Schutzzone_1', 'Schutzzone_2', 'Schutzzone_3', 'Kernzone', 'Pflegezone', 'Entwicklungszone', 'Regenerationszone');

CREATE TABLE so_naturschutz (
    id UUID NOT NULL, 
    "artDerFestlegung" xp_klassifizschutzgebietnaturschutzrecht, 
    zone so_schutzzonennaturschutzrecht, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_naturschutz PRIMARY KEY (id), 
    CONSTRAINT fk_so_naturschutz_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TYPE fp_zweckbestimmungprivilegiertesvorhaben AS ENUM ('LandForstwirtschaft', 'Aussiedlerhof', 'Altenteil', 'Reiterhof', 'Gartenbaubetrieb', 'Baumschule', 'OeffentlicheVersorgung', 'Wasser', 'Gas', 'Waerme', 'Elektrizitaet', 'Telekommunikation', 'Abwasser', 'OrtsgebundenerGewerbebetrieb', 'BesonderesVorhaben', 'BesondereUmgebungsAnforderung', 'NachteiligeUmgebungsWirkung', 'BesondereZweckbestimmung', 'ErneuerbareEnergien', 'Windenergie', 'Wasserenergie', 'Solarenergie', 'Biomasse', 'Kernenergie', 'NutzungKernerergie', 'EntsorgungRadioaktiveAbfaelle', 'Sonstiges', 'StandortEinzelhof', 'BebauteFlaecheAussenbereich');

CREATE TABLE fp_privilegiertes_vorhaben (
    id UUID NOT NULL, 
    zweckbestimmung fp_zweckbestimmungprivilegiertesvorhaben, 
    vorhaben VARCHAR, 
    CONSTRAINT pk_fp_privilegiertes_vorhaben PRIMARY KEY (id), 
    CONSTRAINT fk_fp_privilegiertes_vorhaben_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE lp_raumkonkretisierung AS ENUM ('Scharf', 'Suchraum', 'Unscharf', 'Position', 'Raumunkonkret', 'Unbekannt');

CREATE TABLE lp_objekt (
    id UUID NOT NULL, 
    raumkonkretisierung lp_raumkonkretisierung, 
    "rechtsCharText" VARCHAR, 
    position geometry(GEOMETRY,-1), 
    flaechenschluss BOOLEAN, 
    flussrichtung BOOLEAN, 
    nordwinkel INTEGER, 
    CONSTRAINT pk_lp_objekt PRIMARY KEY (id), 
    CONSTRAINT fk_lp_objekt_id_xp_objekt FOREIGN KEY(id) REFERENCES xp_objekt (id) ON DELETE CASCADE
);

CREATE INDEX idx_lp_objekt_position ON lp_objekt USING gist (position);

ALTER TABLE lp_objekt ADD CONSTRAINT "ck_lp_objekt_`prevent_geometry_collection`" CHECK (GeometryType(position) NOT IN ('GEOMETRYCOLLECTION'));

UPDATE alembic_version SET version_num='e9b38a472653' WHERE alembic_version.version_num = '5b93f2301608'; --- # pragma: allowlist secret;

-- Running upgrade e9b38a472653 -> 31058f6befbd

ALTER TABLE xp_objekt ALTER COLUMN type TYPE varchar;;

CREATE TYPE lp_planungsebene AS ENUM ('Biotopverbund', 'Biotopvernetzung');

CREATE TYPE lp_rechtlichesicherung AS ENUM ('Schutzerklaerung', 'PlanungsrechtlicheFestlegung', 'VertraglicheRegelung', 'Sonstiges');

CREATE TYPE lp_bioverbundsystemart AS ENUM ('Allgemein', 'OffenlandHalboffenland', 'Wald', 'Gewaesser');

CREATE TYPE lp_biovstandortfeuchte AS ENUM ('Feucht', 'Mittel', 'Trocken');

CREATE TABLE lp_biotopverbund_biotopvernetzung (
    id UUID NOT NULL, 
    "planungsEbene" lp_planungsebene[], 
    "rechtlicheSicherung" lp_rechtlichesicherung, 
    "rechtlicheSicherungText" VARCHAR, 
    "bioVerbundsystemArt" lp_bioverbundsystemart NOT NULL, 
    "bioVStandortFeuchte" lp_biovstandortfeuchte, 
    "bioVerbundsystemText" VARCHAR, 
    foerdermoeglichkeit VARCHAR[], 
    CONSTRAINT pk_lp_biotopverbund_biotopvernetzung PRIMARY KEY (id), 
    CONSTRAINT fk_lp_biotopverbund_biotopvernetzung_id_lp_objekt FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE lp_umsetzungsstand AS ENUM ('NachrichtlichUmgesetztOderAngerechnet', 'Vorschlag', 'Unbekannt');

CREATE TYPE lp_massnahmentyp AS ENUM ('Kompensationsmassnahme', 'MassnahmeCEF', 'MassnahmeFCS', 'MassnahmeKohaerenzsicherung', 'Unbekannt');

CREATE TABLE lp_eingriffsregelung (
    id UUID NOT NULL, 
    umsetzungsstand lp_umsetzungsstand NOT NULL, 
    massnahmentyp lp_massnahmentyp[] NOT NULL, 
    "kompensationText" VARCHAR, 
    CONSTRAINT pk_lp_eingriffsregelung PRIMARY KEY (id), 
    CONSTRAINT fk_lp_eingriffsregelung_id_lp_objekt FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE lp_generisches_objekt (
    id UUID NOT NULL, 
    CONSTRAINT pk_lp_generisches_objekt PRIMARY KEY (id), 
    CONSTRAINT fk_lp_generisches_objekt_id_lp_objekt FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE lp_klassifizierungnaturschutzrecht AS ENUM ('Naturschutzgebiet', 'Nationalpark', 'Biosphaerenreservat', 'Landschaftsschutzgebiet', 'Naturpark', 'Naturdenkmal', 'GeschuetzterLandschaftsbestandteil', 'GesetzlichgeschuetztesBiotop', 'Natura2000', 'GebietGemeinschaftlicherBedeutung', 'EuropaeischesVogelschutzgebiet', 'NationalesNaturmonument', 'Sonstiges');

CREATE TYPE lp_rechtsstandschutzgeb AS ENUM ('Geplant', 'Bestehend', 'Fortfallend', 'Eignung', 'Erweiterung', 'Qualifizierung', 'Sonstiges');

CREATE TYPE lp_gesgeschbiotoptyp AS ENUM ('Gewaesserbiotope', 'FeuchtUndNassbiotope', 'Trockenbiotope', 'Waldbiotope', 'FelsenAlpineBiotope', 'Kuestenbiotope', 'Sonstiges');

CREATE TYPE lp_schutzzonennaturschutzrecht AS ENUM ('Schutzzone1', 'Schutzzone2', 'Schutzzone3', 'Kernzone', 'Pflegezone', 'Entwicklungszone', 'Regenerationszone', 'Sonstiges');

CREATE TABLE lp_schutz_bestimmter_teile_von_natur_und_landschaft (
    id UUID NOT NULL, 
    "artDerFestlegung" lp_klassifizierungnaturschutzrecht NOT NULL, 
    "artDerFestlegungText" VARCHAR, 
    "rechtsstandSchG" lp_rechtsstandschutzgeb NOT NULL, 
    "rechtsstandSchGText" VARCHAR, 
    name VARCHAR, 
    nummer VARCHAR, 
    "gesetzlGeschBiotop" lp_gesgeschbiotoptyp, 
    "gesetzlGeschBiotopText" VARCHAR, 
    "detailGesetzlGeschBiotopLR_id" UUID, 
    schutzzone lp_schutzzonennaturschutzrecht, 
    "schutzzonenText" VARCHAR, 
    CONSTRAINT pk_lp_schutz_bestimmter_teile_von_natur_und_landschaft PRIMARY KEY (id), 
    CONSTRAINT fk_lp_schutz_bestimmter_teile_von_natur_und_landschaft__4b8d FOREIGN KEY("detailGesetzlGeschBiotopLR_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_lp_schutz_bestimmter_teile_von_natur_und_landschaft__6eb2 FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE lp_text_abschnitt_objekt (
    id UUID NOT NULL, 
    CONSTRAINT pk_lp_text_abschnitt_objekt PRIMARY KEY (id), 
    CONSTRAINT fk_lp_text_abschnitt_objekt_id_lp_objekt FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE lp_zemtyp AS ENUM ('Ziel', 'Erfordernis', 'Massnahme');

CREATE TABLE lp_ziele_erfordernisse_massnahmen (
    id UUID NOT NULL, 
    "artDerFestlegung" lp_zemtyp[] NOT NULL, 
    freiraeume VARCHAR[], 
    foerdermoeglichkeit VARCHAR[], 
    CONSTRAINT pk_lp_ziele_erfordernisse_massnahmen PRIMARY KEY (id), 
    CONSTRAINT fk_lp_ziele_erfordernisse_massnahmen_id_lp_objekt FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_zweckgenerischeobjekte (
    codelist_user_id UUID, 
    codelist_id UUID, 
    CONSTRAINT fk_assoc_detail_zweckgenerischeobjekte_codelist_id_code_775e FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_assoc_detail_zweckgenerischeobjekte_codelist_user_id_f452 FOREIGN KEY(codelist_user_id) REFERENCES lp_generisches_objekt (id) ON DELETE CASCADE
);

CREATE TYPE lp_adressatart AS ENUM ('Naturschutz', 'Bauleitplanung', 'Raumordnung', 'Flurneuordnung', 'Forstwirtschaft', 'Landwirtschaft', 'Wasserwirtschaft', 'Fischereiwirtschaft', 'Jagd', 'RohstoffgewinnungUndBergbau', 'VerteidigungSicherungDerZivilbevoelkerung', 'Verkehrsplanung', 'Energiegewinnung', 'Abfallwirtschaft', 'Bodenschutz', 'KommunaleKoerperschaften', 'LandKreisverwaltung', 'Land', 'Unbekannt', 'Sonstiges');

CREATE TABLE lp_adressat_komplex (
    id UUID NOT NULL, 
    "adressatArt" lp_adressatart NOT NULL, 
    "adressatText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_adressat_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_adressat_komplex_ziele_erfordernisse_massnahmen_i_0013 FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TABLE lp_biologische_vielfalt_komplex (
    id UUID NOT NULL, 
    "bioVfArtFFHAnhangII" BOOLEAN NOT NULL, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_biologische_vielfalt_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_biologische_vielfalt_komplex_ziele_erfordernisse__c4b2 FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_bodenauspraegung AS ENUM ('Ablagerungen', 'Altablagerungsflaeche', 'Altlastenverdachtsflaeche', 'BodenFilterUndPufferfunktion', 'BodenHoheBodenfruchtbarkeit', 'BodenHoherFunktionglobalerKlimaschutz', 'BodenKulturgeschichtlicheBedeutung', 'BodenNaturgeschichtlicheBedeutung', 'BodenGeowissenschaftlicheBedeutung', 'NatuerlicheBoeedenExtremstandort', 'EhemaligerMilitaerischGenutzterStandort', 'Erosionsgefaehrdet', 'ErosionsgefaehrdetWind', 'ErosionsgefaehrdetWasser', 'Geotop', 'SelteneBodenform', 'NaturnaherBoden', 'BoedenHohesRetentionspotenzial', 'EntsiegelungOderWiederherstellungBodenfunktion', 'Sonstiges');

CREATE TABLE lp_boden_komplex (
    id UUID NOT NULL, 
    "bodenAuspraegung" lp_bodenauspraegung NOT NULL, 
    "bodenText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_boden_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_boden_komplex_ziele_erfordernisse_massnahmen_id_l_7afc FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_erflaechenart AS ENUM ('PotenzielleFlaecheKompensation', 'Flaechenpool', 'KompensationEinzelflaeche', 'Kompensationsverzeichnis', 'Sonstiges');

CREATE TABLE lp_eingriffsregelung_komplex (
    id UUID NOT NULL, 
    "eRFlaechenArt" lp_erflaechenart NOT NULL, 
    "eRFlaechenArtText" VARCHAR, 
    eingriffsregelung_id UUID, 
    CONSTRAINT pk_lp_eingriffsregelung_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_eingriffsregelung_komplex_eingriffsregelung_id_lp_e8c2 FOREIGN KEY(eingriffsregelung_id) REFERENCES lp_eingriffsregelung (id) ON DELETE CASCADE
);

CREATE TYPE lp_erholungfunktionen AS ENUM ('Gruenflaechen', 'ParkanlageGruenanlage', 'Dauerkleingaerten', 'Sportplatz', 'Spielplatz', 'BadeplatzFreibad', 'Liegewiese', 'Erholungsinfrastruktur', 'Schutzhuette', 'Rastplatz', 'Informationstafel', 'FeuerstelleGrillplatz', 'Aussichtsturm', 'Aussichtspunkt', 'Angelteich', 'Modellflugplatz', 'Gleitschirmplatz', 'WildgehegeSchaugatter', 'Parkplatz', 'ZeltplatzCampingplatz', 'JugendzeltplatzEinzelcamp', 'ErholungsInfrastrukturMitBesondererBedeutung', 'WandernAllgemein', 'Wanderweg', 'Lehrpfad', 'Reitweg', 'Radweg', 'Wintersport', 'Skiabfahrt', 'Skilanglaufloipe', 'RodelbahnBobbahn', 'WassersportSchifffahrt', 'Wasserwanderweg', 'Schifffahrtsroute', 'AnlegestelleMitMotorbooten', 'AnlegestelleOhneMotorboote', 'Seilbahn', 'SesselliftSchlepplift', 'Kabinenseilbahn', 'Bildungsstaette', 'Umweltbildungsstaette', 'Museum', 'Sonstiges');

CREATE TABLE lp_erholung_komplex (
    id UUID NOT NULL, 
    "erholungFunktionArt" lp_erholungfunktionen NOT NULL, 
    "erholungFunktionText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_erholung_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_erholung_komplex_ziele_erfordernisse_massnahmen_i_9370 FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_klimaart AS ENUM ('BioklimatischeFunktion', 'Luftleitbahn', 'Frischluftbahn', 'Frischluftentstehungsgebiet', 'Kaltluftbahn', 'Kaltluftentstehungsgebiet', 'Stadtklima', 'THGSenkenKlimaschutzflaechen', 'Sonstiges');

CREATE TABLE lp_klima_komplex (
    id UUID NOT NULL, 
    "klimaArt" lp_klimaart NOT NULL, 
    "klimaText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_klima_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_klima_komplex_ziele_erfordernisse_massnahmen_id_l_ce8b FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_landschaftsbildart AS ENUM ('KircheKlosterKapelle', 'BurgSchloss', 'Turm', 'HistorischesOrtsbild', 'Ruine', 'KulturgeschichtlichWertvollerOrtsteil', 'Aussichtspunkt', 'Aussichtsturm', 'LandschaftsgerechteEinbindung', 'LandschaftsgerechterSiedlungsrand', 'Strukturvielfalt', 'LandschaftMitHoherEigenart', 'Landschaftsachsen', 'Landschaftsraeume', 'HistorischeWaldinsel', 'Waldraender', 'Kulturlandschaft', 'HistorischeKulturlandschaft', 'Kulturlandschaftselement', 'Hohlweg', 'Gartendenkmal', 'Sonstiges');

CREATE TABLE lp_landschaftsbild_komplex (
    id UUID NOT NULL, 
    "landschaftsbildArt" lp_landschaftsbildart NOT NULL, 
    "landschaftsbildText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_landschaftsbild_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_landschaftsbild_komplex_ziele_erfordernisse_massn_a13c FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_luftart AS ENUM ('Geruchsbelastung', 'Laermbelastung', 'LufthygienischeFktStofflBelastung', 'Staubbelastung', 'Sonstiges');

CREATE TABLE lp_luft_komplex (
    id UUID NOT NULL, 
    "luftArt" lp_luftart NOT NULL, 
    "luftText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_luft_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_luft_komplex_ziele_erfordernisse_massnahmen_id_lp_e937 FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TABLE lp_nutzungseinschraenkung_komplex (
    id UUID NOT NULL, 
    "hatNutzungseinschraenkung" BOOLEAN NOT NULL, 
    "nutzungseinschraenkungText" VARCHAR NOT NULL, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_nutzungseinschraenkung_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_nutzungseinschraenkung_komplex_ziele_erforderniss_1439 FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_schutzgutart AS ENUM ('AlleSchutzgueter', 'ArtenUndLebensgemeinschaften', 'Biotope', 'Boden', 'Wasser', 'Klima', 'Luft', 'Landschaftsbild', 'ErholungInNaturUndLandschaft', 'Unbekannt', 'Sonstiges');

CREATE TABLE lp_schutzgut_komplex (
    id UUID NOT NULL, 
    "schutzgutArt" lp_schutzgutart NOT NULL, 
    "schutzgutText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_schutzgut_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_schutzgut_komplex_ziele_erfordernisse_massnahmen__5716 FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_schutzpflegeentwicklung AS ENUM ('Schutz', 'Pflege', 'Entwicklung', 'Anlage', 'Wiederherstellung', 'Vermeidung', 'Minderung', 'Beseitigung', 'Sonstiges');

CREATE TABLE lp_spe_komplex (
    id UUID NOT NULL, 
    "schutzPflegeEntwicklungTyp" lp_schutzpflegeentwicklung[] NOT NULL, 
    "schutzPflegeEntwicklungText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_spe_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_spe_komplex_ziele_erfordernisse_massnahmen_id_lp__aa38 FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_flaechentypbv AS ENUM ('Kernflaeche', 'Verbindungsflaeche', 'Verbindungselement');

CREATE TYPE lp_flaechentypbvspeziell AS ENUM ('Verbindungsraeume', 'Verbundachse', 'Wildtierkorridor', 'Entwicklungsflaeche', 'Entwicklungsmassnahme', 'Vernetzungselement', 'Trittsteinbiotop', 'Sonstiges');

CREATE TABLE lp_typ_bioverbundkomplexe (
    id UUID NOT NULL, 
    "flaechenTypBV" lp_flaechentypbv NOT NULL, 
    "flaechentypBVSpeziell" lp_flaechentypbvspeziell, 
    "flaechentypSpeziellText" VARCHAR, 
    biotopverbund_biotopvernetzung_id UUID, 
    CONSTRAINT pk_lp_typ_bioverbundkomplexe PRIMARY KEY (id), 
    CONSTRAINT fk_lp_typ_bioverbundkomplexe_biotopverbund_biotopvernet_6975 FOREIGN KEY(biotopverbund_biotopvernetzung_id) REFERENCES lp_biotopverbund_biotopvernetzung (id) ON DELETE CASCADE
);

CREATE TYPE lp_wasserauspraegung AS ENUM ('Hochwasserschutz', 'Ueberschwemmungsgebiet', 'Hochwasservorsorge', 'Retentionsraum', 'Polderflaeche', 'Deichrueckverlegung', 'Trinkwassergewinnung', 'Trinkwasserschutz', 'Grundwasserneubildungsgebiet', 'LaengsdurchgaengigkeitGewaesser', 'MindestwasserfuehrungGewaesser', 'Drainage', 'Entwaesserungsgraben', 'NaturnaheGewaesser', 'NaturnaheUferbereiche', 'OekologischeFunktionFliessgewaesser', 'OekologischeFunktionQuellbereich', 'OekologischeFunktionStillgewaesser', 'Gewaesserstruktur', 'Gewaesserdynamik', 'Gewaesserrandstreifen', 'Gewaesserschutzstreifen', 'Pufferzone', 'Ufergehoelze', 'FischaufstiegsOderAbstiegsanlage', 'Wehr', 'Verrohrung', 'Sohlstufe', 'Gewaesserguete', 'StoffeintraegeInGrundwasser', 'StoffeintraegeInOberflaechengewaesser', 'Versickerungsflaeche', 'Verlandungsbereiche', 'Sonstiges');

CREATE TABLE lp_wasser_komplex (
    id UUID NOT NULL, 
    "wasserAuspraegung" lp_wasserauspraegung NOT NULL, 
    "wasserText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_wasser_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_wasser_komplex_ziele_erfordernisse_massnahmen_id__20f0 FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_zieldimensiontyp AS ENUM ('SchutzBiologischeVielfalt', 'SchutzNaturhaushalt', 'SchutzLandschaftsbildErholungsvorsorge', 'Unbekannt', 'Sonstiges');

CREATE TABLE lp_ziel_dim_nat_sch_la_pfl_komplex (
    id UUID NOT NULL, 
    "zielDimensionTyp" lp_zieldimensiontyp NOT NULL, 
    "zielDimensionText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    CONSTRAINT pk_lp_ziel_dim_nat_sch_la_pfl_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_ziel_dim_nat_sch_la_pfl_komplex_ziele_erfordernis_9110 FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TABLE lp_bio_vf_biotoptyp_komplex (
    id UUID NOT NULL, 
    "bioVfBiotoptyp_BKompV_id" UUID, 
    "bioVfBiotoptyp_LandesKS_id" UUID, 
    "bioVf_FFH_LRT_id" UUID, 
    "bioVfBiotoptyp_Text" VARCHAR, 
    biologische_vielfalt_komplex_id UUID, 
    CONSTRAINT pk_lp_bio_vf_biotoptyp_komplex PRIMARY KEY (id), 
    CONSTRAINT "fk_lp_bio_vf_biotoptyp_komplex_bioVfBiotoptyp_BKompV_id_24e8" FOREIGN KEY("bioVfBiotoptyp_BKompV_id") REFERENCES codelist_values (id), 
    CONSTRAINT "fk_lp_bio_vf_biotoptyp_komplex_bioVfBiotoptyp_LandesKS__92c7" FOREIGN KEY("bioVfBiotoptyp_LandesKS_id") REFERENCES codelist_values (id), 
    CONSTRAINT "fk_lp_bio_vf_biotoptyp_komplex_bioVf_FFH_LRT_id_codelist_values" FOREIGN KEY("bioVf_FFH_LRT_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_lp_bio_vf_biotoptyp_komplex_biologische_vielfalt_kom_bf75 FOREIGN KEY(biologische_vielfalt_komplex_id) REFERENCES lp_biologische_vielfalt_komplex (id) ON DELETE CASCADE
);

CREATE TYPE lp_biovfpflanzenartsystematik AS ENUM ('Gefaesspflanze', 'MooseUndFlechten', 'Pilze', 'Sonstiges');

CREATE TYPE lp_biovfpflanzenartrechtlicherschutz AS ENUM ('AnhangIVFFHRL', 'Anlage1BArtSchV', 'Verantwortungsart', 'Sonstige');

CREATE TABLE lp_bio_vf_pflanzen_art_komplex (
    id UUID NOT NULL, 
    "bioVfPflanzenArtName" VARCHAR, 
    "bioVfPflanzenSystematik" lp_biovfpflanzenartsystematik NOT NULL, 
    "bioVfPflanzenSystematikText" VARCHAR, 
    "bioVfPflanzenRechtlicherSchutz" lp_biovfpflanzenartrechtlicherschutz[], 
    "bioVfPflanzenRechtlicherSchutzText" VARCHAR, 
    biologische_vielfalt_komplex_id UUID, 
    CONSTRAINT pk_lp_bio_vf_pflanzen_art_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_bio_vf_pflanzen_art_komplex_biologische_vielfalt__2cfa FOREIGN KEY(biologische_vielfalt_komplex_id) REFERENCES lp_biologische_vielfalt_komplex (id) ON DELETE CASCADE
);

CREATE TYPE lp_biovftiereartsystematik AS ENUM ('Grosssaeuger', 'Wolf', 'Luchs', 'Mittelsaeuger', 'Wildkatze', 'Fischotter', 'Biber', 'Marder', 'Kleinsaeuger', 'KleinsaeugerNagetiere', 'Feldhamster', 'Maeuse', 'KleinsaeugerHasenartige', 'KleinsaeugerInsektenfresser', 'Spitzmaeuse', 'KleinsaeugerFledermaeuse', 'Meeressaeuger', 'Voegel', 'Zugvoegel', 'Brutvoegel', 'Reptilien', 'Amphibien', 'Fische', 'Gliederfuesser', 'Libellen', 'Tagfalter', 'Kaefer', 'Heuschrecken', 'Spinnen', 'Krebstiere', 'Mollusken', 'Sonstiges');

CREATE TYPE lp_biovftierartrechtlicherschutz AS ENUM ('ArtAnhangIVFFHRL', 'ArtAnhangIArt4Abs2VSRL', 'ArtAnlage1BArtSchV', 'Verantwortungsart', 'Sonstige');

CREATE TYPE lp_biovftierarthabitatanforderung AS ENUM ('GrosserHabitatsAnspruch', 'Gebaeudebewohnend', 'Sonstige');

CREATE TABLE lp_bio_vf_tiere_art_komplex (
    id UUID NOT NULL, 
    "bioVfTierArtName" VARCHAR, 
    "bioVfTiereSystematik" lp_biovftiereartsystematik NOT NULL, 
    "bioVfTiereSystematikText" VARCHAR, 
    "bioVfTierArtRechtlicherSchutz" lp_biovftierartrechtlicherschutz[], 
    "bioVfTierArtRechtlicherSchutzText" VARCHAR, 
    "bioVfTierArtHabitatanforderung" lp_biovftierarthabitatanforderung, 
    "bioVfTierArtHabitatanforderungText" VARCHAR, 
    biologische_vielfalt_komplex_id UUID, 
    CONSTRAINT pk_lp_bio_vf_tiere_art_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_bio_vf_tiere_art_komplex_biologische_vielfalt_kom_9011 FOREIGN KEY(biologische_vielfalt_komplex_id) REFERENCES lp_biologische_vielfalt_komplex (id) ON DELETE CASCADE
);

CREATE TYPE lp_biovfbestandteil AS ENUM ('Art', 'BiotopLebensraum', 'LebensstaetteArthabitat', 'Sonstiges');

CREATE TABLE lp_biologische_vielfalt_typ_komplex (
    id UUID NOT NULL, 
    "bioVielfaltTyp" lp_biovfbestandteil NOT NULL, 
    "bioVielfaltTypText" VARCHAR, 
    biologische_vielfalt_komplex_id UUID, 
    CONSTRAINT pk_lp_biologische_vielfalt_typ_komplex PRIMARY KEY (id), 
    CONSTRAINT fk_lp_biologische_vielfalt_typ_komplex_biologische_viel_c200 FOREIGN KEY(biologische_vielfalt_komplex_id) REFERENCES lp_biologische_vielfalt_komplex (id) ON DELETE CASCADE
);

ALTER TABLE codelist_values ADD COLUMN key VARCHAR;

ALTER TABLE xp_po ADD COLUMN darstellungsprioritaet INTEGER;

ALTER TABLE xp_po ADD COLUMN art VARCHAR[];

ALTER TABLE xp_po ADD COLUMN index INTEGER[];

UPDATE alembic_version SET version_num='31058f6befbd' WHERE alembic_version.version_num = 'e9b38a472653'; --- # pragma: allowlist secret;

-- Running upgrade 31058f6befbd -> da3841c7f8d9

ALTER TABLE xp_po ADD COLUMN "stylesheetId" VARCHAR;

DELETE FROM xp_po p
        WHERE EXISTS (
            SELECT 1
            FROM xp_nutzungsschablone n
            WHERE n.id = p.id
              AND n.hidden = true
        );

CREATE TYPE so_klassifiznachbodenschutzrecht AS ENUM ('SchaedlicheBodenveraenderung', 'Altlast', 'Altablagerung', 'Altstandort', 'AltstandortAufAltablagerung');

CREATE TABLE so_bodenschutz (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachbodenschutzrecht, 
    "detailArtDerFestlegung_id" UUID, 
    "istVerdachtsflaeche" BOOLEAN, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_bodenschutz PRIMARY KEY (id), 
    CONSTRAINT "fk_so_bodenschutz_detailArtDerFestlegung_id_codelist_values" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_bodenschutz_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmungwasserwirtschaft AS ENUM ('HochwasserRueckhaltebecken', 'Ueberschwemmgebiet', 'Versickerungsflaeche', 'Entwaesserungsgraben', 'Deich', 'RegenRueckhaltebecken', 'Sonstiges');

CREATE TABLE fp_wasserwirtschaft (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungwasserwirtschaft, 
    CONSTRAINT pk_fp_wasserwirtschaft PRIMARY KEY (id), 
    CONSTRAINT fk_fp_wasserwirtschaft_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE bp_nebenanlagenausschlusstyp AS ENUM ('Einschraenkung', 'Ausschluss');

CREATE TABLE bp_nebenanlagen_ausschluss_flaeche (
    id UUID NOT NULL, 
    typ bp_nebenanlagenausschlusstyp, 
    CONSTRAINT pk_bp_nebenanlagen_ausschluss_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_nebenanlagen_ausschluss_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE bp_typwohngebaeudeflaeche AS ENUM ('Wohngebaeude', 'GebaeudeFoerderung', 'GebaeudeStaedtebaulicherVertrag');

CREATE TABLE bp_wohngebaeude_flaeche (
    id UUID NOT NULL, 
    "FR" INTEGER, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    "wohnnutzungEGStrasse" bp_zulaessigkeit, 
    "ZWohn" INTEGER, 
    "GFAntWohnen" FLOAT, 
    "GFWohnen" FLOAT, 
    "GFAntGewerbe" FLOAT, 
    "GFGewerbe" FLOAT, 
    "VF" FLOAT, 
    typ bp_typwohngebaeudeflaeche NOT NULL, 
    "abweichungBauNVO" xp_abweichungbaunvotypen, 
    bauweise bp_bauweise, 
    "vertikaleDifferenzierung" BOOLEAN, 
    "bebauungsArt" bp_bebauungsart, 
    "bebauungVordereGrenze" bp_grenzbebauung, 
    "bebauungRueckwaertigeGrenze" bp_grenzbebauung, 
    "bebauungSeitlicheGrenze" bp_grenzbebauung, 
    "zugunstenVon" VARCHAR, 
    CONSTRAINT pk_bp_wohngebaeude_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_wohngebaeude_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE xp_text_abschnitt (
    id UUID NOT NULL, 
    type VARCHAR, 
    schluessel VARCHAR, 
    "gesetzlicheGrundlage" VARCHAR, 
    text VARCHAR, 
    rechtscharakter xp_rechtscharakter NOT NULL, 
    xp_bereich_id UUID, 
    xp_objekt_id UUID, 
    xp_plan_id UUID, 
    bp_objekt_id UUID, 
    fp_objekt_id UUID, 
    bp_baugebiet_id UUID, 
    bp_nebenanlagen_ausschluss_flaeche_id UUID, 
    bp_wohngebaeude_flaeche_id UUID, 
    CONSTRAINT pk_xp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_xp_text_abschnitt_bp_baugebiet_id_bp_baugebiet FOREIGN KEY(bp_baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_bp_nebenanlagen_ausschluss_flaeche_c966 FOREIGN KEY(bp_nebenanlagen_ausschluss_flaeche_id) REFERENCES bp_nebenanlagen_ausschluss_flaeche (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_bp_objekt_id_bp_objekt FOREIGN KEY(bp_objekt_id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_bp_wohngebaeude_flaeche_id_bp_wohn_af37 FOREIGN KEY(bp_wohngebaeude_flaeche_id) REFERENCES bp_wohngebaeude_flaeche (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_fp_objekt_id_fp_objekt FOREIGN KEY(fp_objekt_id) REFERENCES fp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_xp_bereich_id_xp_bereich FOREIGN KEY(xp_bereich_id) REFERENCES xp_bereich (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_xp_objekt_id_xp_objekt FOREIGN KEY(xp_objekt_id) REFERENCES xp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_xp_plan_id_xp_plan FOREIGN KEY(xp_plan_id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE bp_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter bp_rechtscharakter NOT NULL, 
    bp_baugebiet_id UUID, 
    bp_nebenanlagen_ausschluss_flaeche_id UUID, 
    CONSTRAINT pk_bp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_bp_text_abschnitt_bp_baugebiet_id_bp_baugebiet FOREIGN KEY(bp_baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_text_abschnitt_bp_nebenanlagen_ausschluss_flaeche_9bda FOREIGN KEY(bp_nebenanlagen_ausschluss_flaeche_id) REFERENCES bp_nebenanlagen_ausschluss_flaeche (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

CREATE TABLE fp_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter fp_rechtscharakter NOT NULL, 
    CONSTRAINT pk_fp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_fp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

CREATE TYPE lp_rechtscharakter AS ENUM ('Festsetzung', 'Geplant', 'NachrichtlicheUebernahme', 'DarstellungKennzeichnung', 'FestsetzungInBPlan', 'Unbekannt', 'SonstigerStatus');

CREATE TABLE lp_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter lp_rechtscharakter NOT NULL, 
    CONSTRAINT pk_lp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_lp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

CREATE TYPE rp_rechtscharakter AS ENUM ('ZielDerRaumordnung', 'GrundsatzDerRaumordnung', 'NachrichtlicheUebernahme', 'NachrichtlicheUebernahmeZiel', 'NachrichtlicheUebernahmeGrundsatz', 'NurInformationsgehalt', 'TextlichesZiel', 'ZielundGrundsatz', 'Vorschlag', 'Unbekannt');

CREATE TABLE rp_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter rp_rechtscharakter NOT NULL, 
    CONSTRAINT pk_rp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_rp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

CREATE TABLE so_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter so_rechtscharakter NOT NULL, 
    CONSTRAINT pk_so_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_so_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

ALTER TABLE bp_dachgestaltung ADD COLUMN bp_wohngebaeude_flaeche_id UUID;

ALTER TABLE bp_dachgestaltung ADD CONSTRAINT fk_bp_dachgestaltung_bp_wohngebaeude_flaeche_id_bp_wohn_7fa5 FOREIGN KEY(bp_wohngebaeude_flaeche_id) REFERENCES bp_wohngebaeude_flaeche (id) ON DELETE CASCADE;

ALTER TABLE lp_ziele_erfordernisse_massnahmen RENAME "artDerFestlegung" TO "zieleErfordernisseMassnahmen";

ALTER TABLE xp_externe_referenz ADD COLUMN xp_text_abschnitt_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_wohngebaeude_flaeche_id UUID;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_wohngebaeude_flaeche_id_bp_wo_3bdf FOREIGN KEY(bp_wohngebaeude_flaeche_id) REFERENCES bp_wohngebaeude_flaeche (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_xp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(xp_text_abschnitt_id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE;

ALTER TABLE xp_nutzungsschablone DROP COLUMN hidden;

CREATE TABLE xp_plan_gesetzlichegrundlage (
    bp_plan_id UUID, 
    fp_plan_id UUID, 
    gesetzlichegrundlage_id UUID NOT NULL, 
    CONSTRAINT fk_xp_plan_gesetzlichegrundlage_bp_plan_id_bp_plan FOREIGN KEY(bp_plan_id) REFERENCES bp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_plan_gesetzlichegrundlage_fp_plan_id_fp_plan FOREIGN KEY(fp_plan_id) REFERENCES fp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_plan_gesetzlichegrundlage_gesetzlichegrundlage_id_eafa FOREIGN KEY(gesetzlichegrundlage_id) REFERENCES xp_gesetzliche_grundlage (id)
);

INSERT INTO xp_plan_gesetzlichegrundlage (bp_plan_id, gesetzlichegrundlage_id)
        SELECT id, "versionSonstRechtsgrundlage_id"
        FROM bp_plan
        WHERE "versionSonstRechtsgrundlage_id" IS NOT NULL;;

INSERT INTO xp_plan_gesetzlichegrundlage (fp_plan_id, gesetzlichegrundlage_id)
        SELECT id, "versionSonstRechtsgrundlage_id"
        FROM fp_plan
        WHERE "versionSonstRechtsgrundlage_id" IS NOT NULL;;

ALTER TABLE bp_plan DROP COLUMN "versionSonstRechtsgrundlage_id";

ALTER TABLE fp_plan DROP COLUMN "versionSonstRechtsgrundlage_id";

ALTER TYPE xp_abemassnahmentypen ADD VALUE IF NOT EXISTS 'AnpflanzungBindungErhaltung';;

UPDATE alembic_version SET version_num='da3841c7f8d9' WHERE alembic_version.version_num = '31058f6befbd'; --- # pragma: allowlist secret;

-- Running upgrade da3841c7f8d9 -> 98624e3008ab

ALTER TABLE bp_plan ALTER "planArt" type bp_planart[] using ARRAY["planArt"];

ALTER TABLE bp_baugebiet ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_gemeinbedarf ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_wohngebaeude_flaeche ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_besondere_nutzung ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_grundstueck_ueberbaubar ALTER COLUMN "FR" TYPE FLOAT USING "FR"::float;;

ALTER TABLE bp_dachgestaltung ALTER COLUMN "DNmin" TYPE FLOAT USING "DNmin"::float;;

ALTER TABLE bp_dachgestaltung ALTER COLUMN "DNmax" TYPE FLOAT USING "DNmax"::float;;

ALTER TABLE bp_dachgestaltung ALTER COLUMN "DN" TYPE FLOAT USING "DN"::float;;

ALTER TABLE bp_dachgestaltung ALTER COLUMN "DNZwingend" TYPE FLOAT USING "DNZwingend"::float;;

ALTER TABLE lp_objekt ALTER COLUMN nordwinkel TYPE FLOAT USING nordwinkel::float;;

ALTER TABLE bp_plan ADD CONSTRAINT ck_planart_not_empty_no_nulls CHECK ("planArt" <> '{}' and array_position("planArt", null) is null);;

UPDATE alembic_version SET version_num='98624e3008ab' WHERE alembic_version.version_num = 'da3841c7f8d9'; --- # pragma: allowlist secret;

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

-- Running upgrade 2b1452b49cc5 -> 250637cd31df

CREATE TYPE xp_grenzetypen AS ENUM ('Bundesgrenze', 'Landesgrenze', 'Regierungsbezirksgrenze', 'Bezirksgrenze', 'Kreisgrenze', 'Gemeindegrenze', 'Verbandsgemeindegrenze', 'Samtgemeindegrenze', 'Mitgliedsgemeindegrenze', 'Amtsgrenze', 'Stadtteilgrenze', 'VorgeschlageneGrundstuecksgrenze', 'GrenzeBestehenderBebauungsplan', 'SonstGrenze');

CREATE TYPE so_klassifizgelaendemorphologie AS ENUM ('Terassenkante', 'Rinne', 'EhemMaeander', 'SonstigeStruktur');

CREATE TYPE so_klassifizschutzgebietsonstrecht AS ENUM ('Laermschutzbereich', 'SchutzzoneLeitungstrasse', 'Sonstiges');

CREATE TYPE so_rechtsstandgebiettyp AS ENUM ('VorbereitendeUntersuchung', 'Aufstellung', 'Festlegung', 'Abgeschlossen', 'Verstetigung', 'Sonstiges');

CREATE TYPE so_gebietsart AS ENUM ('Umlegungsgebiet', 'StaedtebaulicheSanierung', 'StaedtebaulicheEntwicklungsmassnahme', 'Stadtumbaugebiet', 'SozialeStadt', 'BusinessImprovementDistrict', 'HousingImprovementDistrict', 'Erhaltungsverordnung', 'ErhaltungsverordnungStaedtebaulicheGestalt', 'ErhaltungsverordnungWohnbevoelkerung', 'ErhaltungsverordnungUmstrukturierung', 'Erhaltungsgebiet', 'ErhaltungsgebietStaedtebaulicheGestalt', 'ErhaltungsgebietWohnbevoelkerung', 'ErhaltungsgebietUmstrukturierung', 'StaedtebaulEntwicklungskonzeptInnenentwicklung', 'GebietMitAngespanntemWohnungsmarkt', 'GenehmigungWohnungseigentum', 'Sonstiges');

CREATE TYPE so_rechtlichegrundlagebaubeschraenkung AS ENUM ('Luftverkehrsrecht', 'Strassenverkehrsrecht', 'SonstigesRecht');

CREATE TYPE so_klassifizbaubeschraenkung AS ENUM ('Bauverbotszone', 'Baubeschraenkungszone', 'Waldabstand', 'SonstigeBeschraenkung');

CREATE TYPE so_rechtlichegrundlagebauverbot AS ENUM ('Luftverkehrsrecht', 'Strassenverkehrsrecht', 'SonstigesRecht');

CREATE TYPE so_klassifizbauverbot AS ENUM ('Bauverbotszone', 'Baubeschraenkungszone', 'Waldabstand', 'SonstigeBeschraenkung');

CREATE TYPE fp_massnahmeklimawandeltypen AS ENUM ('ErhaltFreiflaechen', 'ErhaltPrivGruen', 'ErhaltOeffentlGruen', 'ErhaltKaltluftschneise', 'SonstMassnahme');

CREATE TYPE bp_zweckbestimmungentmf AS ENUM ('Luftreinhaltung', 'NutzungErneurerbarerEnergien', 'MinderungStoerfallfolgen');

CREATE TYPE bp_abstandsmasstypen AS ENUM ('Masspfeil', 'Masskreis');

CREATE TYPE bp_schallleistungspegelberechnungsgrundlage AS ENUM ('DIN45691', 'DIN18005', 'VDI2714', 'ISO9613_2');

CREATE TYPE bp_schallleistungspegeltypen AS ENUM ('LEK', 'IFSP', 'FSP');

CREATE TYPE bp_gebaeudestellungtypen AS ENUM ('Firstrichtung', 'Dachneigungsrichtung', 'StellungBaulAnlagen');

CREATE TYPE bp_speziellebauweisetypen AS ENUM ('Durchfahrt', 'Durchgang', 'DurchfahrtDurchgang', 'Auskragung', 'Arkade', 'Luftgeschoss', 'Bruecke', 'Tunnel', 'Rampe', 'Sonstiges');

CREATE TYPE bp_zweckbestimmunggemeinschaftsanlagen AS ENUM ('Gemeinschaftsstellplaetze', 'Gemeinschaftsgaragen', 'Spielplatz', 'Carport', 'GemeinschaftsTiefgarage', 'Nebengebaeude', 'AbfallSammelanlagen', 'EnergieVerteilungsanlagen', 'AbfallWertstoffbehaelter', 'Freizeiteinrichtungen', 'Laermschutzanlagen', 'AbwasserRegenwasser', 'Ausgleichsmassnahmen', 'Fahrradstellplaetze', 'Gemeinschaftsdachgaerten', 'GemeinschaftlichNutzbareDachflaechen', 'Sonstiges');

CREATE TABLE bp_abstand (
    id UUID NOT NULL, 
    tiefe FLOAT, 
    CONSTRAINT pk_bp_abstand PRIMARY KEY (id), 
    CONSTRAINT fk_bp_abstand_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_abstands_mass (
    id UUID NOT NULL, 
    typ bp_abstandsmasstypen, 
    wert FLOAT, 
    "startWinkel" FLOAT, 
    "endWinkel" FLOAT, 
    CONSTRAINT pk_bp_abstands_mass PRIMARY KEY (id), 
    CONSTRAINT fk_bp_abstands_mass_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_abweichung_baugrenze (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_abweichung_baugrenze PRIMARY KEY (id), 
    CONSTRAINT fk_bp_abweichung_baugrenze_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_abweichung_ueberbaubare_grundstuecksflaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_abweichung_ueberbaubare_grundstuecksflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_abweichung_ueberbaubare_grundstuecksflaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_ausgleich (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    CONSTRAINT pk_bp_ausgleich PRIMARY KEY (id), 
    CONSTRAINT fk_bp_ausgleich_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_ausgleichsmassnahme (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    CONSTRAINT pk_bp_ausgleichsmassnahme PRIMARY KEY (id), 
    CONSTRAINT fk_bp_ausgleichsmassnahme_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_einfahrtsbereich (
    id UUID NOT NULL, 
    typ bp_einfahrttypen, 
    CONSTRAINT pk_bp_einfahrtsbereich PRIMARY KEY (id), 
    CONSTRAINT fk_bp_einfahrtsbereich_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_eingriffsbereich (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_eingriffsbereich PRIMARY KEY (id), 
    CONSTRAINT fk_bp_eingriffsbereich_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_emissionskontingent_laerm (
    id UUID NOT NULL, 
    type VARCHAR(50), 
    "pegelTyp" bp_schallleistungspegeltypen, 
    berechnungsgrundlage bp_schallleistungspegelberechnungsgrundlage, 
    "berechnungsgrundlageDatum" DATE, 
    "ekwertTag" FLOAT NOT NULL, 
    "ekwertNacht" FLOAT NOT NULL, 
    erlaeuterung VARCHAR, 
    bp_objekt_id UUID, 
    so_objekt_id UUID, 
    bp_objekt_gebiet_id UUID, 
    so_objekt_gebiet_id UUID, 
    CONSTRAINT pk_bp_emissionskontingent_laerm PRIMARY KEY (id), 
    CONSTRAINT fk_bp_emissionskontingent_laerm_bp_objekt_gebiet_id_bp_objekt FOREIGN KEY(bp_objekt_gebiet_id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_emissionskontingent_laerm_bp_objekt_id_bp_objekt FOREIGN KEY(bp_objekt_id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_emissionskontingent_laerm_so_objekt_gebiet_id_so_objekt FOREIGN KEY(so_objekt_gebiet_id) REFERENCES so_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_emissionskontingent_laerm_so_objekt_id_so_objekt FOREIGN KEY(so_objekt_id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_festsetzung_landesrecht (
    id UUID NOT NULL, 
    kurzbeschreibung VARCHAR, 
    CONSTRAINT pk_bp_festsetzung_landesrecht PRIMARY KEY (id), 
    CONSTRAINT fk_bp_festsetzung_landesrecht_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_freiflaeche (
    id UUID NOT NULL, 
    nutzung VARCHAR, 
    CONSTRAINT pk_bp_freiflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_freiflaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_gebaeude_flaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_gebaeude_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_gebaeude_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_gebaeude_stellung (
    id UUID NOT NULL, 
    typ bp_gebaeudestellungtypen NOT NULL, 
    CONSTRAINT pk_bp_gebaeude_stellung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_gebaeude_stellung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_gemeinschaftsanlage (
    id UUID NOT NULL, 
    zweckbestimmung bp_zweckbestimmunggemeinschaftsanlagen[], 
    "Zmax" INTEGER, 
    CONSTRAINT pk_bp_gemeinschaftsanlage PRIMARY KEY (id), 
    CONSTRAINT fk_bp_gemeinschaftsanlage_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_hoehen_mass (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_hoehen_mass PRIMARY KEY (id), 
    CONSTRAINT fk_bp_hoehen_mass_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_kleintierhaltung (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_kleintierhaltung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_kleintierhaltung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_nicht_ueberbaubare_grundstuecksflaeche (
    id UUID NOT NULL, 
    nutzung_id UUID, 
    CONSTRAINT pk_bp_nicht_ueberbaubare_grundstuecksflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_nicht_ueberbaubare_grundstuecksflaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_nicht_ueberbaubare_grundstuecksflaeche_nutzung_id_5738 FOREIGN KEY(nutzung_id) REFERENCES codelist_values (id)
);

CREATE TABLE bp_persgruppen_bestimmte_flaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_persgruppen_bestimmte_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_persgruppen_bestimmte_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_regelung_vergnuegungsstaetten (
    id UUID NOT NULL, 
    zulaessigkeit bp_zulaessigkeit, 
    CONSTRAINT pk_bp_regelung_vergnuegungsstaetten PRIMARY KEY (id), 
    CONSTRAINT fk_bp_regelung_vergnuegungsstaetten_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_richtungssektorgrenze (
    id UUID NOT NULL, 
    winkel FLOAT, 
    CONSTRAINT pk_bp_richtungssektorgrenze PRIMARY KEY (id), 
    CONSTRAINT fk_bp_richtungssektorgrenze_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_spezielle_bauweise (
    id UUID NOT NULL, 
    typ bp_speziellebauweisetypen, 
    "sonstTyp_id" UUID, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    CONSTRAINT pk_bp_spezielle_bauweise PRIMARY KEY (id), 
    CONSTRAINT fk_bp_spezielle_bauweise_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT "fk_bp_spezielle_bauweise_sonstTyp_id_codelist_values" FOREIGN KEY("sonstTyp_id") REFERENCES codelist_values (id)
);

CREATE TABLE bp_technische_massnahmen (
    id UUID NOT NULL, 
    zweckbestimmung bp_zweckbestimmungentmf NOT NULL, 
    "technischeMassnahme" VARCHAR, 
    CONSTRAINT pk_bp_technische_massnahmen PRIMARY KEY (id), 
    CONSTRAINT fk_bp_technische_massnahmen_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_unverbindliche_vormerkung (
    id UUID NOT NULL, 
    vormerkung VARCHAR, 
    CONSTRAINT pk_bp_unverbindliche_vormerkung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_unverbindliche_vormerkung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zentraler_versorgungsbereich (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_zentraler_versorgungsbereich PRIMARY KEY (id), 
    CONSTRAINT fk_bp_zentraler_versorgungsbereich_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zusatzkontingent_laerm (
    id UUID NOT NULL, 
    bezeichnung VARCHAR, 
    CONSTRAINT pk_bp_zusatzkontingent_laerm PRIMARY KEY (id), 
    CONSTRAINT fk_bp_zusatzkontingent_laerm_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zusatzkontingent_laerm_flaeche (
    id UUID NOT NULL, 
    bezeichnung VARCHAR, 
    CONSTRAINT pk_bp_zusatzkontingent_laerm_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_zusatzkontingent_laerm_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_anpassung_klimawandel (
    id UUID NOT NULL, 
    massnahme fp_massnahmeklimawandeltypen, 
    "detailMassnahme_id" UUID, 
    CONSTRAINT pk_fp_anpassung_klimawandel PRIMARY KEY (id), 
    CONSTRAINT "fk_fp_anpassung_klimawandel_detailMassnahme_id_codelist_values" FOREIGN KEY("detailMassnahme_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_fp_anpassung_klimawandel_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_ausgleich (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    CONSTRAINT pk_fp_ausgleich PRIMARY KEY (id), 
    CONSTRAINT fk_fp_ausgleich_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_darstellung_landesrecht (
    id UUID NOT NULL, 
    kurzbeschreibung VARCHAR, 
    CONSTRAINT pk_fp_darstellung_landesrecht PRIMARY KEY (id), 
    CONSTRAINT fk_fp_darstellung_landesrecht_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_keine_zentr_abwasser_beseitigung (
    id UUID NOT NULL, 
    CONSTRAINT pk_fp_keine_zentr_abwasser_beseitigung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_keine_zentr_abwasser_beseitigung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_textabschnittsflaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_fp_textabschnittsflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_fp_textabschnittsflaeche_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_textliche_darstellungsflaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_fp_textliche_darstellungsflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_fp_textliche_darstellungsflaeche_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_unverbindliche_vormerkung (
    id UUID NOT NULL, 
    vormerkung VARCHAR, 
    CONSTRAINT pk_fp_unverbindliche_vormerkung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_unverbindliche_vormerkung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_vorbehalte_flaeche (
    id UUID NOT NULL, 
    vorbehalt VARCHAR, 
    CONSTRAINT pk_fp_vorbehalte_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_fp_vorbehalte_flaeche_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_zentraler_versorgungsbereich (
    id UUID NOT NULL, 
    auspraegung_id UUID, 
    CONSTRAINT pk_fp_zentraler_versorgungsbereich PRIMARY KEY (id), 
    CONSTRAINT fk_fp_zentraler_versorgungsbereich_auspraegung_id_codel_1d3e FOREIGN KEY(auspraegung_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_fp_zentraler_versorgungsbereich_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_baubeschraenkung (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizbaubeschraenkung, 
    "detailArtDerFestlegung_id" UUID, 
    "rechtlicheGrundlage" so_rechtlichegrundlagebaubeschraenkung, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_baubeschraenkung PRIMARY KEY (id), 
    CONSTRAINT "fk_so_baubeschraenkung_detailArtDerFestlegung_id_codeli_6cb9" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_baubeschraenkung_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_bauverbotszone (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizbauverbot, 
    "detailArtDerFestlegung_id" UUID, 
    "rechtlicheGrundlage" so_rechtlichegrundlagebauverbot, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_bauverbotszone PRIMARY KEY (id), 
    CONSTRAINT "fk_so_bauverbotszone_detailArtDerFestlegung_id_codelist_values" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_bauverbotszone_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_forstrecht (
    id UUID NOT NULL, 
    "artDerFestlegung" xp_eigentumsartwald, 
    "detailArtDerFestlegung_id" UUID, 
    funktion xp_zweckbestimmungwald[], 
    betreten xp_waldbetretungtyp[], 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_forstrecht PRIMARY KEY (id), 
    CONSTRAINT "fk_so_forstrecht_detailArtDerFestlegung_id_codelist_values" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_forstrecht_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_gebiet (
    id UUID NOT NULL, 
    gemeinde_id UUID, 
    "gebietsArt" so_gebietsart, 
    "sonstGebietsArt_id" UUID, 
    "rechtsstandGebiet" so_rechtsstandgebiettyp, 
    "sonstRechtsstandGebiet_id" UUID, 
    "aufstellungsbeschhlussDatum" DATE, 
    "durchfuehrungStartDatum" DATE, 
    "durchfuehrungEndDatum" DATE, 
    "traegerMassnahme" VARCHAR, 
    CONSTRAINT pk_so_gebiet PRIMARY KEY (id), 
    CONSTRAINT fk_so_gebiet_gemeinde_id_xp_gemeinde FOREIGN KEY(gemeinde_id) REFERENCES xp_gemeinde (id), 
    CONSTRAINT fk_so_gebiet_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT "fk_so_gebiet_sonstGebietsArt_id_codelist_values" FOREIGN KEY("sonstGebietsArt_id") REFERENCES codelist_values (id), 
    CONSTRAINT "fk_so_gebiet_sonstRechtsstandGebiet_id_codelist_values" FOREIGN KEY("sonstRechtsstandGebiet_id") REFERENCES codelist_values (id)
);

CREATE TABLE so_gelaendemorphologie (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizgelaendemorphologie, 
    "detailArtDerFestlegung_id" UUID, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_gelaendemorphologie PRIMARY KEY (id), 
    CONSTRAINT "fk_so_gelaendemorphologie_detailArtDerFestlegung_id_cod_b142" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_gelaendemorphologie_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_grenze (
    id UUID NOT NULL, 
    typ xp_grenzetypen, 
    "sonstTyp_id" UUID, 
    CONSTRAINT pk_so_grenze PRIMARY KEY (id), 
    CONSTRAINT fk_so_grenze_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT "fk_so_grenze_sonstTyp_id_codelist_values" FOREIGN KEY("sonstTyp_id") REFERENCES codelist_values (id)
);

CREATE TABLE so_schutzgebiet_sonstiges_recht (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizschutzgebietsonstrecht, 
    "detailArtDerFestlegung_id" UUID, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_schutzgebiet_sonstiges_recht PRIMARY KEY (id), 
    CONSTRAINT "fk_so_schutzgebiet_sonstiges_recht_detailArtDerFestlegu_d8e3" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_schutzgebiet_sonstiges_recht_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_landesrecht (
    codelist_user_id UUID, 
    codelist_id UUID, 
    CONSTRAINT fk_assoc_detail_landesrecht_codelist_id_codelist_values FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_assoc_detail_landesrecht_codelist_user_id_fp_darstel_7892 FOREIGN KEY(codelist_user_id) REFERENCES fp_darstellung_landesrecht (id) ON DELETE CASCADE
);

CREATE TABLE assoc_gemeinschaftsanlage_eigentuemer (
    gemeinschaftsanlage_id UUID, 
    baugebiet_id UUID, 
    CONSTRAINT fk_assoc_gemeinschaftsanlage_eigentuemer_baugebiet_id_b_9338 FOREIGN KEY(baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE, 
    CONSTRAINT fk_assoc_gemeinschaftsanlage_eigentuemer_gemeinschaftsa_227e FOREIGN KEY(gemeinschaftsanlage_id) REFERENCES bp_gemeinschaftsanlage (id) ON DELETE CASCADE
);

CREATE TABLE bp_emissionskontingent_laerm_gebiet (
    id UUID NOT NULL, 
    gebietsbezeichnung VARCHAR, 
    CONSTRAINT pk_bp_emissionskontingent_laerm_gebiet PRIMARY KEY (id), 
    CONSTRAINT fk_bp_emissionskontingent_laerm_gebiet_id_bp_emissionsk_2164 FOREIGN KEY(id) REFERENCES bp_emissionskontingent_laerm (id) ON DELETE CASCADE
);

CREATE TABLE bp_richtungssektor (
    id UUID NOT NULL, 
    "winkelAnfang" FLOAT NOT NULL, 
    "winkelEnde" FLOAT NOT NULL, 
    "zkWertTag" FLOAT NOT NULL, 
    "zkWertNacht" FLOAT NOT NULL, 
    zusatzkontingent_id UUID, 
    "zusatzkontingentFlaeche_id" UUID, 
    CONSTRAINT pk_bp_richtungssektor PRIMARY KEY (id), 
    CONSTRAINT "fk_bp_richtungssektor_zusatzkontingentFlaeche_id_bp_zus_df43" FOREIGN KEY("zusatzkontingentFlaeche_id") REFERENCES bp_zusatzkontingent_laerm_flaeche (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_richtungssektor_zusatzkontingent_id_bp_zusatzkont_1130 FOREIGN KEY(zusatzkontingent_id) REFERENCES bp_zusatzkontingent_laerm (id) ON DELETE CASCADE
);

CREATE TABLE bp_veraenderungssperre (
    id UUID NOT NULL, 
    "veraenderungssperreBeschlussDatum" DATE, 
    "veraenderungssperreStartDatum" DATE, 
    "gueltigkeitsDatum" DATE, 
    verlaengerung xp_verlaengerungveraenderungssperre, 
    daten_id UUID, 
    CONSTRAINT pk_bp_veraenderungssperre PRIMARY KEY (id), 
    CONSTRAINT fk_bp_veraenderungssperre_daten_id_bp_veraenderungssperre_daten FOREIGN KEY(daten_id) REFERENCES bp_veraenderungssperre_daten (id), 
    CONSTRAINT fk_bp_veraenderungssperre_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zweckbestimmung_gemeinschaftsanlage (
    id UUID NOT NULL, 
    allgemein bp_zweckbestimmunggemeinschaftsanlagen NOT NULL, 
    "textlicheErgaenzung" VARCHAR, 
    aufschrift VARCHAR, 
    gemeinschaftsanlage_id UUID, 
    CONSTRAINT pk_bp_zweckbestimmung_gemeinschaftsanlage PRIMARY KEY (id), 
    CONSTRAINT fk_bp_zweckbestimmung_gemeinschaftsanlage_gemeinschafts_2620 FOREIGN KEY(gemeinschaftsanlage_id) REFERENCES bp_gemeinschaftsanlage (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_gemeinschaftsanlagen (
    codelist_user_id UUID, 
    codelist_user_v6_id UUID, 
    codelist_id UUID, 
    CONSTRAINT fk_assoc_detail_gemeinschaftsanlagen_codelist_id_codeli_2331 FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_assoc_detail_gemeinschaftsanlagen_codelist_user_id_b_bf8b FOREIGN KEY(codelist_user_id) REFERENCES bp_gemeinschaftsanlage (id) ON DELETE CASCADE, 
    CONSTRAINT fk_assoc_detail_gemeinschaftsanlagen_codelist_user_v6_i_96d6 FOREIGN KEY(codelist_user_v6_id) REFERENCES bp_zweckbestimmung_gemeinschaftsanlage (id) ON DELETE CASCADE
);

ALTER TABLE bp_baugebiet ALTER COLUMN "GFAntWohnen" TYPE FLOAT;

ALTER TABLE bp_baugebiet ALTER COLUMN "GFAntGewerbe" TYPE FLOAT;

ALTER TABLE bp_grundstueck_ueberbaubar ALTER COLUMN "GFAntWohnen" TYPE FLOAT;

ALTER TABLE bp_grundstueck_ueberbaubar ALTER COLUMN "GFAntGewerbe" TYPE FLOAT;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_ausgleichsflaeche_massnahme_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_ausgleichsflaeche_plan_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN fp_ausgleichsflaeche_massnahme_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN fp_ausgleichsflaeche_plan_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_ausgleichsmassnahme_massnahme_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_ausgleichsmassnahme_plan_id UUID;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_ausgleichsflaeche_plan_id_bp__f2fd FOREIGN KEY(bp_ausgleichsflaeche_plan_id) REFERENCES bp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_fp_ausgleichsflaeche_massnahme_i_94c0 FOREIGN KEY(fp_ausgleichsflaeche_massnahme_id) REFERENCES fp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_ausgleichsmassnahme_plan_id_b_d19f FOREIGN KEY(bp_ausgleichsmassnahme_plan_id) REFERENCES bp_ausgleichsmassnahme (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_ausgleichsflaeche_massnahme_i_076a FOREIGN KEY(bp_ausgleichsflaeche_massnahme_id) REFERENCES bp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_ausgleichsmassnahme_massnahme_4aaa FOREIGN KEY(bp_ausgleichsmassnahme_massnahme_id) REFERENCES bp_ausgleichsmassnahme (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_fp_ausgleichsflaeche_plan_id_fp__bedf FOREIGN KEY(fp_ausgleichsflaeche_plan_id) REFERENCES fp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz DROP COLUMN "referenzMimeType";

ALTER TABLE xp_spe_daten ADD COLUMN bp_ausgleichsflaeche_id UUID;

ALTER TABLE xp_spe_daten ADD COLUMN bp_ausgleichsmassnahme_id UUID;

ALTER TABLE xp_spe_daten ADD COLUMN fp_ausgleichsflaeche_id UUID;

ALTER TABLE xp_spe_daten ADD CONSTRAINT fk_xp_spe_daten_bp_ausgleichsflaeche_id_bp_ausgleich FOREIGN KEY(bp_ausgleichsflaeche_id) REFERENCES bp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_spe_daten ADD CONSTRAINT fk_xp_spe_daten_bp_ausgleichsmassnahme_id_bp_ausgleichs_3c4c FOREIGN KEY(bp_ausgleichsmassnahme_id) REFERENCES bp_ausgleichsmassnahme (id) ON DELETE CASCADE;

ALTER TABLE xp_spe_daten ADD CONSTRAINT fk_xp_spe_daten_fp_ausgleichsflaeche_id_fp_ausgleich FOREIGN KEY(fp_ausgleichsflaeche_id) REFERENCES fp_ausgleich (id) ON DELETE CASCADE;

DROP TYPE xp_mime_types;

ALTER TABLE fp_objekt ADD COLUMN flussrichtung BOOLEAN;

ALTER TABLE fp_objekt ADD COLUMN nordwinkel FLOAT;

ALTER TABLE bp_objekt ADD COLUMN flussrichtung BOOLEAN;

ALTER TABLE bp_objekt ADD COLUMN nordwinkel FLOAT;

ALTER TABLE assoc_detail_sondernutzung ADD COLUMN bp_baugebiet_id UUID;

ALTER TABLE assoc_detail_sondernutzung ADD CONSTRAINT fk_assoc_detail_sondernutzung_bp_baugebiet_id_bp_baugebiet FOREIGN KEY(bp_baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE;

ALTER TABLE assoc_detail_sondernutzung DROP CONSTRAINT IF EXISTS assoc_detail_sondernutzung_pkey;;

ALTER TABLE assoc_detail_sondernutzung ALTER COLUMN codelist_user_id DROP NOT NULL;;

DROP TRIGGER IF EXISTS bp_gemeinbedarf_sync_attr_zweckbestimmung ON bp_gemeinbedarf;

DROP TRIGGER IF EXISTS bp_gemeinbedarf_sync_attr_zweckbestimmung ON bp_zweckbestimmung_gemeinbedarf;

ALTER TABLE bp_gemeinbedarf
        ALTER COLUMN "zweckbestimmung" TYPE xp_zweckbestimmunggemeinbedarf[]
        USING CASE
            WHEN zweckbestimmung IS NULL THEN NULL
            ELSE ARRAY[zweckbestimmung::xp_zweckbestimmunggemeinbedarf]
        END;;

DROP TRIGGER IF EXISTS bp_gruenflaeche_sync_attr_zweckbestimmung ON bp_gruenflaeche;

DROP TRIGGER IF EXISTS bp_gruenflaeche_sync_attr_zweckbestimmung ON bp_zweckbestimmung_gruen;

ALTER TABLE bp_gruenflaeche
        ALTER COLUMN "zweckbestimmung" TYPE xp_zweckbestimmunggruen[]
        USING CASE
            WHEN zweckbestimmung IS NULL THEN NULL
            ELSE ARRAY [zweckbestimmung::xp_zweckbestimmunggruen]
        END;;

DROP TRIGGER IF EXISTS bp_landwirtschaft_sync_attr_zweckbestimmung ON bp_landwirtschaft;

DROP TRIGGER IF EXISTS bp_landwirtschaft_sync_attr_zweckbestimmung ON bp_zweckbestimmung_landwirtschaft;

ALTER TABLE bp_landwirtschaft
        ALTER COLUMN "zweckbestimmung" TYPE xp_zweckbestimmunglandwirtschaft[]
        USING CASE
            WHEN zweckbestimmung IS NULL THEN NULL
            ELSE ARRAY [zweckbestimmung::xp_zweckbestimmunglandwirtschaft]
        END;;

DROP TRIGGER IF EXISTS bp_wald_sync_attr_zweckbestimmung ON bp_wald;

DROP TRIGGER IF EXISTS bp_wald_sync_attr_zweckbestimmung ON bp_zweckbestimmung_wald;

ALTER TABLE bp_wald
        ALTER COLUMN "zweckbestimmung" TYPE xp_zweckbestimmungwald[]
        USING CASE
            WHEN zweckbestimmung IS NULL THEN NULL
            ELSE ARRAY [zweckbestimmung::xp_zweckbestimmungwald]
        END;;

ALTER TABLE bp_wald
        ALTER COLUMN "betreten" TYPE xp_waldbetretungtyp[]
        USING CASE
            WHEN betreten IS NULL THEN NULL
            WHEN betreten = 'KeineZusaetzlicheBetretung'::xp_waldbetretungtyp THEN NULL
            ELSE ARRAY [betreten::xp_waldbetretungtyp]
        END;;

DROP TRIGGER IF EXISTS bp_versorgung_sync_attr_zweckbestimmung ON bp_versorgung;

DROP TRIGGER IF EXISTS bp_versorgung_sync_attr_zweckbestimmung ON bp_zweckbestimmung_versorgung;

ALTER TABLE bp_versorgung
        ALTER COLUMN "zweckbestimmung" TYPE xp_zweckbestimmungverentsorgung[]
        USING CASE
            WHEN zweckbestimmung IS NULL THEN NULL
            ELSE ARRAY [zweckbestimmung::xp_zweckbestimmungverentsorgung]
        END;;

ALTER TABLE bp_verkehr_besonders
        ALTER COLUMN "zweckbestimmung" TYPE bp_zweckbestimmungstrassenverkehr[]
        USING CASE
            WHEN zweckbestimmung IS NULL THEN NULL
            ELSE ARRAY [zweckbestimmung::bp_zweckbestimmungstrassenverkehr]
        END;;

UPDATE alembic_version SET version_num='250637cd31df' WHERE alembic_version.version_num = '2b1452b49cc5'; --- # pragma: allowlist secret;

COMMIT;

