import logging

from sqlalchemy import types

from SAGisXPlanung import XPlanVersion
from SAGisXPlanung.XPlan.enums import XP_Rechtscharakter
from SAGisXPlanung.config import export_version

logger = logging.getLogger(__name__)


class BP_Rechtscharakter_EnumType(types.TypeDecorator):
    impl = types.Enum

    def process_bind_param(self, value, dialect):
        if isinstance(value, XP_Rechtscharakter):
            value = value.name
        if value == "FestsetzungBPlan":
            return "Festsetzung"

        from SAGisXPlanung.BPlan.BP_Basisobjekte.enums import BP_Rechtscharakter
        for bp_enum_item in BP_Rechtscharakter:
            if bp_enum_item.name == value:
                return value
        return BP_Rechtscharakter.Unbekannt

    process_literal_param = process_bind_param

    def process_result_value(self, value, dialect):
        return value


class FP_Rechtscharakter_EnumType(types.TypeDecorator):
    impl = types.Enum

    def process_bind_param(self, value, dialect):
        if isinstance(value, XP_Rechtscharakter):
            value = value.name
        if value == "DarstellungFPlan":
            return "Darstellung"

        from SAGisXPlanung.FPlan.FP_Basisobjekte.enums import FP_Rechtscharakter
        for fp_enum_item in FP_Rechtscharakter:
            if fp_enum_item.name == value:
                return value
        return FP_Rechtscharakter.Unbekannt

    process_literal_param = process_bind_param

    def process_result_value(self, value, dialect):
        return value


class SO_Rechtscharakter_EnumType(types.TypeDecorator):
    impl = types.Enum

    def process_bind_param(self, value, dialect):
        if isinstance(value, XP_Rechtscharakter):
            value = value.name
        if value == "FestsetzungImLP":
            return "InhaltLPlan"

        from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte.enums import SO_Rechtscharakter
        for so_enum_item in SO_Rechtscharakter:
            if so_enum_item.name == value:
                return value
        return SO_Rechtscharakter.Unbekannt

    process_literal_param = process_bind_param

    def process_result_value(self, value, dialect):
        return value


class XP_Rechtscharakter_EnumType(types.TypeDecorator):
    impl = types.Enum

    def process_bind_param(self, value, dialect):
        from SAGisXPlanung.BPlan.BP_Basisobjekte.enums import BP_Rechtscharakter
        from SAGisXPlanung.FPlan.FP_Basisobjekte.enums import FP_Rechtscharakter
        from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Rechtscharakter

        if isinstance(value, (SO_Rechtscharakter, BP_Rechtscharakter, FP_Rechtscharakter)):
            return value.to_xp_rechtscharakter()

        if export_version() == XPlanVersion.FIVE_THREE:
            for cls in [SO_Rechtscharakter, BP_Rechtscharakter, FP_Rechtscharakter]:
                try:
                    char = cls[value]
                    return char.to_xp_rechtscharakter()
                except Exception as e:
                    pass
        return value

    process_literal_param = process_bind_param

    def process_result_value(self, value, dialect):
        if export_version() == XPlanVersion.FIVE_THREE:

            from SAGisXPlanung.BPlan.BP_Basisobjekte.enums import BP_Rechtscharakter
            from SAGisXPlanung.FPlan.FP_Basisobjekte.enums import FP_Rechtscharakter
            from SAGisXPlanung.SonstigePlanwerke.SO_Basisobjekte import SO_Rechtscharakter

            if value == XP_Rechtscharakter.FestsetzungBPlan:
                return BP_Rechtscharakter.Festsetzung
            if value == XP_Rechtscharakter.DarstellungFPlan:
                return FP_Rechtscharakter.Darstellung
            if value == XP_Rechtscharakter.FestsetzungImLP:
                return SO_Rechtscharakter.InhaltLPlan

            for cls in [SO_Rechtscharakter, BP_Rechtscharakter, FP_Rechtscharakter]:
                try:
                    char = cls[value.name]
                    return char
                except Exception as e:
                    pass

        return value
