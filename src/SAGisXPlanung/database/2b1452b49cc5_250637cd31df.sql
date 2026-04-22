BEGIN;

-- Running upgrade 2b1452b49cc5 -> 250637cd31df

CREATE TYPE xp_grenzetypen AS ENUM ('Bundesgrenze', 'Landesgrenze', 'Regierungsbezirksgrenze', 'Bezirksgrenze', 'Kreisgrenze', 'Gemeindegrenze', 'Verbandsgemeindegrenze', 'Samtgemeindegrenze', 'Mitgliedsgemeindegrenze', 'Amtsgrenze', 'Stadtteilgrenze', 'VorgeschlageneGrundstuecksgrenze', 'GrenzeBestehenderBebauungsplan', 'SonstGrenze');

CREATE TYPE so_klassifizgelaendemorphologie AS ENUM ('Terassenkante', 'Rinne', 'EhemMaeander', 'SonstigeStruktur');

CREATE TYPE so_klassifizschutzgebietsonstrecht AS ENUM ('Laermschutzbereich', 'SchutzzoneLeitungstrasse', 'Sonstiges');

CREATE TYPE so_rechtsstandgebiettyp AS ENUM ('VorbereitendeUntersuchung', 'Aufstellung', 'Festlegung', 'Abgeschlossen', 'Verstetigung', 'Sonstiges');

CREATE TYPE so_gebietsart AS ENUM ('Umlegungsgebiet', 'StaedtebaulicheSanierung', 'StaedtebaulicheEntwicklungsmassnahme', 'Stadtumbaugebiet', 'SozialeStadt', 'BusinessImprovementDistrict', 'HousingImprovementDistrict', 'Erhaltungsverordnung', 'ErhaltungsverordnungStaedtebaulicheGestalt', 'ErhaltungsverordnungWohnbevoelkerung', 'ErhaltungsverordnungUmstrukturierung', 'Erhaltungsgebiet', 'ErhaltungsgebietStaedtebaulicheGestalt', 'ErhaltungsgebietWohnbevoelkerung', 'ErhaltungsgebietUmstrukturierung', 'StaedtebaulEntwicklungskonzeptInnenentwicklung', 'GebietMitAngespanntemWohnungsmarkt', 'GenehmigungWohnungseigentum', 'Sonstiges');

CREATE TYPE so_rechtlichegrundlagebaubeschraenkung AS ENUM ('Luftverkehrsrecht', 'Strassenverkehrsrecht', 'SonstigesRecht');

CREATE TYPE so_klassifizbaubeschraenkung AS ENUM ('Bauverbotszone', 'Baubeschraenkungszone', 'Waldabstand', 'SonstigeBeschraenkung');

CREATE TYPE so_rechtlichegrundlagebauverbot AS ENUM ('Luftverkehrsrecht', 'Strassenverkehrsrecht', 'SonstigesRecht');

CREATE TYPE so_klassifizbauverbot AS ENUM ('Bauverbotszone', 'Baubeschraenkungszone', 'Waldabstand', 'SonstigeBeschraenkung');

CREATE TYPE fp_massnahmeklimawandeltypen AS ENUM ('ErhaltFreiflaechen', 'ErhaltPrivGruen', 'ErhaltOeffentlGruen', 'ErhaltKaltluftschneise', 'SonstMassnahme');

CREATE TYPE bp_zweckbestimmungentmf AS ENUM ('Luftreinhaltung', 'NutzungErneurerbarerEnergien', 'MinderungStoerfallfolgen');

CREATE TYPE bp_abstandsmasstypen AS ENUM ('Masspfeil', 'Masskreis');

CREATE TYPE bp_schallleistungspegelberechnungsgrundlage AS ENUM ('DIN45691', 'DIN18005', 'VDI2714', 'ISO9613_2');

CREATE TYPE bp_schallleistungspegeltypen AS ENUM ('LEK', 'IFSP', 'FSP');

CREATE TYPE bp_gebaeudestellungtypen AS ENUM ('Firstrichtung', 'Dachneigungsrichtung', 'StellungBaulAnlagen');

CREATE TYPE bp_speziellebauweisetypen AS ENUM ('Durchfahrt', 'Durchgang', 'DurchfahrtDurchgang', 'Auskragung', 'Arkade', 'Luftgeschoss', 'Bruecke', 'Tunnel', 'Rampe', 'Sonstiges');

