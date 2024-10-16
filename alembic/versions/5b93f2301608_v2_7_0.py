"""v2.7.0

Revision ID: 5b93f2301608
Revises: 151ba21532e3
Create Date: 2024-10-14 14:06:45.021191

"""
import os
import sys

from alembic import op
import sqlalchemy as sa

from alembic_postgresql_enum import TableReference, ColumnType


PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)


# revision identifiers, used by Alembic.
revision = '5b93f2301608'
down_revision = '151ba21532e3'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'BauHoehe';")
    op.execute("ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'BauMasse';")
    op.execute("ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'GrundGeschossflaeche';")

    op.execute("ALTER TABLE so_strassenverkehr ALTER COLUMN nutzungsform DROP NOT NULL;")


def downgrade():
    # downgrade not useful as values might be used. what to replace with?
    # op.sync_enum_values('public', 'buildingtemplatecelldatatype',
    #                     ['ArtDerBaulNutzung', 'ZahlVollgeschosse', 'GRZ', 'GFZ', 'BebauungsArt', 'Bauweise',
    #                      'Dachneigung', 'Dachform'],
    #                     [TableReference('xp_nutzungsschablone', 'data_attributes', column_type=ColumnType.ARRAY)],
    #                     enum_values_to_rename=[])
    pass
