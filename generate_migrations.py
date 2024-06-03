"""
Utility Script to generate SQL migration files using Alembic.
(Called from update.sh, but can also be run independently)

Description:
This script generates SQL files for each revision step from the base to the head revision.
It creates separate SQL files for each revision and a combined SQL file for the entire migration history.

Usage:
    python generate_sql_migrations.py <version> [output_directory]

    <version>            The version number for the combined SQL file (e.g., '1.0').
    [output_directory]   Optional. The directory where the SQL files will be saved. Defaults to '.revs'.

Example:
    python generate_migrations.py 1.0 ./migrations

Requirements:
- Alembic must be installed
- An Alembic configuration file (alembic.ini) must be present in the same directory as this script

"""
import io
import os
import sys
from contextlib import redirect_stdout

from alembic.command import upgrade
from alembic.script import ScriptDirectory
from alembic.config import Config

if __name__ == "__main__":
    alembic_config_path = 'alembic.ini'
    output_directory = sys.argv[2] if len(sys.argv) >= 3 else '.revs'

    # Load Alembic configuration
    config = Config(alembic_config_path)
    config.set_main_option("script_location", "alembic")
    script = ScriptDirectory.from_config(config)

    head_revision = script.get_current_head()

    # generate revision steps
    for rev in script.walk_revisions('base', 'head'):
        if rev.down_revision is None:
            continue
        with io.StringIO() as buf, redirect_stdout(buf):
            upgrade(config, f'{rev.down_revision}:{rev.revision}', sql=True)

            sql_filename = f"{rev.down_revision}_{rev.revision}.sql"
            sql_filepath = os.path.join(output_directory, sql_filename)

            # Write SQL content to file
            with open(sql_filepath, 'w') as sql_file:
                sql_file.write(buf.getvalue())

    # generate create file
    with io.StringIO() as buf, redirect_stdout(buf):
        upgrade(config, 'base:head', sql=True)

        sql_filename = f"create_v{sys.argv[1]}.sql"
        sql_filepath = os.path.join(output_directory, sql_filename)

        # Write SQL content to file
        with open(sql_filepath, 'w') as sql_file:
            sql_file.write(buf.getvalue())