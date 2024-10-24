import datetime
import logging
import inspect

from geoalchemy2 import Geometry, WKTElement
from lxml import etree
from osgeo import ogr
from sqlalchemy import ARRAY

from SAGisXPlanung import Base, XPlanVersion
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_Nutzungsschablone
from SAGisXPlanung.XPlan.types import RefURL
from SAGisXPlanung.utils import CLASSES, query_existing, PRE_FILLED_CLASSES, OBJECT_BASE_TYPES

logger = logging.getLogger(__name__)


class GMLReader:
    """
    Ein GMLReader-Objekt konvertiert ein ein valides XPlanGML-Dokument der Version 5.3 in ein XP_Plan-Objekt
    Der XP_Plan-Objekt kann über das Attribut 'plan' abgerufen werden.
    """

    def __init__(self, gml, files=None, progress_callback=None):

        from timeit import default_timer as timer

        self.warnings = []
        self.files = files if files else {}

        parser = etree.XMLParser(remove_blank_text=True)
        self.root = etree.fromstring(gml, parser=parser)

        self.nsmap = self.root.nsmap
        # remove the None entry (top level namespace) if it exists - xpath does not allow it in the namespace map
        self.nsmap.pop(None, None)
        self.import_version = XPlanVersion.from_namespace(self.nsmap['xplan'])

        self.object_count = int(self.root.xpath("count(//gml:featureMember)", namespaces=self.nsmap))
        self.progress_callback = progress_callback
        self.current_progress = 0
        self.setProgress(0)

        plan_element = self.root.xpath(".//xplan:*[contains(name(),'_Plan')][1]", namespaces=self.nsmap)[0]
        type_name = etree.QName(plan_element).localname
        self.type = CLASSES[type_name]
        self.plan = self.read_xp_object(plan_element)

    def setProgress(self, progress):
        if not self.progress_callback:
            return
        self.progress_callback((self.current_progress, self.object_count))
        self.current_progress = progress

    @staticmethod
    def readGeometry(gml_node) -> WKTElement:
        """
        Liest eine beliebige Geometrie aus einem GML-Knoten aus.
        ----------
        gml: lxml.etree.Element
            GML-Knoten vom Typ gml:GeometryPropertyType

        Returns
        -------
        geoalchemy2.elements.WKTElement
            WKT der eingelesenen Geometrie
        """
        try:
            srs_name = gml_node.attrib['srsName']
        except KeyError as e:
            ns = gml_node.nsmap
            ns.pop(None, None) # remove invalid empty namespace
            srs_name_list = gml_node.xpath('//*[@srsName]/@srsName[1]', namespaces=ns)
            if not srs_name_list:
                raise Exception([e, Exception(f"Attribut 'srsName' in Zeile {gml_node.sourceline} erwartet")])
            srs_name = srs_name_list[0]

        srid = int(srs_name.partition(':')[-1])

        gml_string = etree.tostring(gml_node).decode()
        geom = ogr.CreateGeometryFromGML(gml_string)

        return WKTElement(geom.ExportToWkt(), srid=srid)

    def read_xp_object(self, gml):
        """
        Erstellt aus einem XPlanGML-Knoten eine XP_Objekt-Instanz.

        Parameters
        ----------
        gml: lxml.etree.Element
            XPlanGML-Knoten einer von XP_Objekt abgeleiteten Klasse (alle vektoriellen Planinhalte)
        """
        type_name = etree.QName(gml).localname
        if type_name not in CLASSES.keys():
            return
        object_type = CLASSES[type_name]
        if object_type in OBJECT_BASE_TYPES:
            self.warnings.append(f'Basisklasse vom Typ {object_type.__name__} ignoriert... Bitte ein spezifisches '
                                 f'Fachobjekt oder generisches Objekt verwenden (Zeile: {gml.sourceline})')
            return

        obj = object_type()
        obj_id = gml.xpath('@gml:id', namespaces=self.nsmap)[0]
        obj.id = obj_id[obj_id.find('_') + 1:]

        for node in gml.iterchildren():
            node_name = etree.QName(node).localname
            if not hasattr(obj, node_name):
                continue
            if node_name in ['gehoertZuBereich', 'praesentationsobjekt', 'dientZurDarstellungVon', 'boundedBy',
                             'gehoertZuPlan']:
                continue

            col = getattr(object_type, node_name)

            if hasattr(col, 'import_attr') and col.import_attr is not None:
                node_name = col.import_attr(self.import_version)

            if node_name in [r[0] for r in obj.relationships()]:
                # find node content if relationship is not immediately child but instead linked via xlink
                if len(node) == 0:
                    xlink_refs = node.xpath('@xlink:href', namespaces=self.nsmap)
                    if not xlink_refs:
                        continue
                    linked_node_id = str(xlink_refs[0]).lstrip('#')
                    linked_node = self.root.xpath(f"(//*[@gml:id='{linked_node_id}'])[1]", namespaces=self.nsmap)
                    if not linked_node:
                        self.warnings.append(f'xlink verweist auf ein Objekt, das nicht in der XPlanGML-Datei'
                                             f' vorliegt. (ID: {linked_node_id}, Zeile: {node.sourceline})')
                        continue

                    node.append(linked_node[0])
                    value = self.read_xp_object(linked_node[0])

                    if isinstance(value, XP_Nutzungsschablone):
                        value.hidden = False
                        if value.zeilenAnz is not None:
                            value.set_defaults(int(value.zeilenAnz))
                        getattr(obj, node_name).append(value)
                        continue
                else:
                    value = self.read_data_object(node[0], files=self.files)

                # skip if no value is read, e.g. when reading a class that is not present in schema
                if value is None:
                    continue

                pre_classes = [*PRE_FILLED_CLASSES]
                if value.__class__ in pre_classes:
                    obj_from_db = query_existing(value)
                    value = obj_from_db if obj_from_db is not None else value
                    if obj_from_db is not None and hasattr(obj, f'{node_name}_id'):
                        # object could already be in session from previous loops, therefore store only id if possible
                        node_name = f'{node_name}_id'
                        value = obj_from_db.id
                if (a := getattr(obj, node_name)) is not None:
                    a.append(value)
                else:
                    setattr(obj, node_name, value)

                gml.remove(node)
                del node
                continue

            # edge case where same named column exists in base class which should be used
            if not obj.__class__.attr_fits_version(node_name, self.import_version):
                base_classes = [c for c in list(inspect.getmro(obj.__class__)) if issubclass(c, Base)]
                cls = next(c for c in reversed(base_classes) if hasattr(c, node_name))
                col_type = getattr(cls, node_name).property.columns[0].type
            else:
                col_type = getattr(obj.__class__, node_name).property.columns[0].type

            GMLReader.read_attribute(col_type, node_name, obj, node)

        self.setProgress(self.current_progress + 1)
        return obj

    @staticmethod
    def read_attribute(col_type, node_name, obj, node):
        if isinstance(col_type, Geometry):
            value = GMLReader.readGeometry(node[0])
            if value is None:
                return
            setattr(obj, node_name, value)
            return

        value = node.text
        if hasattr(col_type, 'enums'):
            try:
                if col_type.enum_class is not None:
                    value = col_type.enum_class(int(value))
                setattr(obj, node_name, value)
            except ValueError:
                setattr(obj, node_name, col_type.enum_class(value))
        elif col_type.python_type == bool:
            setattr(obj, node_name, str(value).lower() == 'true')
        elif isinstance(col_type, ARRAY) and hasattr(col_type.item_type, 'enums'):
            try:
                value = col_type.item_type.enum_class(int(value))
                getattr(obj, node_name).append(value)
            except Exception as e:
                setattr(obj, node_name, [value])
        elif col_type.python_type == datetime.date:
            setattr(obj, node_name, datetime.datetime.strptime(value, '%Y-%m-%d'))
        elif col_type.python_type == list and col_type.item_type.python_type == datetime.date:
            getattr(obj, node_name).append(datetime.datetime.strptime(value, '%Y-%m-%d'))
        else:
            setattr(obj, node_name, value)

    @staticmethod
    def read_data_object(gml, files=None, only_attributes=False):
        """
        Wandelt ein XPlanGML-Datatype in ein ORM-Objekt des gleichen Typs um.

        Parameters
        ----------
        gml: lxml.etree.Element
            XPlanGML-Knoten eines XPlanGML-Datatype
        files: dict
            Dictionary aus Dateiname und Datei
        only_attributes: bool
            Wenn falsch, kein Aufruf der klasssenspezifischen XPlan-Import Routinen (from_xplan_node)
        Returns
        -------
        any:
            ORM-Objekt vom Typ des XPlanGML-Knoten

        """
        if files is None:
            files = {}

        type_name = etree.QName(gml).localname
        object_type = CLASSES[type_name]

        if not only_attributes and hasattr(object_type, 'from_xplan_node'):
            return object_type.from_xplan_node(gml)

        obj = object_type()
        for node in gml.iterchildren():
            node_name = etree.QName(node).localname
            value = node.text

            if hasattr(obj, node_name):
                try:
                    col_type = getattr(object_type, node_name).property.columns[0].type
                except AttributeError as e:
                    # continue when property is not a column (but a relation instead)
                    # this fail check is a lot faster than doing a lookup whether attr is in relationship properties
                    continue
                GMLReader.read_attribute(col_type, node_name, obj, node)

                if isinstance(col_type, RefURL) and hasattr(obj, 'file') and value in files:
                    setattr(obj, 'file', files[value])

        return obj
