import logging

from qgis.core import (QgsSymbol, QgsWkbTypes, QgsSingleSymbolRenderer, QgsUnitTypes)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt
from sqlalchemy import Column, ForeignKey

from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.XPlan.core import fallback_renderer, generic_objects_renderer
from SAGisXPlanung.XPlan.mixins import MixedGeometry
from SAGisXPlanung.XPlan.types import GeometryType

logger = logging.getLogger(__name__)


class FP_GenerischesObjekt(MixedGeometry, FP_Objekt):
    """ Klasse zur Modellierung aller Inhalte des Bebauungsplans,die durch keine andere spezifische XPlanung Klasse
        repräsentiert werden können """

    __tablename__ = 'fp_generisches_objekt'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_generisches_objekt',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return generic_objects_renderer(geom_type)
