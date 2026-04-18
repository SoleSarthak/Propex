import math
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ScoringEngine:
    @staticmethod
    def depth_factor(depth: int) -> float:
        """
        Closer dependencies are more dangerous.
        Depth 1: 1.0
        Depth 2: 0.5
        Depth 3: 0.33
        """
        if depth <= 0:
            return 1.0
        return 1.0 / depth

    @staticmethod
    def context_multiplier(context_type: str) -> float:
        """
        Runtime dependencies are high risk, dev dependencies are lower.
        """
        multipliers = {
            "runtime": 1.0,
            "prod": 1.0,
            "dev": 0.2,
            "test": 0.1,
            "peer": 0.8,
            "optional": 0.5,
            "unknown": 0.5
        }
        return multipliers.get(context_type.lower(), 0.5)

    @staticmethod
    def popularity_factor(stars: int, downloads: int = 0) -> float:
        """
        Logarithmic scale for popularity. 
        Highly popular projects get a slightly higher score to prioritize them.
        """
        # score = 1.0 + log10(stars + 1) / 10
        # e.g., 1k stars -> 1.3, 100k stars -> 1.5
        return 1.0 + (math.log10(stars + 1) / 10.0)

    @staticmethod
    def compute_score(
        cvss_base: float,
        depth: int,
        context_type: str,
        stars: int = 0,
        downloads: int = 0
    ) -> float:
        """
        Compute the final risk score.
        Formula: CVSS * DepthFactor * ContextMultiplier * PopularityFactor
        """
        df = ScoringEngine.depth_factor(depth)
        cm = ScoringEngine.context_multiplier(context_type)
        pf = ScoringEngine.popularity_factor(stars, downloads)
        
        final_score = cvss_base * df * cm * pf
        
        # Cap at 10.0
        return min(10.0, round(final_score, 2))

    @staticmethod
    def score_to_tier(score: float) -> str:
        """
        Classify score into severity tiers.
        """
        if score >= 9.0:
            return "Critical"
        if score >= 7.0:
            return "High"
        if score >= 4.0:
            return "Medium"
        return "Low"
