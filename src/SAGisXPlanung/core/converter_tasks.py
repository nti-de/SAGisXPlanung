import asyncio
import logging
from collections import namedtuple
from pathlib import PurePath, Path
from typing import Callable, Tuple
from zipfile import ZipFile

from qgis.PyQt.QtWidgets import QFileDialog, QWidget
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from SAGisXPlanung import Session
from SAGisXPlanung.GML.GMLReader import GMLReader
from SAGisXPlanung.GML.GMLWriter import GMLWriter
from SAGisXPlanung.Settings import Settings
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.config import export_version, QgsConfig

logger = logging.getLogger(__name__)


ImportResult = namedtuple('ImportResult', ['plan_name', 'warnings'])


class ActionCanceledException(Exception):
    pass


async def export_action(parent: QWidget, plan_xid: str, out_file_format: str = 'gml') -> str:
    default_dir = QgsConfig.last_export_directory()

    with Session.begin() as session:
        stmt = select(XP_Plan.name).where(XP_Plan.id == plan_xid)
        plan_name = session.execute(stmt).scalar()

    display_name = plan_name.replace("/", "-").replace('"', '\'')
    export_filename = QFileDialog.getSaveFileName(parent, 'Speicherort auswählen',
                                                  directory=f'{default_dir}{display_name}.{out_file_format}',
                                                  filter=f'*.{out_file_format}')
    if not export_filename[0]:
        raise ActionCanceledException()

    export_path = Path(export_filename[0])
    QgsConfig.set_last_export_directory(f'{export_path.parent}\\')

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, export_plan, out_file_format, export_filename[0], plan_xid)

    return export_filename[0]


def export_plan(out_file_format: str, export_filepath: str, plan_xid: str = None):
    with Session.begin() as session:
        plan = session.get(XP_Plan, plan_xid)
        writer = GMLWriter(plan, version=export_version())

        if out_file_format == "gml":
            gml = writer.toGML()
            with open(export_filepath, 'wb') as f:
                f.write(gml)
        elif out_file_format == "zip":
            archive = writer.toArchive()
            with open(export_filepath, 'wb') as f:
                f.write(archive.getvalue())


def import_plan(filepath: str, progress_callback: Callable[[Tuple[int, int]], None]) -> ImportResult:
    extension = PurePath(filepath).suffix
    files = {}

    # read contents of gml file
    if extension == '.gml':
        with open(filepath, 'rb') as f:
            gml_file_content = f.read()

    # extract gml and references from zip archive
    elif extension == '.zip':
        archive = ZipFile(filepath, mode='r')
        if not archive.namelist():
            raise ValueError('ZIP-Archiv enthält keine Dateien.')
        if not any(PurePath(file_name).suffix == '.gml' for file_name in archive.namelist()):
            raise ValueError('ZIP-Archiv enthält keine XPlanGML Datei.')
        gml_file_index = next(i for i, name in enumerate(archive.namelist()) if PurePath(name).suffix == '.gml')
        gml_file_content = archive.read(archive.namelist()[gml_file_index])

        files = {file: archive.read(file) for i, file in enumerate(archive.namelist()) if i != gml_file_index}
    else:
        raise ValueError('Dateipfad muss mit .gml oder .zip enden.')

    reader = GMLReader(gml_file_content, files=files, progress_callback=progress_callback)
    result = ImportResult(reader.plan.name, reader.warnings)

    save_plan(reader.plan)

    return result


def save_plan(plan):
    with Session.begin() as session:
        session.add(plan)
