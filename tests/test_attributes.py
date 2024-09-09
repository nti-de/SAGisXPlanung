from sqlalchemy import String, Enum

from SAGisXPlanung import Base
from SAGisXPlanung.FPlan.FP_Basisobjekte.feature_types import FP_Objekt
from SAGisXPlanung.FPlan.FP_Landwirtschaft_Wald_und_Gruen.feature_types import FP_Gruen
from SAGisXPlanung.XPlan.feature_types import XP_Objekt
from SAGisXPlanung.core.helper import base_models, find_true_class, get_field_type


def test_base_models():
    result = base_models(FP_Gruen)
    assert result == [FP_Gruen, FP_Objekt, XP_Objekt, Base]


def test_find_true_class():
    result = find_true_class(FP_Gruen, 'zweckbestimmung')
    assert result == FP_Gruen
    result = find_true_class(FP_Gruen, 'text')
    assert result == XP_Objekt


def test_get_field_type():
    field_type = get_field_type(FP_Gruen, 'zweckbestimmung')
    assert isinstance(field_type, Enum)

    field_type = get_field_type(FP_Gruen, 'text')
    assert isinstance(field_type, String)