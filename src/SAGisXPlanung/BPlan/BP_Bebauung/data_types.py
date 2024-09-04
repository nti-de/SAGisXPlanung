from typing import List
from uuid import uuid4

from lxml import etree
from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung import Base, XPlanVersion
from SAGisXPlanung.BPlan.BP_Bebauung.enums import BP_Dachform, BP_ZweckbestimmungNebenanlagen
from SAGisXPlanung.XPlan.core import XPCol, XPRelationshipProperty
from SAGisXPlanung.XPlan.enums import XP_Sondernutzungen
from SAGisXPlanung.core.mixins.mixins import RelationshipMixin, ElementOrderMixin
from SAGisXPlanung.XPlan.types import Angle, ConformityException


class BP_Dachgestaltung(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation einer für die Aufstellung des Plans zuständigen Gemeinde. """

    __tablename__ = 'bp_dachgestaltung'
    __avoidRelation__ = ['baugebiet', 'besondere_nutzung', 'gemeinbedarf', 'grundstueck_ueberbaubar']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    DNmin = Column(Angle, doc='Dachneigung, min')
    DNmax = Column(Angle, doc='Dachneigung, max')
    DN = Column(Angle, doc='Dachneigung')
    DNZwingend = Column(Angle, doc='Dachneigung, zwingend')
    dachform = Column(Enum(BP_Dachform), doc='Dachform')

    hoehenangabe = relationship("XP_Hoehenangabe", back_populates="dachgestaltung",
                                cascade="all, delete", passive_deletes=True, uselist=False)

    baugebiet_id = Column(UUID(as_uuid=True), ForeignKey('bp_baugebiet.id', ondelete='CASCADE'))
    baugebiet = relationship('BP_BaugebietsTeilFlaeche', back_populates='dachgestaltung')

    besondere_nutzung_id = Column(UUID(as_uuid=True), ForeignKey('bp_besondere_nutzung.id', ondelete='CASCADE'))
    besondere_nutzung = relationship('BP_BesondererNutzungszweckFlaeche', back_populates='dachgestaltung')

    gemeinbedarf_id = Column(UUID(as_uuid=True), ForeignKey('bp_gemeinbedarf.id', ondelete='CASCADE'))
    gemeinbedarf = relationship('BP_GemeinbedarfsFlaeche', back_populates='dachgestaltung')

    grundstueck_ueberbaubar_id = Column(UUID(as_uuid=True), ForeignKey('bp_grundstueck_ueberbaubar.id', ondelete='CASCADE'))
    grundstueck_ueberbaubar = relationship('BP_UeberbaubareGrundstuecksFlaeche', back_populates='dachgestaltung')

    def to_xplan_node(self, node=None, version=XPlanVersion.FIVE_THREE):
        from SAGisXPlanung.GML.GMLWriter import GMLWriter

        this_node = etree.SubElement(node, f"{{{node.nsmap['xplan']}}}{self.__class__.__name__}")
        GMLWriter.write_attributes(this_node, self, version)

        if self.hoehenangabe is not None and version != XPlanVersion.FIVE_THREE:
            sub_node = etree.SubElement(this_node, f"{{{this_node.nsmap['xplan']}}}{'hoehenangabe'}")
            self.hoehenangabe.to_xplan_node(sub_node)
        return node

    @classmethod
    def from_xplan_node(cls, node):
        from SAGisXPlanung.GML.GMLReader import GMLReader

        this = GMLReader.read_data_object(node, only_attributes=True)

        hoehenangabe_node = node.find('.//xplan:hoehenangabe', namespaces=node.nsmap)
        if hoehenangabe_node is not None:
            hoehenangabe = GMLReader.read_data_object(hoehenangabe_node[0])
            setattr(this, 'hoehenangabe', hoehenangabe)

        return this

    @classmethod
    def avoid_export(cls):
        return ['baugebiet_id', 'besondere_nutzung_id', 'gemeinbedarf_id', 'grundstueck_ueberbaubar_id',
                'detaillierteDachform_id']

    @classmethod
    def xp_relationship_properties(cls) -> List[XPRelationshipProperty]:
        return [
            XPRelationshipProperty(rel_name='hoehenangabe', xplan_attribute='hoehenangabe',
                                   allowed_version=XPlanVersion.SIX)
        ]

    def validate(self):
        if self.DNmin and (not self.DNmax and not self.DN and not self.DNZwingend):
            return
        if self.DNmin and self.DNmax and (not self.DN and not self.DNZwingend):
            return
        if self.DN and (not self.DNmax and not self.DNmin and not self.DNZwingend):
            return
        if self.DNZwingend and (not self.DNmax and not self.DNmin and not self.DN):
            return

        raise ConformityException('Die Attribute <code>DNmin</code>, <code>DNmax</code>, <code>DN</code> und '
                                  '<code>DNZwingend</code> dürfen nur in folgenden Kombinationen '
                                  'belegt werden: <ul><li>DNmin</li><li>DNmin und DNmax</li><li>DN</li>'
                                  '<li>DNzwingend</li>', '4.3.1.1', self.__class__.__name__)


class BP_KomplexeSondernutzung(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation einer Sondernutzung. """

    __tablename__ = 'bp_komplexe_sondernutzung'
    __avoidRelation__ = ['baugebiet']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(XP_Sondernutzungen), nullable=False)

    nutzungText = Column(String)
    aufschrift = Column(String)

    baugebiet_id = Column(UUID(as_uuid=True), ForeignKey('bp_baugebiet.id', ondelete='CASCADE'))
    baugebiet = relationship('BP_BaugebietsTeilFlaeche', back_populates='rel_sondernutzung')

    @classmethod
    def avoid_export(cls):
        return ['baugebiet_id']

class BP_KomplexeZweckbestNebenanlagen(RelationshipMixin, ElementOrderMixin, Base):
    """ Spezifikation der Zweckbestimmung einer Nebenanlagenfläche. """

    __tablename__ = 'bp_zweckbestimmung_nebenanlagen'
    __avoidRelation__ = ['nebenanlage']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    allgemein = Column(Enum(BP_ZweckbestimmungNebenanlagen), nullable=False)

    textlicheErgaenzung = Column(String)
    aufschrift = Column(String)

    nebenanlage_id = Column(UUID(as_uuid=True), ForeignKey('bp_nebenanlage.id', ondelete='CASCADE'))
    nebenanlage = relationship('BP_NebenanlagenFlaeche', back_populates='rel_zweckbestimmung')

    @classmethod
    def avoid_export(cls):
        return ['nebenanlage_id']