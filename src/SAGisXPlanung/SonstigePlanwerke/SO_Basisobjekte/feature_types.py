
from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import Column, ForeignKey, Enum, Boolean, Float

from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Rechtscharakter
from SAGisXPlanung.XPlan.conversions import SO_Rechtscharakter_EnumType
from SAGisXPlanung.XPlan.core import XPCol
from SAGisXPlanung.XPlan.feature_types import XP_Objekt
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

    rechtscharakter = XPCol(SO_Rechtscharakter_EnumType(SO_Rechtscharakter), nullable=False, doc='Rechtscharakter',
                            version=XPlanVersion.FIVE_THREE)

    position = Column(Geometry())
    flaechenschluss = Column(Boolean, doc='Flächenschluss')
    flussrichtung = Column(Boolean)
    nordwinkel = Column(Float)

    def srs(self):
        return QgsCoordinateReferenceSystem(f'EPSG:{self.position.srid}')

    def geometry(self):
        return geometry_from_spatial_element(self.position)

    def setGeometry(self, geom: QgsGeometry, srid: int = None):
        if srid is None and self.position is None:
            raise Exception('geometry needs a srid')
        self.position = WKBElement(geom.asWkb(), srid=srid or self.position.srid)

    def geomType(self) -> GeometryType:
        return self.geometry().type()

    @classmethod
    def hidden_inputs(cls):
        h = super(SO_Objekt, cls).hidden_inputs()
        return h + ['position']
