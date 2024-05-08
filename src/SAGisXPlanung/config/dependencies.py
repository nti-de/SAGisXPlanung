import importlib
import re

from qgis.core import Qgis
from qgis.PyQt.QtWidgets import QMessageBox, QLabel
from qgis.utils import iface


def check(required_packages):
    """ Checks if required packages are correctly installed. """
    missing_packages = []
    for package in required_packages:
        package_name = re.split(r'[<>=~]', package)[0].strip()
        try:
            importlib.import_module(package_name.lower())
        except ImportError:
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
