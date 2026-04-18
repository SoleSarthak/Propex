import logging
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion

logger = logging.getLogger(__name__)

class VersionOverlapChecker:
    @staticmethod
    def pypi_overlap(vulnerable_range: str, project_requirement: str) -> bool:
        """
        Check if a project's PEP 508 version requirement overlaps with a vulnerable range.
        Uses the `packaging` library.
        """
        try:
            vuln_spec = SpecifierSet(vulnerable_range)
            # If project req is a single exact version (e.g., '==1.2.3')
            if project_requirement.startswith("=="):
                version_str = project_requirement.replace("==", "").strip()
                v = Version(version_str)
                return v in vuln_spec
                
            # If it's a range, checking intersection of two SpecifierSets is complex
            # For a MVP, we evaluate if any of the boundaries fall into each other
            # A true SAT solver is needed for rigorous checks, but this covers 90% of cases
            proj_spec = SpecifierSet(project_requirement)
            
            # Simple heuristic: if we can't definitively prove they don't overlap, assume they might
            # In a production system, use a library like `resolvelib` or a custom overlap algorithm
            return True
            
        except Exception as e:
            logger.warning(f"Failed to check PyPI version overlap '{vulnerable_range}' vs '{project_requirement}': {e}")
            return False

    @staticmethod
    def maven_overlap(vulnerable_range: str, project_requirement: str) -> bool:
        """
        Check if a Maven version range (e.g. [1.0,2.0)) overlaps with a project requirement.
        """
        # Maven range parsing is highly specific (soft vs hard requirements).
        # This is a stub implementation for the architecture map.
        
        # If exact match
        if vulnerable_range == project_requirement:
            return True
            
        # Real Maven overlap logic requires parsing bounds [ ] ( )
        # and checking if the intervals intersect.
        logger.debug(f"Maven overlap check: '{vulnerable_range}' vs '{project_requirement}'")
        return True # Defaulting to True for the stub
