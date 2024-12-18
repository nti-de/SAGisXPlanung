BEGIN;

-- Running upgrade 5b93f2301608 -> e9b38a472653

CREATE TABLE assoc_detail_zweckgemeinbedarf (
    codelist_user_id UUID, 
    codelist_user_v6_id UUID, 
    codelist_id UUID, 
    FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    FOREIGN KEY(codelist_user_id) REFERENCES fp_gemeinbedarf (id) ON DELETE CASCADE, 
    FOREIGN KEY(codelist_user_v6_id) REFERENCES fp_zweckbestimmung_gemeinbedarf (id) ON DELETE CASCADE
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

ALTER TABLE bp_objekt ADD CONSTRAINT prevent_geometry_collection CHECK (GeometryType(position) NOT IN ('GEOMETRYCOLLECTION'));

ALTER TABLE fp_objekt ADD CONSTRAINT prevent_geometry_collection CHECK (GeometryType(position) NOT IN ('GEOMETRYCOLLECTION'));

ALTER TABLE so_objekt ADD CONSTRAINT prevent_geometry_collection CHECK (GeometryType(position) NOT IN ('GEOMETRYCOLLECTION'));

CREATE TYPE so_klassifiznachstrassenverkehrsrecht AS ENUM ('Bundesautobahn', 'Bundesstrasse', 'LandesStaatsstrasse', 'Kreisstrasse', 'SonstOeffentlStrasse');

CREATE TABLE so_strassenverkehrsrecht (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachstrassenverkehrsrecht, 
    name VARCHAR, 
    nummer VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
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

UPDATE alembic_version SET version_num='e9b38a472653' WHERE alembic_version.version_num = '5b93f2301608';

COMMIT;

