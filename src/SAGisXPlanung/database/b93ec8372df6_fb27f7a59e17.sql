BEGIN;

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

COMMIT;