CREATE TYPE bp_zweckbestimmunggemeinschaftsanlagen AS ENUM ('Gemeinschaftsstellplaetze', 'Gemeinschaftsgaragen', 'Spielplatz', 'Carport', 'GemeinschaftsTiefgarage', 'Nebengebaeude', 'AbfallSammelanlagen', 'EnergieVerteilungsanlagen', 'AbfallWertstoffbehaelter', 'Freizeiteinrichtungen', 'Laermschutzanlagen', 'AbwasserRegenwasser', 'Ausgleichsmassnahmen', 'Fahrradstellplaetze', 'Gemeinschaftsdachgaerten', 'GemeinschaftlichNutzbareDachflaechen', 'Sonstiges');

CREATE TABLE bp_abstand (
    id UUID NOT NULL, 
    tiefe FLOAT, 
    CONSTRAINT pk_bp_abstand PRIMARY KEY (id), 
    CONSTRAINT fk_bp_abstand_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_abstands_mass (
    id UUID NOT NULL, 
    typ bp_abstandsmasstypen, 
    wert FLOAT, 
    "startWinkel" FLOAT, 
    "endWinkel" FLOAT, 
    CONSTRAINT pk_bp_abstands_mass PRIMARY KEY (id), 
    CONSTRAINT fk_bp_abstands_mass_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_abweichung_baugrenze (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_abweichung_baugrenze PRIMARY KEY (id), 
    CONSTRAINT fk_bp_abweichung_baugrenze_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_abweichung_ueberbaubare_grundstuecksflaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_abweichung_ueberbaubare_grundstuecksflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_abweichung_ueberbaubare_grundstuecksflaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_ausgleich (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    CONSTRAINT pk_bp_ausgleich PRIMARY KEY (id), 
    CONSTRAINT fk_bp_ausgleich_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_ausgleichsmassnahme (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    CONSTRAINT pk_bp_ausgleichsmassnahme PRIMARY KEY (id), 
    CONSTRAINT fk_bp_ausgleichsmassnahme_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_einfahrtsbereich (
    id UUID NOT NULL, 
    typ bp_einfahrttypen, 
    CONSTRAINT pk_bp_einfahrtsbereich PRIMARY KEY (id), 
    CONSTRAINT fk_bp_einfahrtsbereich_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_eingriffsbereich (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_eingriffsbereich PRIMARY KEY (id), 
    CONSTRAINT fk_bp_eingriffsbereich_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_emissionskontingent_laerm (
    id UUID NOT NULL, 
    type VARCHAR(50), 
    "pegelTyp" bp_schallleistungspegeltypen, 
    berechnungsgrundlage bp_schallleistungspegelberechnungsgrundlage, 
    "berechnungsgrundlageDatum" DATE, 
    "ekwertTag" FLOAT NOT NULL, 
    "ekwertNacht" FLOAT NOT NULL, 
    erlaeuterung VARCHAR, 
    bp_objekt_id UUID, 
    so_objekt_id UUID, 
    bp_objekt_gebiet_id UUID, 
    so_objekt_gebiet_id UUID, 
    CONSTRAINT pk_bp_emissionskontingent_laerm PRIMARY KEY (id), 
    CONSTRAINT fk_bp_emissionskontingent_laerm_bp_objekt_gebiet_id_bp_objekt FOREIGN KEY(bp_objekt_gebiet_id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_emissionskontingent_laerm_bp_objekt_id_bp_objekt FOREIGN KEY(bp_objekt_id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_emissionskontingent_laerm_so_objekt_gebiet_id_so_objekt FOREIGN KEY(so_objekt_gebiet_id) REFERENCES so_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_emissionskontingent_laerm_so_objekt_id_so_objekt FOREIGN KEY(so_objekt_id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_festsetzung_landesrecht (
    id UUID NOT NULL, 
    kurzbeschreibung VARCHAR, 
    CONSTRAINT pk_bp_festsetzung_landesrecht PRIMARY KEY (id), 
    CONSTRAINT fk_bp_festsetzung_landesrecht_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_freiflaeche (
    id UUID NOT NULL, 
    nutzung VARCHAR, 
    CONSTRAINT pk_bp_freiflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_freiflaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_gebaeude_flaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_gebaeude_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_gebaeude_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_gebaeude_stellung (
    id UUID NOT NULL, 
    typ bp_gebaeudestellungtypen NOT NULL, 
    CONSTRAINT pk_bp_gebaeude_stellung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_gebaeude_stellung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_gemeinschaftsanlage (
    id UUID NOT NULL, 
    zweckbestimmung bp_zweckbestimmunggemeinschaftsanlagen[], 
    "Zmax" INTEGER, 
    CONSTRAINT pk_bp_gemeinschaftsanlage PRIMARY KEY (id), 
    CONSTRAINT fk_bp_gemeinschaftsanlage_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_hoehen_mass (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_hoehen_mass PRIMARY KEY (id), 
    CONSTRAINT fk_bp_hoehen_mass_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_kleintierhaltung (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_kleintierhaltung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_kleintierhaltung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_nicht_ueberbaubare_grundstuecksflaeche (
    id UUID NOT NULL, 
    nutzung_id UUID, 
    CONSTRAINT pk_bp_nicht_ueberbaubare_grundstuecksflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_nicht_ueberbaubare_grundstuecksflaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_nicht_ueberbaubare_grundstuecksflaeche_nutzung_id_5738 FOREIGN KEY(nutzung_id) REFERENCES codelist_values (id)
);

CREATE TABLE bp_persgruppen_bestimmte_flaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_persgruppen_bestimmte_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_persgruppen_bestimmte_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_regelung_vergnuegungsstaetten (
    id UUID NOT NULL, 
    zulaessigkeit bp_zulaessigkeit, 
    CONSTRAINT pk_bp_regelung_vergnuegungsstaetten PRIMARY KEY (id), 
    CONSTRAINT fk_bp_regelung_vergnuegungsstaetten_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_richtungssektorgrenze (
    id UUID NOT NULL, 
    winkel FLOAT, 
    CONSTRAINT pk_bp_richtungssektorgrenze PRIMARY KEY (id), 
    CONSTRAINT fk_bp_richtungssektorgrenze_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_spezielle_bauweise (
    id UUID NOT NULL, 
    typ bp_speziellebauweisetypen, 
    "sonstTyp_id" UUID, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    CONSTRAINT pk_bp_spezielle_bauweise PRIMARY KEY (id), 
    CONSTRAINT fk_bp_spezielle_bauweise_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT "fk_bp_spezielle_bauweise_sonstTyp_id_codelist_values" FOREIGN KEY("sonstTyp_id") REFERENCES codelist_values (id)
);

CREATE TABLE bp_technische_massnahmen (
    id UUID NOT NULL, 
    zweckbestimmung bp_zweckbestimmungentmf NOT NULL, 
    "technischeMassnahme" VARCHAR, 
    CONSTRAINT pk_bp_technische_massnahmen PRIMARY KEY (id), 
    CONSTRAINT fk_bp_technische_massnahmen_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_unverbindliche_vormerkung (
    id UUID NOT NULL, 
    vormerkung VARCHAR, 
    CONSTRAINT pk_bp_unverbindliche_vormerkung PRIMARY KEY (id), 
    CONSTRAINT fk_bp_unverbindliche_vormerkung_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zentraler_versorgungsbereich (
    id UUID NOT NULL, 
    CONSTRAINT pk_bp_zentraler_versorgungsbereich PRIMARY KEY (id), 
    CONSTRAINT fk_bp_zentraler_versorgungsbereich_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zusatzkontingent_laerm (
    id UUID NOT NULL, 
    bezeichnung VARCHAR, 
    CONSTRAINT pk_bp_zusatzkontingent_laerm PRIMARY KEY (id), 
    CONSTRAINT fk_bp_zusatzkontingent_laerm_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zusatzkontingent_laerm_flaeche (
    id UUID NOT NULL, 
    bezeichnung VARCHAR, 
    CONSTRAINT pk_bp_zusatzkontingent_laerm_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_zusatzkontingent_laerm_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_anpassung_klimawandel (
    id UUID NOT NULL, 
    massnahme fp_massnahmeklimawandeltypen, 
    "detailMassnahme_id" UUID, 
    CONSTRAINT pk_fp_anpassung_klimawandel PRIMARY KEY (id), 
    CONSTRAINT "fk_fp_anpassung_klimawandel_detailMassnahme_id_codelist_values" FOREIGN KEY("detailMassnahme_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_fp_anpassung_klimawandel_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_ausgleich (
    id UUID NOT NULL, 
    ziel xp_speziele, 
    "sonstZiel" VARCHAR, 
    CONSTRAINT pk_fp_ausgleich PRIMARY KEY (id), 
    CONSTRAINT fk_fp_ausgleich_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_darstellung_landesrecht (
    id UUID NOT NULL, 
    kurzbeschreibung VARCHAR, 
    CONSTRAINT pk_fp_darstellung_landesrecht PRIMARY KEY (id), 
    CONSTRAINT fk_fp_darstellung_landesrecht_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_keine_zentr_abwasser_beseitigung (
    id UUID NOT NULL, 
    CONSTRAINT pk_fp_keine_zentr_abwasser_beseitigung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_keine_zentr_abwasser_beseitigung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_textabschnittsflaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_fp_textabschnittsflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_fp_textabschnittsflaeche_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_textliche_darstellungsflaeche (
    id UUID NOT NULL, 
    CONSTRAINT pk_fp_textliche_darstellungsflaeche PRIMARY KEY (id), 
    CONSTRAINT fk_fp_textliche_darstellungsflaeche_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_unverbindliche_vormerkung (
    id UUID NOT NULL, 
    vormerkung VARCHAR, 
    CONSTRAINT pk_fp_unverbindliche_vormerkung PRIMARY KEY (id), 
    CONSTRAINT fk_fp_unverbindliche_vormerkung_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_vorbehalte_flaeche (
    id UUID NOT NULL, 
    vorbehalt VARCHAR, 
    CONSTRAINT pk_fp_vorbehalte_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_fp_vorbehalte_flaeche_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE fp_zentraler_versorgungsbereich (
    id UUID NOT NULL, 
    auspraegung_id UUID, 
    CONSTRAINT pk_fp_zentraler_versorgungsbereich PRIMARY KEY (id), 
    CONSTRAINT fk_fp_zentraler_versorgungsbereich_auspraegung_id_codel_1d3e FOREIGN KEY(auspraegung_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_fp_zentraler_versorgungsbereich_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_baubeschraenkung (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizbaubeschraenkung, 
    "detailArtDerFestlegung_id" UUID, 
    "rechtlicheGrundlage" so_rechtlichegrundlagebaubeschraenkung, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_baubeschraenkung PRIMARY KEY (id), 
    CONSTRAINT "fk_so_baubeschraenkung_detailArtDerFestlegung_id_codeli_6cb9" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_baubeschraenkung_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_bauverbotszone (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizbauverbot, 
    "detailArtDerFestlegung_id" UUID, 
    "rechtlicheGrundlage" so_rechtlichegrundlagebauverbot, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_bauverbotszone PRIMARY KEY (id), 
    CONSTRAINT "fk_so_bauverbotszone_detailArtDerFestlegung_id_codelist_values" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_bauverbotszone_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_forstrecht (
    id UUID NOT NULL, 
    "artDerFestlegung" xp_eigentumsartwald, 
    "detailArtDerFestlegung_id" UUID, 
    funktion xp_zweckbestimmungwald[], 
    betreten xp_waldbetretungtyp[], 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_forstrecht PRIMARY KEY (id), 
    CONSTRAINT "fk_so_forstrecht_detailArtDerFestlegung_id_codelist_values" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_forstrecht_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_gebiet (
    id UUID NOT NULL, 
    gemeinde_id UUID, 
    "gebietsArt" so_gebietsart, 
    "sonstGebietsArt_id" UUID, 
    "rechtsstandGebiet" so_rechtsstandgebiettyp, 
    "sonstRechtsstandGebiet_id" UUID, 
    "aufstellungsbeschhlussDatum" DATE, 
    "durchfuehrungStartDatum" DATE, 
    "durchfuehrungEndDatum" DATE, 
    "traegerMassnahme" VARCHAR, 
    CONSTRAINT pk_so_gebiet PRIMARY KEY (id), 
    CONSTRAINT fk_so_gebiet_gemeinde_id_xp_gemeinde FOREIGN KEY(gemeinde_id) REFERENCES xp_gemeinde (id), 
    CONSTRAINT fk_so_gebiet_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT "fk_so_gebiet_sonstGebietsArt_id_codelist_values" FOREIGN KEY("sonstGebietsArt_id") REFERENCES codelist_values (id), 
    CONSTRAINT "fk_so_gebiet_sonstRechtsstandGebiet_id_codelist_values" FOREIGN KEY("sonstRechtsstandGebiet_id") REFERENCES codelist_values (id)
);

CREATE TABLE so_gelaendemorphologie (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizgelaendemorphologie, 
    "detailArtDerFestlegung_id" UUID, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_gelaendemorphologie PRIMARY KEY (id), 
    CONSTRAINT "fk_so_gelaendemorphologie_detailArtDerFestlegung_id_cod_b142" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_gelaendemorphologie_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE so_grenze (
    id UUID NOT NULL, 
    typ xp_grenzetypen, 
    "sonstTyp_id" UUID, 
    CONSTRAINT pk_so_grenze PRIMARY KEY (id), 
    CONSTRAINT fk_so_grenze_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT "fk_so_grenze_sonstTyp_id_codelist_values" FOREIGN KEY("sonstTyp_id") REFERENCES codelist_values (id)
);

CREATE TABLE so_schutzgebiet_sonstiges_recht (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifizschutzgebietsonstrecht, 
    "detailArtDerFestlegung_id" UUID, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_schutzgebiet_sonstiges_recht PRIMARY KEY (id), 
    CONSTRAINT "fk_so_schutzgebiet_sonstiges_recht_detailArtDerFestlegu_d8e3" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_schutzgebiet_sonstiges_recht_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_landesrecht (
    codelist_user_id UUID, 
    codelist_id UUID, 
    CONSTRAINT fk_assoc_detail_landesrecht_codelist_id_codelist_values FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_assoc_detail_landesrecht_codelist_user_id_fp_darstel_7892 FOREIGN KEY(codelist_user_id) REFERENCES fp_darstellung_landesrecht (id) ON DELETE CASCADE
);

CREATE TABLE assoc_gemeinschaftsanlage_eigentuemer (
    gemeinschaftsanlage_id UUID, 
    baugebiet_id UUID, 
    CONSTRAINT fk_assoc_gemeinschaftsanlage_eigentuemer_baugebiet_id_b_9338 FOREIGN KEY(baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE, 
    CONSTRAINT fk_assoc_gemeinschaftsanlage_eigentuemer_gemeinschaftsa_227e FOREIGN KEY(gemeinschaftsanlage_id) REFERENCES bp_gemeinschaftsanlage (id) ON DELETE CASCADE
);

CREATE TABLE bp_emissionskontingent_laerm_gebiet (
    id UUID NOT NULL, 
    gebietsbezeichnung VARCHAR, 
    CONSTRAINT pk_bp_emissionskontingent_laerm_gebiet PRIMARY KEY (id), 
    CONSTRAINT fk_bp_emissionskontingent_laerm_gebiet_id_bp_emissionsk_2164 FOREIGN KEY(id) REFERENCES bp_emissionskontingent_laerm (id) ON DELETE CASCADE
);

CREATE TABLE bp_richtungssektor (
    id UUID NOT NULL, 
    "winkelAnfang" FLOAT NOT NULL, 
    "winkelEnde" FLOAT NOT NULL, 
    "zkWertTag" FLOAT NOT NULL, 
    "zkWertNacht" FLOAT NOT NULL, 
    zusatzkontingent_id UUID, 
    "zusatzkontingentFlaeche_id" UUID, 
    CONSTRAINT pk_bp_richtungssektor PRIMARY KEY (id), 
    CONSTRAINT "fk_bp_richtungssektor_zusatzkontingentFlaeche_id_bp_zus_df43" FOREIGN KEY("zusatzkontingentFlaeche_id") REFERENCES bp_zusatzkontingent_laerm_flaeche (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_richtungssektor_zusatzkontingent_id_bp_zusatzkont_1130 FOREIGN KEY(zusatzkontingent_id) REFERENCES bp_zusatzkontingent_laerm (id) ON DELETE CASCADE
);

CREATE TABLE bp_veraenderungssperre (
    id UUID NOT NULL, 
    "veraenderungssperreBeschlussDatum" DATE, 
    "veraenderungssperreStartDatum" DATE, 
    "gueltigkeitsDatum" DATE, 
    verlaengerung xp_verlaengerungveraenderungssperre, 
    daten_id UUID, 
    CONSTRAINT pk_bp_veraenderungssperre PRIMARY KEY (id), 
    CONSTRAINT fk_bp_veraenderungssperre_daten_id_bp_veraenderungssperre_daten FOREIGN KEY(daten_id) REFERENCES bp_veraenderungssperre_daten (id), 
    CONSTRAINT fk_bp_veraenderungssperre_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE bp_zweckbestimmung_gemeinschaftsanlage (
    id UUID NOT NULL, 
    allgemein bp_zweckbestimmunggemeinschaftsanlagen NOT NULL, 
    "textlicheErgaenzung" VARCHAR, 
    aufschrift VARCHAR, 
    gemeinschaftsanlage_id UUID, 
    CONSTRAINT pk_bp_zweckbestimmung_gemeinschaftsanlage PRIMARY KEY (id), 
    CONSTRAINT fk_bp_zweckbestimmung_gemeinschaftsanlage_gemeinschafts_2620 FOREIGN KEY(gemeinschaftsanlage_id) REFERENCES bp_gemeinschaftsanlage (id) ON DELETE CASCADE
);

CREATE TABLE assoc_detail_gemeinschaftsanlagen (
    codelist_user_id UUID, 
    codelist_user_v6_id UUID, 
    codelist_id UUID, 
    CONSTRAINT fk_assoc_detail_gemeinschaftsanlagen_codelist_id_codeli_2331 FOREIGN KEY(codelist_id) REFERENCES codelist_values (id), 
    CONSTRAINT fk_assoc_detail_gemeinschaftsanlagen_codelist_user_id_b_bf8b FOREIGN KEY(codelist_user_id) REFERENCES bp_gemeinschaftsanlage (id) ON DELETE CASCADE, 
    CONSTRAINT fk_assoc_detail_gemeinschaftsanlagen_codelist_user_v6_i_96d6 FOREIGN KEY(codelist_user_v6_id) REFERENCES bp_zweckbestimmung_gemeinschaftsanlage (id) ON DELETE CASCADE
);

ALTER TABLE bp_baugebiet ALTER COLUMN "GFAntWohnen" TYPE FLOAT;

ALTER TABLE bp_baugebiet ALTER COLUMN "GFAntGewerbe" TYPE FLOAT;

ALTER TABLE bp_grundstueck_ueberbaubar ALTER COLUMN "GFAntWohnen" TYPE FLOAT;

ALTER TABLE bp_grundstueck_ueberbaubar ALTER COLUMN "GFAntGewerbe" TYPE FLOAT;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_ausgleichsflaeche_massnahme_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_ausgleichsflaeche_plan_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN fp_ausgleichsflaeche_massnahme_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN fp_ausgleichsflaeche_plan_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_ausgleichsmassnahme_massnahme_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_ausgleichsmassnahme_plan_id UUID;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_ausgleichsflaeche_plan_id_bp__f2fd FOREIGN KEY(bp_ausgleichsflaeche_plan_id) REFERENCES bp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_fp_ausgleichsflaeche_massnahme_i_94c0 FOREIGN KEY(fp_ausgleichsflaeche_massnahme_id) REFERENCES fp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_ausgleichsmassnahme_plan_id_b_d19f FOREIGN KEY(bp_ausgleichsmassnahme_plan_id) REFERENCES bp_ausgleichsmassnahme (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_ausgleichsflaeche_massnahme_i_076a FOREIGN KEY(bp_ausgleichsflaeche_massnahme_id) REFERENCES bp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_ausgleichsmassnahme_massnahme_4aaa FOREIGN KEY(bp_ausgleichsmassnahme_massnahme_id) REFERENCES bp_ausgleichsmassnahme (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_fp_ausgleichsflaeche_plan_id_fp__bedf FOREIGN KEY(fp_ausgleichsflaeche_plan_id) REFERENCES fp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz DROP COLUMN "referenzMimeType";

ALTER TABLE xp_spe_daten ADD COLUMN bp_ausgleichsflaeche_id UUID;

ALTER TABLE xp_spe_daten ADD COLUMN bp_ausgleichsmassnahme_id UUID;

ALTER TABLE xp_spe_daten ADD COLUMN fp_ausgleichsflaeche_id UUID;

ALTER TABLE xp_spe_daten ADD CONSTRAINT fk_xp_spe_daten_bp_ausgleichsflaeche_id_bp_ausgleich FOREIGN KEY(bp_ausgleichsflaeche_id) REFERENCES bp_ausgleich (id) ON DELETE CASCADE;

ALTER TABLE xp_spe_daten ADD CONSTRAINT fk_xp_spe_daten_bp_ausgleichsmassnahme_id_bp_ausgleichs_3c4c FOREIGN KEY(bp_ausgleichsmassnahme_id) REFERENCES bp_ausgleichsmassnahme (id) ON DELETE CASCADE;

ALTER TABLE xp_spe_daten ADD CONSTRAINT fk_xp_spe_daten_fp_ausgleichsflaeche_id_fp_ausgleich FOREIGN KEY(fp_ausgleichsflaeche_id) REFERENCES fp_ausgleich (id) ON DELETE CASCADE;

DROP TYPE xp_mime_types;

UPDATE alembic_version SET version_num='250637cd31df' WHERE alembic_version.version_num = '2b1452b49cc5';

COMMIT;

