BEGIN;

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

COMMIT;

