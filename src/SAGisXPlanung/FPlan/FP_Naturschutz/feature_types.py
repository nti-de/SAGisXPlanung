import logging

from sqlalchemy import Column, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.FPlan.FP_Sonstiges.enums import FP_MassnahmeKlimawandelTypen
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


class FP_AusgleichsFlaeche(MixedGeometry, FP_Objekt):
    """ Flaechen und Massnahmen zum Ausgleich gemaess § 5 Abs. 2a BauGB. """

    __tablename__ = 'fp_ausgleich'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_ausgleich',
    }
    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    ziel = Column(XPEnum(XP_SPEZiele, include_default=True))
    sonstZiel = Column(String)
    massnahme = relationship("XP_SPEMassnahmenDaten", back_populates="fp_ausgleichsflaeche", cascade="all, delete",
                             passive_deletes=True)
    refMassnahmenText = relationship("XP_ExterneReferenz", back_populates="fp_ausgleichsflaeche_massnahme",
                                     cascade="all, delete", passive_deletes=True, uselist=False,
                                     foreign_keys='XP_ExterneReferenz.fp_ausgleichsflaeche_massnahme_id')
    refLandschaftsplan = relationship("XP_ExterneReferenz", back_populates="fp_ausgleichsflaeche_plan",
                                      cascade="all, delete", passive_deletes=True, uselist=False,
                                      foreign_keys='XP_ExterneReferenz.fp_ausgleichsflaeche_plan_id')

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return generic_objects_renderer(geom_type)


class FP_AnpassungKlimawandel(MixedGeometry, FP_Objekt):
    """ Massnahmen zur Anpassung an den Klimawandel (§ 5 Abs. 2 Nr. 2c BauGB). """

    __tablename__ = 'fp_anpassung_klimawandel'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    massnahme = Column(XPEnum(FP_MassnahmeKlimawandelTypen, include_default=True))
    detailMassnahme_id = Column(UUID(as_uuid=True), ForeignKey('codelist_values.id'))
    detailMassnahme = relationship(
        'FP_DetailMassnahmeKlimawandel',
        back_populates='codelist_user',
        foreign_keys=[detailMassnahme_id],
        info={
            'form-type': 'inline'
        }
    )

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return generic_objects_renderer(geom_type)
