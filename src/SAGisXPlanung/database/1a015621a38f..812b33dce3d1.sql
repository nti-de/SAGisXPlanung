BEGIN;

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

COMMIT;

