BEGIN;

-- Running upgrade 151ba21532e3 -> 5b93f2301608

ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'BauHoehe';;

ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'BauMasse';;

ALTER TYPE buildingtemplatecelldatatype ADD VALUE IF NOT EXISTS 'GrundGeschossflaeche';;

UPDATE alembic_version SET version_num='5b93f2301608' WHERE alembic_version.version_num = '151ba21532e3';

COMMIT;

