import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

REQUIRED_SECTIONS = ["## Summary", "## Dependency Path", "## Remediation", "## Code Fix", "## Affected Versions"]

def validate_patch_output(text: str) -> tuple[bool, list[str]]:
    """
    Validate that the LLM output contains all required sections.
    Returns (is_valid, list_of_missing_sections).
    """
    missing = []
    for section in REQUIRED_SECTIONS:
        if section not in text:
            missing.append(section)
    
    is_valid = len(missing) == 0
    if not is_valid:
        logger.warning(f"LLM output failed validation. Missing sections: {missing}")
    
    return is_valid, missing
