"""v1.10.0

Revision ID: b93ec8372df6
Revises: 0a6f00a1f663
Create Date: 2023-02-23 10:33:01.286524

"""
import os
import sys

from alembic import op
import sqlalchemy as sa

from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)


# revision identifiers, used by Alembic.
revision = 'b93ec8372df6'
down_revision = '0a6f00a1f663'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE xp_plan ALTER COLUMN "raeumlicherGeltungsbereich" type geometry(Geometry);')
    op.execute('ALTER TABLE xp_plan ADD CONSTRAINT check_geometry_type CHECK (st_dimension("raeumlicherGeltungsbereich") = 2);')

    op.execute('ALTER TABLE xp_bereich ALTER COLUMN "geltungsbereich" type geometry(Geometry);')
    op.execute('ALTER TABLE xp_bereich ADD CONSTRAINT check_geometry_type CHECK (st_dimension("geltungsbereich") = 2);')


def downgrade():
    op.execute('DELETE FROM xp_plan WHERE st_dimension("raeumlicherGeltungsbereich") < 2 or ST_GeometryType("raeumlicherGeltungsbereich") = \'ST_CurvePolygon\';')
    op.execute('ALTER TABLE xp_plan ALTER COLUMN "raeumlicherGeltungsbereich" type geometry(MultiPolygon);')

    op.execute('DELETE FROM xp_bereich WHERE st_dimension("geltungsbereich") < 2 or ST_GeometryType("geltungsbereich") = \'ST_CurvePolygon\';')
    op.execute('ALTER TABLE xp_bereich ALTER COLUMN "geltungsbereich" type geometry(MultiPolygon);')

    op.drop_constraint('check_geometry_type', 'xp_plan')
    op.drop_constraint('check_geometry_type', 'xp_bereich')
