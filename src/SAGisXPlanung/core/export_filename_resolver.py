import logging
import re
from datetime import date

from SAGisXPlanung.config import QgsConfig, export_version

logger = logging.getLogger(__name__)

INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'
PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)}")
PLACEHOLDERS = {
    "name": lambda p: p.name or "",
    "nummer": lambda p: p.nummer or "",
    "ags": lambda p:
        p.gemeinde[0].ags
        if getattr(p, "gemeinde", None)
        else "",
    "gemeindeName": lambda p:
        p.gemeinde[0].gemeindeName
        if getattr(p, "gemeinde", None)
        else "",
    "datum": lambda p:
        date.today().isoformat(),
    "version": lambda p: str(export_version()),
    "planArt": lambda p: p.__class__.__name__.split("_", 1)[0],
}


class ExportFilenameResolver:

    @classmethod
    def available_placeholders(cls) -> list[str]:
        return sorted(PLACEHOLDERS.keys())

    @classmethod
    def render(cls, plan, template: str | None = None) -> str:

        template = template or QgsConfig.xplan_export_filename_schema() or "{name}"

        def replace(match):
            key = match.group(1)

            resolver = PLACEHOLDERS.get(key)
            if resolver is None:
                return ""

            try:
                value = resolver(plan)
                return sanitize_filename(value)
            except Exception:
                logger.exception("Failed resolving export placeholder '%s'",key)
                return ""

        filename = PLACEHOLDER_PATTERN.sub(replace, template)

        filename = re.sub(r"_+", "_", filename)
        filename = re.sub(r"-+", "-", filename)

        return filename.strip("._- ")


def sanitize_filename(value) -> str:
    if value is None:
        return ""

    value = str(value)

    value = re.sub(INVALID_FILENAME_CHARS, "-", value)
    value = re.sub(r"\s+", "_", value)

    return value.strip("._- ")