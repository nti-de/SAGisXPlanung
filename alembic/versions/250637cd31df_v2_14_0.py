"""v2.14.0

Revision ID: 250637cd31df
Revises: 2b1452b49cc5
Create Date: 2026-04-22 09:55:58.941850

"""
import os
import sys

from alembic import op, context
import sqlalchemy as sa

from alembic_postgresql_enum import ColumnType
from alembic_postgresql_enum import TableReference
from sqlalchemy.dialects import postgresql

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)


# revision identifiers, used by Alembic.
revision = '250637cd31df'
down_revision = '2b1452b49cc5'
branch_labels = None
depends_on = None


NEW_ENUMS = [
    ('xp_grenzetypen',
     'Bundesgrenze', 'Landesgrenze', 'Regierungsbezirksgrenze', 'Bezirksgrenze',
     'Kreisgrenze', 'Gemeindegrenze', 'Verbandsgemeindegrenze', 'Samtgemeindegrenze',
     'Mitgliedsgemeindegrenze', 'Amtsgrenze', 'Stadtteilgrenze', 'VorgeschlageneGrundstuecksgrenze',
     'GrenzeBestehenderBebauungsplan', 'SonstGrenze'),
    ('so_klassifizgelaendemorphologie',
     'Terassenkante', 'Rinne', 'EhemMaeander', 'SonstigeStruktur'),
    ('so_klassifizschutzgebietsonstrecht',
     'Laermschutzbereich', 'SchutzzoneLeitungstrasse', 'Sonstiges'),
    ('so_rechtsstandgebiettyp',
     'VorbereitendeUntersuchung', 'Aufstellung', 'Festlegung', 'Abgeschlossen',
     'Verstetigung', 'Sonstiges'),
    ('so_gebietsart',
     'Umlegungsgebiet', 'StaedtebaulicheSanierung', 'StaedtebaulicheEntwicklungsmassnahme',
     'Stadtumbaugebiet', 'SozialeStadt', 'BusinessImprovementDistrict', 'HousingImprovementDistrict',
     'Erhaltungsverordnung', 'ErhaltungsverordnungStaedtebaulicheGestalt',
     'ErhaltungsverordnungWohnbevoelkerung', 'ErhaltungsverordnungUmstrukturierung',
     'Erhaltungsgebiet', 'ErhaltungsgebietStaedtebaulicheGestalt',
     'ErhaltungsgebietWohnbevoelkerung', 'ErhaltungsgebietUmstrukturierung',
     'StaedtebaulEntwicklungskonzeptInnenentwicklung', 'GebietMitAngespanntemWohnungsmarkt',
     'GenehmigungWohnungseigentum', 'Sonstiges'),
    ('so_rechtlichegrundlagebaubeschraenkung',
     'Luftverkehrsrecht', 'Strassenverkehrsrecht', 'SonstigesRecht'),
    ('so_klassifizbaubeschraenkung',
     'Bauverbotszone', 'Baubeschraenkungszone', 'Waldabstand', 'SonstigeBeschraenkung'),
    ('so_rechtlichegrundlagebauverbot',
     'Luftverkehrsrecht', 'Strassenverkehrsrecht', 'SonstigesRecht'),
    ('so_klassifizbauverbot',
     'Bauverbotszone', 'Baubeschraenkungszone', 'Waldabstand', 'SonstigeBeschraenkung'),
    ('fp_massnahmeklimawandeltypen',
     'ErhaltFreiflaechen', 'ErhaltPrivGruen', 'ErhaltOeffentlGruen', 'ErhaltKaltluftschneise',
     'SonstMassnahme'),
    ('bp_zweckbestimmungentmf',
     'Luftreinhaltung', 'NutzungErneurerbarerEnergien', 'MinderungStoerfallfolgen'),
    ('bp_abstandsmasstypen',
     'Masspfeil', 'Masskreis'),
    ('bp_schallleistungspegelberechnungsgrundlage',
     'DIN45691', 'DIN18005', 'VDI2714', 'ISO9613_2'),
    ('bp_schallleistungspegeltypen',
     'LEK', 'IFSP', 'FSP'),
    ('bp_gebaeudestellungtypen',
     'Firstrichtung', 'Dachneigungsrichtung', 'StellungBaulAnlagen'),
    ('bp_speziellebauweisetypen',
     'Durchfahrt', 'Durchgang', 'DurchfahrtDurchgang', 'Auskragung', 'Arkade',
     'Luftgeschoss', 'Bruecke', 'Tunnel', 'Rampe', 'Sonstiges'),
    ('bp_zweckbestimmunggemeinschaftsanlagen',
     'Gemeinschaftsstellplaetze', 'Gemeinschaftsgaragen', 'Spielplatz', 'Carport',
     'GemeinschaftsTiefgarage', 'Nebengebaeude', 'AbfallSammelanlagen',
     'EnergieVerteilungsanlagen', 'AbfallWertstoffbehaelter', 'Freizeiteinrichtungen',
     'Laermschutzanlagen', 'AbwasserRegenwasser', 'Ausgleichsmassnahmen',
     'Fahrradstellplaetze', 'Gemeinschaftsdachgaerten', 'GemeinschaftlichNutzbareDachflaechen',
     'Sonstiges'),
]

