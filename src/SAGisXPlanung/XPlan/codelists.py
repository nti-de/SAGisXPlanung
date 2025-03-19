import logging
import re
from typing import Type
from uuid import uuid4

from lxml import etree
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base, XPlanVersion

logger = logging.getLogger(__name__)


def is_codelist_attribute(xtype: type, attribute: str) -> bool:
    if not hasattr(a := getattr(xtype, attribute), 'property'):
        return False
    return issubclass(a.property.mapper.class_, CodeListValue)


class CodeListLegacy:
    """ XP_Basisobjekte::CodeList """

    XP_MIME_TYPES = [
        "application/pdf",
        "application/zip",
        "application/xml",
        "application/msword",
        "application/msexcel",
        "application/vnd.ogc.sld+xml",
        "application/vnd.ogc.wms_xml",
        "application/vnd.ogc.gml",
        "application/vnd.shp",
        "application/vnd.dbf",
        "application/vnd.shx",
        "application/octet-stream",
        "image/vnd.dxf",
        "image/vnd.dwg",
        "image/jpg",
        "image/png",
        "image/tiff",
        "image/bmp",
        "image/ecw",
        "image/svg+xml",
        "text/html",
        "text/plain"
    ]

    XP_GesetzlicheGrundlage = [
        ""
    ]


class CodeList(Base):
    __tablename__ = "codelist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    name = Column(String)
    uri = Column(String)
    description = Column(String)

    values = relationship("CodeListValue", back_populates="codelist")


class CodeListValue(Base):
    __tablename__ = "codelist_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    key = Column(String)
    value = Column(String)
    uri = Column(String)
    definition = Column(String)

    type = Column(String)

    codelist_id = Column(UUID(as_uuid=True), ForeignKey('codelist.id', ondelete='CASCADE'))
    codelist = relationship("CodeList", back_populates="values")

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "codelist",
    }

    def to_xplan_node(self, node=None, version=XPlanVersion.FIVE_THREE):
        node.attrib["codeSpace"] = self.codelist.uri
        node.text = self.value
        return node

    @classmethod
    def from_xplan_node(cls, node):
        new = cls()
        # regex pattern trying to match codelist keys
        # 1. ^(?:[A-Z]+_)? → Optional prefix with uppercase letters (SON_, etc.).
        # 2. \d+ → Starts with a number
        # 3. (?:_\d+)* → Can be followed by multiple _number segments
        key_pattern = re.compile(r"^(?:[A-Z]+_)?\d+(?:_\d+)*$")

        if key_pattern.match(node.text):
            new.key = node.text
        else:
            new.value = node.text
        return new

    @classmethod
    def codelist_class(cls, xtype: type, attribute: str) -> Type['CodeListValue']:
        if not is_codelist_attribute(xtype, attribute):
            raise Exception(f'{attribute} is no codelist attribute on class {xtype.__name__}')
        return getattr(xtype, attribute).property.mapper.class_

    def __str__(self):
        return f'{self.key}-{self.value}'

    def __eq__(self, other):
        if type(other) is type(self) or issubclass(type(other), type(self)) or issubclass(type(self), type(other)):
            return self.value == other.value or self.key == other.key
        return False


class CodeListParser:

    @classmethod
    def from_iso_19135_xml(cls, xml: str):
        tree = etree.fromstring(xml)

        codelist = CodeList()
        codelist.description = tree.findtext('.//contentSummary/gco:CharacterString', namespaces=tree.nsmap)
        codelist.uri = tree.findtext('.//gmd:URL', namespaces=tree.nsmap)
        codelist.name = codelist.uri.rsplit('/', 1)[1]

        for item_node in tree.findall('.//containedItem', namespaces=tree.nsmap):
            if len(item_node) == 0:
                continue
            codelist_value = CodeListValue()
            codelist_value.value = item_node.findtext('.//name/gco:CharacterString', namespaces=tree.nsmap)
            codelist_value.definition = item_node.findtext('.//definition/gco:CharacterString', namespaces=tree.nsmap)
            codelist_value.uri = item_node.attrib[f"{{{tree.nsmap['xlink']}}}href"]
            codelist_value.key = codelist_value.uri.rsplit('/', 1)[1]
            codelist_value.type = codelist.name

            codelist.values.append(codelist_value)

        return codelist
