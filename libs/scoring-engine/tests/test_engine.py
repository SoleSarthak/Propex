import pytest
from hypothesis import given, strategies as st
from odepm_scoring.engine import ScoringEngine

def test_depth_factor():
    assert ScoringEngine.depth_factor(1) == 1.0
    assert ScoringEngine.depth_factor(2) == 0.5
    assert ScoringEngine.depth_factor(4) == 0.25
    assert ScoringEngine.depth_factor(0) == 1.0

def test_context_multiplier():
    assert ScoringEngine.context_multiplier("runtime") == 1.0
    assert ScoringEngine.context_multiplier("dev") == 0.2
    assert ScoringEngine.context_multiplier("INVALID") == 0.5

@given(st.floats(min_value=0, max_value=10.0), st.integers(min_value=1, max_value=10))
def test_score_never_exceeds_max(cvss, depth):
    score = ScoringEngine.compute_score(cvss, depth, "runtime", stars=1000000)
    assert score <= 10.0
    assert score >= 0.0

def test_tier_classification():
    assert ScoringEngine.score_to_tier(9.5) == "Critical"
    assert ScoringEngine.score_to_tier(7.5) == "High"
    assert ScoringEngine.score_to_tier(5.0) == "Medium"
    assert ScoringEngine.score_to_tier(2.0) == "Low"

def test_popularity_impact():
    low_pop = ScoringEngine.compute_score(5.0, 1, "runtime", stars=0)
    high_pop = ScoringEngine.compute_score(5.0, 1, "runtime", stars=10000)
    assert high_pop > low_pop
