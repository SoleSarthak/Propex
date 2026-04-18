import logging

logger = logging.getLogger(__name__)

class MavenVersionParser:
    @staticmethod
    def parse_range(version_range: str) -> dict:
        """
        Parses a Maven version range string into structured bounds.
        Example: "[1.0, 2.0)" -> {'lower': '1.0', 'lower_inclusive': True, 'upper': '2.0', 'upper_inclusive': False}
        """
        version_range = version_range.strip()
        result = {
            "is_range": False,
            "exact_version": None,
            "lower": None,
            "lower_inclusive": False,
            "upper": None,
            "upper_inclusive": False
        }

        # If it's a soft requirement or exact version (no brackets/parentheses)
        if not (version_range.startswith('[') or version_range.startswith('(')):
            result["exact_version"] = version_range
            return result

        result["is_range"] = True
        
        # Check lower bound inclusion
        if version_range.startswith('['):
            result["lower_inclusive"] = True
            
        # Check upper bound inclusion
        if version_range.endswith(']'):
            result["upper_inclusive"] = True

        # Strip brackets
        inner = version_range[1:-1]
        
        # Split on comma
        if ',' in inner:
            parts = inner.split(',')
            if parts[0].strip():
                result["lower"] = parts[0].strip()
            if parts[1].strip():
                result["upper"] = parts[1].strip()
        else:
            # E.g. [1.0] -> Exact version hard requirement
            result["exact_version"] = inner.strip()
            result["is_range"] = False

        return result
