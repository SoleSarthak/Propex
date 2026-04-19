"""
EPSS (Exploit Prediction Scoring System) integration for the Propex Scoring Engine.
EPSS API: https://api.first.org/data/v1/epss (completely free, no auth needed)
"""
import math
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

EPSS_API_URL = "https://api.first.org/data/v1/epss"

async def fetch_epss_score(cve_id: str) -> Optional[float]:
    """
    Fetch the EPSS probability score for a CVE (0.0 - 1.0).
    EPSS = probability that a CVE will be exploited in the wild within 30 days.
    Returns None on failure (fallback: use CVSS only).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(EPSS_API_URL, params={"cve": cve_id})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data"):
                    epss_score = float(data["data"][0].get("epss", 0.0))
                    percentile = float(data["data"][0].get("percentile", 0.0))
                    logger.info(f"EPSS for {cve_id}: score={epss_score:.4f}, percentile={percentile:.2%}")
                    return epss_score
    except Exception as e:
        logger.warning(f"EPSS fetch failed for {cve_id}: {e}")
    return None


def epss_multiplier(epss_score: Optional[float]) -> float:
    """
    Convert EPSS probability into a score multiplier.
    High exploit probability = higher urgency.

    Mapping:
    - epss > 0.5  (top 5% most likely exploited) → 1.4x
    - epss > 0.1  (top 20%)                       → 1.2x
    - epss > 0.01 (top 50%)                        → 1.0x (neutral)
    - epss < 0.01 (low probability)                → 0.85x
    - None (unknown)                               → 1.0x (neutral)
    """
    if epss_score is None:
        return 1.0
    if epss_score > 0.5:
        return 1.4
    if epss_score > 0.1:
        return 1.2
    if epss_score > 0.01:
        return 1.0
    return 0.85
