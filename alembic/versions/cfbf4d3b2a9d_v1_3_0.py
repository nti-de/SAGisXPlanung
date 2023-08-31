"""v1.3.0

Revision ID: cfbf4d3b2a9d
Revises: 
Create Date: 2021-12-03 12:19:36.787492

"""
import os
import sys
from geoalchemy2 import Geometry
from sqlalchemy import text

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(
    PROJECT_PATH, "src"
)
sys.path.append(SOURCE_PATH)

# revision identifiers, used by Alembic.
revision = 'cfbf4d3b2a9d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    op.create_table('xp_bereich',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('type', sa.String(length=50), nullable=True),
                    sa.Column('srs', sa.String(length=20), nullable=True),
                    sa.Column('nummer', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('bedeutung',
                              sa.Enum('Teilbereich', 'Kompensationsbereich', 'Sonstiges', name='xp_bedeutungenbereich'),
                              nullable=True),
                    sa.Column('detaillierteBedeutung', sa.String(), nullable=True),
                    sa.Column('erstellungsMassstab', sa.Integer(), nullable=True),
                    sa.Column('geltungsbereich',
                              Geometry(geometry_type='MULTIPOLYGON', from_text='ST_GeomFromEWKT',
                                       name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_gemeinde',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('ags', sa.String(), nullable=True),
                    sa.Column('rs', sa.String(), nullable=True),
                    sa.Column('gemeindeName', sa.String(), nullable=False),
                    sa.Column('ortsteilName', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_plangeber',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('kennziffer', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_objekt',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('type', sa.String(length=50), nullable=True),
                    sa.Column('uuid', sa.String(), nullable=True),
                    sa.Column('text', sa.String(), nullable=True),
                    sa.Column('rechtsstand', sa.Enum('Geplant', 'Bestehend', 'Fortfallend', name='xp_rechtsstand'),
                              nullable=True),
                    sa.Column('gesetzlicheGrundlage', sa.Enum('', name='xp_gesetzliche_grundlage'), nullable=True),
                    sa.Column('gliederung1', sa.String(), nullable=True),
                    sa.Column('gliederung2', sa.String(), nullable=True),
                    sa.Column('ebene', sa.Integer(), nullable=True),
                    sa.Column('gehoertZuBereich_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.Column('aufschrift', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['gehoertZuBereich_id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_plan',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('type', sa.String(length=50), nullable=True),
                    sa.Column('srs', sa.String(length=20), nullable=True),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('nummer', sa.String(), nullable=True),
                    sa.Column('internalId', sa.String(), nullable=True),
                    sa.Column('beschreibung', sa.String(), nullable=True),
                    sa.Column('kommentar', sa.String(), nullable=True),
                    sa.Column('technHerstellDatum', sa.Date(), nullable=True),
                    sa.Column('genehmigungsDatum', sa.Date(), nullable=True),
                    sa.Column('untergangsDatum', sa.Date(), nullable=True),
                    sa.Column('erstellungsMassstab', sa.Integer(), nullable=True),
                    sa.Column('bezugshoehe', sa.Float(), nullable=True),
                    sa.Column('technischerPlanersteller', sa.String(), nullable=True),
                    sa.Column('raeumlicherGeltungsbereich',
                              Geometry(geometry_type='MULTIPOLYGON', from_text='ST_GeomFromEWKT',
                                       name='geometry'), nullable=True),
                    sa.Column('plangeber_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.ForeignKeyConstraint(['plangeber_id'], ['xp_plangeber.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_po',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('gehoertZuBereich_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.Column('type', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['gehoertZuBereich_id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_simple_geometry',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('xplanung_type', sa.String(), nullable=True),
                    sa.Column('position', Geometry(from_text='ST_GeomFromEWKT', name='geometry'),
                              nullable=True),
                    sa.Column('gehoertZuBereich_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.ForeignKeyConstraint(['gehoertZuBereich_id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('bp_objekt',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('rechtscharakter',
                              sa.Enum('Festsetzung', 'NachrichtlicheUebernahme', 'Hinweis', 'Vermerk', 'Kennzeichnung',
                                      'Unbekannt', name='bp_rechtscharakter'), nullable=True),
                    sa.Column('position', Geometry(from_text='ST_GeomFromEWKT', name='geometry'),
                              nullable=True),
                    sa.Column('flaechenschluss', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['xp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('bp_plan',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('planArt',
                              sa.Enum('BPlan', 'EinfacherBPlan', 'QualifizierterBPlan', 'VorhabenbezogenerBPlan',
                                      'VorhabenUndErschliessungsplan', 'InnenbereichsSatzung', 'KlarstellungsSatzung',
                                      'EntwicklungsSatzung', 'ErgaenzungsSatzung', 'AussenbereichsSatzung',
                                      'OertlicheBauvorschrift', 'Sonstiges', name='bp_planart'), nullable=False),
                    sa.Column('verfahren', sa.Enum('Normal', 'Parag13', 'Parag13a', 'Parag13b', name='bp_verfahren'),
                              nullable=True),
                    sa.Column('rechtsstand',
                              sa.Enum('Aufstellungsbeschluss', 'Entwurf', 'FruehzeitigeBehoerdenBeteiligung',
                                      'FruehzeitigeOeffentlichkeitsBeteiligung', 'BehoerdenBeteiligung',
                                      'OeffentlicheAuslegung', 'Satzung', 'InkraftGetreten', 'TeilweiseUntergegangen',
                                      'Untergegangen', 'Aufgehoben', 'AusserKraft', name='bp_rechtsstand'),
                              nullable=True),
                    sa.Column('hoehenbezug', sa.String(), nullable=True),
                    sa.Column('aenderungenBisDatum', sa.Date(), nullable=True),
                    sa.Column('aufstellungsbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('veraenderungssperreBeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('veraenderungssperreDatum', sa.Date(), nullable=True),
                    sa.Column('veraenderungssperreEndDatum', sa.Date(), nullable=True),
                    sa.Column('verlaengerungVeraenderungssperre',
                              sa.Enum('Keine', 'ErsteVerlaengerung', 'ZweiteVerlaengerung',
                                      name='xp_verlaengerungveraenderungssperre'), nullable=True),
                    sa.Column('auslegungsStartDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('auslegungsEndDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('traegerbeteiligungsStartDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('traegerbeteiligungsEndDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('satzungsbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('rechtsverordnungsDatum', sa.Date(), nullable=True),
                    sa.Column('inkrafttretensDatum', sa.Date(), nullable=True),
                    sa.Column('ausfertigungsDatum', sa.Date(), nullable=True),
                    sa.Column('veraenderungssperre', sa.Boolean(), nullable=True),
                    sa.Column('staedtebaulicherVertrag', sa.Boolean(), nullable=True),
                    sa.Column('erschliessungsVertrag', sa.Boolean(), nullable=True),
                    sa.Column('durchfuehrungsVertrag', sa.Boolean(), nullable=True),
                    sa.Column('gruenordnungsplan', sa.Boolean(), nullable=True),
                    sa.Column('versionBauNVODatum', sa.Date(), nullable=True),
                    sa.Column('versionBauNVOText', sa.String(), nullable=True),
                    sa.Column('versionBauGBDatum', sa.Date(), nullable=True),
                    sa.Column('versionBauGBText', sa.String(), nullable=True),
                    sa.Column('versionSonstRechtsgrundlageDatum', sa.Date(), nullable=True),
                    sa.Column('versionSonstRechtsgrundlageText', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['xp_plan.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_plan',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('planArt',
                              sa.Enum('FPlan', 'GemeinsamerFPlan', 'RegFPlan', 'FPlanRegPlan', 'SachlicherTeilplan',
                                      'Sonstiges', name='fp_planart'), nullable=False),
                    sa.Column('sachgebiet', sa.String(), nullable=True),
                    sa.Column('verfahren', sa.Enum('Normal', 'Parag13', name='fp_verfahren'), nullable=True),
                    sa.Column('rechtsstand',
                              sa.Enum('Aufstellungsbeschluss', 'Entwurf', 'FruehzeitigeBehoerdenBeteiligung',
                                      'FruehzeitigeOeffentlichkeitsBeteiligung', 'BehoerdenBeteiligung',
                                      'OeffentlicheAuslegung', 'Plan', 'Wirksamkeit', 'Untergegangen', 'Aufgehoben',
                                      'AusserKraft', name='fp_rechtsstand'), nullable=True),
                    sa.Column('aufstellungsbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('auslegungsStartDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('auslegungsEndDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('traegerbeteiligungsStartDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('traegerbeteiligungsEndDatum', sa.ARRAY(sa.Date()), nullable=True),
                    sa.Column('aenderungenBisDatum', sa.Date(), nullable=True),
                    sa.Column('entwurfsbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('planbeschlussDatum', sa.Date(), nullable=True),
                    sa.Column('wirksamkeitsDatum', sa.Date(), nullable=True),
                    sa.Column('versionBauNVODatum', sa.Date(), nullable=True),
                    sa.Column('versionBauNVOText', sa.String(), nullable=True),
                    sa.Column('versionBauGBDatum', sa.Date(), nullable=True),
                    sa.Column('versionBauGBText', sa.String(), nullable=True),
                    sa.Column('versionSonstRechtsgrundlageDatum', sa.Date(), nullable=True),
                    sa.Column('versionSonstRechtsgrundlageText', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['xp_plan.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_plan_gemeinde',
                    sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.Column('gemeinde_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.ForeignKeyConstraint(['gemeinde_id'], ['xp_gemeinde.id'], ),
                    sa.ForeignKeyConstraint(['plan_id'], ['xp_plan.id'], )
                    )
    op.create_table('xp_ppo',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('position', Geometry(geometry_type='POINT', from_text='ST_GeomFromEWKT',
                                                   name='geometry'), nullable=True),
                    sa.Column('drehwinkel', sa.Integer(), nullable=True),
                    sa.Column('skalierung', sa.Float(), nullable=True),
                    sa.Column('symbol_path', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['xp_po.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_spez_externe_referenz',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('georefURL', sa.String(), nullable=True),
                    sa.Column('art', sa.Enum('Dokument', 'PlanMitGeoreferenz', name='xp_externereferenzart'),
                              nullable=True),
                    sa.Column('referenzName', sa.String(), nullable=True),
                    sa.Column('referenzURL', sa.String(), nullable=True),
                    sa.Column('referenzMimeType',
                              sa.Enum('application/pdf', 'application/zip', 'application/xml', 'application/msword',
                                      'application/msexcel', 'application/vnd.ogc.sld+xml',
                                      'application/vnd.ogc.wms_xml', 'application/vnd.ogc.gml', 'application/vnd.shp',
                                      'application/vnd.dbf', 'application/vnd.shx', 'application/octet-stream',
                                      'image/vnd.dxf', 'image/vnd.dwg', 'image/jpg', 'image/png', 'image/tiff',
                                      'image/bmp', 'image/ecw', 'image/svg+xml', 'text/html', 'text/plain',
                                      name='xp_mime_types'), nullable=True),
                    sa.Column('beschreibung', sa.String(), nullable=True),
                    sa.Column('datum', sa.Date(), nullable=True),
                    sa.Column('file', postgresql.BYTEA(), nullable=True),
                    sa.Column('typ', sa.Enum('Beschreibung', 'Begruendung', 'Legende', 'Rechtsplan', 'Plangrundlage',
                                             'Umweltbericht', 'Satzung', 'Verordnung', 'Karte', 'Erlaeuterung',
                                             'ZusammenfassendeErklaerung', 'Koordinatenliste',
                                             'Grundstuecksverzeichnis', 'Pflanzliste', 'Gruenordnungsplan',
                                             'Erschliessungsvertrag', 'Durchfuehrungsvertrag',
                                             'StaedtebaulicherVertrag', 'UmweltbezogeneStellungnahmen', 'Beschluss',
                                             'VorhabenUndErschliessungsplan', 'MetadatenPlan', 'Genehmigung',
                                             'Bekanntmachung', 'Rechtsverbindlich', 'Informell',
                                             name='xp_externereferenztyp'), nullable=True),
                    sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.CheckConstraint('NOT("referenzName" IS NULL AND "referenzURL" IS NULL)'),
                    sa.ForeignKeyConstraint(['plan_id'], ['xp_plan.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_tpo',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('position', Geometry(geometry_type='POINT', from_text='ST_GeomFromEWKT',
                                                   name='geometry'), nullable=True),
                    sa.Column('drehwinkel', sa.Integer(), nullable=True),
                    sa.Column('schriftinhalt', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['xp_po.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_verfahrens_merkmal',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.Column('vermerk', sa.String(), nullable=False),
                    sa.Column('datum', sa.Date(), nullable=False),
                    sa.Column('signatur', sa.String(), nullable=False),
                    sa.Column('signiert', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['plan_id'], ['xp_plan.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('bp_baugebiet',
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
                    sa.Column('wohnnutzungEGStrasse',
                              sa.Enum('Zulaessig', 'NichtZulaessig', 'AusnahmsweiseZulaessig', name='bp_zulaessigkeit'),
                              nullable=True),
                    sa.Column('ZWohn', sa.Integer(), nullable=True),
                    sa.Column('GFAntWohnen', sa.Integer(), nullable=True),
                    sa.Column('GFWohnen', sa.Float(), nullable=True),
                    sa.Column('GFAntGewerbe', sa.Integer(), nullable=True),
                    sa.Column('GFGewerbe', sa.Float(), nullable=True),
                    sa.Column('VF', sa.Float(), nullable=True),
                    sa.Column('allgArtDerBaulNutzung',
                              sa.Enum('WohnBauflaeche', 'GemischteBauflaeche', 'GewerblicheBauflaeche',
                                      'SonderBauflaeche', 'Sonstiges', name='xp_allgartderbaulnutzung'), nullable=True),
                    sa.Column('besondereArtDerBaulNutzung',
                              sa.Enum('Kleinsiedlungsgebiet', 'ReinesWohngebiet', 'AllgWohngebiet',
                                      'BesonderesWohngebiet', 'Dorfgebiet', 'Mischgebiet', 'UrbanesGebiet',
                                      'Kerngebiet', 'Gewerbegebiet', 'Industriegebiet', 'SondergebietErholung',
                                      'SondergebietSonst', 'Wochenendhausgebiet', 'Sondergebiet', 'SonstigesGebiet',
                                      name='xp_besondereartderbaulnutzung'), nullable=True),
                    sa.Column('sondernutzung', sa.Enum('KeineSondernutzung', 'Wochendhausgebiet', 'Ferienhausgebiet',
                                                       'Campingplatzgebiet', 'Kurgebiet', 'SonstSondergebietErholung',
                                                       'Einzelhandelsgebiet', 'GrossflaechigerEinzelhandel',
                                                       'Ladengebiet', 'Einkaufszentrum', 'SonstGrossflEinzelhandel',
                                                       'Verkehrsuebungsplatz', 'Hafengebiet',
                                                       'SondergebietErneuerbareEnergie', 'SondergebietMilitaer',
                                                       'SondergebietLandwirtschaft', 'SondergebietSport',
                                                       'SondergebietGesundheitSoziales', 'Klinikgebiet', 'Golfplatz',
                                                       'SondergebietKultur', 'SondergebietTourismus',
                                                       'SondergebietBueroUndVerwaltung', 'SondergebietJustiz',
                                                       'SondergebietHochschuleForschung', 'SondergebietMesse',
                                                       'SondergebietAndereNutzungen', name='xp_sondernutzungen'),
                              nullable=True),
                    sa.Column('nutzungText', sa.String(), nullable=True),
                    sa.Column('abweichungBauNVO',
                              sa.Enum('KeineAbweichung', 'EinschraenkungNutzung', 'AusschlussNutzung',
                                      'AusweitungNutzung', 'SonstAbweichung', name='xp_abweichungbaunvotypen'),
                              nullable=True),
                    sa.Column('bauweise',
                              sa.Enum('KeineAngabe', 'OffeneBauweise', 'GeschlosseneBauweise', 'AbweichendeBauweise',
                                      name='bp_bauweise'), nullable=True),
                    sa.Column('vertikaleDifferenzierung', sa.Boolean(), nullable=True),
                    sa.Column('bebauungsArt',
                              sa.Enum('Einzelhaeuser', 'Doppelhaeuser', 'Hausgruppen', 'EinzelDoppelhaeuser',
                                      'EinzelhaeuserHausgruppen', 'DoppelhaeuserHausgruppen', 'Reihenhaeuser',
                                      'EinzelhaeuserDoppelhaeuserHausgruppen', name='bp_bebauungsart'), nullable=True),
                    sa.Column('bebauungVordereGrenze',
                              sa.Enum('KeineAngabe', 'Verboten', 'Erlaubt', 'Erzwungen', name='bp_grenzbebauung'),
                              nullable=True),
                    sa.Column('bebauungRueckwaertigeGrenze',
                              sa.Enum('KeineAngabe', 'Verboten', 'Erlaubt', 'Erzwungen', name='bp_grenzbebauung'),
                              nullable=True),
                    sa.Column('bebauungSeitlicheGrenze',
                              sa.Enum('KeineAngabe', 'Verboten', 'Erlaubt', 'Erzwungen', name='bp_grenzbebauung'),
                              nullable=True),
                    sa.Column('zugunstenVon', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('bp_baugrenze',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('bautiefe', sa.Float(), nullable=True),
                    sa.Column('geschossMin', sa.Integer(), nullable=True),
                    sa.Column('geschossMax', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['id'], ['bp_objekt.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('bp_bereich',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('versionBauGBDatum', sa.Date(), nullable=True),
                    sa.Column('versionBauGBText', sa.String(), nullable=True),
                    sa.Column('versionSonstRechtsgrundlageDatum', sa.Date(), nullable=True),
                    sa.Column('versionSonstRechtsgrundlageText', sa.String(), nullable=True),
                    sa.Column('gehoertZuPlan_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.ForeignKeyConstraint(['gehoertZuPlan_id'], ['bp_plan.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('fp_bereich',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('gehoertZuPlan_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.ForeignKeyConstraint(['gehoertZuPlan_id'], ['fp_plan.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('bp_dachgestaltung',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('DNmin', sa.Integer(), nullable=True),
                    sa.Column('DNmax', sa.Integer(), nullable=True),
                    sa.Column('DN', sa.Integer(), nullable=True),
                    sa.Column('DNZwingend', sa.Integer(), nullable=True),
                    sa.Column('dachform',
                              sa.Enum('Flachdach', 'Pultdach', 'VersetztesPultdach', 'GeneigtesDach', 'Satteldach',
                                      'Walmdach', 'KrueppelWalmdach', 'Mansarddach', 'Zeltdach', 'Kegeldach',
                                      'Kuppeldach', 'Sheddach', 'Bogendach', 'Turmdach', 'Tonnendach', 'Mischform',
                                      'Sonstiges', name='bp_dachform'), nullable=True),
                    sa.Column('baugebiet_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.ForeignKeyConstraint(['baugebiet_id'], ['bp_baugebiet.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('xp_externe_referenz',
                    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
                    sa.Column('georefURL', sa.String(), nullable=True),
                    sa.Column('art', sa.Enum('Dokument', 'PlanMitGeoreferenz', name='xp_externereferenzart'),
                              nullable=True),
                    sa.Column('referenzName', sa.String(), nullable=True),
                    sa.Column('referenzURL', sa.String(), nullable=True),
                    sa.Column('referenzMimeType',
                              sa.Enum('application/pdf', 'application/zip', 'application/xml', 'application/msword',
                                      'application/msexcel', 'application/vnd.ogc.sld+xml',
                                      'application/vnd.ogc.wms_xml', 'application/vnd.ogc.gml', 'application/vnd.shp',
                                      'application/vnd.dbf', 'application/vnd.shx', 'application/octet-stream',
                                      'image/vnd.dxf', 'image/vnd.dwg', 'image/jpg', 'image/png', 'image/tiff',
                                      'image/bmp', 'image/ecw', 'image/svg+xml', 'text/html', 'text/plain',
                                      name='xp_mime_types'), nullable=True),
                    sa.Column('beschreibung', sa.String(), nullable=True),
                    sa.Column('datum', sa.Date(), nullable=True),
                    sa.Column('file', postgresql.BYTEA(), nullable=True),
                    sa.Column('bereich_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.Column('baugebiet_id', postgresql.UUID(as_uuid=True), nullable=True),
                    sa.CheckConstraint('NOT("referenzName" IS NULL AND "referenzURL" IS NULL)'),
                    sa.ForeignKeyConstraint(['baugebiet_id'], ['bp_baugebiet.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['bereich_id'], ['xp_bereich.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('xp_externe_referenz')
    op.drop_table('bp_dachgestaltung')
    op.drop_table('fp_bereich')
    op.drop_table('bp_bereich')
    op.drop_table('bp_baugrenze')
    op.drop_table('bp_baugebiet')
    op.drop_table('xp_verfahrens_merkmal')
    op.drop_table('xp_tpo')
    op.drop_table('xp_spez_externe_referenz')
    op.drop_table('xp_ppo')
    op.drop_table('xp_plan_gemeinde')
    op.drop_table('fp_plan')
    op.drop_table('bp_plan')
    op.drop_table('bp_objekt')
    op.drop_table('xp_simple_geometry')
    op.drop_table('xp_po')
    op.drop_table('xp_plan')
    op.drop_table('xp_objekt')
    op.drop_table('xp_plangeber')
    op.drop_table('xp_gemeinde')
    op.drop_table('xp_bereich')
