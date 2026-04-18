def compute_score(
    base_cvss: float, depth: int, popularity: int, context_type: str
) -> float:
    """
    Stub for the scoring engine formula.

    Formula (Draft):
    Score = (Base CVSS * Depth Factor) * (Popularity Factor) * (Context Multiplier)
    """
    depth_factor = 1.0 / (depth + 1)
    popularity_factor = 1.0 + (popularity / 100000.0)  # Dummy factor

    context_multipliers = {"runtime": 1.0, "dev": 0.5, "test": 0.3}
    context_multiplier = context_multipliers.get(context_type, 1.0)

    final_score = (base_cvss * depth_factor) * popularity_factor * context_multiplier
    return min(10.0, max(0.0, round(final_score, 2)))


def get_tier(score: float) -> str:
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW"
