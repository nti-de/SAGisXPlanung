"""v2.6.0

Revision ID: 151ba21532e3
Revises: 20238c1f2cf8
Create Date: 2024-07-22 13:11:40.729774

"""
import os
import sys

from sqlalchemy.dialects import postgresql

from alembic import op, context
import sqlalchemy as sa



PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)


# revision identifiers, used by Alembic.
revision = '151ba21532e3'
down_revision = '20238c1f2cf8'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
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
        end $$;
    """)

    op.execute("""
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
        end $$;
        """)

    op.execute("""
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
        end $$;
        """)

    op.create_table('fp_abgrabung',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('abbaugut', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_aufschuettung',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('aufschuettungsmaterial', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    spe_ziele_enum = postgresql.ENUM('SchutzPflege', 'Entwicklung', 'Anlage', 'SchutzPflegeEntwicklung',
                                     'Sonstiges', name='xp_speziele', create_type=False)

    if not context.is_offline_mode():
        spe_ziele_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('fp_schutzflaeche',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('ziel', spe_ziele_enum, nullable=True),
                    sa.Column('sonstZiel', sa.String(), nullable=True),
                    sa.Column('istAusgleich', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.add_column('xp_spe_daten', sa.Column('fp_schutzflaeche_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_spe_daten_schutzflaeche', 'xp_spe_daten', 'fp_schutzflaeche', ['fp_schutzflaeche_id'],
                          ['id'], ondelete='CASCADE')


def downgrade():
    op.drop_table('fp_aufschuettung')
    op.drop_table('fp_abgrabung')

    op.drop_constraint('fk_spe_daten_schutzflaeche', 'xp_spe_daten', type_='foreignkey')
    op.drop_column('xp_spe_daten', 'fp_schutzflaeche_id')
    op.drop_table('fp_schutzflaeche')
