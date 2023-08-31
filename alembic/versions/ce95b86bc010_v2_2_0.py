"""v2.2.0

Revision ID: ce95b86bc010
Revises: 8cdbef1a55d6
Create Date: 2023-08-01 12:42:07.002746

"""
import os
import sys

from alembic import op
import sqlalchemy as sa

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)

# revision identifiers, used by Alembic.
revision = 'ce95b86bc010'
down_revision = '8cdbef1a55d6'
branch_labels = None
depends_on = None


def upgrade():
    # region CODELISTS
    op.execute("""
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
        ALTER TABLE so_denkmalschutz ADD COLUMN "detailArtDerFestlegung_id" uuid REFERENCES codelist_values(id);
    """
    )

    op.execute("""
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
        );
    """)
    # endregion CODELISTS

    # region XP_Hoehenangabe
    op.execute("""
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
        );
    """)
    # endregion XP_Hoehenangabe

    op.execute("""
        CREATE TYPE bp_abgrenzungentypen AS ENUM (
            'Nutzungsartengrenze',
            'UnterschiedlicheHoehen',
            'SonstigeAbgrenzung'
            );
        
        CREATE TABLE bp_nutzungsgrenze (
            id UUID NOT NULL,
            typ bp_abgrenzungentypen,
        
            PRIMARY KEY (id)
        );
    """)

    op.execute("""
        CREATE TYPE bp_bereichohneeinausfahrttypen  AS ENUM (
            'KeineEinfahrt',
            'KeineAusfahrt',
            'KeineEinAusfahrt'
            );
        
        CREATE TABLE bp_keine_ein_ausfahrt (
            id UUID NOT NULL,
            typ bp_bereichohneeinausfahrttypen,
        
            PRIMARY KEY (id)
        );
    """)

    op.execute("""
        CREATE TYPE bp_einfahrttypen AS ENUM (
            'Einfahrt',
            'Ausfahrt',
            'EinAusfahrt'
            );
        
        CREATE TABLE bp_einfahrtpunkt (
            id UUID NOT NULL,
            typ bp_einfahrttypen,
        
            PRIMARY KEY (id)
        );
    """)


def downgrade():
    op.execute('DROP TABLE assoc_detail_sondernutzung')
    op.execute('DROP TABLE assoc_detail_zweckgruen')

    op.execute("DROP TABLE codelist_values CASCADE")
    op.execute("DROP TABLE codelist")

    op.execute('ALTER TABLE bp_plan DROP COLUMN "sonstPlanArt_id";')
    op.execute('ALTER TABLE bp_plan DROP COLUMN "status_id";')
    op.execute('ALTER TABLE bp_baugebiet DROP COLUMN "detaillierteArtDerBaulNutzung_id"')
    op.execute('ALTER TABLE bp_dachgestaltung DROP COLUMN "detaillierteDachform_id"')
    op.execute('ALTER TABLE fp_plan DROP COLUMN "sonstPlanArt_id"')
    op.execute('ALTER TABLE fp_plan DROP COLUMN "status_id"')
    op.execute('ALTER TABLE fp_baugebiet DROP COLUMN "detaillierteArtDerBaulNutzung_id"')

    op.execute('ALTER TABLE so_denkmalschutz DROP COLUMN "detailArtDerFestlegung_id"')
    op.execute('ALTER TABLE so_schienenverkehr DROP COLUMN "detailArtDerFestlegung_id"')

    op.execute("""
        DROP TABLE xp_hoehenangabe CASCADE;
        DROP TYPE xp_arthoehenbezug CASCADE;
        DROP TYPE xp_arthoehenbezugspunkt CASCADE;
    """)

    op.execute("""
        DROP TABLE bp_nutzungsgrenze;
        DROP TYPE bp_abgrenzungentypen CASCADE;
    """)

    op.execute("""
        DROP TABLE bp_keine_ein_ausfahrt;
        DROP TYPE bp_bereichohneeinausfahrttypen CASCADE;
    """)

    op.execute("""
        DROP TABLE bp_einfahrtpunkt;
        DROP TYPE bp_einfahrttypen CASCADE;
    """)
