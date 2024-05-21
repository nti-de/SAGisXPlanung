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

UPDATE alembic_version SET version_num='20238c1f2cf8' WHERE alembic_version.version_num = '1983d6b6e2c1';

COMMIT;

