import logging
import itertools
from enum import Enum
from io import BytesIO
from pathlib import PurePath
from uuid import uuid4
from zipfile import ZipFile

from lxml import etree
from geoalchemy2 import WKBElement, WKTElement
from osgeo import ogr, osr

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.GML.geometry import enforce_wkb_constraints
from SAGisXPlanung.XPlan.XP_Praesentationsobjekte.feature_types import XP_AbstraktesPraesentationsobjekt, \
    XP_Nutzungsschablone
from SAGisXPlanung.XPlan.data_types import XP_ExterneReferenz
from SAGisXPlanung.XPlan.feature_types import XP_Plan, XP_Bereich
from SAGisXPlanung.XPlan.mixins import FlaechenschlussObjekt, UeberlagerungsObjekt
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

        self.plan_name = plan.name

        self.root.append(self.writeEnvelope(plan.raeumlicherGeltungsbereich))
        self.root.append(self.writePlan(plan))
        for b in plan.bereich:
            self.root.append(self.writeXPBereich(b))

    def toGML(self) -> bytes:
        xml = etree.tostring(self.root, pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone=True)
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

    def writePlan(self, plan):
        """
        Erstellt einen XML-Knoten der entsprechenden Planart.

        Parameters
        ----------
        plan: XP_Plan
            XP_Plan Objekt
        Returns
        -------
        lxml.etree.Element
            <xplan:XP_Plan>-Knoten des XP_Plan Objekts

        """
        feature = etree.Element(f"{{{self.nsmap['gml']}}}featureMember", nsmap=self.nsmap)
        xplan = etree.SubElement(feature, f"{{{self.nsmap['xplan']}}}{plan.__class__.__name__}",
                                 {f"{{{self.nsmap['gml']}}}id": f"GML_{plan.id}"})
        xplan.append(self.writeEnvelope(plan.raeumlicherGeltungsbereich))

        elements = plan.__class__.element_order(version=self.version)
        rels = plan.relationships()
        for attr in elements:
            value = getattr(plan, attr)
            if value is None:
                continue
            if isinstance(value, list) and not value:
                continue
            if isinstance(value, Enum) and hasattr(value, 'version'):
                if value.version not in [None, self.version]:
                    continue
            f = etree.Element(f"{{{self.nsmap['xplan']}}}{attr}")
            if attr == "raeumlicherGeltungsbereich":
                f.append(self.writeGeometry(value))
            elif attr == "bereich":
                f.attrib[f"{{{self.nsmap['xlink']}}}href"] = f"#GML_{value[0].id}"
                for bereich in value[1:]:
                    etree.SubElement(xplan, f"{{{self.nsmap['xplan']}}}{attr}",
                                     {f"{{{self.nsmap['xlink']}}}href": f"#GML_{bereich.id}"})
            elif attr == "plangeber" or attr == "rel_veraenderungssperre":
                rel = getattr(plan.__class__, attr).property
                attr, _ = plan.__class__.relation_prop_display((attr, rel))
                f.tag = f"{{{self.nsmap['xplan']}}}{attr.lower()}"
                f.append(self.writeSubObject(value))
            elif isinstance(value, list) and value:  # TODO: `and value` can never be reached?; also move to further up and make full loop
                f.text = writeTextNode(value[0])
                for e in value[1:]:
                    if isinstance(e, Enum) and hasattr(e, 'version'):
                        if e.version not in [None, self.version]:
                            continue
                    el = etree.SubElement(xplan, f"{{{self.nsmap['xplan']}}}{attr}")
                    el.text = writeTextNode(e)
            else:
                f.text = writeTextNode(value)

            xplan.append(f)

        return feature

    def writeGeometry(self, geom):
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

    def writeSubObject(self, obj):
        """
        Erstellt einen XPlanGML-Knoten aus einem simplen XPlan-Basisobjekt, das über keine weiteren Relationen verfügt

        Parameters
        ----------
        obj:
            XPlan-Basisobjekt

        Returns
        -------
        lxml.etree.Element
            Zum Objekt korrespondierender XPlanGML-Knoten

        Examples
        --------
        >>> gemeinde = XP_Gemeinde()
        >>> gemeinde.ags = "37815"
        >>> gemeinde.gemeindeName = "Berlin"
        >>> node = self.writeSubObject(gemeinde)
        >>> etree.tostring(node)
        <xplan:XP_Gemeinde>
          <xplan:ags>37815</xplan:ags>
          <xplan:gemeindeName>Berlin</xplan:gemeindeName>
        </xplan:XP_Gemeinde>

        """
        o = etree.Element(f"{{{self.nsmap['xplan']}}}{obj.__class__.__name__}", nsmap=self.nsmap)

        if isinstance(obj, XP_ExterneReferenz):
            file = getattr(obj, 'file')
            if file is not None:
                self.files[obj.referenzURL] = (getattr(obj, 'file'))

        self.write_attributes(o, obj, version=self.version)

        return o

    def writeXPBereich(self, bereich):
        """
        Erstellt einen XPlanGML-Knoten aus einem XP_Bereich-Objekt. Für ein valides XPlanGML muss das Feld
        gehoertZuPlan_id belegt sein, um die Referenz zu eine XP_Plan-Objekt herzustellen.

        Parameters
        ----------
        bereich: XP_Bereich
            XP_Bereich-Objekt eines Plans

        Returns
        -------
        lxml.etree.Element
            XPlanGML-Knoten des Bereichs
        """
        feature = etree.Element(f"{{{self.nsmap['gml']}}}featureMember", nsmap=self.nsmap)
        xp_bereich = etree.SubElement(feature, f"{{{self.nsmap['xplan']}}}{bereich.__class__.__name__}",
                                      {f"{{{self.nsmap['gml']}}}id": f"GML_{bereich.id}"})
        if bereich.geltungsbereich:
            xp_bereich.append(self.writeEnvelope(bereich.geltungsbereich))

        for attr in bereich.__class__.element_order(version=self.version):
            if attr in ['praesentationsobjekt', 'simple_geometry', 'planinhalt']:
                continue
            value = getattr(bereich, attr)
            if attr == "gehoertZuPlan_id":
                etree.SubElement(xp_bereich, f"{{{self.nsmap['xplan']}}}gehoertZuPlan",
                                 {f"{{{self.nsmap['xlink']}}}href": f"#GML_{value}"})
                continue
            if value is None or isinstance(value, XP_Plan):
                continue
            if attr == "refScan":
                for r in bereich.refScan:
                    f = etree.SubElement(xp_bereich, f"{{{self.nsmap['xplan']}}}{attr}")
                    f.append(self.writeSubObject(r))
                continue
            if isinstance(value, Enum) and hasattr(value, 'version'):
                if value.version not in [None, self.version]:
                    continue
            f = etree.SubElement(xp_bereich, f"{{{self.nsmap['xplan']}}}{attr}")
            if attr == "geltungsbereich":
                f.append(self.writeGeometry(value))
            else:
                f.text = writeTextNode(value)

        return feature

    def writePO(self, obj: XP_AbstraktesPraesentationsobjekt):
        """
        Erstellt einen XPlanGML-Knoten aus einer XP_AbstraktesPraesentationsobjekt - Instanz.
        Fügt zum Root-Knoten hinzu!

        Parameters
        ----------
        obj: XP_AbstraktesPraesentationsobjekt
            Instanz einer von XP_AbstraktesPraesentationsobjekt erbenden Klasse
        """
        if isinstance(obj, XP_Nutzungsschablone) and obj.hidden:
            return

        feature = etree.Element(f"{{{self.nsmap['gml']}}}featureMember", nsmap=self.nsmap)
        xp_po = etree.SubElement(feature, f"{{{self.nsmap['xplan']}}}{obj.__class__.__name__}",
                                 {f"{{{self.nsmap['gml']}}}id": f"GML_{obj.id}"})
        xp_po.append(self.writeEnvelope(obj.position))

        for attr in obj.__class__.element_order(version=self.version):
            value = getattr(obj, attr)
            if value is None:
                continue
            if isinstance(value, Enum) and hasattr(value, 'version'):
                if value.version not in [None, self.version]:
                    continue
            if attr.endswith('_id'):
                etree.SubElement(xp_po, f"{{{self.nsmap['xplan']}}}{attr[:-3]}",
                                 {f"{{{self.nsmap['xlink']}}}href": f"#GML_{value}"})
                continue

            f = etree.SubElement(xp_po, f"{{{self.nsmap['xplan']}}}{attr}")
            if isinstance(value, WKBElement):
                f.append(self.writeGeometry(value))
            else:
                f.text = writeTextNode(value)
                self.writeUOM(f, attr, obj)

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
    def write_attributes(node, xplan_object, version: XPlanVersion):
        rels = xplan_object.relationships()
        for attr in xplan_object.__class__.element_order(version=version):
            # don't process any relations at this point (this method only writes direct attributes)
            if any(attr in rel for rel in rels):
                continue
            value = getattr(xplan_object, attr)
            if value is None:
                continue
            if isinstance(value, Enum) and hasattr(value, 'version'):
                if value.version not in [None, version]:
                    continue
            field = etree.SubElement(node, f"{{{node.nsmap['xplan']}}}{attr}")
            field.text = writeTextNode(value)
            GMLWriter.writeUOM(field, attr, xplan_object)


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