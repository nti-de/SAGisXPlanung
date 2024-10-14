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
    PRIMARY KEY (id)
);

CREATE INDEX idx_xp_bereich_geltungsbereich ON xp_bereich USING gist (geltungsbereich);

CREATE TABLE xp_gemeinde (
    id UUID NOT NULL, 
    ags VARCHAR, 
    rs VARCHAR, 
    "gemeindeName" VARCHAR NOT NULL, 
    "ortsteilName" VARCHAR, 
    PRIMARY KEY (id)
);

CREATE TABLE xp_plangeber (
    id UUID NOT NULL, 
    name VARCHAR NOT NULL, 
    kennziffer VARCHAR, 
    PRIMARY KEY (id)
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
    PRIMARY KEY (id), 
    FOREIGN KEY("gehoertZuBereich_id") REFERENCES xp_bereich (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(plangeber_id) REFERENCES xp_plangeber (id)
);

CREATE INDEX "idx_xp_plan_raeumlicherGeltungsbereich" ON xp_plan USING gist ("raeumlicherGeltungsbereich");

CREATE TABLE xp_po (
    id UUID NOT NULL, 
    "gehoertZuBereich_id" UUID, 
    type VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY("gehoertZuBereich_id") REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE TABLE xp_simple_geometry (
    id UUID NOT NULL, 
    name VARCHAR, 
    xplanung_type VARCHAR, 
    position geometry(GEOMETRY,-1), 
    "gehoertZuBereich_id" UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY("gehoertZuBereich_id") REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE INDEX idx_xp_simple_geometry_position ON xp_simple_geometry USING gist (position);

CREATE TYPE bp_rechtscharakter AS ENUM ('Festsetzung', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk', 'Kennzeichnung', 'Unbekannt');

CREATE TABLE bp_objekt (
    id UUID NOT NULL, 
    rechtscharakter bp_rechtscharakter, 
    position geometry(GEOMETRY,-1), 
    flaechenschluss BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_plan (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE xp_plan_gemeinde (
    plan_id UUID, 
    gemeinde_id UUID, 
    FOREIGN KEY(gemeinde_id) REFERENCES xp_gemeinde (id), 
    FOREIGN KEY(plan_id) REFERENCES xp_plan (id)
);

CREATE TABLE xp_ppo (
    id UUID NOT NULL, 
    position geometry(POINT,-1), 
    drehwinkel INTEGER, 
    skalierung FLOAT, 
    symbol_path VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_po (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    CHECK (NOT("referenzName" IS NULL AND "referenzURL" IS NULL)), 
    FOREIGN KEY(plan_id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE xp_tpo (
    id UUID NOT NULL, 
    position geometry(POINT,-1), 
    drehwinkel INTEGER, 
    schriftinhalt VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_po (id) ON DELETE CASCADE
);

CREATE INDEX idx_xp_tpo_position ON xp_tpo USING gist (position);

CREATE TABLE xp_verfahrens_merkmal (
    id UUID NOT NULL, 
    plan_id UUID, 
    vermerk VARCHAR NOT NULL, 
    datum DATE NOT NULL, 
    signatur VARCHAR NOT NULL, 
    signiert BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(plan_id) REFERENCES xp_plan (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_baugrenze (
    id UUID NOT NULL, 
    bautiefe FLOAT, 
    "geschossMin" INTEGER, 
    "geschossMax" INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_bereich (
    id UUID NOT NULL, 
    "versionBauGBDatum" DATE, 
    "versionBauGBText" VARCHAR, 
    "versionSonstRechtsgrundlageDatum" DATE, 
    "versionSonstRechtsgrundlageText" VARCHAR, 
    "gehoertZuPlan_id" UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY("gehoertZuPlan_id") REFERENCES bp_plan (id) ON DELETE CASCADE, 
    FOREIGN KEY(id) REFERENCES xp_bereich (id) ON DELETE CASCADE
);

CREATE TABLE fp_bereich (
    id UUID NOT NULL, 
    "gehoertZuPlan_id" UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY("gehoertZuPlan_id") REFERENCES fp_plan (id) ON DELETE CASCADE, 
    FOREIGN KEY(id) REFERENCES xp_bereich (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    CHECK (NOT("referenzName" IS NULL AND "referenzURL" IS NULL)), 
    FOREIGN KEY(baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE, 
    FOREIGN KEY(bereich_id) REFERENCES xp_bereich (id) ON DELETE CASCADE
);

INSERT INTO alembic_version (version_num) VALUES ('cfbf4d3b2a9d') RETURNING alembic_version.version_num;

-- Running upgrade cfbf4d3b2a9d -> 20c50b38b0af

CREATE TABLE bp_flaeche_ohne_festsetzung (
    id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE bp_objekt ALTER COLUMN rechtscharakter SET NOT NULL;

ALTER TABLE xp_bereich DROP COLUMN srs;

ALTER TABLE xp_plan DROP COLUMN srs;

UPDATE alembic_version SET version_num='20c50b38b0af' WHERE alembic_version.version_num = 'cfbf4d3b2a9d';

-- Running upgrade 20c50b38b0af -> 2cee32cfc646

CREATE TABLE bp_baulinie (
    id UUID NOT NULL, 
    bautiefe FLOAT, 
    "geschossMin" INTEGER, 
    "geschossMax" INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmunggewaesser AS ENUM ('Hafen', 'Sportboothafen', 'Wasserflaeche', 'Fliessgewaesser', 'Sonstiges');

CREATE TABLE bp_gewaesser (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunggewaesser, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmunglandwirtschaft AS ENUM ('LandwirtschaftAllgemein', 'Ackerbau', 'WiesenWeidewirtschaft', 'GartenbaulicheErzeugung', 'Obstbau', 'Weinbau', 'Imkerei', 'Binnenfischerei', 'Sonstiges');

CREATE TABLE bp_landwirtschaft (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunglandwirtschaft, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_strassenbegrenzung (
    id UUID NOT NULL, 
    bautiefe FLOAT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmungwald AS ENUM ('Naturwald', 'Waldschutzgebiet', 'Nutzwald', 'Erholungswald', 'Schutzwald', 'Bodenschutzwald', 'Biotopschutzwald', 'NaturnaherWald', 'SchutzwaldSchaedlicheUmwelteinwirkungen', 'Schonwald', 'Bannwald', 'FlaecheForstwirtschaft', 'ImmissionsgeschaedigterWald', 'Sonstiges');

CREATE TYPE xp_eigentumsartwald AS ENUM ('OeffentlicherWald', 'Staatswald', 'Koerperschaftswald', 'Kommunalwald', 'Stiftungswald', 'Privatwald', 'Gemeinschaftswald', 'Genossenschaftswald', 'Kirchenwald', 'Sonstiges');

CREATE TYPE xp_waldbetretungtyp AS ENUM ('KeineZusaetzlicheBetretung', 'Radfahren', 'Reiten', 'Fahren', 'Hundesport', 'Sonstiges');

CREATE TABLE bp_wald (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungwald, 
    eigentumsart xp_eigentumsartwald, 
    betreten xp_waldbetretungtyp, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE bp_dachgestaltung ADD COLUMN besondere_nutzung_id UUID;

ALTER TABLE bp_dachgestaltung ADD COLUMN gemeinbedarf_id UUID;

ALTER TABLE bp_dachgestaltung ADD CONSTRAINT fk_dachgestaltung_gemeinbedarf FOREIGN KEY(gemeinbedarf_id) REFERENCES bp_gemeinbedarf (id) ON DELETE CASCADE;

ALTER TABLE bp_dachgestaltung ADD CONSTRAINT fk_dachgestaltung_besondere_nutzung FOREIGN KEY(besondere_nutzung_id) REFERENCES bp_besondere_nutzung (id) ON DELETE CASCADE;

UPDATE alembic_version SET version_num='2cee32cfc646' WHERE alembic_version.version_num = '20c50b38b0af';

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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_po (id) ON DELETE CASCADE
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

UPDATE alembic_version SET version_num='873e18b73036' WHERE alembic_version.version_num = '54455ce1e9f6';

-- Running upgrade 873e18b73036 -> 1a015621a38f

CREATE TYPE fp_rechtscharakter AS ENUM ('Darstellung', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk', 'Kennzeichnung', 'Unbekannt');

CREATE TABLE fp_objekt (
    id UUID NOT NULL, 
    rechtscharakter fp_rechtscharakter NOT NULL, 
    "vonGenehmigungAusgenommen" BOOLEAN, 
    position geometry(GEOMETRY,-1), 
    flaechenschluss BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_objekt (id) ON DELETE CASCADE
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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_gemeinbedarf (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunggemeinbedarf, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_gewaesser (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunggewaesser, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_gruen (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunggruen, 
    nutzungsform xp_nutzungsform, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_landwirtschaft (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmunglandwirtschaft, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_spiel_sportanlage (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungspielsportanlage, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE fp_zweckbestimmungstrassenverkehr AS ENUM ('Autobahn', 'Hauptverkehrsstrasse', 'Ortsdurchfahrt', 'SonstigerVerkehrswegAnlage', 'VerkehrsberuhigterBereich', 'Platz', 'Fussgaengerbereich', 'RadGehweg', 'Radweg', 'Gehweg', 'Wanderweg', 'ReitKutschweg', 'Rastanlage', 'Busbahnhof', 'UeberfuehrenderVerkehrsweg', 'UnterfuehrenderVerkehrsweg', 'Wirtschaftsweg', 'LandwirtschaftlicherVerkehr', 'RuhenderVerkehr', 'Parkplatz', 'FahrradAbstellplatz', 'P_RAnlage', 'CarSharing', 'BikeSharing', 'B_RAnlage', 'Parkhaus', 'Mischverkehrsflaeche', 'Ladestation', 'Sonstiges');

CREATE TABLE fp_strassenverkehr (
    id UUID NOT NULL, 
    zweckbestimmung fp_zweckbestimmungstrassenverkehr, 
    nutzungsform xp_nutzungsform, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_wald (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungwald, 
    eigentumsart xp_eigentumsartwald, 
    betreten xp_waldbetretungtyp[], 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='1a015621a38f' WHERE alembic_version.version_num = '873e18b73036';

-- Running upgrade 1a015621a38f -> 812b33dce3d1

CREATE TYPE so_rechtscharakter AS ENUM ('FestsetzungBPlan', 'DarstellungFPlan', 'InhaltLPlan', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk', 'Kennzeichnung', 'Unbekannt', 'Sonstiges');

CREATE TABLE so_objekt (
    id UUID NOT NULL, 
    rechtscharakter so_rechtscharakter NOT NULL, 
    position geometry(GEOMETRY,-1), 
    flaechenschluss BOOLEAN, 
    flussrichtung BOOLEAN, 
    nordwinkel INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES xp_objekt (id) ON DELETE CASCADE
);

CREATE INDEX idx_so_objekt_position ON so_objekt USING gist (position);

CREATE TYPE so_klassifiznachdenkmalschutzrecht AS ENUM ('DenkmalschutzEnsemble', 'DenkmalschutzEinzelanlage', 'Grabungsschutzgebiet', 'PufferzoneWeltkulturerbeEnger', 'PufferzoneWeltkulturerbeWeiter', 'ArcheologischesDenkmal', 'Bodendenkmal', 'Sonstiges');

CREATE TABLE so_denkmalschutz (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachdenkmalschutzrecht, 
    weltkulturerbe BOOLEAN, 
    name VARCHAR, 
    nummer VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TYPE so_klassifiznachschienenverkehrsrecht AS ENUM ('Bahnanlage', 'DB_Bahnanlage', 'Personenbahnhof', 'Fernbahnhof', 'Gueterbahnhof', 'Bahnlinie', 'Personenbahnlinie', 'Regionalbahn', 'Kleinbahn', 'Gueterbahnlinie', 'WerksHafenbahn', 'Seilbahn', 'OEPNV', 'Strassenbahn', 'UBahn', 'SBahn', 'OEPNV_Haltestelle', 'Sonstiges');

CREATE TABLE so_schienenverkehr (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachschienenverkehrsrecht, 
    name VARCHAR, 
    nummer VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TYPE so_klassifizschutzgebietwasserrecht AS ENUM ('Wasserschutzgebiet', 'QuellGrundwasserSchutzgebiet', 'OberflaechengewaesserSchutzgebiet', 'Heilquellenschutzgebiet', 'Sonstiges');

CREATE TYPE so_schutzzonenwasserrecht AS ENUM ('Zone_1', 'Zone_2', 'Zone_3', 'Zone_3a', 'Zone_3b', 'Zone_4');

CREATE TABLE so_wasserschutz (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizschutzgebietwasserrecht, 
    zone so_schutzzonenwasserrecht, 
    name VARCHAR, 
    nummer VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
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

UPDATE alembic_version SET version_num='812b33dce3d1' WHERE alembic_version.version_num = '1a015621a38f';

-- Running upgrade 812b33dce3d1 -> 0a6f00a1f663

UPDATE xp_po SET type='xp_pto' WHERE type='xp_tpo';;

ALTER INDEX idx_xp_tpo_position RENAME TO idx_xp_pto_position;;

ALTER TABLE xp_tpo RENAME CONSTRAINT xp_tpo_id_fkey TO xp_pto_id_fkey;;

ALTER TABLE xp_tpo RENAME CONSTRAINT xp_tpo_pkey TO xp_pto_pkey;;

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

UPDATE alembic_version SET version_num='0a6f00a1f663' WHERE alembic_version.version_num = '812b33dce3d1';

-- Running upgrade 0a6f00a1f663 -> b93ec8372df6

ALTER TABLE xp_plan ALTER COLUMN "raeumlicherGeltungsbereich" type geometry(Geometry);;

ALTER TABLE xp_plan ADD CONSTRAINT check_geometry_type CHECK (st_dimension("raeumlicherGeltungsbereich") = 2);;

ALTER TABLE xp_bereich ALTER COLUMN "geltungsbereich" type geometry(Geometry);;

ALTER TABLE xp_bereich ADD CONSTRAINT check_geometry_type CHECK (st_dimension("geltungsbereich") = 2);;

UPDATE alembic_version SET version_num='b93ec8372df6' WHERE alembic_version.version_num = '0a6f00a1f663';

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
    PRIMARY KEY (id)
);

ALTER TYPE xp_externereferenztyp ADD VALUE IF NOT EXISTS 'Schutzgebietsverordnung';;

CREATE TYPE xp_traegerschaft AS ENUM('EinrichtungBund','EinrichtungLand', 'EinrichtungKreis', 'KommunaleEinrichtung', 'ReligioeserTraeger', 'SonstTraeger');;

ALTER TABLE bp_gemeinbedarf ADD COLUMN traeger xp_traegerschaft;;

UPDATE xp_externe_referenz SET "referenzName"='Unbekannt' WHERE "referenzName" is NULL;;

UPDATE xp_externe_referenz SET "referenzURL"="referenzURL" WHERE "referenzURL" is NULL;;

ALTER TYPE xp_sondernutzungen ADD VALUE IF NOT EXISTS 'SondergebietGrosshandel';;

ALTER TYPE xp_spemassnahmentypen ADD VALUE IF NOT EXISTS 'ArtenreicherGehoelzbestand';;

ALTER TYPE xp_spemassnahmentypen ADD VALUE IF NOT EXISTS 'Moor';;

ALTER TYPE public.xp_spemassnahmentypen RENAME TO xp_spemassnahmentypen_old;

CREATE TYPE public.xp_spemassnahmentypen AS ENUM('ArtenreicherGehoelzbestand', 'NaturnaherWald', 'ExtensivesGruenland', 'Feuchtgruenland', 'Obstwiese', 'NaturnaherUferbereich', 'Roehrichtzone', 'Ackerrandstreifen', 'Ackerbrache', 'Gruenlandbrache', 'Sukzessionsflaeche', 'Hochstaudenflur', 'Trockenrasen', 'Heide', 'Sonstiges');

CREATE FUNCTION new_old_not_equals(
                new_enum_val public.xp_spemassnahmentypen, old_enum_val public.xp_spemassnahmentypen_old
            )
            RETURNS boolean AS $$
                SELECT new_enum_val::text != CASE
                    WHEN old_enum_val::text = 'ArtentreicherGehoelzbestand' THEN 'ArtenreicherGehoelzbestand'

                    ELSE old_enum_val::text
                END;
            $$ LANGUAGE SQL IMMUTABLE;

CREATE OPERATOR != (
            leftarg = public.xp_spemassnahmentypen,
            rightarg = public.xp_spemassnahmentypen_old,
            procedure = new_old_not_equals
        );

CREATE FUNCTION new_old_equals(
                new_enum_val public.xp_spemassnahmentypen, old_enum_val public.xp_spemassnahmentypen_old
            )
            RETURNS boolean AS $$
                SELECT new_enum_val::text = CASE
                    WHEN old_enum_val::text = 'ArtentreicherGehoelzbestand' THEN 'ArtenreicherGehoelzbestand'

                    ELSE old_enum_val::text
                END;
            $$ LANGUAGE SQL IMMUTABLE;

CREATE OPERATOR = (
            leftarg = public.xp_spemassnahmentypen,
            rightarg = public.xp_spemassnahmentypen_old,
            procedure = new_old_equals
        );

ALTER TABLE public.xp_spe_daten 
                ALTER COLUMN "klassifizMassnahme" TYPE public.xp_spemassnahmentypen 
                USING CASE 
                WHEN "klassifizMassnahme"::text = 'ArtentreicherGehoelzbestand' THEN 'ArtenreicherGehoelzbestand'::public.xp_spemassnahmentypen

                ELSE "klassifizMassnahme"::text::public.xp_spemassnahmentypen
                END;

DROP FUNCTION new_old_not_equals(
            new_enum_val public.xp_spemassnahmentypen, old_enum_val public.xp_spemassnahmentypen_old
        ) CASCADE;

DROP FUNCTION new_old_equals(
            new_enum_val public.xp_spemassnahmentypen, old_enum_val public.xp_spemassnahmentypen_old
        ) CASCADE;

DROP TYPE public.xp_spemassnahmentypen_old;

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

UPDATE alembic_version SET version_num='fb27f7a59e17' WHERE alembic_version.version_num = 'b93ec8372df6';

-- Running upgrade fb27f7a59e17 -> 8cdbef1a55d6

ALTER TABLE bp_plan ADD COLUMN "versionBauNVO_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
            ALTER TABLE bp_plan ADD COLUMN "versionBauGB_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
            ALTER TABLE bp_plan ADD COLUMN "versionSonstRechtsgrundlage_id" uuid REFERENCES xp_gesetzliche_grundlage(id);;

ALTER TYPE xp_zweckbestimmunggemeinbedarf ADD VALUE IF NOT EXISTS 'SonstigeInfrastruktur';

ALTER TYPE xp_zweckbestimmunggemeinbedarf ADD VALUE IF NOT EXISTS 'SonstigeSicherheitOrdnung';

UPDATE alembic_version SET version_num='8cdbef1a55d6' WHERE alembic_version.version_num = 'fb27f7a59e17';

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

UPDATE alembic_version SET version_num='ce95b86bc010' WHERE alembic_version.version_num = '8cdbef1a55d6';

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

DELETE FROM bp_einfahrtpunkt WHERE id NOT IN (SELECT id FROM bp_objekt);

DELETE FROM bp_keine_ein_ausfahrt WHERE id NOT IN (SELECT id FROM bp_objekt);

DELETE FROM bp_nutzungsgrenze WHERE id NOT IN (SELECT id FROM bp_objekt);

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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE bp_dachgestaltung ADD COLUMN grundstueck_ueberbaubar_id UUID;

ALTER TABLE bp_dachgestaltung ADD FOREIGN KEY(grundstueck_ueberbaubar_id) REFERENCES bp_grundstueck_ueberbaubar (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD COLUMN grundstueck_ueberbaubar_id UUID;

ALTER TABLE xp_externe_referenz ADD FOREIGN KEY(grundstueck_ueberbaubar_id) REFERENCES bp_grundstueck_ueberbaubar (id) ON DELETE CASCADE;

UPDATE alembic_version SET version_num='20238c1f2cf8' WHERE alembic_version.version_num = '1983d6b6e2c1';

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
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_aufschuettung (
    id UUID NOT NULL, 
    aufschuettungsmaterial VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_schutzflaeche (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    "istAusgleich" BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE xp_spe_daten ADD COLUMN fp_schutzflaeche_id UUID;

ALTER TABLE xp_spe_daten ADD CONSTRAINT fk_spe_daten_schutzflaeche FOREIGN KEY(fp_schutzflaeche_id) REFERENCES fp_schutzflaeche (id) ON DELETE CASCADE;

CREATE TABLE fp_kennzeichnung (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungkennzeichnung[], 
    "istVerdachtsflaeche" BOOLEAN, 
    nummer VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='151ba21532e3' WHERE alembic_version.version_num = '20238c1f2cf8';

-- Running upgrade 151ba21532e3 -> 5b93f2301608

ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'BauHoehe';;

ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'BauMasse';;

ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'GrundGeschossflaeche';;

UPDATE alembic_version SET version_num='5b93f2301608' WHERE alembic_version.version_num = '151ba21532e3';

COMMIT;

