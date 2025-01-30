from qgis.core import QgsSymbol, QgsSingleSymbolRenderer

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.LPlan.LP_Basisobjekte.feature_types import LP_Objekt
from SAGisXPlanung.LPlan.LP_Sonstiges.codelists import LP_ZweckbestimmungGenerischeObjekteCodelistAssoc
from SAGisXPlanung.XPlan.core import xp_version
from SAGisXPlanung.XPlan.types import GeometryType
from SAGisXPlanung.core.mixins.mixins import MixedGeometry


@xp_version(versions=[XPlanVersion.SIX])
class LP_GenerischesObjekt(MixedGeometry, LP_Objekt):
    """ Klasse zur Modellierung aller Inhalte des Landschaftsplans,
        die durch keine spezifische XPlanung-Klasse repräsentiert werden können. """

    __tablename__ = 'lp_generisches_objekt'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("lp_objekt.id", ondelete='CASCADE'), primary_key=True)

    # [0..*]
    zweckbestimmung = relationship("LP_ZweckbestimmungGenerischeObjekte", back_populates='codelist_user',
                                   secondary=LP_ZweckbestimmungGenerischeObjekteCodelistAssoc,
                                   info={ 'form-type': 'inline' })

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


@xp_version(versions=[XPlanVersion.SIX])
class LP_TextAbschnittObjekt(MixedGeometry, LP_Objekt):
    """ Bereich, in dem bestimmte textliche Festsetzungen gültig sind,
        die über die Relation "refTextInhalt" (Basisklasse XP_Objekt) spezifiziert werden. """

    __tablename__ = 'lp_text_abschnitt_objekt'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("lp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    def renderer(cls, geom_type: GeometryType):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
