import logging
import semver
from typing import List, Optional

logger = logging.getLogger(__name__)

class VersionChecker:
    @staticmethod
    def is_vulnerable(version: str, vulnerable_ranges: List[str]) -> bool:
        """
        Check if a given version string matches any of the vulnerable ranges.
        Note: This is a simplified version for Phase 1. 
        NPM ranges like ^1.2.3 or ~2.0.0 require more complex parsing.
        """
        try:
            # Clean version (strip 'v' prefix if exists)
            clean_ver = version.lstrip('v')
            ver_obj = semver.Version.parse(clean_ver)
            
            for range_str in vulnerable_ranges:
                # Basic range support (e.g., ">=1.0.0 <2.0.0")
                if VersionChecker.matches_range(ver_obj, range_str):
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to check version {version} against ranges {vulnerable_ranges}: {e}")
            return False

    @staticmethod
    def matches_range(version: semver.Version, range_str: str) -> bool:
        """
        Simple range matcher. 
        Supports basic comparisons like >=, <=, >, <, ==
        """
        # This is a placeholder for a more robust NPM-compatible semver parser.
        # For Phase 1, we will assume standard semver comparison strings.
        try:
            return version.match(range_str)
        except:
            return False
