import re
import importlib
from importlib.metadata import version

from qgis.core import Qgis
from qgis.PyQt.QtWidgets import QMessageBox, QLabel
from qgis.utils import iface


def check(required_packages):
    """ Checks if required packages are correctly installed. """
    missing_packages = []
    with_packaging = True
    for package in required_packages:
        try:
            # fallback to use std importlib, when packaging is not installed
            if not with_packaging:
                package_name = re.split(r'[<>=~]', package)[0].strip()
                importlib.import_module(package_name.lower())
            else:
                from packaging.requirements import Requirement
                from packaging.version import Version

                requirement = Requirement(package)
                installed_version = Version(version(requirement.name))
                if requirement.specifier:
                    if installed_version not in requirement.specifier:
                        missing_packages.append(package)
        except ImportError:
            if 'packaging' in package:
                with_packaging = False
            missing_packages.append(package)

    if not missing_packages:
        return True

    message = "Die folgenden Softwarekomponenten werden zur Ausführung von SAGis XPlanung benötigt:\n\n"
    message += "\n".join(missing_packages)
    message += "\n\nSollen die fehlenden Komponenten installliert werden?"

    dialog = QMessageBox(QMessageBox.Question, 'Fehlende Abhängigkeiten', message, QMessageBox.Yes | QMessageBox.No)
    reply = dialog.exec()

    if reply == QMessageBox.No:
        return False

    error = False
    log = []
    for package in missing_packages:
        try:
            import subprocess
            ret = subprocess.call(['python3', '-m', 'pip', 'install', package])
            if ret == 0:
                log.append(f'{package} ... installiert')
            else:
                raise Exception('Konnte nicht installiert werden.')
        except:
            error = True
            log.append(f'{package} ... Fehler bei Installation')

    if error:
        iface.messageBar().pushMessage("XPlanung",
                                       f'Fehler beim Installieren der Python-Pakete', '\n'.join(log),
                                       level=Qgis.Critical)
    else:
        iface.messageBar().pushMessage("XPlanung",
                                       f'Python-Pakete erfolgreich installiert', '\n'.join(log),
                                       level=Qgis.Success)
        return True
