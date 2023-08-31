"""v1.9.0

Revision ID: 0a6f00a1f663
Revises: 812b33dce3d1
Create Date: 2023-01-12 12:38:21.165151

"""
import os
import sys

from alembic import op, context
import sqlalchemy as sa

from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)

# revision identifiers, used by Alembic.
revision = '0a6f00a1f663'
down_revision = '812b33dce3d1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE xp_po SET type='xp_pto' WHERE type='xp_tpo';")

    op.execute("ALTER INDEX idx_xp_tpo_position RENAME TO idx_xp_pto_position;")

    op.execute("ALTER TABLE xp_tpo RENAME CONSTRAINT xp_tpo_id_fkey TO xp_pto_id_fkey;")
    op.execute("ALTER TABLE xp_tpo RENAME CONSTRAINT xp_tpo_pkey TO xp_pto_pkey;")

    op.execute("ALTER TABLE xp_tpo RENAME TO xp_pto;")

    # change gml:AngleType columns to float
    op.execute('ALTER TABLE xp_ppo ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;')
    op.execute('ALTER TABLE xp_pto ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;')
    op.execute('ALTER TABLE xp_nutzungsschablone ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;')
    op.execute('ALTER TABLE xp_objekt ALTER COLUMN drehwinkel TYPE FLOAT USING drehwinkel::float;')

    # update inheritance hierarchy
    op.execute(
        'INSERT INTO xp_externe_referenz (id, datum, "referenzMimeType", art, "referenzName", beschreibung, file, "georefURL", "referenzURL") '
        'SELECT id, datum, "referenzMimeType", art, "referenzName", beschreibung, file, "georefURL", "referenzURL" FROM xp_spez_externe_referenz')
    op.create_foreign_key('xp_spez_externe_referenz_id_fkey', 'xp_spez_externe_referenz', 'xp_externe_referenz', ['id'],
                          ['id'], ondelete='CASCADE')
    op.drop_column('xp_spez_externe_referenz', 'datum')
    op.drop_column('xp_spez_externe_referenz', 'referenzMimeType')
    op.drop_column('xp_spez_externe_referenz', 'art')
    op.drop_column('xp_spez_externe_referenz', 'referenzName')
    op.drop_column('xp_spez_externe_referenz', 'beschreibung')
    op.drop_column('xp_spez_externe_referenz', 'file')
    op.drop_column('xp_spez_externe_referenz', 'georefURL')
    op.drop_column('xp_spez_externe_referenz', 'referenzURL')
    op.add_column('xp_externe_referenz', sa.Column('type', sa.String(length=50), nullable=True))
    op.execute("UPDATE xp_externe_referenz SET type='xp_spez_externe_referenz' WHERE id in (SELECT id FROM xp_spez_externe_referenz);")
    op.execute("UPDATE xp_externe_referenz SET type='xp_externe_referenz' WHERE type IS NULL")


def downgrade():
    # change gml:AngleType columns back to int
    op.execute('ALTER TABLE xp_ppo ALTER COLUMN drehwinkel TYPE integer USING drehwinkel::integer;')
    op.execute('ALTER TABLE xp_pto ALTER COLUMN drehwinkel TYPE integer USING drehwinkel::integer;')
    op.execute('ALTER TABLE xp_nutzungsschablone ALTER COLUMN drehwinkel TYPE integer USING drehwinkel::integer;')
    op.execute('ALTER TABLE xp_objekt ALTER COLUMN drehwinkel TYPE integer USING drehwinkel::integer;')

    # rename pto back to tpo
    op.execute("UPDATE xp_po SET type='xp_tpo' WHERE type='xp_pto';")

    op.execute("ALTER INDEX idx_xp_pto_position RENAME TO idx_xp_tpo_position;")

    op.execute("ALTER TABLE xp_pto RENAME CONSTRAINT xp_pto_id_fkey TO xp_tpo_id_fkey;")
    op.execute("ALTER TABLE xp_pto RENAME CONSTRAINT xp_pto_pkey TO xp_tpo_pkey;")

    op.execute("ALTER TABLE xp_pto RENAME TO xp_tpo;")

    # revert inheritance hierarchy of xp_externereferenz
    xp_externereferenzart_enum = postgresql.ENUM('Dokument', 'PlanMitGeoreferenz', name='xp_externereferenzart',
                                                 create_type=False)
    referenzMimeType_enum = postgresql.ENUM('application/pdf', 'application/zip', 'application/xml',
                                            'application/msword', 'application/msexcel',
                                            'application/vnd.ogc.sld+xml', 'application/vnd.ogc.wms_xml',
                                            'application/vnd.ogc.gml', 'application/vnd.shp',
                                            'application/vnd.dbf', 'application/vnd.shx',
                                            'application/octet-stream', 'image/vnd.dxf', 'image/vnd.dwg',
                                            'image/jpg', 'image/png', 'image/tiff', 'image/bmp', 'image/ecw',
                                            'image/svg+xml', 'text/html', 'text/plain',
                                            name='xp_mime_types', create_type=False)
    if not context.is_offline_mode():
        xp_externereferenzart_enum.create(op.get_bind(), checkfirst=True)
        referenzMimeType_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('xp_spez_externe_referenz',
                  sa.Column('referenzURL', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('xp_spez_externe_referenz', sa.Column('georefURL', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('xp_spez_externe_referenz', sa.Column('file', postgresql.BYTEA(), autoincrement=False, nullable=True))
    op.add_column('xp_spez_externe_referenz',
                  sa.Column('beschreibung', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('xp_spez_externe_referenz',
                  sa.Column('referenzName', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('xp_spez_externe_referenz',
                  sa.Column('art', xp_externereferenzart_enum, autoincrement=False, nullable=True))
    op.add_column('xp_spez_externe_referenz',
                  sa.Column('referenzMimeType', referenzMimeType_enum, autoincrement=False, nullable=True))
    op.add_column('xp_spez_externe_referenz', sa.Column('datum', sa.DATE(), autoincrement=False, nullable=True))
    op.drop_constraint('xp_spez_externe_referenz_id_fkey', 'xp_spez_externe_referenz', type_='foreignkey')

    op.execute('UPDATE xp_spez_externe_referenz spez SET datum=o.datum, "referenzMimeType"=o."referenzMimeType", art=o.art, "referenzName"=o."referenzName", beschreibung=o.beschreibung, file=o.file, "georefURL"=o."georefURL", "referenzURL"=o."referenzURL" '
               'FROM xp_externe_referenz o WHERE spez.id=o.id;')
    op.execute('DELETE FROM xp_externe_referenz WHERE id in (SELECT id FROM xp_spez_externe_referenz);')
    op.drop_column('xp_externe_referenz', 'type')
