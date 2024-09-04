from enum import Enum
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from qgis.core import QgsCoordinateReferenceSystem, QgsGeometry

from SAGisXPlanung import Base
from SAGisXPlanung.GML.geometry import geometry_from_spatial_element
from SAGisXPlanung.core.mixins.mixins import RelationshipMixin, MapCanvasMixin
from SAGisXPlanung.XPlan.types import GeometryType


class XP_SimpleGeometry(Base, RelationshipMixin, MapCanvasMixin):
    """ Klasse zum Erfassen von vektoriellen Planinhalten mit einfacher Erfassungstiefe """

    __tablename__ = 'xp_simple_geometry'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    name = Column(String)
    xplanung_type = Column(String)
    position = Column(Geometry())

    gehoertZuBereich_id = Column(UUID(as_uuid=True), ForeignKey('xp_bereich.id', ondelete='CASCADE'))
    gehoertZuBereich = relationship('XP_Bereich', back_populates='simple_geometry')

    def geomType(self) -> GeometryType:
        return self.geometry().type()

    def displayName(self):
        return self.xplanung_type

    def srs(self) -> QgsCoordinateReferenceSystem:
        return QgsCoordinateReferenceSystem(f'EPSG:{self.position.srid}')

    def geometry(self) -> QgsGeometry:
        return geometry_from_spatial_element(self.position)


class XPlanungPointTypes(Enum):
    """ XPlanung Objekttypen für die einfache Erfassungstiefe: Punktgeometrien"""

    BP_ZusatzkontingentLaerm = '2.6.5'
    BP_AnpflanzungBindungErhaltung = '2.8.1'
    BP_FestsetzungNachLandesrecht = '2.9.2'
    BP_EinfahrtPunkt = '2.12.2'


class XPlanungLineTypes(Enum):
    """ XPlanung Objekttypen für die einfache Erfassungstiefe: Liniengeometrien"""

    BP_AbweichungVonBaugrenze = '2.3.2'
    BP_BauGrenze = '2.3.5'
    BP_BauLinie = '2.3.6'
    BP_FirstRichtungsLinie = '2.3.9'
    BP_RichtungssektorGrenze = '2.6.4'
    BP_AnpflanzungBindungErhaltung = '2.8.1'
    BP_AbstandsMass = '2.9.1'
    BP_FestsetzungNachLandesrecht = '2.9.2'
    BP_NutzungsartenGrenze = '2.9.8'
    BP_Wegerecht = '2.9.13'
    BP_VerEntsorgung = '2.11.1'
    BP_BereichOhneEinAusfahrtLinie = '2.12.1'
    BP_EinfahrtsbereichLinie = '2.12.3'
    BP_StrassenbegrenzungsLinie = '2.12.4'
    BP_Strassenkoerper = '2.12.5'


class XPlanungPolygonTypes(Enum):
    """ XPlanung Objekttypen für die einfache Erfassungstiefe: Flächengeometrien"""

    BP_AbgrabungsFlaeche = '2.2.1'
    BP_AufschuettungsFlaeche = '2.2.2'
    BP_BodenschaetzeFlaeche = '2.2.3'
    BP_RekultivierungsFlaeche = '2.2.4'
    BP_AbstandsFlaeche = '2.3.1'
    BP_AbweichungVonUeberbaubererGrundstuecksFlaeche = '2.3.3'
    BP_BaugebietsTeilFlaeche = '2.3.4'
    BP_BesondererNutzungszweckFlaeche = '2.3.7'
    BP_FoerderungsFlaeche = '2.3.10'
    BP_GebaeudeFlaeche = '2.3.11'
    BP_GemeinschaftsanlagenFlaeche = '2.3.12'
    BP_NebenanlagenAusschlussFlaeche = '2.3.14'
    BP_NebenanlagenFlaeche = '2.3.15'
    BP_NichtUeberbaubareGrundstuecksflaeche = '2.3.16'
    BP_PersGruppenBestimmteFlaeche = '2.3.17'
    BP_RegelungVergnuegungsstaetten = '2.3.18'
    BP_SpezielleBauweise = '2.3.19'
    BP_UeberbaubareGrundstuecksFlaeche = '2.3.20'
    BP_ErhaltungsBereichFlaeche = '2.4.1'
    BP_GemeinbedarfsFlaeche = '2.5.1'
    BP_SpielSportanlagenFlaeche = '2.5.2'
    BP_ZusatzkontingentLaermFlaeche = '2.6.6'
    BP_GruenFlaeche = '2.7.1'
    BP_KleintierhaltungFlaeche = '2.7.2'
    BP_Landwirtschaft = '2.7.3'
    BP_LandwirtschaftsFlaeche = '2.7.4'
    BP_WaldFlaeche = '2.7.5'
    BP_AnpflanzungBindungErhaltung = '2.8.1'
    BP_AusgleichsFlaeche = '2.8.2'
    BP_EingriffsBereich = '2.8.4'
    BP_SchutzPflegeEntwicklungsFlaeche = '2.8.5'
    BP_AbstandsMass = '2.9.1'
    BP_FestsetzungNachLandesrecht = '2.9.2'
    BP_FlaecheOhneFestsetzung = '2.9.3'
    BP_FreiFlaeche = '2.9.4'
    BP_KennzeichnungsFlaeche = '2.9.7'
    BP_Sichtflaeche = '2.9.9'
    BP_TextlicheFestsetzungsFlaeche = '2.9.10'
    BP_Veraenderungssperre = '2.9.12'
    BP_Wegerecht = '2.9.13'
    BP_Immissionsschutz = '2.10.1'
    BP_TechnischeMassnahmenFlaeche = '2.10.2'
    BP_VerEntsorgung = '2.11.1'
    BP_ZentralerVersorgungsbereich = '2.11.1'
    BP_Strassenkoerper = '2.12.5'
    BP_StrassenVerkehrsFlaeche = '2.12.6'
    BP_VerkehrsflaecheBesondererZweckbestimmung = '2.12.7'
    BP_GewaesserFlaeche = '2.13.1'
    BP_WasserwirtschaftsFlaeche = '2.13.2'




