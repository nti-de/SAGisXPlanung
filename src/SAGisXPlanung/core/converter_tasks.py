import asyncio
import logging
from collections import namedtuple
from dataclasses import dataclass
from pathlib import PurePath, Path
from typing import Callable, Tuple, Dict, List
from zipfile import ZipFile

from lxml import etree
from qgis.PyQt.QtWidgets import QFileDialog, QWidget
from sqlalchemy import select

from SAGisXPlanung import Session, XPlanVersion
from SAGisXPlanung.GML.GMLReader import GMLReader
from SAGisXPlanung.GML.GMLWriter import GMLWriter
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.config import export_version, QgsConfig

logger = logging.getLogger(__name__)


ImportResult = namedtuple('ImportResult', ['plan_name', 'warnings'])


@dataclass
class GMLInputData:
    gml_content: bytes
    files: Dict[str, bytes]  # referenced files from ZIP if any
    filepath: str            # original file path


@dataclass
class PrecheckWarning:
    title: str
    message: str


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


def export_plan(out_file_format: str, export_filepath: str = None, plan_xid: str = None, raw=False):
    with Session.begin() as session:
        plan = session.get(XP_Plan, plan_xid)
        writer = GMLWriter(plan, version=export_version())

        if out_file_format == "gml":
            gml = writer.toGML()
            if raw:
                return gml
            with open(export_filepath, 'wb') as f:
                f.write(gml)
        elif out_file_format == "zip":
            archive = writer.toArchive()
            if raw:
                return archive.getvalue()
            with open(export_filepath, 'wb') as f:
                f.write(archive.getvalue())


def import_plan(input_data: GMLInputData, progress_callback: Callable[[Tuple[int, int]], None], overwrite=False) -> ImportResult:
    with Session.begin() as session:
        reader = GMLReader(
            input_data.gml_content,
            files=input_data.files,
            progress_callback=progress_callback,
            session=session
        )
        result = ImportResult(reader.plan.name, reader.warnings)
        if overwrite:
            session.expunge_all()
            session.merge(reader.plan)
        else:
            session.add(reader.plan)

    return result


def prepare_gml_input(filepath: str) -> GMLInputData:
    extension = PurePath(filepath).suffix.lower()
    files = {}

    if extension == '.gml':
        with open(filepath, 'rb') as f:
            gml_content = f.read()
    elif extension == '.zip':
        with ZipFile(filepath, mode='r') as archive:
            gml_name = next((name for name in archive.namelist() if name.endswith('.gml')), None)
            if not gml_name:
                raise ValueError('ZIP-Archiv enthält keine XPlanGML-Datei.')
            gml_content = archive.read(gml_name)
            files = {name: archive.read(name) for name in archive.namelist() if name != gml_name}
    else:
        raise ValueError("Dateiendung muss .gml oder .zip sein.")

    return GMLInputData(gml_content=gml_content, files=files, filepath=filepath)


def run_import_prechecks(input_data: GMLInputData) -> List[PrecheckWarning]:
    warnings = []

    try:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(input_data.gml_content, parser=parser)
        xplan_ns = tree.nsmap.get('xplan')
        if xplan_ns is None and 'xplangml' in tree.nsmap[None]:
            xplan_ns = tree.nsmap[None]
        version = XPlanVersion.from_namespace(xplan_ns)

        if version != export_version():
            warnings.append(PrecheckWarning(
                title="Abweichende XPlanGML Version",
                message=f"Die Datei verwendet XPlan-Version {version}, die Anwendung verwendet Version {export_version()}. "
                        f"Möglicherweise wird der Datensatz nach Import nicht vollständig dargestellt. Zur korrekten "
                        f"Darstellung die XPlan-Version in den Einstellungen anpassen."
            ))

    except Exception as e:
        warnings.append(PrecheckWarning(
            title="Interner Fehler",
            message=f"Fehler beim Interpretieren der Datei: {str(e)}"
        ))

    return warnings
