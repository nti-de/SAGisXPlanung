"""v2.1.0

Revision ID: 8cdbef1a55d6
Revises: fb27f7a59e17
Create Date: 2023-07-20 08:27:50.660157

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
revision = '8cdbef1a55d6'
down_revision = 'fb27f7a59e17'
branch_labels = None
depends_on = None


def upgrade():
    # CR-039 BP_Plan
    op.execute("""
            ALTER TABLE bp_plan ADD COLUMN "versionBauNVO_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
            ALTER TABLE bp_plan ADD COLUMN "versionBauGB_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
            ALTER TABLE bp_plan ADD COLUMN "versionSonstRechtsgrundlage_id" uuid REFERENCES xp_gesetzliche_grundlage(id);
        """)

    op.execute("ALTER TYPE xp_zweckbestimmunggemeinbedarf ADD VALUE 'SonstigeInfrastruktur'")
    op.execute("ALTER TYPE xp_zweckbestimmunggemeinbedarf ADD VALUE 'SonstigeSicherheitOrdnung'")


def downgrade():
    op.execute("""
            ALTER TABLE bp_plan DROP COLUMN "versionBauNVO_id";
            ALTER TABLE bp_plan DROP COLUMN "versionBauGB_id";
            ALTER TABLE bp_plan DROP COLUMN "versionSonstRechtsgrundlage_id";
        """)
    # ### end Alembic commands ###
