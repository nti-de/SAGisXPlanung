BEGIN;

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

UPDATE alembic_version SET version_num='151ba21532e3' WHERE alembic_version.version_num = '20238c1f2cf8';

COMMIT;

