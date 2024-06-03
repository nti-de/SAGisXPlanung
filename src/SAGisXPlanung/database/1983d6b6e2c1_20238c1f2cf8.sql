BEGIN;

-- Running upgrade 1983d6b6e2c1 -> 20238c1f2cf8

CREATE OR REPLACE FUNCTION immutable_date_to_char(date) RETURNS text AS
        $$ select extract(year from $1)::text || '-' ||
                    lpad(extract(week from $1)::text, 2, '0') || '-' ||
                    lpad(extract(day from $1)::text, 2, '0'); $$
        LANGUAGE sql immutable;;

ALTER TABLE xp_plan
        ADD COLUMN _sa_search_col tsvector
        GENERATED ALWAYS AS (to_tsvector('german',
            xp_plan.id::text || ' ' ||
            xp_plan.name || ' ' ||
            coalesce(xp_plan.type, '') || ' ' ||
            coalesce(xp_plan.nummer, '') || ' ' ||
            coalesce(xp_plan."internalId", '') || ' ' ||
            coalesce(xp_plan.beschreibung, '') || ' ' ||
            coalesce(xp_plan.kommentar, '') || ' ' ||
            coalesce(immutable_date_to_char(xp_plan."technHerstellDatum"), '') || ' ' ||
            coalesce(immutable_date_to_char(xp_plan."genehmigungsDatum"), '') || ' ' ||
            coalesce(immutable_date_to_char(xp_plan."untergangsDatum"), '') || ' ' ||
            coalesce(xp_plan."erstellungsMassstab"::text, '') || ' ' ||
            coalesce(xp_plan.bezugshoehe::text, '') || ' ' ||
            coalesce(xp_plan."technischerPlanersteller", '')
        )) STORED;;

CREATE INDEX textsearch_idx ON xp_plan USING GIN (_sa_search_col);;

CREATE TABLE bp_grundstueck_ueberbaubar (
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
    "GFAntWohnen" INTEGER, 
    "GFWohnen" FLOAT, 
    "GFAntGewerbe" INTEGER, 
    "GFGewerbe" FLOAT, 
    "VF" FLOAT, 
    bauweise bp_bauweise, 
    "vertikaleDifferenzierung" BOOLEAN, 
    "bebauungsArt" bp_bebauungsart, 
    "bebauungVordereGrenze" bp_grenzbebauung, 
    "bebauungRueckwaertigeGrenze" bp_grenzbebauung, 
    "bebauungSeitlicheGrenze" bp_grenzbebauung, 
    "geschossMin" INTEGER, 
    "geschossMax" INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE bp_dachgestaltung ADD COLUMN grundstueck_ueberbaubar_id UUID;

ALTER TABLE bp_dachgestaltung ADD FOREIGN KEY(grundstueck_ueberbaubar_id) REFERENCES bp_grundstueck_ueberbaubar (id) ON DELETE CASCADE;

ALTER TABLE xp_externe_referenz ADD COLUMN grundstueck_ueberbaubar_id UUID;

ALTER TABLE xp_externe_referenz ADD FOREIGN KEY(grundstueck_ueberbaubar_id) REFERENCES bp_grundstueck_ueberbaubar (id) ON DELETE CASCADE;

UPDATE alembic_version SET version_num='20238c1f2cf8' WHERE alembic_version.version_num = '1983d6b6e2c1';

COMMIT;

