BEGIN;

-- Running upgrade 31058f6befbd -> da3841c7f8d9

ALTER TABLE xp_po ADD COLUMN "stylesheetId" VARCHAR;

DELETE FROM xp_po p
        WHERE EXISTS (
            SELECT 1
            FROM xp_nutzungsschablone n
            WHERE n.id = p.id
              AND n.hidden = true
        );

CREATE TYPE so_klassifiznachbodenschutzrecht AS ENUM ('SchaedlicheBodenveraenderung', 'Altlast', 'Altablagerung', 'Altstandort', 'AltstandortAufAltablagerung');

CREATE TABLE so_bodenschutz (
    id UUID NOT NULL, 
    "artDerFestlegung" so_klassifiznachbodenschutzrecht, 
    "detailArtDerFestlegung_id" UUID, 
    "istVerdachtsflaeche" BOOLEAN, 
    name VARCHAR, 
    nummer VARCHAR, 
    CONSTRAINT pk_so_bodenschutz PRIMARY KEY (id), 
    CONSTRAINT "fk_so_bodenschutz_detailArtDerFestlegung_id_codelist_values" FOREIGN KEY("detailArtDerFestlegung_id") REFERENCES codelist_values (id), 
    CONSTRAINT fk_so_bodenschutz_id_so_objekt FOREIGN KEY(id) REFERENCES so_objekt (id) ON DELETE CASCADE
);

CREATE TYPE xp_zweckbestimmungwasserwirtschaft AS ENUM ('HochwasserRueckhaltebecken', 'Ueberschwemmgebiet', 'Versickerungsflaeche', 'Entwaesserungsgraben', 'Deich', 'RegenRueckhaltebecken', 'Sonstiges');

