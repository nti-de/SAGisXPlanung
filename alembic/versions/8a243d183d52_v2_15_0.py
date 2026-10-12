"""v2.15.0

Revision ID: 8a243d183d52
Revises: 250637cd31df
Create Date: 2026-10-12 14:09:39.876065

Cleaned up autogenerate output:
Only includes actual data model changes after v2.14.3 (see git diff v2.14.3..HEAD):
- 748b340c: new object type BP_SchutzPflegeEntwicklungsMassnahme (table bp_schutzmassnahme,
  plus FK columns on xp_externe_referenz and xp_spe_daten)
- dab2a161: 4 new values for enum bp_wegerechttypen

Removed autogenerate noise:
- all op.sync_enum_values calls (pre-existing drift, enum ordering differences,
  and broken syntax like new_values=[<XP_ArtHoehenbezug.absolutNHN: 1000>, ...]
  which is invalid Python; integer-valued Python Enums are rendered as repr
  instead of string labels by alembic-postgresql-enum)
- nullable-only alter_column on assoc_detail_sondernutzung, assoc_detail_zweckgruen,
  xp_textabschnitt_assoc (no model change after 2.14.3, pre-existing DB drift)
- referenzName/referenzURL nullable alters and veraenderungssperre FK rename
  (no model change after 2.14.3)
- xp_plan _sa_search_col / textsearch_idx handling (full-text search column,
  no model change after 2.14.3)
- xp_text_abschnitt fp_objekt_id/bp_objekt_id drops (legacy columns, no model
  change after 2.14.3)
"""
import os
import sys

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)


# revision identifiers, used by Alembic.
revision = '8a243d183d52'
down_revision = '250637cd31df'
branch_labels = None
depends_on = None


def upgrade():
    # New object type BP_SchutzPflegeEntwicklungsMassnahme (commit 748b340c)
    op.create_table('bp_schutzmassnahme',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('ziel', postgresql.ENUM('SchutzPflege', 'Entwicklung', 'Anlage', 'SchutzPflegeEntwicklung', 'Sonstiges', name='xp_speziele', create_type=False), nullable=True),
    sa.Column('sonstZiel', sa.String(), nullable=True),
    sa.Column('istAusgleich', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_schutzmassnahme_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_schutzmassnahme'))
    )

    op.add_column('xp_externe_referenz', sa.Column('bp_schutzmassnahme_massnahme_id', sa.UUID(), nullable=True))
    op.add_column('xp_externe_referenz', sa.Column('bp_schutzmassnahme_plan_id', sa.UUID(), nullable=True))
    op.create_foreign_key(op.f('fk_xp_externe_referenz_bp_schutzmassnahme_massnahme_id_bp_schutzmassnahme'), 'xp_externe_referenz', 'bp_schutzmassnahme', ['bp_schutzmassnahme_massnahme_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_xp_externe_referenz_bp_schutzmassnahme_plan_id_bp_schutzmassnahme'), 'xp_externe_referenz', 'bp_schutzmassnahme', ['bp_schutzmassnahme_plan_id'], ['id'], ondelete='CASCADE')

    op.add_column('xp_spe_daten', sa.Column('bp_schutzmassnahme_id', sa.UUID(), nullable=True))
    op.create_foreign_key(op.f('fk_xp_spe_daten_bp_schutzmassnahme_id_bp_schutzmassnahme'), 'xp_spe_daten', 'bp_schutzmassnahme', ['bp_schutzmassnahme_id'], ['id'], ondelete='CASCADE')

    # New enum values for BP_WegerechtTypen (commit dab2a161).
    op.execute("ALTER TYPE bp_wegerechttypen ADD VALUE IF NOT EXISTS 'GehFahrrecht'")
    op.execute("ALTER TYPE bp_wegerechttypen ADD VALUE IF NOT EXISTS 'GehLeitungsrecht'")
    op.execute("ALTER TYPE bp_wegerechttypen ADD VALUE IF NOT EXISTS 'FahrLeitungsrecht'")
    op.execute("ALTER TYPE bp_wegerechttypen ADD VALUE IF NOT EXISTS 'GehFahrLeitungsrecht'")


def downgrade():
    op.drop_constraint(op.f('fk_xp_spe_daten_bp_schutzmassnahme_id_bp_schutzmassnahme'), 'xp_spe_daten', type_='foreignkey')
    op.drop_column('xp_spe_daten', 'bp_schutzmassnahme_id')

    op.drop_constraint(op.f('fk_xp_externe_referenz_bp_schutzmassnahme_plan_id_bp_schutzmassnahme'), 'xp_externe_referenz', type_='foreignkey')
    op.drop_constraint(op.f('fk_xp_externe_referenz_bp_schutzmassnahme_massnahme_id_bp_schutzmassnahme'), 'xp_externe_referenz', type_='foreignkey')
    op.drop_column('xp_externe_referenz', 'bp_schutzmassnahme_plan_id')
    op.drop_column('xp_externe_referenz', 'bp_schutzmassnahme_massnahme_id')

    op.drop_table('bp_schutzmassnahme')
    op.execute("DELETE FROM xp_objekt CASCADE WHERE type in ('bp_schutzmassnahme');")
