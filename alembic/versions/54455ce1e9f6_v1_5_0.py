"""v1.5.0

Revision ID: 54455ce1e9f6
Revises: 2cee32cfc646
Create Date: 2022-04-20 10:30:40.643937

"""
import os
import sys
from geoalchemy2 import Geometry
from alembic import op, context
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)

# revision identifiers, used by Alembic.
revision = '54455ce1e9f6'
down_revision = '2cee32cfc646'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('bp_schutzflaeche',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('ziel',
                              sa.Enum('SchutzPflege', 'Entwicklung', 'Anlage', 'SchutzPflegeEntwicklung', 'Sonstiges',
                                      name='xp_speziele'), nullable=True),
                    sa.Column('sonstZiel', sa.String(), nullable=True),
                    sa.Column('istAusgleich', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_spe_daten',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('klassifizMassnahme',
                              sa.Enum('ArtentreicherGehoelzbestand', 'NaturnaherWald', 'ExtensivesGruenland',
                                      'Feuchtgruenland', 'Obstwiese', 'NaturnaherUferbereich', 'Roehrichtzone',
                                      'Ackerrandstreifen', 'Ackerbrache', 'Gruenlandbrache', 'Sukzessionsflaeche',
                                      'Hochstaudenflur', 'Trockenrasen', 'Heide', 'Sonstiges',
                                      name='xp_spemassnahmentypen'), nullable=True),
                    sa.Column('massnahmeText', sa.String(), nullable=True),
                    sa.Column('massnahmeKuerzel', sa.String(), nullable=True),
                    sa.Column('bp_schutzflaeche_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.ForeignKeyConstraint(['bp_schutzflaeche_id'], ['bp_schutzflaeche.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('bp_wegerecht',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('typ',
                              sa.ARRAY(sa.Enum('Gehrecht', 'Fahrrecht', 'Radfahrrecht', 'Leitungsrecht', 'Sonstiges',
                                               name='bp_wegerechttypen')), nullable=True),
                    sa.Column('zugunstenVon', sa.String(), nullable=True),
                    sa.Column('thema', sa.String(), nullable=True),
                    sa.Column('breite', sa.Float(), nullable=True),
                    sa.Column('istSchmal', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    bundesland_enum = postgresql.ENUM('BB', 'BE', 'BW', 'BY', 'HB', 'HE', 'HH', 'MV', 'NI', 'NW', 'RP', 'SH', 'SL',
                                      'SN', 'ST', 'TH', 'Bund', name='xp_bundeslaender')

    # RP
    op.create_table('rp_plan',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('bundesland', bundesland_enum, nullable=True),
                    sa.Column('planArt', sa.Enum('Regionalplan', 'SachlicherTeilplanRegionalebene',
                                                 'SachlicherTeilplanLandesebene', 'Braunkohlenplan',
                                                 'LandesweiterRaumordnungsplan', 'StandortkonzeptBund', 'AWZPlan',
                                                 'RaeumlicherTeilplan', 'Sonstiges', name='rp_art'), nullable=False),
                    sa.Column('planungsregion', sa.Integer(), nullable=True),
                    sa.Column('teilabschnitt', sa.Integer(), nullable=True),
                    sa.Column('rechtsstand',
                              sa.Enum('Aufstellungsbeschluss', 'Entwurf', 'EntwurfGenehmigt', 'EntwurfGeaendert',
                                      'EntwurfAufgegeben', 'EntwurfRuht', 'Plan', 'Inkraftgetreten',
                                      'AllgemeinePlanungsabsicht', 'AusserKraft', 'PlanUngueltig',
                                      name='rp_rechtsstand'), nullable=True),
                    sa.Column('aufstellungsbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('auslegungsStartDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('auslegungsEndDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('traegerbeteiligungsStartDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('traegerbeteiligungsEndDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('aenderungenBisDatum', sa.Date(), nullable=True),
                    sa.Column('entwurfsbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('planbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('datumDesInkrafttretens', sa.Date(), nullable=True),
                    sa.Column('verfahren',
                              sa.Enum('Aenderung', 'Teilfortschreibung', 'Neuaufstellung', 'Gesamtfortschreibung',
                                      'Aktualisierung', 'Neubekanntmachung', name='rp_verfahren'), nullable=True),
                    sa.Column('amtlicherSchluessel', sa.String(), nullable=True),
                    sa.Column('genehmigungsbehoerde', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['xp_plan.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('rp_bereich',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('versionBROG', sa.Date(), nullable=True),
                    sa.Column('versionBROGText', sa.String(), nullable=True),
                    sa.Column('versionLPLG', sa.Date(), nullable=True),
                    sa.Column('versionLPLGText', sa.String(), nullable=True),
                    sa.Column('geltungsmassstab', sa.Integer(), nullable=True),
                    sa.Column('gehoertZuPlan_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.ForeignKeyConstraint(['gehoertZuPlan_id'], ['rp_plan.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    # LP
    op.create_table('lp_plan',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('bundesland', bundesland_enum, nullable=True),
                    sa.Column('rechtlicheAussenwirkung', sa.Boolean(), nullable=True),
                    sa.Column('planArt', sa.ARRAY(
                        sa.Enum('Landschaftsprogramm', 'Landschaftsrahmenplan', 'Landschaftsplan', 'Gruenordnungsplan',
                                'Sonstiges', name='lp_planart')), nullable=False),
                    sa.Column('planungstraegerGKZ', sa.String(), nullable=True),
                    sa.Column('planungstraeger', sa.String(), nullable=True),
                    sa.Column('rechtsstand',
                              sa.Enum('Aufstellungsbeschluss', 'Entwurf', 'Plan', 'Wirksamkeit', 'Untergegangen',
                                      name='lp_rechtsstand'), nullable=True),
                    sa.Column('aufstellungsbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('auslegungsDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('tOeBbeteiligungsDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('oeffentlichkeitsbeteiligungDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('aenderungenBisDatum', sa.Date(), nullable=True),
                    sa.Column('entwurfsbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('planbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('inkrafttretenDatum', sa.Date(), nullable=True),
                    sa.Column('sonstVerfahrensDatum', sa.Date(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['xp_plan.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('lp_bereich',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('gehoertZuPlan_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.ForeignKeyConstraint(['gehoertZuPlan_id'], ['lp_plan.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.add_column('xp_externe_referenz',
                  sa.Column('bp_schutzflaeche_massnahme_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('xp_externe_referenz',
                  sa.Column('bp_schutzflaeche_plan_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_schutzflaeche_plan_ref', 'xp_externe_referenz', 'bp_schutzflaeche',
                          ['bp_schutzflaeche_plan_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_schutzflaeche_massnahme_ref', 'xp_externe_referenz', 'bp_schutzflaeche',
                          ['bp_schutzflaeche_massnahme_id'], ['id'], ondelete='CASCADE')

    op.add_column('xp_tpo', sa.Column('skalierung', sa.Float(), nullable=True, server_default='0.5'))
    op.add_column('xp_objekt', sa.Column('skalierung', sa.Float(), nullable=True, server_default='0.5'))
    op.add_column('xp_objekt', sa.Column('drehwinkel', sa.Integer(), nullable=True, server_default='0'))

    # op.drop_constraint('xp_plan_gemeinde_plan_id_fkey', 'xp_plan_gemeinde', type_='foreignkey')
    # op.create_foreign_key('xp_plan_gemeinde_plan_id_fkey', 'xp_plan_gemeinde', 'xp_plan', ['plan_id'], ['id'], ondelete='CASCADE')

    # refactor plangeber relations
    op.add_column('bp_plan', sa.Column('plangeber_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_plangeber_bp_plan', 'bp_plan', 'xp_plangeber', ['plangeber_id'], ['id'])

    op.add_column('fp_plan', sa.Column('plangeber_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_plangeber_fp_plan', 'fp_plan', 'xp_plangeber', ['plangeber_id'], ['id'])

    op.execute("UPDATE bp_plan bp SET plangeber_id = xp.plangeber_id FROM xp_plan xp WHERE xp.id = bp.id;")
    op.execute("UPDATE fp_plan fp SET plangeber_id = xp.plangeber_id FROM xp_plan xp WHERE xp.id = fp.id;")

    op.drop_constraint('xp_plan_plangeber_id_fkey', 'xp_plan', type_='foreignkey')
    op.drop_column('xp_plan', 'plangeber_id')

    # refactor gemeinde relations
    op.add_column('xp_plan_gemeinde', sa.Column('bp_plan_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('xp_plan_gemeinde', sa.Column('fp_plan_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.drop_constraint('xp_plan_gemeinde_plan_id_fkey', 'xp_plan_gemeinde', type_='foreignkey')

    op.create_foreign_key('xp_plan_gemeinde_bp_plan_id_fkey', 'xp_plan_gemeinde', 'bp_plan', ['bp_plan_id'], ['id'],
                          ondelete='CASCADE')
    op.create_foreign_key('xp_plan_gemeinde_fp_plan_id_fkey', 'xp_plan_gemeinde', 'fp_plan', ['fp_plan_id'], ['id'],
                          ondelete='CASCADE')

    op.execute("UPDATE xp_plan_gemeinde g SET bp_plan_id = xp.id FROM xp_plan xp WHERE xp.id = g.plan_id AND xp.type = 'bp_plan';")
    op.execute("UPDATE xp_plan_gemeinde g SET fp_plan_id = xp.id FROM xp_plan xp WHERE xp.id = g.plan_id AND xp.type = 'fp_plan';")

    op.drop_column('xp_plan_gemeinde', 'plan_id')


def downgrade():
    op.drop_column('xp_tpo', 'skalierung')
    op.drop_column('xp_objekt', 'skalierung')
    op.drop_column('xp_objekt', 'drehwinkel')

    op.drop_constraint('fk_schutzflaeche_plan_ref', 'xp_externe_referenz', type_='foreignkey')
    op.drop_constraint('fk_schutzflaeche_massnahme_ref', 'xp_externe_referenz', type_='foreignkey')
    op.drop_column('xp_externe_referenz', 'bp_schutzflaeche_plan_id')
    op.drop_column('xp_externe_referenz', 'bp_schutzflaeche_massnahme_id')

    op.drop_table('xp_spe_daten')
    op.drop_table('bp_schutzflaeche')
    op.drop_table('bp_wegerecht')

    op.drop_table('rp_bereich')
    op.drop_table('rp_plan')
    op.drop_table('lp_bereich')
    op.drop_table('lp_plan')

    op.execute("DELETE FROM xp_objekt CASCADE WHERE type in ('bp_schutzflaeche', 'bp_wegerecht');")
    op.execute("DELETE FROM xp_bereich CASCADE WHERE type in ('rp_bereich', 'lp_bereich');")
    op.execute("DELETE FROM xp_plan CASCADE WHERE type in ('rp_plan', 'lp_plan');")

    op.execute("DROP TYPE xp_speziele CASCADE;")
    op.execute("DROP TYPE xp_spemassnahmentypen CASCADE;")
    op.execute("DROP TYPE bp_wegerechttypen CASCADE;")
    op.execute("DROP TYPE xp_bundeslaender CASCADE;")
    op.execute("DROP TYPE rp_art CASCADE;")
    op.execute("DROP TYPE rp_rechtsstand CASCADE;")
    op.execute("DROP TYPE rp_verfahren CASCADE;")
    op.execute("DROP TYPE lp_planart CASCADE;")
    op.execute("DROP TYPE lp_rechtsstand CASCADE;")

    # revert: refactor plangeber relations
    op.add_column('xp_plan', sa.Column('plangeber_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.create_foreign_key('xp_plan_plangeber_id_fkey', 'xp_plan', 'xp_plangeber', ['plangeber_id'], ['id'])

    op.execute("UPDATE xp_plan xp SET plangeber_id = bp.plangeber_id FROM bp_plan bp WHERE bp.id = xp.id")
    op.execute("UPDATE xp_plan xp SET plangeber_id = fp.plangeber_id FROM fp_plan fp WHERE fp.id = xp.id")

    op.drop_constraint('fk_plangeber_fp_plan', 'fp_plan', type_='foreignkey')
    op.drop_constraint('fk_plangeber_bp_plan', 'bp_plan', type_='foreignkey')
    op.drop_column('bp_plan', 'plangeber_id')
    op.drop_column('fp_plan', 'plangeber_id')

    # revert: refactor gemeinde relations
    op.add_column('xp_plan_gemeinde', sa.Column('plan_id', postgresql.UUID(), autoincrement=False, nullable=True))

    op.drop_constraint('xp_plan_gemeinde_bp_plan_id_fkey', 'xp_plan_gemeinde', type_='foreignkey')
    op.drop_constraint('xp_plan_gemeinde_fp_plan_id_fkey', 'xp_plan_gemeinde', type_='foreignkey')
    op.create_foreign_key('xp_plan_gemeinde_plan_id_fkey', 'xp_plan_gemeinde', 'xp_plan', ['plan_id'], ['id'])

    op.execute("UPDATE xp_plan_gemeinde g SET plan_id = xp.id FROM xp_plan xp WHERE xp.id = g.bp_plan_id;")
    op.execute("UPDATE xp_plan_gemeinde g SET plan_id = xp.id FROM xp_plan xp WHERE xp.id = g.fp_plan_id;")

    op.drop_column('xp_plan_gemeinde', 'fp_plan_id')
    op.drop_column('xp_plan_gemeinde', 'bp_plan_id')
