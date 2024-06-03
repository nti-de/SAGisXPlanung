BEGIN;

-- Running upgrade cfbf4d3b2a9d -> 20c50b38b0af

CREATE TABLE bp_flaeche_ohne_festsetzung (
    id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(id) REFERENCES bp_objekt (id) ON DELETE CASCADE
);

ALTER TABLE bp_objekt ALTER COLUMN rechtscharakter SET NOT NULL;

ALTER TABLE xp_bereich DROP COLUMN srs;

ALTER TABLE xp_plan DROP COLUMN srs;

UPDATE alembic_version SET version_num='20c50b38b0af' WHERE alembic_version.version_num = 'cfbf4d3b2a9d';

COMMIT;

