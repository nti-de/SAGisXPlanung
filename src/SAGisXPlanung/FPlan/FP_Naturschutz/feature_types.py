import logging

from sqlalchemy import Column, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship

from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import LayerPriorityType
from SAGisXPlanung.XPlan.renderer import fallback_renderer, generic_objects_renderer
from SAGisXPlanung.XPlan.enums import XP_SPEZiele
from SAGisXPlanung.core.mixins.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum

logger = logging.getLogger(__name__)


class FP_SchutzPflegeEntwicklung(MixedGeometry, FP_Objekt):
    """ Umgrenzung von Flächen für Maßnahmen zum Schutz, zur Pflege und zur Entwicklung von Natur und Landschaft
        (§5 Abs. 2, Nr. 10 BauGB) """

    __tablename__ = 'fp_schutzflaeche'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_schutzflaeche',
    }
    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    ziel = Column(XPEnum(XP_SPEZiele, include_default=True))
    sonstZiel = Column(String)
    massnahme = relationship("XP_SPEMassnahmenDaten", back_populates="fp_schutzflaeche", cascade="all, delete",
                             passive_deletes=True)
    istAusgleich = Column(Boolean)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return generic_objects_renderer(geom_type)
