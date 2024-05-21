BEGIN;

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

COMMIT;

