import logging

from qgis.PyQt.QtGui import QColor
from qgis._core import QgsFillSymbol, QgsLinePatternFillSymbolLayer, QgsUnitTypes, QgsSimpleLineSymbolLayer
from sqlalchemy import Column, ForeignKey, ARRAY, Enum, Boolean, String

from qgis.core import QgsWkbTypes, QgsSymbol, QgsSingleSymbolRenderer
from sqlalchemy.orm import relationship

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.FPlan.FP_Sonstiges.codelists import XP_DetailTechnVorkehrungImmissionsschutzCodelistAssoc
from SAGisXPlanung.FPlan.FP_Sonstiges.enums import FP_ZweckbestimmungPrivilegiertesVorhaben
from SAGisXPlanung.XPlan.core import LayerPriorityType, xp_version
from SAGisXPlanung.XPlan.renderer import fallback_renderer, generic_objects_renderer, icon_renderer
from SAGisXPlanung.XPlan.enums import XP_ZweckbestimmungKennzeichnung, XP_ImmissionsschutzTypen, \
    XP_TechnVorkehrungenImmissionsschutz
from SAGisXPlanung.core.mixins.mixins import MixedGeometry, UeberlagerungsObjekt, PolygonGeometry, FlaechenschlussObjekt
from SAGisXPlanung.XPlan.types import GeometryType, XPEnum

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


class FP_Kennzeichnung(MixedGeometry, FP_Objekt):
    """ Kennzeichnung gemäß §5 Abs. 3 BauGB """

    __tablename__ = 'fp_kennzeichnung'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_kennzeichnung',
    }
    __LAYER_PRIORITY__ = LayerPriorityType.CustomLayerOrder | LayerPriorityType.OutlineStyle

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(ARRAY(Enum(XP_ZweckbestimmungKennzeichnung)))
    istVerdachtsflaeche = Column(Boolean)
    nummer = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            return icon_renderer('Kennzeichnung', QgsSymbol.defaultSymbol(geom_type),
                                 'Sonstiges', geometry_type=geom_type,
                                 scale_factor=5)
        return generic_objects_renderer(geom_type)

@xp_version(versions=[XPlanVersion.FIVE_THREE])
class FP_NutzungsbeschraenkungsFlaeche(PolygonGeometry, UeberlagerungsObjekt, FP_Objekt):
    """ Umgrenzungen der Flächen für besondere Anlagen und Vorkehrungen zum Schutz vor schädlichen Umwelteinwirkungen
        im Sinne des Bundes-Immissionsschutzgesetzes (§ 5, Abs. 2, Nr. 6 BauGB) """

    __tablename__ = 'fp_nutzungsbeschraenkung_flaeche'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


@xp_version(versions=[XPlanVersion.SIX])
class FP_Nutzungsbeschraenkung(MixedGeometry, FP_Objekt):
    """ Umgrenzungen von Flächen für Nutzungsbeschränkungen oder für Vorkehrungen zum Schutz gegen schädliche
        Umwelteinwirkungen im Sinne des Bundes-Immissionsschutzgesetzes (§ 5, Abs. 2, Nr. 6 BauGB) """

    __tablename__ = 'fp_nutzungsbeschraenkung'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    nutzung = Column(String)
    typ = Column(XPEnum(XP_ImmissionsschutzTypen, include_default=True))
    technVorkehrung = Column(XPEnum(XP_TechnVorkehrungenImmissionsschutz, include_default=True))

    detaillierteTechnVorkehrung = relationship(
        'XP_DetailTechnVorkehrungImmissionsschutz',
        back_populates='codelist_user',
        secondary=XP_DetailTechnVorkehrungImmissionsschutzCodelistAssoc,
        info={
            'form-type': 'inline'
        }
    )

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))


class FP_PrivilegiertesVorhaben(MixedGeometry, FP_Objekt):
    """ Standorte für privilegierte Außenbereichsvorhaben und für sonstige Anlagen in Außenbereichen gem. § 35 Abs. 1
        und 2 BauGB """

    __tablename__ = 'fp_privilegiertes_vorhaben'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    zweckbestimmung = Column(XPEnum(FP_ZweckbestimmungPrivilegiertesVorhaben, include_default=True))
    vorhaben = Column(String)

    @classmethod
    def polygon_symbol(cls) -> QgsSymbol:
        line_pattern = QgsLinePatternFillSymbolLayer()
        line_pattern.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        line_pattern.setLineAngle(45)
        line_pattern.setDistance(30)
        line_pattern.setLineWidth(1)
        line_pattern.setColor(QColor(0, 0, 0))

        symbol = QgsFillSymbol()
        symbol.changeSymbolLayer(0, line_pattern)

        line = QgsSimpleLineSymbolLayer(QColor(0, 0, 0))
        line.setWidth(0.5)
        line.setOutputUnit(QgsUnitTypes.RenderUnit.RenderMapUnits)
        symbol.appendSymbolLayer(line)

        return symbol

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            return QgsSingleSymbolRenderer(cls.polygon_symbol())
        elif geom_type is not None:
            return QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(geom_type))
        raise Exception('parameter geometryType should not be None')


class FP_FlaecheOhneDarstellung(PolygonGeometry, FlaechenschlussObjekt, FP_Objekt):
    """ Fläche, für die keine geplante Nutzung angegben werden kann """

    __tablename__ = 'fp_flaeche_ohne_darstellung'
    __mapper_args__ = {
        'polymorphic_identity': 'fp_flaeche_ohne_darstellung',
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return generic_objects_renderer(geom_type)


class FP_VorbehalteFlaeche(PolygonGeometry, FP_Objekt):
    """ Flaechen auf denen bestimmte Vorbehalte wirksam sind. """

    __tablename__ = 'fp_vorbehalte_flaeche'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Column(ForeignKey("fp_objekt.id", ondelete='CASCADE'), primary_key=True)

    vorbehalt = Column(String)

    @classmethod
    @fallback_renderer
    def renderer(cls, geom_type: GeometryType = None):
        return generic_objects_renderer(geom_type)