CREATE TABLE fp_wasserwirtschaft (
    id UUID NOT NULL, 
    zweckbestimmung xp_zweckbestimmungwasserwirtschaft, 
    CONSTRAINT pk_fp_wasserwirtschaft PRIMARY KEY (id), 
    CONSTRAINT fk_fp_wasserwirtschaft_id_fp_objekt FOREIGN KEY(id) REFERENCES fp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE bp_nebenanlagenausschlusstyp AS ENUM ('Einschraenkung', 'Ausschluss');

CREATE TABLE bp_nebenanlagen_ausschluss_flaeche (
    id UUID NOT NULL, 
    typ bp_nebenanlagenausschlusstyp, 
    CONSTRAINT pk_bp_nebenanlagen_ausschluss_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_nebenanlagen_ausschluss_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TYPE bp_typwohngebaeudeflaeche AS ENUM ('Wohngebaeude', 'GebaeudeFoerderung', 'GebaeudeStaedtebaulicherVertrag');

CREATE TABLE bp_wohngebaeude_flaeche (
    id UUID NOT NULL, 
    "FR" INTEGER, 
    "MaxZahlWohnungen" INTEGER, 
    "MinGRWohneinheit" FLOAT, 
    "Fmin" FLOAT, 
    "Fmax" FLOAT, 
    "Bmin" FLOAT, 
    "Bmax" FLOAT, 
    "Tmin" FLOAT, 
    "Tmax" FLOAT, 
    "GFZmin" FLOAT, 
    "GFZmax" FLOAT, 
    "GFZ" FLOAT, 
    "GFZ_Ausn" FLOAT, 
    "GFmin" FLOAT, 
    "GFmax" FLOAT, 
    "GF" FLOAT, 
    "GF_Ausn" FLOAT, 
    "BMZ" FLOAT, 
    "BMZ_Ausn" FLOAT, 
    "BM" FLOAT, 
    "BM_Ausn" FLOAT, 
    "GRZmin" FLOAT, 
    "GRZmax" FLOAT, 
    "GRZ" FLOAT, 
    "GRZ_Ausn" FLOAT, 
    "GRmin" FLOAT, 
    "GRmax" FLOAT, 
    "GR" FLOAT, 
    "GR_Ausn" FLOAT, 
    "Zmin" INTEGER, 
    "Zmax" INTEGER, 
    "Zzwingend" INTEGER, 
    "Z" INTEGER, 
    "Z_Ausn" INTEGER, 
    "Z_Staffel" INTEGER, 
    "Z_Dach" INTEGER, 
    "ZUmin" INTEGER, 
    "ZUmax" INTEGER, 
    "ZUzwingend" INTEGER, 
    "ZU" INTEGER, 
    "ZU_Ausn" INTEGER, 
    "wohnnutzungEGStrasse" bp_zulaessigkeit, 
    "ZWohn" INTEGER, 
    "GFAntWohnen" FLOAT, 
    "GFWohnen" FLOAT, 
    "GFAntGewerbe" FLOAT, 
    "GFGewerbe" FLOAT, 
    "VF" FLOAT, 
    typ bp_typwohngebaeudeflaeche NOT NULL, 
    "abweichungBauNVO" xp_abweichungbaunvotypen, 
    bauweise bp_bauweise, 
    "vertikaleDifferenzierung" BOOLEAN, 
    "bebauungsArt" bp_bebauungsart, 
    "bebauungVordereGrenze" bp_grenzbebauung, 
    "bebauungRueckwaertigeGrenze" bp_grenzbebauung, 
    "bebauungSeitlicheGrenze" bp_grenzbebauung, 
    "zugunstenVon" VARCHAR, 
    CONSTRAINT pk_bp_wohngebaeude_flaeche PRIMARY KEY (id), 
    CONSTRAINT fk_bp_wohngebaeude_flaeche_id_bp_objekt FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

CREATE TABLE xp_text_abschnitt (
    id UUID NOT NULL, 
    type VARCHAR, 
    schluessel VARCHAR, 
    "gesetzlicheGrundlage" VARCHAR, 
    text VARCHAR, 
    rechtscharakter xp_rechtscharakter NOT NULL, 
    xp_bereich_id UUID, 
    xp_objekt_id UUID, 
    xp_plan_id UUID, 
    bp_objekt_id UUID, 
    fp_objekt_id UUID, 
    bp_baugebiet_id UUID, 
    bp_nebenanlagen_ausschluss_flaeche_id UUID, 
    bp_wohngebaeude_flaeche_id UUID, 
    CONSTRAINT pk_xp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_xp_text_abschnitt_bp_baugebiet_id_bp_baugebiet FOREIGN KEY(bp_baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_bp_nebenanlagen_ausschluss_flaeche_c966 FOREIGN KEY(bp_nebenanlagen_ausschluss_flaeche_id) REFERENCES bp_nebenanlagen_ausschluss_flaeche (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_bp_objekt_id_bp_objekt FOREIGN KEY(bp_objekt_id) REFERENCES bp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_bp_wohngebaeude_flaeche_id_bp_wohn_af37 FOREIGN KEY(bp_wohngebaeude_flaeche_id) REFERENCES bp_wohngebaeude_flaeche (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_fp_objekt_id_fp_objekt FOREIGN KEY(fp_objekt_id) REFERENCES fp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_xp_bereich_id_xp_bereich FOREIGN KEY(xp_bereich_id) REFERENCES xp_bereich (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_xp_objekt_id_xp_objekt FOREIGN KEY(xp_objekt_id) REFERENCES xp_objekt (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_text_abschnitt_xp_plan_id_xp_plan FOREIGN KEY(xp_plan_id) REFERENCES xp_plan (id) ON DELETE CASCADE
);

CREATE TABLE bp_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter bp_rechtscharakter NOT NULL, 
    bp_baugebiet_id UUID, 
    bp_nebenanlagen_ausschluss_flaeche_id UUID, 
    CONSTRAINT pk_bp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_bp_text_abschnitt_bp_baugebiet_id_bp_baugebiet FOREIGN KEY(bp_baugebiet_id) REFERENCES bp_baugebiet (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_text_abschnitt_bp_nebenanlagen_ausschluss_flaeche_9bda FOREIGN KEY(bp_nebenanlagen_ausschluss_flaeche_id) REFERENCES bp_nebenanlagen_ausschluss_flaeche (id) ON DELETE CASCADE, 
    CONSTRAINT fk_bp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

CREATE TABLE fp_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter fp_rechtscharakter NOT NULL, 
    CONSTRAINT pk_fp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_fp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

CREATE TYPE lp_rechtscharakter AS ENUM ('Festsetzung', 'Geplant', 'NachrichtlicheUebernahme', 'DarstellungKennzeichnung', 'FestsetzungInBPlan', 'Unbekannt', 'SonstigerStatus');

CREATE TABLE lp_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter lp_rechtscharakter NOT NULL, 
    CONSTRAINT pk_lp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_lp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

CREATE TYPE rp_rechtscharakter AS ENUM ('ZielDerRaumordnung', 'GrundsatzDerRaumordnung', 'NachrichtlicheUebernahme', 'NachrichtlicheUebernahmeZiel', 'NachrichtlicheUebernahmeGrundsatz', 'NurInformationsgehalt', 'TextlichesZiel', 'ZielundGrundsatz', 'Vorschlag', 'Unbekannt');

CREATE TABLE rp_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter rp_rechtscharakter NOT NULL, 
    CONSTRAINT pk_rp_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_rp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

CREATE TABLE so_text_abschnitt (
    id UUID NOT NULL, 
    rechtscharakter so_rechtscharakter NOT NULL, 
    CONSTRAINT pk_so_text_abschnitt PRIMARY KEY (id), 
    CONSTRAINT fk_so_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE
);

ALTER TABLE bp_dachgestaltung ADD COLUMN bp_wohngebaeude_flaeche_id UUID;

ALTER TABLE bp_dachgestaltung ADD CONSTRAINT fk_bp_dachgestaltung_bp_wohngebaeude_flaeche_id_bp_wohn_7fa5 FOREIGN KEY(bp_wohngebaeude_flaeche_id) REFERENCES bp_wohngebaeude_flaeche (id) ON DELETE CASCADE;

ALTER TABLE lp_ziele_erfordernisse_massnahmen RENAME "artDerFestlegung" TO "zieleErfordernisseMassnahmen";

ALTER TABLE xp_externe_referenz ADD COLUMN xp_text_abschnitt_id UUID;

ALTER TABLE xp_externe_referenz ADD COLUMN bp_wohngebaeude_flaeche_id UUID;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_bp_wohngebaeude_flaeche_id_bp_wo_3bdf FOREIGN KEY(bp_wohngebaeude_flaeche_id) REFERENCES bp_wohngebaeude_flaeche (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD CONSTRAINT fk_xp_externe_referenz_xp_text_abschnitt_id_xp_text_abschnitt FOREIGN KEY(xp_text_abschnitt_id) REFERENCES xp_text_abschnitt (id) ON DELETE CASCADE;

ALTER TABLE xp_nutzungsschablone DROP COLUMN hidden;

CREATE TABLE xp_plan_gesetzlichegrundlage (
    bp_plan_id UUID, 
    fp_plan_id UUID, 
    gesetzlichegrundlage_id UUID NOT NULL, 
    CONSTRAINT fk_xp_plan_gesetzlichegrundlage_bp_plan_id_bp_plan FOREIGN KEY(bp_plan_id) REFERENCES bp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_plan_gesetzlichegrundlage_fp_plan_id_fp_plan FOREIGN KEY(fp_plan_id) REFERENCES fp_plan (id) ON DELETE CASCADE, 
    CONSTRAINT fk_xp_plan_gesetzlichegrundlage_gesetzlichegrundlage_id_eafa FOREIGN KEY(gesetzlichegrundlage_id) REFERENCES xp_gesetzliche_grundlage (id)
);

INSERT INTO xp_plan_gesetzlichegrundlage (bp_plan_id, gesetzlichegrundlage_id)
        SELECT id, "versionSonstRechtsgrundlage_id"
        FROM bp_plan
        WHERE "versionSonstRechtsgrundlage_id" IS NOT NULL;;

INSERT INTO xp_plan_gesetzlichegrundlage (fp_plan_id, gesetzlichegrundlage_id)
        SELECT id, "versionSonstRechtsgrundlage_id"
        FROM fp_plan
        WHERE "versionSonstRechtsgrundlage_id" IS NOT NULL;;

ALTER TABLE bp_plan DROP COLUMN "versionSonstRechtsgrundlage_id";

ALTER TABLE fp_plan DROP COLUMN "versionSonstRechtsgrundlage_id";

ALTER TYPE xp_abemassnahmentypen ADD VALUE IF NOT EXISTS 'AnpflanzungBindungErhaltung';;

UPDATE alembic_version SET version_num='da3841c7f8d9' WHERE alembic_version.version_num = '31058f6befbd'; --- # pragma: allowlist secret;

COMMIT;

