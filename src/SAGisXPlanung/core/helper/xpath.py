import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Union, List, Any, Optional

from SAGisXPlanung.config import export_version

logger = logging.getLogger(__name__)


@dataclass
class PathSegment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    namespace: Optional[str] = ""
    element: str = ""
    index: str = ""

@dataclass
class XPathExpression:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    segments: List[PathSegment] = field(default_factory=lambda: [PathSegment()])
    xpath: str = field(init=False)

    def __post_init__(self):
        self.xpath = self.generate_xpath()

    def generate_xpath(self):
        """Generate XPath string from segments"""
        parts = []
        for segment in self.segments:
            base = f"{segment.namespace}:{segment.element}" if segment.namespace else segment.element
            if segment.index:
                parts.append(f"{base}[{segment.index}]")
            else:
                parts.append(base)
        return "/".join(parts)

    @classmethod
    def from_xpath(cls, xpath_str: str) -> 'XPathExpression':
        # Match [optional namespace:]element[optional[index]]
        segment_pattern = re.compile(
            r'(?:(?P<namespace>[^:/\[]+):)?(?P<element>[^/\[]+)(?:\[(?P<index>[^\]]+)\])?'
        )
        segments = []
        for match in segment_pattern.finditer(xpath_str):
            namespace = match.group("namespace") or ""
            element = match.group("element")
            index = match.group("index") or ""
            segments.append(PathSegment(namespace=namespace, element=element, index=index))
        return XPathExpression(segments=segments)


@dataclass
class ResolvedXPathResult:
    value: Any
    target_class: type
    attribute_name: str
    target_xid: str


class XPathMatcher:
    """Utility class for matching XPath expressions against config entries"""

    @staticmethod
    def normalize_xpath(xpath: str, remove_index=True) -> str:
        """Remove namespace prefixes from xpath for comparison"""
        # Remove namespace prefixes (e.g., "xplan:" -> "")
        normalized = re.sub(r'\w+:', '', xpath)
        if remove_index:
            # Remove array indices (e.g., "[1]" -> "")
            normalized = re.sub(r'\[\d+\]', '', normalized)
        return normalized.strip('/')

    @staticmethod
    def xpath_matches_config(orm_xpath: List[str], config_xpath: Union[str, List[str]], match_mode='any') -> bool:
        """Check if ORM xpath matches any of the config xpath patterns"""
        orm_xpaths = [XPathMatcher.normalize_xpath(x) for x in orm_xpath]

        # Handle list of possible xpaths in config
        if isinstance(config_xpath, list):
            config_xpaths = config_xpath
        else:
            config_xpaths = [config_xpath]

        config_xpaths = [XPathMatcher.normalize_xpath(cp) for cp in config_xpaths]

        def _matches(config_path_normalized: str) -> bool:
            for orm_path in orm_xpaths:
                # Exact match
                if orm_path == config_path_normalized:
                    return True

                # Last-N-component match
                orm_components = orm_path.split('/')
                config_components = config_path_normalized.split('/')

                if len(orm_components) >= len(config_components):
                    if orm_components[-len(config_components):] == config_components:
                        return True
            return False

        if match_mode == 'any':
            return any(_matches(cfg) for cfg in config_xpaths)
        elif match_mode == 'all':
            return all(_matches(cfg) for cfg in config_xpaths)
        else:
            raise ValueError(f"Invalid match_mode: {match_mode}. Use 'any' or 'all'.")

    @staticmethod
    def resolve_xpath_value(base_obj, xpath: str, _index=None) -> Optional[ResolvedXPathResult]:
        """Resolve xpath expression to get the actual value from the object"""
        if not xpath:
            return None

        clean_xpath = XPathMatcher.normalize_xpath(xpath, remove_index=False)
        if not clean_xpath:
            return None

        # Split path and traverse
        path_components = clean_xpath.split('/')
        current_obj = base_obj
        previous_obj = None
        last_attribute = None

        for component in path_components:
            match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\[(\d+)\]$', component)
            if match:
                attr_name = match.group(1)
                attr_name = current_obj.attribute_by_version(attr_name, export_version())
                index = int(match.group(2)) - 1  # XPath syntax is 1-based
            elif _index is not None:
                attr_name = component
                index = _index  # index from ORM attribute is 0-based
            else:
                attr_name = component
                index = None

            if attr_name == current_obj.__class__.__name__ :
                continue
            if not hasattr(current_obj, attr_name):
                return None

            previous_obj = current_obj
            last_attribute = attr_name
            current_obj = getattr(current_obj, attr_name)

            # Handle lists/arrays
            if current_obj is not None and isinstance(current_obj, (list, tuple)):
                if index is not None:
                    if 0 <= index < len(current_obj):
                        current_obj = current_obj[index]
                    else:
                        # Index out of bounds - XPath evaluation error
                        return None
                elif len(current_obj) > 0:
                    current_obj = current_obj[0]
                else:
                    # Empty list when no specific index requested - XPath evaluation error
                    return None
            elif current_obj is None and index is not None:
                # Trying to index into None - XPath evaluation error
                return None

        return ResolvedXPathResult(
            value=current_obj,
            target_class=previous_obj.__class__,
            attribute_name=last_attribute,
            target_xid=str(previous_obj.id)
        )