"""v2.3.0

Revision ID: 346f4a91caf3
Revises: ce95b86bc010
Create Date: 2024-01-10 11:34:48.880466

"""
import os
import sys

from alembic import op, context
import sqlalchemy as sa

from alembic_postgresql_enum import ColumnType
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)

# revision identifiers, used by Alembic.
revision = '346f4a91caf3'
down_revision = 'ce95b86bc010'
branch_labels = None
depends_on = None


def upgrade():
    nebenanlagen_enum = postgresql.ENUM('Stellplaetze', 'Garagen', 'Spielplatz', 'Carport', 'Tiefgarage',
                                        'Nebengebaeude',
                                        'AbfallSammelanlagen', 'EnergieVerteilungsanlagen', 'AbfallWertstoffbehaelter',
                                        'Fahrradstellplaetze', 'Sonstiges',
                                        name='bp_zweckbestimmungnebenanlagen')

    op.create_table('bp_nebenanlage',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('zweckbestimmung', postgresql.ARRAY(nebenanlagen_enum)),
                    sa.Column('Zmax', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('bp_zweckbestimmung_nebenanlagen',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('allgemein', nebenanlagen_enum),
                    sa.Column('textlicheErgaenzung', sa.String(), nullable=True),
                    sa.Column('aufschrift', sa.String(), nullable=True),
                    sa.Column('nebenanlage_id', sa.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['nebenanlage_id'], ['bp_nebenanlage.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('so_luftverkehr',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('artDerFestlegung', sa.Enum('Flughafen', 'Landeplatz', 'Segelfluggelaende',
                                                          'HubschrauberLandeplatz', 'Ballonstartplatz', 'Haengegleiter',
                                                          'Gleitsegler', 'Laermschutzbereich',
                                                          'Baubeschraenkungsbereich', 'Sonstiges',
                                                          name='so_klassifiznachluftverkehrsrecht'), nullable=True),
                    sa.Column('detailArtDerFestlegung_id', sa.UUID(), nullable=True),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('nummer', sa.String(), nullable=True),
                    sa.Column('laermschutzzone', sa.Enum('TagZone1', 'TagZone2', 'Nacht',
                                                         name='so_laermschutzzonetypen'), nullable=True),
                    sa.ForeignKeyConstraint(['detailArtDerFestlegung_id'], ['codelist_values.id'], ),
                    sa.ForeignKeyConstraint(['id'], ['so_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('xp_verbundener_plan',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('planName', sa.String(), nullable=True),
                    sa.Column('rechtscharakter',
                              sa.Enum('Aenderung', 'Ergaenzung', 'Aufhebung', 'Aufhebungsverfahren',
                                      'Ueberplanung', name='xp_rechtscharakterplanaenderung')),
                    sa.Column('aenderungsArt',
                              sa.Enum('Änderung', 'Ersetzung', 'Ergänzung', 'Streichung', 'Aufhebung',
                                      'Überplanung', name='xp_aenderungsarten')),
                    sa.Column('nummer', sa.String(), nullable=True),
                    sa.Column('aenderungsdatum', sa.Date(), nullable=True),
                    sa.Column('aendert_verbundenerPlan_id', sa.UUID(), nullable=True),
                    sa.Column('wurdeGeaendertVon_verbundenerPlan_id', sa.UUID(), nullable=True),
                    sa.Column('aendertPlan_verbundenerPlan_id', sa.UUID(), nullable=True),
                    sa.Column('wurdeGeaendertVonPlan_verbundenerPlan_id', sa.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['aendert_verbundenerPlan_id'], ['xp_plan.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['wurdeGeaendertVon_verbundenerPlan_id'], ['xp_plan.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['aendertPlan_verbundenerPlan_id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['wurdeGeaendertVonPlan_verbundenerPlan_id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('bp_generisches_objekt',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_generisches_objekt',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('bp_immissionsschutz',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('nutzung', sa.String(), nullable=True),
                    sa.Column('laermpegelbereich', sa.Enum('I', 'II', 'III', 'IV', 'V', 'VI', 'VII',
                                                           'SpezifizierungBereich', name='bp_laermpegelbereich'),
                              nullable=True),
                    sa.Column('massgeblAussenLaermpegelTag', sa.Float(), nullable=True),
                    sa.Column('massgeblAussenLaermpegelNacht', sa.Float(), nullable=True),
                    sa.Column('typ', sa.Enum('Schutzflaeche', 'BesondereAnlagenVorkehrungen',
                                             name='xp_immissionsschutztypen'), nullable=True),
                    sa.Column('technVorkehrung', sa.Enum('Laermschutzvorkehrung',
                                                         'FassadenMitSchallschutzmassnahmen', 'Laermschutzwand',
                                                         'Laermschutzwall', 'SonstigeVorkehrung',
                                                         name='xp_technvorkehrungenimmissionsschutz'), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_foreign_key(None, 'bp_einfahrtpunkt', 'bp_objekt', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'bp_keine_ein_ausfahrt', 'bp_objekt', ['id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'bp_nutzungsgrenze', 'bp_objekt', ['id'], ['id'], ondelete='CASCADE')

    op.add_column('bp_komplexe_sondernutzung', sa.Column('detail_id', sa.UUID(), nullable=True))
    op.add_column('bp_zweckbestimmung_gruen', sa.Column('detail_id', sa.UUID(), nullable=True))

    op.alter_column('lp_plan', 'bundesland',
                    existing_type=postgresql.ENUM('BB', 'BE', 'BW', 'BY', 'HB', 'HE', 'HH', 'MV', 'NI', 'NW', 'RP',
                                                  'SH', 'SL', 'SN', 'ST', 'TH', 'Bund', name='xp_bundeslaender'),
                    nullable=False)
    op.alter_column('lp_plan', 'rechtlicheAussenwirkung',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)
    op.alter_column('so_strassenverkehr', 'hatDarstellungMitBesondZweckbest',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)

    op.create_foreign_key(None, 'xp_objekt', 'xp_gesetzliche_grundlage', ['gesetzlicheGrundlage_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bp_komplexe_sondernutzung', 'detail_id')
    op.drop_column('bp_zweckbestimmung_gruen', 'detail_id')

    op.execute("DELETE FROM xp_objekt CASCADE WHERE type in ('bp_nebenanlage', 'so_luftverkehr', "
               "'bp_generisches_objekt', 'fp_generisches_objekt', 'bp_immissionsschutz');")

    op.drop_table('bp_zweckbestimmung_nebenanlagen')
    op.drop_table('bp_nebenanlage')
    op.execute('DROP TYPE bp_zweckbestimmungnebenanlagen CASCADE;')

    op.drop_table('so_luftverkehr')
    op.execute('DROP TYPE so_laermschutzzonetypen;')
    op.execute('DROP TYPE so_klassifiznachluftverkehrsrecht;')

    op.drop_table('xp_verbundener_plan')
    op.execute('DROP TYPE xp_aenderungsarten;')
    op.execute('DROP TYPE xp_rechtscharakterplanaenderung;')

    op.drop_table('bp_generisches_objekt')
    op.drop_table('fp_generisches_objekt')

    op.drop_table('bp_immissionsschutz')
    op.execute('DROP TYPE bp_laermpegelbereich;')
    op.execute('DROP TYPE xp_immissionsschutztypen;')
    op.execute('DROP TYPE xp_technvorkehrungenimmissionsschutz;')
    # ### end Alembic commands ###
