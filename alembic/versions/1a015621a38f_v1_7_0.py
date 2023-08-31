"""v1.7.0

Revision ID: 1a015621a38f
Revises: 873e18b73036
Create Date: 2022-10-05 09:41:30.415953

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
revision = '1a015621a38f'
down_revision = '873e18b73036'
branch_labels = None
depends_on = None


def upgrade():
    allgartderbaulnutzung_enum = postgresql.ENUM('WohnBauflaeche', 'GemischteBauflaeche', 'GewerblicheBauflaeche',
                                                 'SonderBauflaeche', 'Sonstiges', name='xp_allgartderbaulnutzung',
                                                 create_type=False)
    besondereartderbaulnutzung_enum = postgresql.ENUM('Kleinsiedlungsgebiet', 'ReinesWohngebiet', 'AllgWohngebiet',
                                                      'BesonderesWohngebiet', 'Dorfgebiet', 'Mischgebiet',
                                                      'UrbanesGebiet',
                                                      'Kerngebiet', 'Gewerbegebiet', 'Industriegebiet',
                                                      'SondergebietErholung',
                                                      'SondergebietSonst', 'Wochenendhausgebiet', 'Sondergebiet',
                                                      'SonstigesGebiet',
                                                      name='xp_besondereartderbaulnutzung', create_type=False)

    sondernutzung_enum = postgresql.ENUM('KeineSondernutzung', 'Wochendhausgebiet', 'Ferienhausgebiet',
                                         'Campingplatzgebiet',
                                         'Kurgebiet', 'SonstSondergebietErholung', 'Einzelhandelsgebiet',
                                         'GrossflaechigerEinzelhandel', 'Ladengebiet', 'Einkaufszentrum',
                                         'SonstGrossflEinzelhandel', 'Verkehrsuebungsplatz', 'Hafengebiet',
                                         'SondergebietErneuerbareEnergie', 'SondergebietMilitaer',
                                         'SondergebietLandwirtschaft',
                                         'SondergebietSport', 'SondergebietGesundheitSoziales', 'Klinikgebiet',
                                         'Golfplatz',
                                         'SondergebietKultur', 'SondergebietTourismus',
                                         'SondergebietBueroUndVerwaltung',
                                         'SondergebietJustiz', 'SondergebietHochschuleForschung', 'SondergebietMesse',
                                         'SondergebietAndereNutzungen', name='xp_sondernutzungen', create_type=False)

    zweckbestimmung_enum = postgresql.ENUM('OeffentlicheVerwaltung', 'KommunaleEinrichtung',
                                           'BetriebOeffentlZweckbestimmung', 'AnlageBundLand',
                                           'BildungForschung', 'Schule', 'Hochschule',
                                           'BerufsbildendeSchule', 'Forschungseinrichtung', 'Kirche',
                                           'Sakralgebaeude', 'KirchlicheVerwaltung', 'Kirchengemeinde',
                                           'Sozial', 'EinrichtungKinder', 'EinrichtungJugendliche',
                                           'EinrichtungFamilienErwachsene', 'EinrichtungSenioren',
                                           'SonstigeSozialeEinrichtung', 'EinrichtungBehinderte',
                                           'Gesundheit', 'Krankenhaus', 'Kultur', 'MusikTheater',
                                           'Bildung', 'Sport', 'Bad', 'SportplatzSporthalle',
                                           'SicherheitOrdnung', 'Feuerwehr', 'Schutzbauwerk', 'Justiz',
                                           'Infrastruktur', 'Post', 'Sonstiges',
                                           name='xp_zweckbestimmunggemeinbedarf', create_type=False)

    zweck_gruen_enum = postgresql.ENUM('Parkanlage', 'ParkanlageHistorisch', 'ParkanlageNaturnah',
                                       'ParkanlageWaldcharakter', 'NaturnaheUferParkanlage',
                                       'Dauerkleingarten', 'ErholungsGaerten', 'Sportplatz',
                                       'Reitsportanlage', 'Hundesportanlage', 'Wassersportanlage',
                                       'Schiessstand', 'Golfplatz', 'Skisport', 'Tennisanlage',
                                       'Spielplatz', 'Bolzplatz', 'Abenteuerspielplatz', 'Zeltplatz',
                                       'Campingplatz', 'Badeplatz', 'FreizeitErholung',
                                       'Kleintierhaltung', 'Festplatz', 'SpezGruenflaeche',
                                       'StrassenbegleitGruen', 'BoeschungsFlaeche', 'FeldWaldWiese',
                                       'Uferschutzstreifen', 'Abschirmgruen',
                                       'UmweltbildungsparkSchaugatter', 'RuhenderVerkehr', 'Friedhof',
                                       'Sonstiges', 'Gaertnerei', name='xp_zweckbestimmunggruen', create_type=False)

    zweck_wasser_enum = postgresql.ENUM('Hafen', 'Sportboothafen', 'Wasserflaeche', 'Fliessgewaesser', 'Sonstiges',
                                        name='xp_zweckbestimmunggewaesser', create_type=False)
    nutzungsform_enum = postgresql.ENUM('Privat', 'Oeffentlich', name='xp_nutzungsform', create_type=False)
    betretung_wald_enum = postgresql.ENUM('KeineZusaetzlicheBetretung', 'Radfahren', 'Reiten', 'Fahren', 'Hundesport',
                                          'Sonstiges', name='xp_waldbetretungtyp', create_type=False)
    eigentum_wald_enum = postgresql.ENUM('OeffentlicherWald', 'Staatswald', 'Koerperschaftswald', 'Kommunalwald',
                                         'Stiftungswald', 'Privatwald', 'Gemeinschaftswald', 'Genossenschaftswald',
                                         'Kirchenwald', 'Sonstiges', name='xp_eigentumsartwald', create_type=False)
    zweck_wald_enum = postgresql.ENUM('Naturwald', 'Waldschutzgebiet', 'Nutzwald', 'Erholungswald', 'Schutzwald',
                                      'Bodenschutzwald', 'Biotopschutzwald', 'NaturnaherWald',
                                      'SchutzwaldSchaedlicheUmwelteinwirkungen', 'Schonwald', 'Bannwald',
                                      'FlaecheForstwirtschaft', 'ImmissionsgeschaedigterWald', 'Sonstiges',
                                      name='xp_zweckbestimmungwald', create_type=False)
    zweck_sport_enum = postgresql.ENUM('Sportanlage', 'Spielanlage', 'SpielSportanlage', 'Sonstiges',
                                       name='xp_zweckbestimmungspielsportanlage', create_type=False)
    zweck_landwirtschaft_enum = postgresql.ENUM('LandwirtschaftAllgemein', 'Ackerbau', 'WiesenWeidewirtschaft',
                                                'GartenbaulicheErzeugung', 'Obstbau', 'Weinbau', 'Imkerei',
                                                'Binnenfischerei', 'Sonstiges',
                                                name='xp_zweckbestimmunglandwirtschaft', create_type=False)

    if not context.is_offline_mode():
        allgartderbaulnutzung_enum.create(op.get_bind(), checkfirst=True)
        besondereartderbaulnutzung_enum.create(op.get_bind(), checkfirst=True)
        sondernutzung_enum.create(op.get_bind(), checkfirst=True)
        zweckbestimmung_enum.create(op.get_bind(), checkfirst=True)
        zweck_gruen_enum.create(op.get_bind(), checkfirst=True)
        zweck_wasser_enum.create(op.get_bind(), checkfirst=True)
        nutzungsform_enum.create(op.get_bind(), checkfirst=True)
        zweck_landwirtschaft_enum.create(op.get_bind(), checkfirst=True)
        zweck_sport_enum.create(op.get_bind(), checkfirst=True)
        zweck_wald_enum.create(op.get_bind(), checkfirst=True)
        eigentum_wald_enum.create(op.get_bind(), checkfirst=True)

    op.create_geospatial_table('fp_objekt',
                               sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                               sa.Column('rechtscharakter',
                                         sa.Enum('Darstellung', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk',
                                                 'Kennzeichnung', 'Unbekannt', name='fp_rechtscharakter'),
                                         nullable=False),
                               sa.Column('vonGenehmigungAusgenommen', sa.Boolean(), nullable=True),
                               sa.Column('position',
                                         Geometry(spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'),
                                         nullable=True),
                               sa.Column('flaechenschluss', sa.Boolean(), nullable=True),
                               sa.ForeignKeyConstraint(['id'], ['xp_objekt.id'], ondelete='CASCADE'),
                               sa.PrimaryKeyConstraint('id')
                               )
    op.create_geospatial_index('idx_fp_objekt_position', 'fp_objekt', ['position'], unique=False,
                               postgresql_using='gist', postgresql_ops={})
    op.create_table('fp_baugebiet',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('GFZ', sa.Float(), nullable=True),
                    sa.Column('GFZmin', sa.Float(), nullable=True),
                    sa.Column('GFZmax', sa.Float(), nullable=True),
                    sa.Column('BMZ', sa.Float(), nullable=True),
                    sa.Column('GRZ', sa.Float(), nullable=True),
                    sa.Column('allgArtDerBaulNutzung', allgartderbaulnutzung_enum, nullable=True),
                    sa.Column('besondereArtDerBaulNutzung', besondereartderbaulnutzung_enum, nullable=True),
                    sa.Column('sonderNutzung', sa.ARRAY(sondernutzung_enum), nullable=True),
                    sa.Column('nutzungText', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_gemeinbedarf',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('zweckbestimmung', zweckbestimmung_enum, nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_gewaesser',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('zweckbestimmung', zweck_wasser_enum, nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_gruen',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('zweckbestimmung', zweck_gruen_enum, nullable=True),
                    sa.Column('nutzungsform', nutzungsform_enum, nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_landwirtschaft',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('zweckbestimmung', zweck_landwirtschaft_enum, nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_spiel_sportanlage',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('zweckbestimmung', zweck_sport_enum, nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_strassenverkehr',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('zweckbestimmung', sa.Enum('Autobahn', 'Hauptverkehrsstrasse', 'Ortsdurchfahrt',
                                                         'SonstigerVerkehrswegAnlage', 'VerkehrsberuhigterBereich',
                                                         'Platz', 'Fussgaengerbereich', 'RadGehweg', 'Radweg', 'Gehweg',
                                                         'Wanderweg', 'ReitKutschweg', 'Rastanlage', 'Busbahnhof',
                                                         'UeberfuehrenderVerkehrsweg', 'UnterfuehrenderVerkehrsweg',
                                                         'Wirtschaftsweg', 'LandwirtschaftlicherVerkehr',
                                                         'RuhenderVerkehr', 'Parkplatz', 'FahrradAbstellplatz',
                                                         'P_RAnlage', 'CarSharing', 'BikeSharing', 'B_RAnlage',
                                                         'Parkhaus', 'Mischverkehrsflaeche', 'Ladestation', 'Sonstiges',
                                                         name='fp_zweckbestimmungstrassenverkehr'), nullable=True),
                    sa.Column('nutzungsform', nutzungsform_enum, nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_wald',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('zweckbestimmung', zweck_wald_enum, nullable=True),
                    sa.Column('eigentumsart', eigentum_wald_enum, nullable=True),
                    sa.Column('betreten', sa.ARRAY(betretung_wald_enum), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.execute("DELETE FROM xp_objekt CASCADE WHERE type in ('fp_wald', 'fp_strassenverkehr', 'fp_spiel_sportanlage', "
               "'fp_landwirtschaft', 'fp_gruen', 'fp_gewaesser', 'fp_gemeinbedarf', "
               "'fp_baugebiet');")

    op.drop_table('fp_wald')
    op.drop_table('fp_strassenverkehr')
    op.drop_table('fp_spiel_sportanlage')
    op.drop_table('fp_landwirtschaft')
    op.drop_table('fp_gruen')
    op.drop_table('fp_gewaesser')
    op.drop_table('fp_gemeinbedarf')
    op.drop_table('fp_baugebiet')
    op.drop_geospatial_index('idx_fp_objekt_position', table_name='fp_objekt', postgresql_using='gist',
                             column_name='position')
    op.drop_geospatial_table('fp_objekt')

    op.execute("DROP TYPE fp_zweckbestimmungstrassenverkehr CASCADE;")
    op.execute("DROP TYPE fp_rechtscharakter CASCADE;")
    # ### end Alembic commands ###