NEW_TABLE_TYPES = [
    'bp_abstand', 'bp_abstands_mass', 'bp_abweichung_baugrenze',
    'bp_abweichung_ueberbaubare_grundstuecksflaeche', 'bp_ausgleich', 'bp_ausgleichsmassnahme',
    'bp_einfahrtsbereich', 'bp_eingriffsbereich', 'bp_emissionskontingent_laerm',
    'bp_festsetzung_landesrecht', 'bp_freiflaeche', 'bp_gebaeude_flaeche', 'bp_gebaeude_stellung',
    'bp_gemeinschaftsanlage', 'bp_hoehen_mass', 'bp_kleintierhaltung',
    'bp_nicht_ueberbaubare_grundstuecksflaeche', 'bp_persgruppen_bestimmte_flaeche',
    'bp_regelung_vergnuegungsstaetten', 'bp_richtungssektorgrenze', 'bp_spezielle_bauweise',
    'bp_technische_massnahmen', 'bp_unverbindliche_vormerkung', 'bp_zentraler_versorgungsbereich',
    'bp_zusatzkontingent_laerm', 'bp_zusatzkontingent_laerm_flaeche',
    'fp_anpassung_klimawandel', 'fp_ausgleich', 'fp_darstellung_landesrecht',
    'fp_keine_zentr_abwasser_beseitigung', 'fp_textabschnittsflaeche',
    'fp_textliche_darstellungsflaeche', 'fp_unverbindliche_vormerkung',
    'fp_vorbehalte_flaeche', 'fp_zentraler_versorgungsbereich',
    'so_baubeschraenkung', 'so_bauverbotszone', 'so_forstrecht', 'so_gebiet',
    'so_gelaendemorphologie', 'so_grenze', 'so_schutzgebiet_sonstiges_recht',
    'assoc_detail_landesrecht', 'assoc_gemeinschaftsanlage_eigentuemer',
    'bp_emissionskontingent_laerm_gebiet', 'bp_richtungssektor', 'bp_veraenderungssperre',
    'bp_zweckbestimmung_gemeinschaftsanlage', 'assoc_detail_gemeinschaftsanlagen',
]


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    for enum_name, *labels in NEW_ENUMS:
        enum = postgresql.ENUM(*labels, name=enum_name, create_type=False)
        enum.create(op.get_bind(), checkfirst=True)

    op.create_table('bp_abstand',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tiefe', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_abstand_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_abstand'))
    )
    op.create_table('bp_abstands_mass',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('typ', postgresql.ENUM('Masspfeil', 'Masskreis', name='bp_abstandsmasstypen', create_type=False), nullable=True),
    sa.Column('wert', sa.Float(), nullable=True),
    sa.Column('startWinkel', sa.Float(), nullable=True),
    sa.Column('endWinkel', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_abstands_mass_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_abstands_mass'))
    )
    op.create_table('bp_abweichung_baugrenze',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_abweichung_baugrenze_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_abweichung_baugrenze'))
    )
    op.create_table('bp_abweichung_ueberbaubare_grundstuecksflaeche',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_abweichung_ueberbaubare_grundstuecksflaeche_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_abweichung_ueberbaubare_grundstuecksflaeche'))
    )
    op.create_table('bp_ausgleich',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('ziel', postgresql.ENUM('SchutzPflege', 'Entwicklung', 'Anlage', 'SchutzPflegeEntwicklung', 'Sonstiges', name='xp_speziele', create_type=False), nullable=True),
    sa.Column('sonstZiel', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_ausgleich_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_ausgleich'))
    )
    op.create_table('bp_ausgleichsmassnahme',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('ziel', postgresql.ENUM('SchutzPflege', 'Entwicklung', 'Anlage', 'SchutzPflegeEntwicklung', 'Sonstiges', name='xp_speziele', create_type=False), nullable=True),
    sa.Column('sonstZiel', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_ausgleichsmassnahme_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_ausgleichsmassnahme'))
    )
    op.create_table('bp_einfahrtsbereich',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('typ', postgresql.ENUM('Einfahrt', 'Ausfahrt', 'EinAusfahrt', name='bp_einfahrttypen', create_type=False), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_einfahrtsbereich_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_einfahrtsbereich'))
    )
    op.create_table('bp_eingriffsbereich',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_eingriffsbereich_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_eingriffsbereich'))
    )
    op.create_table('bp_emissionskontingent_laerm',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('pegelTyp', postgresql.ENUM('LEK', 'IFSP', 'FSP', name='bp_schallleistungspegeltypen', create_type=False), nullable=True),
    sa.Column('berechnungsgrundlage', postgresql.ENUM('DIN45691', 'DIN18005', 'VDI2714', 'ISO9613_2', name='bp_schallleistungspegelberechnungsgrundlage', create_type=False), nullable=True),
    sa.Column('berechnungsgrundlageDatum', sa.Date(), nullable=True),
    sa.Column('ekwertTag', sa.Float(), nullable=False),
    sa.Column('ekwertNacht', sa.Float(), nullable=False),
    sa.Column('erlaeuterung', sa.String(), nullable=True),
    sa.Column('bp_objekt_id', sa.UUID(), nullable=True),
    sa.Column('so_objekt_id', sa.UUID(), nullable=True),
    sa.Column('bp_objekt_gebiet_id', sa.UUID(), nullable=True),
    sa.Column('so_objekt_gebiet_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['bp_objekt_gebiet_id'], ['bp_objekt.id'], name=op.f('fk_bp_emissionskontingent_laerm_bp_objekt_gebiet_id_bp_objekt'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['bp_objekt_id'], ['bp_objekt.id'], name=op.f('fk_bp_emissionskontingent_laerm_bp_objekt_id_bp_objekt'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['so_objekt_gebiet_id'], ['so_objekt.id'], name=op.f('fk_bp_emissionskontingent_laerm_so_objekt_gebiet_id_so_objekt'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['so_objekt_id'], ['so_objekt.id'], name=op.f('fk_bp_emissionskontingent_laerm_so_objekt_id_so_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_emissionskontingent_laerm'))
    )
    op.create_table('bp_festsetzung_landesrecht',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('kurzbeschreibung', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_festsetzung_landesrecht_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_festsetzung_landesrecht'))
    )
    op.create_table('bp_freiflaeche',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('nutzung', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_freiflaeche_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_freiflaeche'))
    )
    op.create_table('bp_gebaeude_flaeche',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_gebaeude_flaeche_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_gebaeude_flaeche'))
    )
    op.create_table('bp_gebaeude_stellung',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('typ', postgresql.ENUM('Firstrichtung', 'Dachneigungsrichtung', 'StellungBaulAnlagen', name='bp_gebaeudestellungtypen', create_type=False), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_gebaeude_stellung_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_gebaeude_stellung'))
    )
    op.create_table('bp_gemeinschaftsanlage',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('zweckbestimmung', postgresql.ARRAY(postgresql.ENUM('Gemeinschaftsstellplaetze', 'Gemeinschaftsgaragen', 'Spielplatz', 'Carport', 'GemeinschaftsTiefgarage', 'Nebengebaeude', 'AbfallSammelanlagen', 'EnergieVerteilungsanlagen', 'AbfallWertstoffbehaelter', 'Freizeiteinrichtungen', 'Laermschutzanlagen', 'AbwasserRegenwasser', 'Ausgleichsmassnahmen', 'Fahrradstellplaetze', 'Gemeinschaftsdachgaerten', 'GemeinschaftlichNutzbareDachflaechen', 'Sonstiges', name='bp_zweckbestimmunggemeinschaftsanlagen', create_type=False)), nullable=True),
    sa.Column('Zmax', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_gemeinschaftsanlage_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_gemeinschaftsanlage'))
    )
    op.create_table('bp_hoehen_mass',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_hoehen_mass_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_hoehen_mass'))
    )
    op.create_table('bp_kleintierhaltung',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_kleintierhaltung_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_kleintierhaltung'))
    )
    op.create_table('bp_nicht_ueberbaubare_grundstuecksflaeche',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('nutzung_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_nicht_ueberbaubare_grundstuecksflaeche_id_bp_objekt'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['nutzung_id'], ['codelist_values.id'], name=op.f('fk_bp_nicht_ueberbaubare_grundstuecksflaeche_nutzung_id_codelist_values')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_nicht_ueberbaubare_grundstuecksflaeche'))
    )
    op.create_table('bp_persgruppen_bestimmte_flaeche',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_persgruppen_bestimmte_flaeche_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_persgruppen_bestimmte_flaeche'))
    )
    op.create_table('bp_regelung_vergnuegungsstaetten',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('zulaessigkeit', postgresql.ENUM('Zulaessig', 'NichtZulaessig', 'AusnahmsweiseZulaessig', name='bp_zulaessigkeit', create_type=False), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_regelung_vergnuegungsstaetten_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_regelung_vergnuegungsstaetten'))
    )
    op.create_table('bp_richtungssektorgrenze',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('winkel', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_richtungssektorgrenze_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_richtungssektorgrenze'))
    )
    op.create_table('bp_spezielle_bauweise',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('typ', postgresql.ENUM('Durchfahrt', 'Durchgang', 'DurchfahrtDurchgang', 'Auskragung', 'Arkade', 'Luftgeschoss', 'Bruecke', 'Tunnel', 'Rampe', 'Sonstiges', name='bp_speziellebauweisetypen', create_type=False), nullable=True),
    sa.Column('sonstTyp_id', sa.UUID(), nullable=True),
    sa.Column('Bmin', sa.Float(), nullable=True),
    sa.Column('Bmax', sa.Float(), nullable=True),
    sa.Column('Tmin', sa.Float(), nullable=True),
    sa.Column('Tmax', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_spezielle_bauweise_id_bp_objekt'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sonstTyp_id'], ['codelist_values.id'], name=op.f('fk_bp_spezielle_bauweise_sonstTyp_id_codelist_values')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_spezielle_bauweise'))
    )
    op.create_table('bp_technische_massnahmen',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('zweckbestimmung', postgresql.ENUM('Luftreinhaltung', 'NutzungErneurerbarerEnergien', 'MinderungStoerfallfolgen', name='bp_zweckbestimmungentmf', create_type=False), nullable=False),
    sa.Column('technischeMassnahme', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_technische_massnahmen_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_technische_massnahmen'))
    )
    op.create_table('bp_unverbindliche_vormerkung',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('vormerkung', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_unverbindliche_vormerkung_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_unverbindliche_vormerkung'))
    )
    op.create_table('bp_zentraler_versorgungsbereich',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_zentraler_versorgungsbereich_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_zentraler_versorgungsbereich'))
    )
    op.create_table('bp_zusatzkontingent_laerm',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('bezeichnung', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_zusatzkontingent_laerm_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_zusatzkontingent_laerm'))
    )
    op.create_table('bp_zusatzkontingent_laerm_flaeche',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('bezeichnung', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_zusatzkontingent_laerm_flaeche_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_zusatzkontingent_laerm_flaeche'))
    )
    op.create_table('fp_anpassung_klimawandel',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('massnahme', postgresql.ENUM('ErhaltFreiflaechen', 'ErhaltPrivGruen', 'ErhaltOeffentlGruen', 'ErhaltKaltluftschneise', 'SonstMassnahme', name='fp_massnahmeklimawandeltypen', create_type=False), nullable=True),
    sa.Column('detailMassnahme_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['detailMassnahme_id'], ['codelist_values.id'], name=op.f('fk_fp_anpassung_klimawandel_detailMassnahme_id_codelist_values')),
    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], name=op.f('fk_fp_anpassung_klimawandel_id_fp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fp_anpassung_klimawandel'))
    )
    op.create_table('fp_ausgleich',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('ziel', postgresql.ENUM('SchutzPflege', 'Entwicklung', 'Anlage', 'SchutzPflegeEntwicklung', 'Sonstiges', name='xp_speziele', create_type=False), nullable=True),
    sa.Column('sonstZiel', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], name=op.f('fk_fp_ausgleich_id_fp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fp_ausgleich'))
    )
    op.create_table('fp_darstellung_landesrecht',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('kurzbeschreibung', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], name=op.f('fk_fp_darstellung_landesrecht_id_fp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fp_darstellung_landesrecht'))
    )
    op.create_table('fp_keine_zentr_abwasser_beseitigung',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], name=op.f('fk_fp_keine_zentr_abwasser_beseitigung_id_fp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fp_keine_zentr_abwasser_beseitigung'))
    )
    op.create_table('fp_textabschnittsflaeche',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], name=op.f('fk_fp_textabschnittsflaeche_id_fp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fp_textabschnittsflaeche'))
    )
    op.create_table('fp_textliche_darstellungsflaeche',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], name=op.f('fk_fp_textliche_darstellungsflaeche_id_fp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fp_textliche_darstellungsflaeche'))
    )
    op.create_table('fp_unverbindliche_vormerkung',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('vormerkung', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], name=op.f('fk_fp_unverbindliche_vormerkung_id_fp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fp_unverbindliche_vormerkung'))
    )
    op.create_table('fp_vorbehalte_flaeche',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('vorbehalt', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], name=op.f('fk_fp_vorbehalte_flaeche_id_fp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fp_vorbehalte_flaeche'))
    )
    op.create_table('fp_zentraler_versorgungsbereich',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('auspraegung_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['auspraegung_id'], ['codelist_values.id'], name=op.f('fk_fp_zentraler_versorgungsbereich_auspraegung_id_codelist_values')),
    sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], name=op.f('fk_fp_zentraler_versorgungsbereich_id_fp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fp_zentraler_versorgungsbereich'))
    )
    op.create_table('so_baubeschraenkung',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('artDerFestlegung', postgresql.ENUM('Bauverbotszone', 'Baubeschraenkungszone', 'Waldabstand', 'SonstigeBeschraenkung', name='so_klassifizbaubeschraenkung', create_type=False), nullable=True),
    sa.Column('detailArtDerFestlegung_id', sa.UUID(), nullable=True),
    sa.Column('rechtlicheGrundlage', postgresql.ENUM('Luftverkehrsrecht', 'Strassenverkehrsrecht', 'SonstigesRecht', name='so_rechtlichegrundlagebaubeschraenkung', create_type=False), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('nummer', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['detailArtDerFestlegung_id'], ['codelist_values.id'], name=op.f('fk_so_baubeschraenkung_detailArtDerFestlegung_id_codelist_values')),
    sa.ForeignKeyConstraint(['id'], ['so_objekt.id'], name=op.f('fk_so_baubeschraenkung_id_so_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_so_baubeschraenkung'))
    )
    op.create_table('so_bauverbotszone',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('artDerFestlegung', postgresql.ENUM('Bauverbotszone', 'Baubeschraenkungszone', 'Waldabstand', 'SonstigeBeschraenkung', name='so_klassifizbauverbot', create_type=False), nullable=True),
    sa.Column('detailArtDerFestlegung_id', sa.UUID(), nullable=True),
    sa.Column('rechtlicheGrundlage', postgresql.ENUM('Luftverkehrsrecht', 'Strassenverkehrsrecht', 'SonstigesRecht', name='so_rechtlichegrundlagebauverbot', create_type=False), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('nummer', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['detailArtDerFestlegung_id'], ['codelist_values.id'], name=op.f('fk_so_bauverbotszone_detailArtDerFestlegung_id_codelist_values')),
    sa.ForeignKeyConstraint(['id'], ['so_objekt.id'], name=op.f('fk_so_bauverbotszone_id_so_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_so_bauverbotszone'))
    )
    op.create_table('so_forstrecht',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('artDerFestlegung', postgresql.ENUM('OeffentlicherWald', 'Staatswald', 'Koerperschaftswald', 'Kommunalwald', 'Stiftungswald', 'Privatwald', 'Gemeinschaftswald', 'Genossenschaftswald', 'Kirchenwald', 'Sonstiges', name='xp_eigentumsartwald', create_type=False), nullable=True),
    sa.Column('detailArtDerFestlegung_id', sa.UUID(), nullable=True),
    sa.Column('funktion', sa.ARRAY(postgresql.ENUM('Naturwald', 'Waldschutzgebiet', 'Nutzwald', 'Erholungswald', 'Schutzwald', 'Bodenschutzwald', 'Biotopschutzwald', 'NaturnaherWald', 'SchutzwaldSchaedlicheUmwelteinwirkungen', 'Schonwald', 'Bannwald', 'FlaecheForstwirtschaft', 'ImmissionsgeschaedigterWald', 'Sonstiges', name='xp_zweckbestimmungwald', create_type=False)), nullable=True),
    sa.Column('betreten', sa.ARRAY(postgresql.ENUM('KeineZusaetzlicheBetretung', 'Radfahren', 'Reiten', 'Fahren', 'Hundesport', 'Sonstiges', name='xp_waldbetretungtyp', create_type=False)), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('nummer', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['detailArtDerFestlegung_id'], ['codelist_values.id'], name=op.f('fk_so_forstrecht_detailArtDerFestlegung_id_codelist_values')),
    sa.ForeignKeyConstraint(['id'], ['so_objekt.id'], name=op.f('fk_so_forstrecht_id_so_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_so_forstrecht'))
    )
    op.create_table('so_gebiet',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('gemeinde_id', sa.UUID(), nullable=True),
    sa.Column('gebietsArt', postgresql.ENUM('Umlegungsgebiet', 'StaedtebaulicheSanierung', 'StaedtebaulicheEntwicklungsmassnahme', 'Stadtumbaugebiet', 'SozialeStadt', 'BusinessImprovementDistrict', 'HousingImprovementDistrict', 'Erhaltungsverordnung', 'ErhaltungsverordnungStaedtebaulicheGestalt', 'ErhaltungsverordnungWohnbevoelkerung', 'ErhaltungsverordnungUmstrukturierung', 'Erhaltungsgebiet', 'ErhaltungsgebietStaedtebaulicheGestalt', 'ErhaltungsgebietWohnbevoelkerung', 'ErhaltungsgebietUmstrukturierung', 'StaedtebaulEntwicklungskonzeptInnenentwicklung', 'GebietMitAngespanntemWohnungsmarkt', 'GenehmigungWohnungseigentum', 'Sonstiges', name='so_gebietsart', create_type=False), nullable=True),
    sa.Column('sonstGebietsArt_id', sa.UUID(), nullable=True),
    sa.Column('rechtsstandGebiet', postgresql.ENUM('VorbereitendeUntersuchung', 'Aufstellung', 'Festlegung', 'Abgeschlossen', 'Verstetigung', 'Sonstiges', name='so_rechtsstandgebiettyp', create_type=False), nullable=True),
    sa.Column('sonstRechtsstandGebiet_id', sa.UUID(), nullable=True),
    sa.Column('aufstellungsbeschhlussDatum', sa.Date(), nullable=True),
    sa.Column('durchfuehrungStartDatum', sa.Date(), nullable=True),
    sa.Column('durchfuehrungEndDatum', sa.Date(), nullable=True),
    sa.Column('traegerMassnahme', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['gemeinde_id'], ['xp_gemeinde.id'], name=op.f('fk_so_gebiet_gemeinde_id_xp_gemeinde')),
    sa.ForeignKeyConstraint(['id'], ['so_objekt.id'], name=op.f('fk_so_gebiet_id_so_objekt'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sonstGebietsArt_id'], ['codelist_values.id'], name=op.f('fk_so_gebiet_sonstGebietsArt_id_codelist_values')),
    sa.ForeignKeyConstraint(['sonstRechtsstandGebiet_id'], ['codelist_values.id'], name=op.f('fk_so_gebiet_sonstRechtsstandGebiet_id_codelist_values')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_so_gebiet'))
    )
    op.create_table('so_gelaendemorphologie',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('artDerFestlegung', postgresql.ENUM('Terassenkante', 'Rinne', 'EhemMaeander', 'SonstigeStruktur', name='so_klassifizgelaendemorphologie', create_type=False), nullable=True),
    sa.Column('detailArtDerFestlegung_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('nummer', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['detailArtDerFestlegung_id'], ['codelist_values.id'], name=op.f('fk_so_gelaendemorphologie_detailArtDerFestlegung_id_codelist_values')),
    sa.ForeignKeyConstraint(['id'], ['so_objekt.id'], name=op.f('fk_so_gelaendemorphologie_id_so_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_so_gelaendemorphologie'))
    )
    op.create_table('so_grenze',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('typ', postgresql.ENUM('Bundesgrenze', 'Landesgrenze', 'Regierungsbezirksgrenze', 'Bezirksgrenze', 'Kreisgrenze', 'Gemeindegrenze', 'Verbandsgemeindegrenze', 'Samtgemeindegrenze', 'Mitgliedsgemeindegrenze', 'Amtsgrenze', 'Stadtteilgrenze', 'VorgeschlageneGrundstuecksgrenze', 'GrenzeBestehenderBebauungsplan', 'SonstGrenze', name='xp_grenzetypen', create_type=False), nullable=True),
    sa.Column('sonstTyp_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['so_objekt.id'], name=op.f('fk_so_grenze_id_so_objekt'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sonstTyp_id'], ['codelist_values.id'], name=op.f('fk_so_grenze_sonstTyp_id_codelist_values')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_so_grenze'))
    )
    op.create_table('so_schutzgebiet_sonstiges_recht',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('artDerFestlegung', postgresql.ENUM('Laermschutzbereich', 'SchutzzoneLeitungstrasse', 'Sonstiges', name='so_klassifizschutzgebietsonstrecht', create_type=False), nullable=True),
    sa.Column('detailArtDerFestlegung_id', sa.UUID(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('nummer', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['detailArtDerFestlegung_id'], ['codelist_values.id'], name=op.f('fk_so_schutzgebiet_sonstiges_recht_detailArtDerFestlegung_id_codelist_values')),
    sa.ForeignKeyConstraint(['id'], ['so_objekt.id'], name=op.f('fk_so_schutzgebiet_sonstiges_recht_id_so_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_so_schutzgebiet_sonstiges_recht'))
    )
    op.create_table('assoc_detail_landesrecht',
    sa.Column('codelist_user_id', sa.UUID(), nullable=True),
    sa.Column('codelist_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['codelist_id'], ['codelist_values.id'], name=op.f('fk_assoc_detail_landesrecht_codelist_id_codelist_values')),
    sa.ForeignKeyConstraint(['codelist_user_id'], ['fp_darstellung_landesrecht.id'], name=op.f('fk_assoc_detail_landesrecht_codelist_user_id_fp_darstellung_landesrecht'), ondelete='CASCADE')
    )
    op.create_table('assoc_gemeinschaftsanlage_eigentuemer',
    sa.Column('gemeinschaftsanlage_id', sa.UUID(), nullable=True),
    sa.Column('baugebiet_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['baugebiet_id'], ['bp_baugebiet.id'], name=op.f('fk_assoc_gemeinschaftsanlage_eigentuemer_baugebiet_id_bp_baugebiet'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['gemeinschaftsanlage_id'], ['bp_gemeinschaftsanlage.id'], name=op.f('fk_assoc_gemeinschaftsanlage_eigentuemer_gemeinschaftsanlage_id_bp_gemeinschaftsanlage'), ondelete='CASCADE')
    )
    op.create_table('bp_emissionskontingent_laerm_gebiet',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('gebietsbezeichnung', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['bp_emissionskontingent_laerm.id'], name=op.f('fk_bp_emissionskontingent_laerm_gebiet_id_bp_emissionskontingent_laerm'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_emissionskontingent_laerm_gebiet'))
    )
    op.create_table('bp_richtungssektor',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('winkelAnfang', sa.Float(), nullable=False),
    sa.Column('winkelEnde', sa.Float(), nullable=False),
    sa.Column('zkWertTag', sa.Float(), nullable=False),
    sa.Column('zkWertNacht', sa.Float(), nullable=False),
    sa.Column('zusatzkontingent_id', sa.UUID(), nullable=True),
    sa.Column('zusatzkontingentFlaeche_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['zusatzkontingentFlaeche_id'], ['bp_zusatzkontingent_laerm_flaeche.id'], name=op.f('fk_bp_richtungssektor_zusatzkontingentFlaeche_id_bp_zusatzkontingent_laerm_flaeche'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['zusatzkontingent_id'], ['bp_zusatzkontingent_laerm.id'], name=op.f('fk_bp_richtungssektor_zusatzkontingent_id_bp_zusatzkontingent_laerm'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_richtungssektor'))
    )
    op.create_table('bp_veraenderungssperre',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('veraenderungssperreBeschlussDatum', sa.Date(), nullable=True),
    sa.Column('veraenderungssperreStartDatum', sa.Date(), nullable=True),
    sa.Column('gueltigkeitsDatum', sa.Date(), nullable=True),
    sa.Column('verlaengerung', postgresql.ENUM('Keine', 'ErsteVerlaengerung', 'ZweiteVerlaengerung', name='xp_verlaengerungveraenderungssperre', create_type=False), nullable=True),
    sa.Column('daten_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['daten_id'], ['bp_veraenderungssperre_daten.id'], name=op.f('fk_bp_veraenderungssperre_daten_id_bp_veraenderungssperre_daten')),
    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], name=op.f('fk_bp_veraenderungssperre_id_bp_objekt'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_veraenderungssperre'))
    )
    op.create_table('bp_zweckbestimmung_gemeinschaftsanlage',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('allgemein', postgresql.ENUM('Gemeinschaftsstellplaetze', 'Gemeinschaftsgaragen', 'Spielplatz', 'Carport', 'GemeinschaftsTiefgarage', 'Nebengebaeude', 'AbfallSammelanlagen', 'EnergieVerteilungsanlagen', 'AbfallWertstoffbehaelter', 'Freizeiteinrichtungen', 'Laermschutzanlagen', 'AbwasserRegenwasser', 'Ausgleichsmassnahmen', 'Fahrradstellplaetze', 'Gemeinschaftsdachgaerten', 'GemeinschaftlichNutzbareDachflaechen', 'Sonstiges', name='bp_zweckbestimmunggemeinschaftsanlagen', create_type=False), nullable=False),
    sa.Column('textlicheErgaenzung', sa.String(), nullable=True),
    sa.Column('aufschrift', sa.String(), nullable=True),
    sa.Column('gemeinschaftsanlage_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['gemeinschaftsanlage_id'], ['bp_gemeinschaftsanlage.id'], name=op.f('fk_bp_zweckbestimmung_gemeinschaftsanlage_gemeinschaftsanlage_id_bp_gemeinschaftsanlage'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bp_zweckbestimmung_gemeinschaftsanlage'))
    )
    op.create_table('assoc_detail_gemeinschaftsanlagen',
    sa.Column('codelist_user_id', sa.UUID(), nullable=True),
    sa.Column('codelist_user_v6_id', sa.UUID(), nullable=True),
    sa.Column('codelist_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['codelist_id'], ['codelist_values.id'], name=op.f('fk_assoc_detail_gemeinschaftsanlagen_codelist_id_codelist_values')),
    sa.ForeignKeyConstraint(['codelist_user_id'], ['bp_gemeinschaftsanlage.id'], name=op.f('fk_assoc_detail_gemeinschaftsanlagen_codelist_user_id_bp_gemeinschaftsanlage'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['codelist_user_v6_id'], ['bp_zweckbestimmung_gemeinschaftsanlage.id'], name=op.f('fk_assoc_detail_gemeinschaftsanlagen_codelist_user_v6_id_bp_zweckbestimmung_gemeinschaftsanlage'), ondelete='CASCADE')
    )
    op.alter_column('bp_baugebiet', 'GFAntWohnen',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    op.alter_column('bp_baugebiet', 'GFAntGewerbe',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    op.alter_column('bp_grundstueck_ueberbaubar', 'GFAntWohnen',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    op.alter_column('bp_grundstueck_ueberbaubar', 'GFAntGewerbe',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    op.add_column('xp_externe_referenz', sa.Column('bp_ausgleichsflaeche_massnahme_id', sa.UUID(), nullable=True))
    op.add_column('xp_externe_referenz', sa.Column('bp_ausgleichsflaeche_plan_id', sa.UUID(), nullable=True))
    op.add_column('xp_externe_referenz', sa.Column('fp_ausgleichsflaeche_massnahme_id', sa.UUID(), nullable=True))
    op.add_column('xp_externe_referenz', sa.Column('fp_ausgleichsflaeche_plan_id', sa.UUID(), nullable=True))
    op.add_column('xp_externe_referenz', sa.Column('bp_ausgleichsmassnahme_massnahme_id', sa.UUID(), nullable=True))
    op.add_column('xp_externe_referenz', sa.Column('bp_ausgleichsmassnahme_plan_id', sa.UUID(), nullable=True))

    op.create_foreign_key(op.f('fk_xp_externe_referenz_bp_ausgleichsflaeche_plan_id_bp_ausgleich'), 'xp_externe_referenz', 'bp_ausgleich', ['bp_ausgleichsflaeche_plan_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_xp_externe_referenz_fp_ausgleichsflaeche_massnahme_id_fp_ausgleich'), 'xp_externe_referenz', 'fp_ausgleich', ['fp_ausgleichsflaeche_massnahme_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_xp_externe_referenz_bp_ausgleichsmassnahme_plan_id_bp_ausgleichsmassnahme'), 'xp_externe_referenz', 'bp_ausgleichsmassnahme', ['bp_ausgleichsmassnahme_plan_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_xp_externe_referenz_bp_ausgleichsflaeche_massnahme_id_bp_ausgleich'), 'xp_externe_referenz', 'bp_ausgleich', ['bp_ausgleichsflaeche_massnahme_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_xp_externe_referenz_bp_ausgleichsmassnahme_massnahme_id_bp_ausgleichsmassnahme'), 'xp_externe_referenz', 'bp_ausgleichsmassnahme', ['bp_ausgleichsmassnahme_massnahme_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_xp_externe_referenz_fp_ausgleichsflaeche_plan_id_fp_ausgleich'), 'xp_externe_referenz', 'fp_ausgleich', ['fp_ausgleichsflaeche_plan_id'], ['id'], ondelete='CASCADE')

    op.drop_column('xp_externe_referenz', 'referenzMimeType')

    op.add_column('xp_spe_daten', sa.Column('bp_ausgleichsflaeche_id', sa.UUID(), nullable=True))
    op.add_column('xp_spe_daten', sa.Column('bp_ausgleichsmassnahme_id', sa.UUID(), nullable=True))
    op.add_column('xp_spe_daten', sa.Column('fp_ausgleichsflaeche_id', sa.UUID(), nullable=True))
    op.create_foreign_key(op.f('fk_xp_spe_daten_bp_ausgleichsflaeche_id_bp_ausgleich'), 'xp_spe_daten', 'bp_ausgleich', ['bp_ausgleichsflaeche_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_xp_spe_daten_bp_ausgleichsmassnahme_id_bp_ausgleichsmassnahme'), 'xp_spe_daten', 'bp_ausgleichsmassnahme', ['bp_ausgleichsmassnahme_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_xp_spe_daten_fp_ausgleichsflaeche_id_fp_ausgleich'), 'xp_spe_daten', 'fp_ausgleich', ['fp_ausgleichsflaeche_id'], ['id'], ondelete='CASCADE')

    sa.Enum('application/pdf', 'application/zip', 'application/xml', 'application/msword', 'application/msexcel', 'application/vnd.ogc.sld+xml', 'application/vnd.ogc.wms_xml', 'application/vnd.ogc.gml', 'application/vnd.shp', 'application/vnd.dbf', 'application/vnd.shx', 'application/octet-stream', 'image/vnd.dxf', 'image/vnd.dwg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp', 'image/ecw', 'image/svg+xml', 'text/html', 'text/plain', name='xp_mime_types').drop(op.get_bind())

    op.add_column("fp_objekt", sa.Column("flussrichtung", sa.Boolean(), nullable=True))
    op.add_column("fp_objekt", sa.Column("nordwinkel", sa.Float(), nullable=True))
    op.add_column("bp_objekt", sa.Column("flussrichtung", sa.Boolean(), nullable=True))
    op.add_column("bp_objekt", sa.Column("nordwinkel", sa.Float(), nullable=True))

    op.add_column('assoc_detail_sondernutzung', sa.Column('bp_baugebiet_id', sa.UUID(), nullable=True))
    op.create_foreign_key(op.f('fk_assoc_detail_sondernutzung_bp_baugebiet_id_bp_baugebiet'),
                          'assoc_detail_sondernutzung', 'bp_baugebiet', ['bp_baugebiet_id'], ['id'], ondelete='CASCADE')
    op.execute("ALTER TABLE assoc_detail_sondernutzung DROP CONSTRAINT IF EXISTS assoc_detail_sondernutzung_pkey;")
    op.execute("ALTER TABLE assoc_detail_sondernutzung ALTER COLUMN codelist_user_id DROP NOT NULL;")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    sa.Enum('application/pdf', 'application/zip', 'application/xml', 'application/msword', 'application/msexcel', 'application/vnd.ogc.sld+xml', 'application/vnd.ogc.wms_xml', 'application/vnd.ogc.gml', 'application/vnd.shp', 'application/vnd.dbf', 'application/vnd.shx', 'application/octet-stream', 'image/vnd.dxf', 'image/vnd.dwg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp', 'image/ecw', 'image/svg+xml', 'text/html', 'text/plain', name='xp_mime_types').create(op.get_bind())

    for enum_name, *labels in NEW_ENUMS:
        enum = postgresql.ENUM(*labels, name=enum_name, create_type=False)
        if not context.is_offline_mode():
            enum.create(op.get_bind(), checkfirst=True)

    op.drop_column('xp_spe_daten', 'fp_ausgleichsflaeche_id')
    op.drop_column('xp_spe_daten', 'bp_ausgleichsmassnahme_id')
    op.drop_column('xp_spe_daten', 'bp_ausgleichsflaeche_id')

    op.add_column('xp_externe_referenz', sa.Column('referenzMimeType', postgresql.ENUM('application/pdf', 'application/zip', 'application/xml', 'application/msword', 'application/msexcel', 'application/vnd.ogc.sld+xml', 'application/vnd.ogc.wms_xml', 'application/vnd.ogc.gml', 'application/vnd.shp', 'application/vnd.dbf', 'application/vnd.shx', 'application/octet-stream', 'image/vnd.dxf', 'image/vnd.dwg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp', 'image/ecw', 'image/svg+xml', 'text/html', 'text/plain', name='xp_mime_types', create_type=False), autoincrement=False, nullable=True))

    op.drop_column('xp_externe_referenz', 'bp_ausgleichsmassnahme_plan_id')
    op.drop_column('xp_externe_referenz', 'bp_ausgleichsmassnahme_massnahme_id')
    op.drop_column('xp_externe_referenz', 'fp_ausgleichsflaeche_plan_id')
    op.drop_column('xp_externe_referenz', 'fp_ausgleichsflaeche_massnahme_id')
    op.drop_column('xp_externe_referenz', 'bp_ausgleichsflaeche_plan_id')
    op.drop_column('xp_externe_referenz', 'bp_ausgleichsflaeche_massnahme_id')

    op.drop_table('assoc_detail_gemeinschaftsanlagen')
    op.drop_table('bp_zweckbestimmung_gemeinschaftsanlage')
    op.drop_table('bp_veraenderungssperre')
    op.drop_table('bp_richtungssektor')
    op.drop_table('bp_emissionskontingent_laerm_gebiet')
    op.drop_table('assoc_gemeinschaftsanlage_eigentuemer')
    op.drop_table('assoc_detail_landesrecht')
    op.drop_table('so_schutzgebiet_sonstiges_recht')
    op.drop_table('so_grenze')
    op.drop_table('so_gelaendemorphologie')
    op.drop_table('so_gebiet')
    op.drop_table('so_forstrecht')
    op.drop_table('so_bauverbotszone')
    op.drop_table('so_baubeschraenkung')
    op.drop_table('fp_zentraler_versorgungsbereich')
    op.drop_table('fp_vorbehalte_flaeche')
    op.drop_table('fp_unverbindliche_vormerkung')
    op.drop_table('fp_textliche_darstellungsflaeche')
    op.drop_table('fp_textabschnittsflaeche')
    op.drop_table('fp_keine_zentr_abwasser_beseitigung')
    op.drop_table('fp_darstellung_landesrecht')
    op.drop_table('fp_ausgleich')
    op.drop_table('fp_anpassung_klimawandel')
    op.drop_table('bp_zusatzkontingent_laerm_flaeche')
    op.drop_table('bp_zusatzkontingent_laerm')
    op.drop_table('bp_zentraler_versorgungsbereich')
    op.drop_table('bp_unverbindliche_vormerkung')
    op.drop_table('bp_technische_massnahmen')
    op.drop_table('bp_spezielle_bauweise')
    op.drop_table('bp_richtungssektorgrenze')
    op.drop_table('bp_regelung_vergnuegungsstaetten')
    op.drop_table('bp_persgruppen_bestimmte_flaeche')
    op.drop_table('bp_nicht_ueberbaubare_grundstuecksflaeche')
    op.drop_table('bp_kleintierhaltung')
    op.drop_table('bp_hoehen_mass')
    op.drop_table('bp_gemeinschaftsanlage')
    op.drop_table('bp_gebaeude_stellung')
    op.drop_table('bp_gebaeude_flaeche')
    op.drop_table('bp_freiflaeche')
    op.drop_table('bp_festsetzung_landesrecht')
    op.drop_table('bp_emissionskontingent_laerm')
    op.drop_table('bp_eingriffsbereich')
    op.drop_table('bp_einfahrtsbereich')
    op.drop_table('bp_ausgleichsmassnahme')
    op.drop_table('bp_ausgleich')
    op.drop_table('bp_abweichung_ueberbaubare_grundstuecksflaeche')
    op.drop_table('bp_abweichung_baugrenze')
    op.drop_table('bp_abstands_mass')
    op.drop_table('bp_abstand')

    for enum_name, *labels in reversed(NEW_ENUMS):
        op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))

    table_types_list = ', '.join(f"'{t}'" for t in NEW_TABLE_TYPES)
    op.execute(sa.text(f"DELETE FROM xp_objekt WHERE type IN ({table_types_list})"))


    op.drop_column("fp_objekt", "nordwinkel")
    op.drop_column("fp_objekt", "flussrichtung")
    op.drop_column("bp_objekt", "nordwinkel")
    op.drop_column("bp_objekt", "flussrichtung")

    op.drop_column('assoc_detail_sondernutzung', 'bp_baugebiet_id')

    # ### end Alembic commands ###