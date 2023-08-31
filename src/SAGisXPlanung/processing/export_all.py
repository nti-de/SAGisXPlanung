from enum import Enum
from pathlib import Path

from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterFolderDestination, QgsProcessingParameterEnum)

from SAGisXPlanung import Session
from SAGisXPlanung.GML.GMLWriter import GMLWriter
from SAGisXPlanung.utils import CLASSES


class XPlanungExportTypes(Enum):

    XP_Plan = 'Alle Objektklassen'
    BP_Plan = 'Bebauungspläne'
    FP_Plan = 'Flächennutzungspläne'
    RP_Plan = 'Regionalpläne'
    LP_Plan = 'Landschaftspläne'


class ExportAllAlgorithm(QgsProcessingAlgorithm):
    """
    Verarbeitungswerkzeug zum Exportieren aller Pläne in der Datenbank
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT_FOLDER = 'OUTPUT_FOLDER'
    OUTPUT_FORMAT = 'OUTPUT_FORMAT'
    XPLANUNG_TYPES = 'XPLANUNG_TYPES'

    def createInstance(self):
        return ExportAllAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'exportall'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'Bauleitpläne exportieren'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return 'Export'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'sagis-xplanung-export'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return 'Alle in der SAGis XPlanung-Datenbank erfassten Pläne als XPlanGML exportieren'

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                'Ausgabe Ordner',
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.XPLANUNG_TYPES,
                'Objektklassen',
                options=[x.value for x in XPlanungExportTypes],
                defaultValue=XPlanungExportTypes.XP_Plan
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.OUTPUT_FORMAT,
                'Ausgabeformat',
                options=['ZIP-Archiv', 'XPlanGML'],
                defaultValue='ZIP-Archiv'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        feedback.pushInfo('Start process')

        output_path = self.parameterAsFile(parameters, self.OUTPUT_FOLDER, context)
        Path(output_path).mkdir(parents=True, exist_ok=True)

        if not output_path:
            feedback.reportError('Ausgabeordner nicht gefunden', True)
            return {self.OUTPUT_FOLDER: output_path}

        export_format = self.parameterAsInt(parameters, self.OUTPUT_FORMAT, context)

        export_type = self.parameterAsInt(parameters, self.XPLANUNG_TYPES, context)
        feedback.pushInfo(str([x.value for x in XPlanungExportTypes][export_type]))
        export_type_name = [x.name for x in XPlanungExportTypes][export_type]
        export_cls_type = CLASSES[export_type_name]

        feedback.pushDebugInfo(f'XPlanung Typ: {export_cls_type.__name__}')

        with Session.begin() as session:
            all_plans = session.query(export_cls_type).all()
            count = len(all_plans)

            for i, plan in enumerate(all_plans):
                try:
                    writer = GMLWriter(plan)
                    file_name = plan.name.replace("/", "-").replace('"', '\'')
                    if export_format == 0:
                        buffer = writer.toArchive()
                        with open(f'{output_path}/{file_name}.zip', 'wb') as f:
                            f.write(buffer.getvalue())
                    elif export_format == 1:
                        gml = writer.toGML()
                        with open(f'{output_path}/{file_name}.gml', 'wb') as f:
                            f.write(gml)
                except ValueError as e:
                    feedback.pushWarning(f'{plan.name} konnte nicht exportiert werden')
                    feedback.pushWarning(str(e))
                    continue
                finally:
                    prog = self.translateProgress(i, 0, count, 0, 100)
                    feedback.setProgress(prog)

                feedback.pushInfo(f'{plan.name}')

        return {self.OUTPUT_FOLDER: output_path}

    def translateProgress(self, value, left_min, left_max, right_min, right_max):
        # Figure out how 'wide' each range is
        leftSpan = left_max - left_min
        rightSpan = right_max - right_min

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - left_min) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return right_min + (valueScaled * rightSpan)