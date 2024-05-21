BEGIN;

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

COMMIT;

