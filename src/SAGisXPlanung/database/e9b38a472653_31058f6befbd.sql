BEGIN;

-- Running upgrade e9b38a472653 -> 31058f6befbd

ALTER TABLE xp_objekt ALTER COLUMN type TYPE varchar;;

CREATE TYPE lp_planungsebene AS ENUM ('Biotopverbund', 'Biotopvernetzung');

CREATE TYPE lp_rechtlichesicherung AS ENUM ('Schutzerklaerung', 'PlanungsrechtlicheFestlegung', 'VertraglicheRegelung', 'Sonstiges');

CREATE TYPE lp_bioverbundsystemart AS ENUM ('Allgemein', 'OffenlandHalboffenland', 'Wald', 'Gewaesser');

CREATE TYPE lp_biovstandortfeuchte AS ENUM ('Feucht', 'Mittel', 'Trocken');

CREATE TABLE lp_biotopverbund_biotopvernetzung (
    id UUID NOT NULL, 
    "planungsEbene" lp_planungsebene[], 
    "rechtlicheSicherung" lp_rechtlichesicherung, 
    "rechtlicheSicherungText" VARCHAR, 
    "bioVerbundsystemArt" lp_bioverbundsystemart NOT NULL, 
    "bioVStandortFeuchte" lp_biovstandortfeuchte, 
    "bioVerbundsystemText" VARCHAR, 
    foerdermoeglichkeit VARCHAR[], 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE lp_umsetzungsstand AS ENUM ('NachrichtlichUmgesetztOderAngerechnet', 'Vorschlag', 'Unbekannt');

CREATE TYPE lp_massnahmentyp AS ENUM ('Kompensationsmassnahme', 'MassnahmeCEF', 'MassnahmeFCS', 'MassnahmeKohaerenzsicherung', 'Unbekannt');

CREATE TABLE lp_eingriffsregelung (
    id UUID NOT NULL, 
    umsetzungsstand lp_umsetzungsstand NOT NULL, 
    massnahmentyp lp_massnahmentyp[] NOT NULL, 
    "kompensationText" VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE lp_generisches_objekt (
    id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE lp_klassifizierungnaturschutzrecht AS ENUM ('Naturschutzgebiet', 'Nationalpark', 'Biosphaerenreservat', 'Landschaftsschutzgebiet', 'Naturpark', 'Naturdenkmal', 'GeschuetzterLandschaftsbestandteil', 'GesetzlichgeschuetztesBiotop', 'Natura2000', 'GebietGemeinschaftlicherBedeutung', 'EuropaeischesVogelschutzgebiet', 'NationalesNaturmonument', 'Sonstiges');

CREATE TYPE lp_rechtsstandschutzgeb AS ENUM ('Geplant', 'Bestehend', 'Fortfallend', 'Eignung', 'Erweiterung', 'Qualifizierung', 'Sonstiges');

CREATE TYPE lp_gesgeschbiotoptyp AS ENUM ('Gewaesserbiotope', 'FeuchtUndNassbiotope', 'Trockenbiotope', 'Waldbiotope', 'FelsenAlpineBiotope', 'Kuestenbiotope', 'Sonstiges');

CREATE TYPE lp_schutzzonennaturschutzrecht AS ENUM ('Schutzzone1', 'Schutzzone2', 'Schutzzone3', 'Kernzone', 'Pflegezone', 'Entwicklungszone', 'Regenerationszone', 'Sonstiges');

CREATE TABLE lp_schutz_bestimmter_teile_von_natur_und_landschaft (
    id UUID NOT NULL, 
    "artDerFestlegung" lp_klassifizierungnaturschutzrecht NOT NULL, 
    "artDerFestlegungText" VARCHAR, 
    "rechtsstandSchG" lp_rechtsstandschutzgeb NOT NULL, 
    "rechtsstandSchGText" VARCHAR, 
    name VARCHAR, 
    nummer VARCHAR, 
    "gesetzlGeschBiotop" lp_gesgeschbiotoptyp, 
    "gesetzlGeschBiotopText" VARCHAR, 
    "detailGesetzlGeschBiotopLR_id" UUID, 
    schutzzone lp_schutzzonennaturschutzrecht, 
    "schutzzonenText" VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY("detailGesetzlGeschBiotopLR_id") REFERENCES codelist_values (id), 
    FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE lp_text_abschnitt_objekt (
    id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE lp_zemtyp AS ENUM ('Ziel', 'Erfordernis', 'Massnahme');

CREATE TABLE lp_ziele_erfordernisse_massnahmen (
    id UUID NOT NULL, 
    "artDerFestlegung" lp_zemtyp[] NOT NULL, 
    freiraeume VARCHAR[], 
    foerdermoeglichkeit VARCHAR[], 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES lp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_zweckgenerischeobjekte (
    codelist_user_id UUID, 
    codelist_id UUID, 
    FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    FOREIGN KEY(codelist_user_id) REFERENCES lp_generisches_objekt (id) ON DELETE CASCADE
);

CREATE TYPE lp_adressatart AS ENUM ('Naturschutz', 'Bauleitplanung', 'Raumordnung', 'Flurneuordnung', 'Forstwirtschaft', 'Landwirtschaft', 'Wasserwirtschaft', 'Fischereiwirtschaft', 'Jagd', 'RohstoffgewinnungUndBergbau', 'VerteidigungSicherungDerZivilbevoelkerung', 'Verkehrsplanung', 'Energiegewinnung', 'Abfallwirtschaft', 'Bodenschutz', 'KommunaleKoerperschaften', 'LandKreisverwaltung', 'Land', 'Unbekannt', 'Sonstiges');

CREATE TABLE lp_adressat_komplex (
    id UUID NOT NULL, 
    "adressatArt" lp_adressatart NOT NULL, 
    "adressatText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TABLE lp_biologische_vielfalt_komplex (
    id UUID NOT NULL, 
    "bioVfArtFFHAnhangII" BOOLEAN NOT NULL, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_bodenauspraegung AS ENUM ('Ablagerungen', 'Altablagerungsflaeche', 'Altlastenverdachtsflaeche', 'BodenFilterUndPufferfunktion', 'BodenHoheBodenfruchtbarkeit', 'BodenHoherFunktionglobalerKlimaschutz', 'BodenKulturgeschichtlicheBedeutung', 'BodenNaturgeschichtlicheBedeutung', 'BodenGeowissenschaftlicheBedeutung', 'NatuerlicheBoeedenExtremstandort', 'EhemaligerMilitaerischGenutzterStandort', 'Erosionsgefaehrdet', 'ErosionsgefaehrdetWind', 'ErosionsgefaehrdetWasser', 'Geotop', 'SelteneBodenform', 'NaturnaherBoden', 'BoedenHohesRetentionspotenzial', 'EntsiegelungOderWiederherstellungBodenfunktion', 'Sonstiges');

CREATE TABLE lp_boden_komplex (
    id UUID NOT NULL, 
    "bodenAuspraegung" lp_bodenauspraegung NOT NULL, 
    "bodenText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_erflaechenart AS ENUM ('PotenzielleFlaecheKompensation', 'Flaechenpool', 'KompensationEinzelflaeche', 'Kompensationsverzeichnis', 'Sonstiges');

CREATE TABLE lp_eingriffsregelung_komplex (
    id UUID NOT NULL, 
    "eRFlaechenArt" lp_erflaechenart NOT NULL, 
    "eRFlaechenArtText" VARCHAR, 
    eingriffsregelung_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(eingriffsregelung_id) REFERENCES lp_eingriffsregelung (id) ON DELETE CASCADE
);

CREATE TYPE lp_erholungfunktionen AS ENUM ('Gruenflaechen', 'ParkanlageGruenanlage', 'Dauerkleingaerten', 'Sportplatz', 'Spielplatz', 'BadeplatzFreibad', 'Liegewiese', 'Erholungsinfrastruktur', 'Schutzhuette', 'Rastplatz', 'Informationstafel', 'FeuerstelleGrillplatz', 'Aussichtsturm', 'Aussichtspunkt', 'Angelteich', 'Modellflugplatz', 'Gleitschirmplatz', 'WildgehegeSchaugatter', 'Parkplatz', 'ZeltplatzCampingplatz', 'JugendzeltplatzEinzelcamp', 'ErholungsInfrastrukturMitBesondererBedeutung', 'WandernAllgemein', 'Wanderweg', 'Lehrpfad', 'Reitweg', 'Radweg', 'Wintersport', 'Skiabfahrt', 'Skilanglaufloipe', 'RodelbahnBobbahn', 'WassersportSchifffahrt', 'Wasserwanderweg', 'Schifffahrtsroute', 'AnlegestelleMitMotorbooten', 'AnlegestelleOhneMotorboote', 'Seilbahn', 'SesselliftSchlepplift', 'Kabinenseilbahn', 'Bildungsstaette', 'Umweltbildungsstaette', 'Museum', 'Sonstiges');

CREATE TABLE lp_erholung_komplex (
    id UUID NOT NULL, 
    "erholungFunktionArt" lp_erholungfunktionen NOT NULL, 
    "erholungFunktionText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_klimaart AS ENUM ('BioklimatischeFunktion', 'Luftleitbahn', 'Frischluftbahn', 'Frischluftentstehungsgebiet', 'Kaltluftbahn', 'Kaltluftentstehungsgebiet', 'Stadtklima', 'THGSenkenKlimaschutzflaechen', 'Sonstiges');

CREATE TABLE lp_klima_komplex (
    id UUID NOT NULL, 
    "klimaArt" lp_klimaart NOT NULL, 
    "klimaText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_landschaftsbildart AS ENUM ('KircheKlosterKapelle', 'BurgSchloss', 'Turm', 'HistorischesOrtsbild', 'Ruine', 'KulturgeschichtlichWertvollerOrtsteil', 'Aussichtspunkt', 'Aussichtsturm', 'LandschaftsgerechteEinbindung', 'LandschaftsgerechterSiedlungsrand', 'Strukturvielfalt', 'LandschaftMitHoherEigenart', 'Landschaftsachsen', 'Landschaftsraeume', 'HistorischeWaldinsel', 'Waldraender', 'Kulturlandschaft', 'HistorischeKulturlandschaft', 'Kulturlandschaftselement', 'Hohlweg', 'Gartendenkmal', 'Sonstiges');

CREATE TABLE lp_landschaftsbild_komplex (
    id UUID NOT NULL, 
    "landschaftsbildArt" lp_landschaftsbildart NOT NULL, 
    "landschaftsbildText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_luftart AS ENUM ('Geruchsbelastung', 'Laermbelastung', 'LufthygienischeFktStofflBelastung', 'Staubbelastung', 'Sonstiges');

CREATE TABLE lp_luft_komplex (
    id UUID NOT NULL, 
    "luftArt" lp_luftart NOT NULL, 
    "luftText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TABLE lp_nutzungseinschraenkung_komplex (
    id UUID NOT NULL, 
    "hatNutzungseinschraenkung" BOOLEAN NOT NULL, 
    "nutzungseinschraenkungText" VARCHAR NOT NULL, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_schutzgutart AS ENUM ('AlleSchutzgueter', 'ArtenUndLebensgemeinschaften', 'Biotope', 'Boden', 'Wasser', 'Klima', 'Luft', 'Landschaftsbild', 'ErholungInNaturUndLandschaft', 'Unbekannt', 'Sonstiges');

CREATE TABLE lp_schutzgut_komplex (
    id UUID NOT NULL, 
    "schutzgutArt" lp_schutzgutart NOT NULL, 
    "schutzgutText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_schutzpflegeentwicklung AS ENUM ('Schutz', 'Pflege', 'Entwicklung', 'Anlage', 'Wiederherstellung', 'Vermeidung', 'Minderung', 'Beseitigung', 'Sonstiges');

CREATE TABLE lp_spe_komplex (
    id UUID NOT NULL, 
    "schutzPflegeEntwicklungTyp" lp_schutzpflegeentwicklung[] NOT NULL, 
    "schutzPflegeEntwicklungText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_flaechentypbv AS ENUM ('Kernflaeche', 'Verbindungsflaeche', 'Verbindungselement');

CREATE TYPE lp_flaechentypbvspeziell AS ENUM ('Verbindungsraeume', 'Verbundachse', 'Wildtierkorridor', 'Entwicklungsflaeche', 'Entwicklungsmassnahme', 'Vernetzungselement', 'Trittsteinbiotop', 'Sonstiges');

CREATE TABLE lp_typ_bioverbundkomplexe (
    id UUID NOT NULL, 
    "flaechenTypBV" lp_flaechentypbv NOT NULL, 
    "flaechentypBVSpeziell" lp_flaechentypbvspeziell, 
    "flaechentypSpeziellText" VARCHAR, 
    biotopverbund_biotopvernetzung_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(biotopverbund_biotopvernetzung_id) REFERENCES lp_biotopverbund_biotopvernetzung (id) ON DELETE CASCADE
);

CREATE TYPE lp_wasserauspraegung AS ENUM ('Hochwasserschutz', 'Ueberschwemmungsgebiet', 'Hochwasservorsorge', 'Retentionsraum', 'Polderflaeche', 'Deichrueckverlegung', 'Trinkwassergewinnung', 'Trinkwasserschutz', 'Grundwasserneubildungsgebiet', 'LaengsdurchgaengigkeitGewaesser', 'MindestwasserfuehrungGewaesser', 'Drainage', 'Entwaesserungsgraben', 'NaturnaheGewaesser', 'NaturnaheUferbereiche', 'OekologischeFunktionFliessgewaesser', 'OekologischeFunktionQuellbereich', 'OekologischeFunktionStillgewaesser', 'Gewaesserstruktur', 'Gewaesserdynamik', 'Gewaesserrandstreifen', 'Gewaesserschutzstreifen', 'Pufferzone', 'Ufergehoelze', 'FischaufstiegsOderAbstiegsanlage', 'Wehr', 'Verrohrung', 'Sohlstufe', 'Gewaesserguete', 'StoffeintraegeInGrundwasser', 'StoffeintraegeInOberflaechengewaesser', 'Versickerungsflaeche', 'Verlandungsbereiche', 'Sonstiges');

CREATE TABLE lp_wasser_komplex (
    id UUID NOT NULL, 
    "wasserAuspraegung" lp_wasserauspraegung NOT NULL, 
    "wasserText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TYPE lp_zieldimensiontyp AS ENUM ('SchutzBiologischeVielfalt', 'SchutzNaturhaushalt', 'SchutzLandschaftsbildErholungsvorsorge', 'Unbekannt', 'Sonstiges');

CREATE TABLE lp_ziel_dim_nat_sch_la_pfl_komplex (
    id UUID NOT NULL, 
    "zielDimensionTyp" lp_zieldimensiontyp NOT NULL, 
    "zielDimensionText" VARCHAR, 
    ziele_erfordernisse_massnahmen_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ziele_erfordernisse_massnahmen_id) REFERENCES lp_ziele_erfordernisse_massnahmen (id) ON DELETE CASCADE
);

CREATE TABLE lp_bio_vf_biotoptyp_komplex (
    id UUID NOT NULL, 
    "bioVfBiotoptyp_BKompV_id" UUID, 
    "bioVfBiotoptyp_LandesKS_id" UUID, 
    "bioVf_FFH_LRT_id" UUID, 
    "bioVfBiotoptyp_Text" VARCHAR, 
    biologische_vielfalt_komplex_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY("bioVfBiotoptyp_BKompV_id") REFERENCES codelist_values (id), 
    FOREIGN KEY("bioVfBiotoptyp_LandesKS_id") REFERENCES codelist_values (id), 
    FOREIGN KEY("bioVf_FFH_LRT_id") REFERENCES codelist_values (id), 
    FOREIGN KEY(biologische_vielfalt_komplex_id) REFERENCES lp_biologische_vielfalt_komplex (id) ON DELETE CASCADE
);

CREATE TYPE lp_biovfpflanzenartsystematik AS ENUM ('Gefaesspflanze', 'MooseUndFlechten', 'Pilze', 'Sonstiges');

CREATE TYPE lp_biovfpflanzenartrechtlicherschutz AS ENUM ('AnhangIVFFHRL', 'Anlage1BArtSchV', 'Verantwortungsart', 'Sonstige');

CREATE TABLE lp_bio_vf_pflanzen_art_komplex (
    id UUID NOT NULL, 
    "bioVfPflanzenArtName" VARCHAR, 
    "bioVfPflanzenSystematik" lp_biovfpflanzenartsystematik NOT NULL, 
    "bioVfPflanzenSystematikText" VARCHAR, 
    "bioVfPflanzenRechtlicherSchutz" lp_biovfpflanzenartrechtlicherschutz[], 
    "bioVfPflanzenRechtlicherSchutzText" VARCHAR, 
    biologische_vielfalt_komplex_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(biologische_vielfalt_komplex_id) REFERENCES lp_biologische_vielfalt_komplex (id) ON DELETE CASCADE
);

CREATE TYPE lp_biovftiereartsystematik AS ENUM ('Grosssaeuger', 'Wolf', 'Luchs', 'Mittelsaeuger', 'Wildkatze', 'Fischotter', 'Biber', 'Marder', 'Kleinsaeuger', 'KleinsaeugerNagetiere', 'Feldhamster', 'Maeuse', 'KleinsaeugerHasenartige', 'KleinsaeugerInsektenfresser', 'Spitzmaeuse', 'KleinsaeugerFledermaeuse', 'Meeressaeuger', 'Voegel', 'Zugvoegel', 'Brutvoegel', 'Reptilien', 'Amphibien', 'Fische', 'Gliederfuesser', 'Libellen', 'Tagfalter', 'Kaefer', 'Heuschrecken', 'Spinnen', 'Krebstiere', 'Mollusken', 'Sonstiges');

CREATE TYPE lp_biovftierartrechtlicherschutz AS ENUM ('ArtAnhangIVFFHRL', 'ArtAnhangIArt4Abs2VSRL', 'ArtAnlage1BArtSchV', 'Verantwortungsart', 'Sonstige');

CREATE TYPE lp_biovftierarthabitatanforderung AS ENUM ('GrosserHabitatsAnspruch', 'Gebaeudebewohnend', 'Sonstige');

CREATE TABLE lp_bio_vf_tiere_art_komplex (
    id UUID NOT NULL, 
    "bioVfTierArtName" VARCHAR, 
    "bioVfTiereSystematik" lp_biovftiereartsystematik NOT NULL, 
    "bioVfTiereSystematikText" VARCHAR, 
    "bioVfTierArtRechtlicherSchutz" lp_biovftierartrechtlicherschutz[], 
    "bioVfTierArtRechtlicherSchutzText" VARCHAR, 
    "bioVfTierArtHabitatanforderung" lp_biovftierarthabitatanforderung, 
    "bioVfTierArtHabitatanforderungText" VARCHAR, 
    biologische_vielfalt_komplex_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(biologische_vielfalt_komplex_id) REFERENCES lp_biologische_vielfalt_komplex (id) ON DELETE CASCADE
);

CREATE TYPE lp_biovfbestandteil AS ENUM ('Art', 'BiotopLebensraum', 'LebensstaetteArthabitat', 'Sonstiges');

CREATE TABLE lp_biologische_vielfalt_typ_komplex (
    id UUID NOT NULL, 
    "bioVielfaltTyp" lp_biovfbestandteil NOT NULL, 
    "bioVielfaltTypText" VARCHAR, 
    biologische_vielfalt_komplex_id UUID, 
    PRIMARY KEY (id), 
    FOREIGN KEY(biologische_vielfalt_komplex_id) REFERENCES lp_biologische_vielfalt_komplex (id) ON DELETE CASCADE
);

ALTER TABLE codelist_values ADD COLUMN key VARCHAR;

ALTER TABLE xp_po ADD COLUMN darstellungsprioritaet INTEGER;

ALTER TABLE xp_po ADD COLUMN art VARCHAR[];

ALTER TABLE xp_po ADD COLUMN index INTEGER[];

UPDATE alembic_version SET version_num='31058f6befbd' WHERE alembic_version.version_num = 'e9b38a472653'; --- # pragma: allowlist secret;

COMMIT;

