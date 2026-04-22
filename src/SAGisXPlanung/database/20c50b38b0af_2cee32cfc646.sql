BEGIN;

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

COMMIT;

