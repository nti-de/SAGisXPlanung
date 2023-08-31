import logging
from pathlib import PurePath
from typing import Callable, Tuple
from zipfile import ZipFile

from sqlalchemy.orm import joinedload

from SAGisXPlanung import Session
from SAGisXPlanung.GML.GMLReader import GMLReader
from SAGisXPlanung.GML.GMLWriter import GMLWriter
from SAGisXPlanung.Settings import Settings
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.config import export_version

logger = logging.getLogger(__name__)


def export_plan(out_file_format: str, export_filepath: str, plan_name: str):
    with Session.begin() as session:
        plan = session.query(XP_Plan).filter(XP_Plan.name == plan_name).first()
        writer = GMLWriter(plan, version=export_version())

        if out_file_format == "gml":
            gml = writer.toGML()
            with open(export_filepath, 'wb') as f:
                f.write(gml)
        elif out_file_format == "zip":
            archive = writer.toArchive()
            with open(export_filepath, 'wb') as f:
                f.write(archive.getvalue())


def import_plan(filepath: str, progress_callback: Callable[[Tuple[int, int]], None]) -> str:
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

    if reader.exeptions:
        raise Exception('\n\n '.join([str(exc) for exc in reader.exeptions]))

    plan_name = reader.plan.name

    save_plan(reader.plan)

    return plan_name


def save_plan(plan):
    with Session.begin() as session:
        session.add(plan)
