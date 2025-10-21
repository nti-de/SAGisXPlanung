import logging
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import PurePath
from uuid import uuid4
from zipfile import ZipFile

from lxml import etree
from geoalchemy2 import WKBElement, WKTElement
from osgeo import ogr, osr
from sqlalchemy.orm import RelationshipProperty

from SAGisXPlanung import XPlanVersion, VERSION
from SAGisXPlanung.GML.geometry import enforce_wkb_constraints
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_AbstraktesPraesentationsobjekt
from SAGisXPlanung.XPlan.data_types import XP_ExterneReferenz
from SAGisXPlanung.XPlan.feature_types import XP_Plan
from SAGisXPlanung.core.mixins.mixins import FlaechenschlussObjekt, UeberlagerungsObjekt, GeometryObject, FeatureType
from SAGisXPlanung.utils import is_url

logger = logging.getLogger(__name__)


class GMLWriter:
    """
    Ein GMLWriter-Objekt konvertiert ein XP_Plan-Objekt in ein valides XPlanGML Dokument der Version 5.3
    Der XPlanGML-Knoten kann über das Attribut 'root' abgerufen werden.
    """

    nsmap = {
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "wfs": "http://www.opengis.net/wfs",
        "xlink": "http://www.w3.org/1999/xlink",
        "gml": "http://www.opengis.net/gml/3.2"
    }

    version_urls = {
        XPlanVersion.FIVE_THREE: "http://www.xplanung.de/xplangml/5/3",
        XPlanVersion.SIX: "http://www.xplanung.de/xplangml/6/0"
    }

    def __init__(self, plan: XP_Plan, version=XPlanVersion.FIVE_THREE, root_tag=None):

        self.files = {}
        self.version = version
        self.nsmap['xplan'] = self.version_urls[version]

        self.root = etree.Element(root_tag if root_tag else f"{{{self.nsmap['xplan']}}}XPlanAuszug",
                                  {f"{{{self.nsmap['gml']}}}id": f"GML_{uuid4()}"}, nsmap=self.nsmap)
        self.root.addprevious(etree.Comment(f" Erzeugt am {datetime.today().strftime('%d.%m.%Y')}, SAGis XPlanung ({VERSION}) "))
        self.root.addprevious(etree.Comment(f" NTI Deutschland GmbH https://www.nti-group.com/de/produkte/sagis-loesungen/sagis-xplanung/ "))

        self.plan_name = plan.name

        self.root.append(self.writeEnvelope(plan.raeumlicherGeltungsbereich))
        self.write_feature(plan)

    def toGML(self) -> bytes:
        xml = etree.tostring(etree.ElementTree(self.root), pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone=True)
        return xml

    def toArchive(self) -> BytesIO:
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, mode='w') as zip_file:
            for elm in self.root.findall(".//xplan:referenzURL", namespaces=self.root.nsmap):
                if not is_url(elm.text):
                    if elm.text not in self.files:
                        raise ValueError(f'Datei {elm.text} konnte nicht gefunden werden')

                    from qgis.PyQt.QtCore import QSettings
                    qs = QSettings()
                    path_prefix = qs.value(f"plugins/xplanung/export_path", '')
                    file = self.files[elm.text]
                    elm.text = f'{path_prefix}{PurePath(elm.text).name}'
                    zip_file.writestr(elm.text, file)

            file_name = self.plan_name.replace("/", "-").replace('"', '\'')
            zip_file.writestr(f"{file_name}.gml", self.toGML())

        return zip_buffer

    def writeEnvelope(self, geom: WKBElement) -> etree.Element:
        """
        Erstellt einen boundedBy GML-Knoten aus einer beliebigen Geometrie

        Parameters
        ----------
        geom: geoalchemy2.elements.WKBElement
            WKB einer beliebigen Geometrie

        Returns
        -------
        lxml.etree.Element
            boundedBy-Knoten der Polygon-Geometrie

        """
        srs = f'EPSG:{geom.srid}'

        if isinstance(geom, WKBElement):
            wkb_hex = enforce_wkb_constraints(geom.data.hex())
            ogr_geom = ogr.CreateGeometryFromWkb(bytes.fromhex(wkb_hex))
        elif isinstance(geom, WKTElement):
            ogr_geom = ogr.CreateGeometryFromWkt(geom.data)
        else:
            raise AttributeError('unexpected geometry type')
        bounds = ogr_geom.GetEnvelope()
        boundedBy = etree.Element(f"{{{self.nsmap['gml']}}}boundedBy")
        envelope = etree.SubElement(boundedBy, f"{{{self.nsmap['gml']}}}Envelope", {"srsName": srs})
        etree.SubElement(envelope, f"{{{self.nsmap['gml']}}}lowerCorner").text = str(bounds[0]) + ' ' + str(bounds[2])
        etree.SubElement(envelope, f"{{{self.nsmap['gml']}}}upperCorner").text = str(bounds[1]) + ' ' + str(bounds[3])

        return boundedBy

    def write_feature(self, xplan_object, parent_node=None, only_attributes=False):
        """
        Erstellt einen XPlanGML-Knoten aus einem beliebigen FeatureType.
        Fügt FeautureTypes am Ende der Rootnode des XPlanGML ein, ansonsten als Inline-Objekt der node.
        """
        # if no parent_node is given, the object is a new feature
        if parent_node is None:
            feature = etree.Element(f"{{{self.nsmap['gml']}}}featureMember", nsmap=self.nsmap)
        else:
            feature = parent_node

        xp_objekt = etree.SubElement(feature, f"{{{self.nsmap['xplan']}}}{xplan_object.__class__.__name__}",
                                     nsmap=self.nsmap)
        if not parent_node:
            xp_objekt.attrib[f"{{{self.nsmap['gml']}}}id"] = f"GML_{xplan_object.id}"

        # if feature has a geometry, write envelope
        if isinstance(xplan_object, GeometryObject):
            xp_objekt.append(
                self.writeEnvelope(getattr(xplan_object, xplan_object.__geometry_column_name__))
            )

        # if feature is a reference, load its reference
        if isinstance(xplan_object, XP_ExterneReferenz):
            file = getattr(xplan_object, 'file')
            if file is not None:
                self.files[xplan_object.referenzURL] = (getattr(xplan_object, 'file'))

        for (attr, mapper_property) in xplan_object.__class__.element_order(version=self.version, ret_fmt='sqla'):
            value = getattr(xplan_object, attr)
            if isinstance(mapper_property, RelationshipProperty) and only_attributes is True:
                continue
            if isinstance(mapper_property, RelationshipProperty):
                if not mapper_property.uselist:
                    value = [value] if value is not None else []
                for o in value:
                    # other feature types should appear via xlink
                    if isinstance(o, FeatureType):
                        if hasattr(o, 'xp_versions') and self.version not in o.xp_versions:
                            continue
                        if isinstance(o, XP_AbstraktesPraesentationsobjekt):
                            if o.position is None:
                                continue

                        f = etree.SubElement(xp_objekt, f"{{{self.nsmap['xplan']}}}{attr}")
                        f.attrib[f"{{{self.nsmap['xlink']}}}href"] = f"#GML_{o.id}"
                        if mapper_property.info.get('link') == 'xlink-only':
                            continue

                        self.write_feature(o)
                        continue

                    # export with xplan_name instead of attribute name
                    xplan_name = xplan_object.__class__.xplan_attribute_name(attr)
                    tag = f"{{{self.nsmap['xplan']}}}{xplan_name}"
                    f = etree.SubElement(xp_objekt, tag)

                    if hasattr(o, 'to_xplan_node'):
                        o.to_xplan_node(f, version=self.version)
                    else:
                        self.write_feature(o, parent_node=f)
                continue

            self.write_attribute(xp_objekt, xplan_object, attr, self.version)

        if isinstance(xplan_object, FeatureType):
            self.root.append(feature)

        return feature

    @staticmethod
    def writeUOM(node, attr, obj):
        """ Fügt einem XML-Knoten je nach Datentyp die passende XPlanGML-Einheit als Attribut hinzu"""
        try:
            node.attrib['uom'] = getattr(obj.__class__, attr).property.columns[0].type.UOM
        except:
            pass

    @staticmethod
    def write_geometry(geom):
        """
        Erstellt einen GML-Knoten für eine beliebige Geometrie
        Parameters
        ----------
        geom: geoalchemy2.elements._SpatialElement
            WKT oder WKB einer (Multi)Polygon-Geometrie

        Returns
        -------
        lxml.etree.Element
            GML-Knoten der Geometrie
        """
        if isinstance(geom, WKBElement):
            wkb_hex = enforce_wkb_constraints(geom.data.hex())
            ogr_geom = ogr.CreateGeometryFromWkb(bytes.fromhex(wkb_hex))
        elif isinstance(geom, WKTElement):
            ogr_geom = ogr.CreateGeometryFromWkt(geom.data)
        else:
            raise AttributeError('unexpected geometry type')

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(geom.srid)
        ogr_geom.AssignSpatialReference(srs)

        gml = ogr_geom.ExportToGML(options=["FORMAT=GML32", f"GMLID=GML_{uuid4()}", "GML3_LONGSRS=NO", "NAMESPACE_DECL=YES"])
        return parse_etree(gml)

    @staticmethod
    def write_attribute(node, xplan_object, attr, version: XPlanVersion):
        value = getattr(xplan_object, attr)

        if value is None:
            # enforce writing of attribute `flaechenschluss` even if its value is None
            if attr == 'flaechenschluss':
                if isinstance(xplan_object, FlaechenschlussObjekt):
                    el = etree.SubElement(node, f"{{{node.nsmap['xplan']}}}{attr}")
                    el.text = 'true'
                elif isinstance(xplan_object, UeberlagerungsObjekt):
                    el = etree.SubElement(node, f"{{{node.nsmap['xplan']}}}{attr}")
                    el.text = 'false'
                return
            return
        if isinstance(value, Enum) and value.value is None:
            return
        if isinstance(value, Enum) and hasattr(value, 'version'):
            if value.version not in [None, version]:
                return
        if isinstance(value, list):
            for o in value:
                if isinstance(o, Enum) and hasattr(o, 'version'):
                    if o.version not in [None, version]:
                        continue
                el = etree.SubElement(node, f"{{{node.nsmap['xplan']}}}{attr}")
                el.text = writeTextNode(o)
            return
        f = etree.SubElement(node, f"{{{node.nsmap['xplan']}}}{attr}")
        if isinstance(value, (WKBElement, WKTElement)):
            f.append(GMLWriter.write_geometry(value))
        else:
            f.text = writeTextNode(value)
            GMLWriter.writeUOM(f, attr, xplan_object)

    @staticmethod
    def write_attributes(node, xplan_object, version: XPlanVersion):
        for attr in xplan_object.__class__.element_order(version=version):
            # don't process any relations at this point (this method only writes direct attributes)
            if isinstance(xplan_object, RelationshipProperty):
                continue

            GMLWriter.write_attribute(node, xplan_object, attr, version)


def writeTextNode(value):
    """
    Wandelt einen beliebigen Wert in eine Textrepräsentation um. Nützlich um diese danach als Inhalt
    eines XML-Knotens zu verwenden.

    Parameters
    ----------
    value

    Returns
    -------
    str:
        Textinhalt des eingebenen Werts

    """
    if isinstance(value, Enum):
        return str(value.value)
    if type(value) is bool:
        return str(value).lower()
    return str(value)


def parse_etree(xml_string: str) -> etree.Element:
    parser = etree.XMLParser(recover=True, remove_blank_text=True)
    return etree.fromstring(xml_string, parser)