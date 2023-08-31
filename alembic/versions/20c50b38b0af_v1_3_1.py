"""v1.3.1

Revision ID: 20c50b38b0af
Revises: cfbf4d3b2a9d
Create Date: 2022-01-07 09:39:09.632579

"""
import os
import sys
from geoalchemy2 import Geometry
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)

# revision identifiers, used by Alembic.
revision = '20c50b38b0af'
down_revision = 'cfbf4d3b2a9d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('bp_flaeche_ohne_festsetzung',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.alter_column('bp_objekt', 'rechtscharakter',
                    existing_type=postgresql.ENUM('Festsetzung', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk',
                                                  'Kennzeichnung', 'Unbekannt', name='bp_rechtscharakter'),
                    nullable=False)
    op.drop_column('xp_bereich', 'srs')
    op.drop_column('xp_plan', 'srs')


def downgrade():
    op.add_column('xp_plan', sa.Column('srs', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('xp_bereich', sa.Column('srs', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.alter_column('bp_objekt', 'rechtscharakter',
                    existing_type=postgresql.ENUM('Festsetzung', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk',
                                                  'Kennzeichnung', 'Unbekannt', name='bp_rechtscharakter'),
                    nullable=True)
    op.drop_table('bp_flaeche_ohne_festsetzung')
