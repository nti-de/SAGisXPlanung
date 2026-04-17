
from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import Column, ForeignKey, Enum, Boolean, Float, CheckConstraint
from sqlalchemy.orm import relationship

from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry, QgsSingleSymbolRenderer, QgsSymbol

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Rechtscharakter
from SAGisXPlanung.XPlan.conversions import SO_Rechtscharakter_EnumType
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.feature_types import XP_Objekt, XP_TextAbschnitt
from SAGisXPlanung.XPlan.types import Angle, GeometryType


class SO_Objekt(XP_Objekt):
    """ Basisklasse für die Inhalte sonstiger raumbezogener Planwerke ,von Klassen zur Modellierung nachrichtlicher
        Übernahmen, sowie Planart-übergreifende Planinhalte """

    __tablename__ = 'so_objekt'
    __mapper_args__ = {
        'polymorphic_identity': 'so_objekt',
    }
    __readonly_columns__ = ['position']

    id = Column(ForeignKey("xp_objekt.id", ondelete='CASCADE'), primary_key=True)

    rechtscharakter = Column(SO_Rechtscharakter_EnumType(SO_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    position = Column(Geometry(), CheckConstraint("GeometryType(position) NOT IN ('GEOMETRYCOLLECTION')",
                                                        name='prevent_geometry_collection'))
    flaechenschluss = Column(Boolean, doc='Flächenschluss')
    flussrichtung = Column(Boolean)
    nordwinkel = Column(Angle)

    laermkontingent = relationship('BP_EmissionskontingentLaerm', back_populates='so_objekt', uselist=False,
                                   cascade='all, delete', passive_deletes=True,
                                   foreign_keys='BP_EmissionskontingentLaerm.so_objekt_id',
                                   info={
                                        'xplan_version': XPlanVersion.SIX,
                                   })

    laermkontingentGebiet = relationship('BP_EmissionskontingentLaermGebiet', back_populates='so_objekt_gebiet',
                                         cascade='all, delete', passive_deletes=True,
                                         foreign_keys='BP_EmissionskontingentLaerm.so_objekt_gebiet_id',
                                         info={
                                             'xplan_version': XPlanVersion.SIX,
                                         })

    def srs(self):
        return QgsCoordinateReferenceSystem(f'EPSG:{self.position.srid}')

    def geometry(self):
        return geometry_from_spatial_element(self.position)

    def setGeometry(self, geom: QgsGeometry, srid: int = None):
        if srid is None and self.position is None:
            raise Exception('geometry needs a srid')
        self.position = WKBElement(geom.asWkb().data(), srid=srid or self.position.srid)

    def geomType(self) -> GeometryType:
        return self.geometry().type()

    @classmethod
    def hidden_inputs(cls):
        h = super(SO_Objekt, cls).hidden_inputs()
        return h + ['position']


@xp_version(versions=[XPlanVersion.FIVE_THREE])
class SO_TextAbschnitt(XP_TextAbschnitt):
    """ Textlich formulierter Inhalt eines Sonstigen Plans, der einen anderen Rechtscharakter als das zugrunde liegende
        Fachobjekt hat (Attribut rechtscharakter des Fachobjektes), oder dem Plan als Ganzes zugeordnet ist. """

    __tablename__ = 'so_text_abschnitt'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("xp_text_abschnitt.id", ondelete='CASCADE'), primary_key=True)

    rechtscharakter = Column(SO_Rechtscharakter_EnumType(SO_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                             info={'xplan_version': XPlanVersion.FIVE_THREE})

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
