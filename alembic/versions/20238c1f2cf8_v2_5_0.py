"""v2.5.0

Revision ID: 20238c1f2cf8
Revises: 1983d6b6e2c1
Create Date: 2024-04-29 07:49:39.972200

"""
import os
import sys

from alembic import op, context
import sqlalchemy as sa

from alembic_postgresql_enum import ColumnType
from alembic_postgresql_enum import TableReference
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)


# revision identifiers, used by Alembic.
revision = '20238c1f2cf8'
down_revision = '1983d6b6e2c1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("""
        CREATE OR REPLACE FUNCTION immutable_date_to_char(date) RETURNS text AS
        $$ select extract(year from $1)::text || '-' ||
                    lpad(extract(week from $1)::text, 2, '0') || '-' ||
                    lpad(extract(day from $1)::text, 2, '0'); $$
        LANGUAGE sql immutable;
    """)

    op.execute("""
        ALTER TABLE xp_plan
        ADD COLUMN _sa_search_col tsvector
        GENERATED ALWAYS AS (to_tsvector('german',
            xp_plan.id::text || ' ' ||
            xp_plan.name || ' ' ||
            coalesce(xp_plan.type, '') || ' ' ||
            coalesce(xp_plan.nummer, '') || ' ' ||
            coalesce(xp_plan."internalId", '') || ' ' ||
            coalesce(xp_plan.beschreibung, '') || ' ' ||
            coalesce(xp_plan.kommentar, '') || ' ' ||
            coalesce(immutable_date_to_char(xp_plan."technHerstellDatum"), '') || ' ' ||
            coalesce(immutable_date_to_char(xp_plan."genehmigungsDatum"), '') || ' ' ||
            coalesce(immutable_date_to_char(xp_plan."untergangsDatum"), '') || ' ' ||
            coalesce(xp_plan."erstellungsMassstab"::text, '') || ' ' ||
            coalesce(xp_plan.bezugshoehe::text, '') || ' ' ||
            coalesce(xp_plan."technischerPlanersteller", '')
        )) STORED;
    """)
    op.execute("CREATE INDEX textsearch_idx ON xp_plan USING GIN (_sa_search_col);")

    bp_zulaessigkeit_enum = postgresql.ENUM('Zulaessig', 'NichtZulaessig', 'AusnahmsweiseZulaessig',
                                               name='bp_zulaessigkeit', create_type=False)
    bauweise_enum = postgresql.ENUM('KeineAngabe', 'OffeneBauweise', 'GeschlosseneBauweise', 'AbweichendeBauweise',
                                    name='bp_bauweise', create_type=False)
    bebauungsart_enum = postgresql.ENUM('Einzelhaeuser', 'Doppelhaeuser', 'Hausgruppen', 'EinzelDoppelhaeuser',
                                        'EinzelhaeuserHausgruppen', 'DoppelhaeuserHausgruppen', 'Reihenhaeuser',
                                        'EinzelhaeuserDoppelhaeuserHausgruppen', name='bp_bebauungsart',
                                        create_type=False)
    grenzbebauung_enum = postgresql.ENUM('KeineAngabe', 'Verboten', 'Erlaubt', 'Erzwungen',
                                         name='bp_grenzbebauung', create_type=False)

    if not context.is_offline_mode():
        bp_zulaessigkeit_enum.create(op.get_bind(), checkfirst=True)
        bauweise_enum.create(op.get_bind(), checkfirst=True)
        bebauungsart_enum.create(op.get_bind(), checkfirst=True)
        grenzbebauung_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('bp_grundstueck_ueberbaubar',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('FR', sa.Integer(), nullable=True),
                    sa.Column('MaxZahlWohnungen', sa.Integer(), nullable=True),
                    sa.Column('MinGRWohneinheit', sa.Float(), nullable=True),
                    sa.Column('Fmin', sa.Float(), nullable=True),
                    sa.Column('Fmax', sa.Float(), nullable=True),
                    sa.Column('Bmin', sa.Float(), nullable=True),
                    sa.Column('Bmax', sa.Float(), nullable=True),
                    sa.Column('Tmin', sa.Float(), nullable=True),
                    sa.Column('Tmax', sa.Float(), nullable=True),
                    sa.Column('GFZmin', sa.Float(), nullable=True),
                    sa.Column('GFZmax', sa.Float(), nullable=True),
                    sa.Column('GFZ', sa.Float(), nullable=True),
                    sa.Column('GFZ_Ausn', sa.Float(), nullable=True),
                    sa.Column('GFmin', sa.Float(), nullable=True),
                    sa.Column('GFmax', sa.Float(), nullable=True),
                    sa.Column('GF', sa.Float(), nullable=True),
                    sa.Column('GF_Ausn', sa.Float(), nullable=True),
                    sa.Column('BMZ', sa.Float(), nullable=True),
                    sa.Column('BMZ_Ausn', sa.Float(), nullable=True),
                    sa.Column('BM', sa.Float(), nullable=True),
                    sa.Column('BM_Ausn', sa.Float(), nullable=True),
                    sa.Column('GRZmin', sa.Float(), nullable=True),
                    sa.Column('GRZmax', sa.Float(), nullable=True),
                    sa.Column('GRZ', sa.Float(), nullable=True),
                    sa.Column('GRZ_Ausn', sa.Float(), nullable=True),
                    sa.Column('GRmin', sa.Float(), nullable=True),
                    sa.Column('GRmax', sa.Float(), nullable=True),
                    sa.Column('GR', sa.Float(), nullable=True),
                    sa.Column('GR_Ausn', sa.Float(), nullable=True),
                    sa.Column('Zmin', sa.Integer(), nullable=True),
                    sa.Column('Zmax', sa.Integer(), nullable=True),
                    sa.Column('Zzwingend', sa.Integer(), nullable=True),
                    sa.Column('Z', sa.Integer(), nullable=True),
                    sa.Column('Z_Ausn', sa.Integer(), nullable=True),
                    sa.Column('Z_Staffel', sa.Integer(), nullable=True),
                    sa.Column('Z_Dach', sa.Integer(), nullable=True),
                    sa.Column('ZUmin', sa.Integer(), nullable=True),
                    sa.Column('ZUmax', sa.Integer(), nullable=True),
                    sa.Column('ZUzwingend', sa.Integer(), nullable=True),
                    sa.Column('ZU', sa.Integer(), nullable=True),
                    sa.Column('ZU_Ausn', sa.Integer(), nullable=True),
                    sa.Column('wohnnutzungEGStrasse', bp_zulaessigkeit_enum, nullable=True),
                    sa.Column('ZWohn', sa.Integer(), nullable=True),
                    sa.Column('GFAntWohnen', sa.Integer(), nullable=True),
                    sa.Column('GFWohnen', sa.Float(), nullable=True),
                    sa.Column('GFAntGewerbe', sa.Integer(), nullable=True),
                    sa.Column('GFGewerbe', sa.Float(), nullable=True),
                    sa.Column('VF', sa.Float(), nullable=True),
                    sa.Column('bauweise', bauweise_enum, nullable=True),
                    sa.Column('vertikaleDifferenzierung', sa.Boolean(), nullable=True),
                    sa.Column('bebauungsArt', bebauungsart_enum, nullable=True),
                    sa.Column('bebauungVordereGrenze', grenzbebauung_enum, nullable=True),
                    sa.Column('bebauungRueckwaertigeGrenze', grenzbebauung_enum, nullable=True),
                    sa.Column('bebauungSeitlicheGrenze', grenzbebauung_enum, nullable=True),
                    sa.Column('geschossMin', sa.Integer(), nullable=True),
                    sa.Column('geschossMax', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.add_column('bp_dachgestaltung', sa.Column('grundstueck_ueberbaubar_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'bp_dachgestaltung', 'bp_grundstueck_ueberbaubar', ['grundstueck_ueberbaubar_id'],['id'], ondelete='CASCADE')

    op.add_column('xp_externe_referenz', sa.Column('grundstueck_ueberbaubar_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'xp_externe_referenz', 'bp_grundstueck_ueberbaubar', ['grundstueck_ueberbaubar_id'],['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('xp_plan', '_sa_search_col')
    op.execute("DROP FUNCTION immutable_date_to_char")

    op.execute("DELETE FROM xp_objekt CASCADE WHERE type in ('bp_grundstueck_ueberbaubar');")
    op.drop_column('xp_externe_referenz', 'grundstueck_ueberbaubar_id')
    op.drop_column('bp_dachgestaltung', 'grundstueck_ueberbaubar_id')
    op.drop_table('bp_grundstueck_ueberbaubar')
    # ### end Alembic commands ###
