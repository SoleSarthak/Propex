import logging
from typing import List, Dict, Any, Optional
from packaging.requirements import Requirement, InvalidRequirement

logger = logging.getLogger(__name__)

class Pep508Parser:
    @staticmethod
    def parse_requires_dist(requires_dist: List[str]) -> List[Dict[str, Any]]:
        """
        Parse PEP 508 requirements strings into structured data.
        Returns a list of dictionaries with package name, version specifier, and extras.
        """
        if not requires_dist:
            return []

        parsed_deps = []
        for req_str in requires_dist:
            try:
                req = Requirement(req_str)
                
                # Check if this is an extra requirement (e.g., test or dev)
                is_extra = False
                extra_name = None
                if req.marker:
                    # simplistic check, real evaluation requires an environment
                    marker_str = str(req.marker)
                    if 'extra' in marker_str:
                        is_extra = True
                        # This is a simplification; full marker eval is complex
                        parts = marker_str.split('==')
                        if len(parts) > 1:
                            extra_name = parts[1].strip().strip("'\"")

                parsed_deps.append({
                    "name": req.name,
                    "specifier": str(req.specifier) if req.specifier else "*",
                    "is_extra": is_extra,
                    "extra_name": extra_name
                })
            except InvalidRequirement:
                logger.warning(f"Failed to parse PEP 508 requirement: {req_str}")
            except Exception as e:
                logger.error(f"Unexpected error parsing {req_str}: {e}")

        return parsed_deps
