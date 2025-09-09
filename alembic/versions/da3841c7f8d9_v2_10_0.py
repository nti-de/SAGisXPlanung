"""v2.10.0

Revision ID: da3841c7f8d9
Revises: 31058f6befbd
Create Date: 2025-08-26 10:43:26.412589

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
revision = 'da3841c7f8d9'
down_revision = '31058f6befbd'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('xp_po', sa.Column('stylesheetId', sa.String(), nullable=True))

    op.execute("""
        DELETE FROM xp_po p
        WHERE EXISTS (
            SELECT 1
            FROM xp_nutzungsschablone n
            WHERE n.id = p.id
              AND n.hidden = true
        )
    """)

    op.create_table('so_bodenschutz',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('artDerFestlegung', sa.Enum('SchaedlicheBodenveraenderung', 'Altlast', 'Altablagerung', 'Altstandort', 'AltstandortAufAltablagerung',
                                              name='so_klassifiznachbodenschutzrecht'), nullable=True),
        sa.Column('detailArtDerFestlegung_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('istVerdachtsflaeche', sa.Boolean(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('nummer', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['detailArtDerFestlegung_id'], ['codelist_values.id'], ),
        sa.ForeignKeyConstraint(['id'], ['so_objekt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('fp_wasserwirtschaft',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('zweckbestimmung', sa.Enum('HochwasserRueckhaltebecken', 'Ueberschwemmgebiet',
                                             'Versickerungsflaeche', 'Entwaesserungsgraben', 'Deich',
                                             'RegenRueckhaltebecken', 'Sonstiges',
                                             name='xp_zweckbestimmungwasserwirtschaft'), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['fp_objekt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # textabschnitt
    bp_zulaessigkeit_enum = postgresql.ENUM('Zulaessig', 'NichtZulaessig', 'AusnahmsweiseZulaessig',
                                            name='bp_zulaessigkeit', create_type=False)
    bauweise_enum = postgresql.ENUM('KeineAngabe', 'OffeneBauweise', 'GeschlosseneBauweise', 'AbweichendeBauweise',
                                    name='bp_bauweise', create_type=False)
    bebauungsart_enum = postgresql.ENUM('Einzelhaeuser', 'Doppelhaeuser', 'Hausgruppen', 'EinzelDoppelhaeuser',
                                        'EinzelhaeuserHausgruppen', 'DoppelhaeuserHausgruppen', 'Reihenhaeuser',
                                        'EinzelhaeuserDoppelhaeuserHausgruppen', name='bp_bebauungsart',
                                        create_type=False)
    grenzbebauung_enum = postgresql.ENUM('KeineAngabe', 'Verboten', 'Erlaubt', 'Erzwungen',
                                         name='bp_grenzbebauung', create_type=False)
    abweichung_baunvo_enum = postgresql.ENUM('KeineAbweichung', 'EinschraenkungNutzung', 'AusschlussNutzung',
            'AusweitungNutzung', 'SonstAbweichung', name='xp_abweichungbaunvotypen', create_type=False)
    xp_rechtscharakter_enum = postgresql.ENUM(
        'FestsetzungBPlan', 'NachrichtlicheUebernahme', 'DarstellungFPlan',
        'ZielDerRaumordnung', 'GrundsatzDerRaumordnung',
        'NachrichtlicheUebernahmeZiel', 'NachrichtlicheUebernahmeGrundsatz',
        'NurInformationsgehaltRPlan', 'TextlichesZielRaumordnung',
        'ZielUndGrundsatzRaumordnung', 'VorschlagRaumordnung',
        'FestsetzungImLP', 'GeplanteFestsetzungImLP',
        'DarstellungKennzeichnungImLP',
        'LandschaftsplanungsInhaltZurBeruecksichtigung',
        'Hinweis', 'Kennzeichnung', 'Vermerk', 'Unbekannt', 'Sonstiges',
        name='xp_rechtscharakter', create_type=False
    )
    bp_rechtscharakter_enum = postgresql.ENUM(
        'Festsetzung', 'NachrichtlicheUebernahme', 'Hinweis',
        'Vermerk', 'Kennzeichnung', 'Unbekannt',
        name='bp_rechtscharakter', create_type=False
    )
    fp_rechtscharakter_enum = postgresql.ENUM(
        'Darstellung', 'NachrichtlicheUebernahme', 'Hinweis',
        'Vermerk', 'Kennzeichnung', 'Unbekannt',
        name='fp_rechtscharakter', create_type=False
    )
    lp_rechtscharakter_enum = postgresql.ENUM(
        'Festsetzung', 'Geplant', 'NachrichtlicheUebernahme',
        'DarstellungKennzeichnung', 'FestsetzungInBPlan',
        'Unbekannt', 'SonstigerStatus',
        name='lp_rechtscharakter'
    )
    rp_rechtscharakter_enum = postgresql.ENUM(
        'ZielDerRaumordnung', 'GrundsatzDerRaumordnung', 'NachrichtlicheUebernahme',
        'NachrichtlicheUebernahmeZiel', 'NachrichtlicheUebernahmeGrundsatz',
        'NurInformationsgehalt', 'TextlichesZiel', 'ZielundGrundsatz',
        'Vorschlag', 'Unbekannt',
        name='rp_rechtscharakter'
    )
    so_rechtscharakter_enum = postgresql.ENUM(
        'FestsetzungBPlan', 'DarstellungFPlan', 'InhaltLPlan',
        'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk',
        'Kennzeichnung', 'Unbekannt', 'Sonstiges',
        name='so_rechtscharakter', create_type=False
    )

    if not context.is_offline_mode():
        for enum in [
            bp_zulaessigkeit_enum, bauweise_enum, bebauungsart_enum,
            grenzbebauung_enum, abweichung_baunvo_enum,
            xp_rechtscharakter_enum, bp_rechtscharakter_enum,
            fp_rechtscharakter_enum, so_rechtscharakter_enum
        ]:
            enum.create(op.get_bind(), checkfirst=True)

    op.create_table('bp_nebenanlagen_ausschluss_flaeche',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('typ', sa.Enum('Einschraenkung', 'Ausschluss', name='bp_nebenanlagenausschlusstyp'),
                  nullable=True),
        sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bp_wohngebaeude_flaeche',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('FR', sa.Integer(), nullable=True),
        sa.Column('MaxZahlWohnungen', sa.Integer(), nullable=True),
        sa.Column('MinGRWohneinheit', sa.Float(), nullable=True),
        sa.Column('Fmin', sa.Float(), nullable=True),
        sa.Column('Fmax', sa.Float(), nullable=True),
        sa.Column('Bmin', sa.Float(), nullable=True),
        sa.Column('Bmax', sa.Float(), nullable=True),
        sa.Column('Tmin', sa.Float(), nullable=True),
        sa.Column('Tmax', sa.Float(), nullable=True),
        sa.Column('GFZmin', sa.Float(), nullable=True),
        sa.Column('GFZmax', sa.Float(), nullable=True),
        sa.Column('GFZ', sa.Float(), nullable=True),
        sa.Column('GFZ_Ausn', sa.Float(), nullable=True),
        sa.Column('GFmin', sa.Float(), nullable=True),
        sa.Column('GFmax', sa.Float(), nullable=True),
        sa.Column('GF', sa.Float(), nullable=True),
        sa.Column('GF_Ausn', sa.Float(), nullable=True),
        sa.Column('BMZ', sa.Float(), nullable=True),
        sa.Column('BMZ_Ausn', sa.Float(), nullable=True),
        sa.Column('BM', sa.Float(), nullable=True),
        sa.Column('BM_Ausn', sa.Float(), nullable=True),
        sa.Column('GRZmin', sa.Float(), nullable=True),
        sa.Column('GRZmax', sa.Float(), nullable=True),
        sa.Column('GRZ', sa.Float(), nullable=True),
        sa.Column('GRZ_Ausn', sa.Float(), nullable=True),
        sa.Column('GRmin', sa.Float(), nullable=True),
        sa.Column('GRmax', sa.Float(), nullable=True),
        sa.Column('GR', sa.Float(), nullable=True),
        sa.Column('GR_Ausn', sa.Float(), nullable=True),
        sa.Column('Zmin', sa.Integer(), nullable=True),
        sa.Column('Zmax', sa.Integer(), nullable=True),
        sa.Column('Zzwingend', sa.Integer(), nullable=True),
        sa.Column('Z', sa.Integer(), nullable=True),
        sa.Column('Z_Ausn', sa.Integer(), nullable=True),
        sa.Column('Z_Staffel', sa.Integer(), nullable=True),
        sa.Column('Z_Dach', sa.Integer(), nullable=True),
        sa.Column('ZUmin', sa.Integer(), nullable=True),
        sa.Column('ZUmax', sa.Integer(), nullable=True),
        sa.Column('ZUzwingend', sa.Integer(), nullable=True),
        sa.Column('ZU', sa.Integer(), nullable=True),
        sa.Column('ZU_Ausn', sa.Integer(), nullable=True),
        sa.Column('wohnnutzungEGStrasse', bp_zulaessigkeit_enum, nullable=True),
        sa.Column('ZWohn', sa.Integer(), nullable=True),
        sa.Column('GFAntWohnen', sa.Float(), nullable=True),
        sa.Column('GFWohnen', sa.Float(), nullable=True),
        sa.Column('GFAntGewerbe', sa.Float(), nullable=True),
        sa.Column('GFGewerbe', sa.Float(), nullable=True),
        sa.Column('VF', sa.Float(), nullable=True),
        sa.Column('typ', sa.Enum('Wohngebaeude', 'GebaeudeFoerderung', 'GebaeudeStaedtebaulicherVertrag',
                                 name='bp_typwohngebaeudeflaeche'), nullable=False),
        sa.Column('abweichungBauNVO', abweichung_baunvo_enum, nullable=True),
        sa.Column('bauweise', bauweise_enum, nullable=True),
        sa.Column('vertikaleDifferenzierung', sa.Boolean(), nullable=True),
        sa.Column('bebauungsArt', bebauungsart_enum, nullable=True),
        sa.Column('bebauungVordereGrenze', grenzbebauung_enum, nullable=True),
        sa.Column('bebauungRueckwaertigeGrenze', grenzbebauung_enum, nullable=True),
        sa.Column('bebauungSeitlicheGrenze', grenzbebauung_enum, nullable=True),
        sa.Column('zugunstenVon', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('xp_text_abschnitt',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('schluessel', sa.String(), nullable=True),
        sa.Column('gesetzlicheGrundlage', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('rechtscharakter', xp_rechtscharakter_enum, nullable=False),
        sa.Column('xp_bereich_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('xp_objekt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('xp_plan_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bp_objekt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('fp_objekt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bp_baugebiet_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bp_nebenanlagen_ausschluss_flaeche_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bp_wohngebaeude_flaeche_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['bp_baugebiet_id'], ['bp_baugebiet.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bp_nebenanlagen_ausschluss_flaeche_id'], ['bp_nebenanlagen_ausschluss_flaeche.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bp_objekt_id'], ['bp_objekt.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bp_wohngebaeude_flaeche_id'], ['bp_wohngebaeude_flaeche.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fp_objekt_id'], ['fp_objekt.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['xp_bereich_id'], ['xp_bereich.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['xp_objekt_id'], ['xp_objekt.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['xp_plan_id'], ['xp_plan.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bp_text_abschnitt',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rechtscharakter', bp_rechtscharakter_enum, nullable=False),
        sa.Column('bp_baugebiet_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('bp_nebenanlagen_ausschluss_flaeche_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['bp_baugebiet_id'], ['bp_baugebiet.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bp_nebenanlagen_ausschluss_flaeche_id'], ['bp_nebenanlagen_ausschluss_flaeche.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id'], ['xp_text_abschnitt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('fp_text_abschnitt',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rechtscharakter', fp_rechtscharakter_enum, nullable=False),
        sa.ForeignKeyConstraint(['id'], ['xp_text_abschnitt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lp_text_abschnitt',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rechtscharakter', lp_rechtscharakter_enum, nullable=False),
        sa.ForeignKeyConstraint(['id'], ['xp_text_abschnitt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('rp_text_abschnitt',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rechtscharakter', rp_rechtscharakter_enum, nullable=False),
        sa.ForeignKeyConstraint(['id'], ['xp_text_abschnitt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('so_text_abschnitt',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rechtscharakter', so_rechtscharakter_enum, nullable=False),
        sa.ForeignKeyConstraint(['id'], ['xp_text_abschnitt.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.add_column('bp_dachgestaltung', sa.Column('bp_wohngebaeude_flaeche_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'bp_dachgestaltung', 'bp_wohngebaeude_flaeche', ['bp_wohngebaeude_flaeche_id'], ['id'], ondelete='CASCADE')

    op.alter_column(
        'lp_ziele_erfordernisse_massnahmen',
        'artDerFestlegung',
        new_column_name='zieleErfordernisseMassnahmen',
        existing_type=sa.ARRAY(
            postgresql.ENUM('Ziel', 'Erfordernis', 'Massnahme', name='lp_zemtyp', create_type=False)),
        existing_nullable=False
    )
    op.add_column('xp_externe_referenz', sa.Column('xp_text_abschnitt_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('xp_externe_referenz', sa.Column('bp_wohngebaeude_flaeche_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'xp_externe_referenz', 'bp_wohngebaeude_flaeche', ['bp_wohngebaeude_flaeche_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'xp_externe_referenz', 'xp_text_abschnitt', ['xp_text_abschnitt_id'], ['id'], ondelete='CASCADE')

    op.drop_column('xp_nutzungsschablone', 'hidden')

    # Issue #136
    op.create_table(
        "xp_plan_gesetzlichegrundlage",
        sa.Column("bp_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bp_plan.id", ondelete="CASCADE"),
                  nullable=True),
        sa.Column("fp_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fp_plan.id", ondelete="CASCADE"),
                  nullable=True),
        sa.Column("gesetzlichegrundlage_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("xp_gesetzliche_grundlage.id"), nullable=False),
    )
    op.execute("""
        INSERT INTO xp_plan_gesetzlichegrundlage (bp_plan_id, gesetzlichegrundlage_id)
        SELECT id, "versionSonstRechtsgrundlage_id"
        FROM bp_plan
        WHERE "versionSonstRechtsgrundlage_id" IS NOT NULL;
    """)
    op.execute("""
        INSERT INTO xp_plan_gesetzlichegrundlage (fp_plan_id, gesetzlichegrundlage_id)
        SELECT id, "versionSonstRechtsgrundlage_id"
        FROM fp_plan
        WHERE "versionSonstRechtsgrundlage_id" IS NOT NULL;
    """)
    op.drop_column("bp_plan", "versionSonstRechtsgrundlage_id")
    op.drop_column("fp_plan", "versionSonstRechtsgrundlage_id")

    # Issue #137
    op.execute("ALTER TYPE xp_abemassnahmentypen ADD VALUE IF NOT EXISTS 'AnpflanzungBindungErhaltung';")


def downgrade():
    op.drop_column('xp_po', 'stylesheetId')

    op.drop_table('so_bodenschutz')
    op.drop_table('fp_wasserwirtschaft')
    op.execute("DROP TYPE so_klassifiznachbodenschutzrecht CASCADE;")
    op.execute("DROP TYPE xp_zweckbestimmungwasserwirtschaft CASCADE;")

    op.add_column('xp_nutzungsschablone', sa.Column('hidden', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.alter_column(
        'lp_ziele_erfordernisse_massnahmen',
        'zieleErfordernisseMassnahmen',
        new_column_name='artDerFestlegung',
        existing_type=sa.ARRAY(
            postgresql.ENUM('Ziel', 'Erfordernis', 'Massnahme', name='lp_zemtyp', create_type=False)),
        existing_nullable=False
    )

    op.drop_column('xp_externe_referenz', 'bp_wohngebaeude_flaeche_id')
    op.drop_column('xp_externe_referenz', 'xp_text_abschnitt_id')
    op.drop_column('bp_dachgestaltung', 'bp_wohngebaeude_flaeche_id')

    op.drop_table('so_text_abschnitt')
    op.drop_table('rp_text_abschnitt')
    op.drop_table('lp_text_abschnitt')
    op.drop_table('fp_text_abschnitt')
    op.drop_table('bp_text_abschnitt')
    op.drop_table('xp_text_abschnitt')
    op.drop_table('bp_wohngebaeude_flaeche')
    op.drop_table('bp_nebenanlagen_ausschluss_flaeche')
    # drop types separately: https://github.com/sqlalchemy/alembic/issues/886
    op.execute('DROP TYPE bp_nebenanlagenausschlusstyp;')
    op.execute('DROP TYPE bp_typwohngebaeudeflaeche;')
    op.execute('DROP TYPE lp_rechtscharakter;')
    op.execute('DROP TYPE rp_rechtscharakter;')

    op.execute("DELETE FROM xp_objekt CASCADE WHERE type in ('so_bodenschutz', 'fp_wasserwirtschaft', "
               "'bp_wohngebaeude_flaeche', 'bp_nebenanlagen_ausschluss_flaeche');")

    op.add_column("bp_plan", sa.Column("versionSonstRechtsgrundlage_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "bp_plan_versionSonstRechtsgrundlage_id_fkey",
        "bp_plan",
        "xp_gesetzliche_grundlage",
        ["versionSonstRechtsgrundlage_id"],
        ["id"],
    )
    op.add_column("fp_plan", sa.Column("versionSonstRechtsgrundlage_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fp_plan_versionSonstRechtsgrundlage_id_fkey",
        "fp_plan",
        "xp_gesetzliche_grundlage",
        ["versionSonstRechtsgrundlage_id"],
        ["id"],
    )
    op.execute("""
        UPDATE bp_plan
        SET "versionSonstRechtsgrundlage_id" = sub.gesetzlichegrundlage_id FROM (
            SELECT DISTINCT ON (bp_plan_id) bp_plan_id, gesetzlichegrundlage_id
            FROM xp_plan_gesetzlichegrundlage
            WHERE bp_plan_id IS NOT NULL
        ) AS sub
        WHERE bp_plan.id = sub.bp_plan_id;
    """)
    op.execute("""
        UPDATE fp_plan
        SET "versionSonstRechtsgrundlage_id" = sub.gesetzlichegrundlage_id FROM (
            SELECT DISTINCT ON (fp_plan_id) fp_plan_id, gesetzlichegrundlage_id
            FROM xp_plan_gesetzlichegrundlage
            WHERE fp_plan_id IS NOT NULL
        ) AS sub
        WHERE fp_plan.id = sub.fp_plan_id;
    """)
    op.drop_table("xp_plan_gesetzlichegrundlage")