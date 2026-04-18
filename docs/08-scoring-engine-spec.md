# 08 — Scoring Engine Specification
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. Purpose

The Scoring Engine computes a **Contextual Severity Score** for each (CVE, Repository) pair. Unlike CVSS, which scores a vulnerability in isolation, the Contextual Severity Score accounts for _how_ a repository uses the vulnerable package — making it a better predictor of actual exploitability and urgency.

---

## 2. Score Range & Tiers

| Score Range | Tier     | Color  | Action                               |
|-------------|----------|--------|--------------------------------------|
| 9.0 – 10.0  | Critical | 🔴 Red  | Immediate issue creation (< 15 min)  |
| 7.0 – 8.9   | High     | 🟠 Orange | Issue within 1 hour               |
| 4.0 – 6.9   | Medium   | 🟡 Yellow | Issue within 24 hours             |
| 0.1 – 3.9   | Low      | 🟢 Green | Dashboard notification only          |

---

## 3. Score Formula

```
Contextual Score = min(10.0,
    CVSS_Base × Depth_Factor × Context_Multiplier × Popularity_Factor
)
```

### 3.1 CVSS_Base

The base CVSS score from NVD/OSV, representing the inherent severity of the vulnerability in isolation.

- Source: `cves.cvss_score` field
- Range: 0.0 – 10.0
- Version preference: CVSS 3.1 > CVSS 3.0 > CVSS 2.0 (with conversion)
- If CVSS not available: use OSV severity heuristic or default to 5.0 (Medium)

**CVSS 2.0 to 3.x conversion table:**
| CVSS 2.0 Range | Converted CVSS 3.x |
|----------------|--------------------|
| 0.0 – 3.9      | 0.0 – 3.9          |
| 4.0 – 6.9      | 4.0 – 6.9          |
| 7.0 – 10.0     | 7.0 – 10.0         |

---

### 3.2 Depth_Factor

Penalizes transitive dependencies — a vulnerability buried 5 levels deep in the dependency tree is less likely to be reachable than a direct dependency.

| Dependency Depth | Factor |
|------------------|--------|
| 1 (direct)       | 1.00   |
| 2                | 0.85   |
| 3                | 0.70   |
| 4                | 0.55   |
| 5+               | 0.40   |

**Formula:**
```python
def depth_factor(depth: int) -> float:
    factors = {1: 1.00, 2: 0.85, 3: 0.70, 4: 0.55}
    return factors.get(depth, 0.40)
```

---

### 3.3 Context_Multiplier

Adjusts for where in the dependency manifest the vulnerable package appears. A runtime dependency is more dangerous than one only used during development or testing.

| Dependency Context          | Multiplier |
|-----------------------------|------------|
| runtime / compile / default | 1.00       |
| peer                        | 0.90       |
| optional                    | 0.70       |
| dev / devDependency         | 0.50       |
| test / testCompile          | 0.30       |

**Manifest detection logic:**
- npm `package.json`: `"dependencies"` → runtime; `"devDependencies"` → dev; `"peerDependencies"` → peer
- Python `requirements.txt`: all runtime; `requirements-dev.txt` or `requirements-test.txt` → dev
- Python `setup.py`/`pyproject.toml`: `install_requires` → runtime; `extras_require["dev"]` → dev
- Maven `pom.xml`: `<scope>compile</scope>` or none → runtime; `<scope>test</scope>` → test; `<scope>provided</scope>` → peer

---

### 3.4 Popularity_Factor

Accounts for the downstream impact of the affected repository. A critical vulnerability in a package downloaded 50M times/week has more real-world impact than the same vulnerability in a package downloaded 100 times/week.

```python
import math

def popularity_factor(weekly_downloads: int) -> float:
    if weekly_downloads <= 0:
        return 0.1
    # log10 scale, normalized to 0.1–1.0
    factor = math.log10(weekly_downloads) / 8.0  # 10^8 = 100M DL/week = factor 1.0
    return max(0.1, min(1.0, factor))
```

**Examples:**

| Weekly Downloads | log10  | Factor |
|------------------|--------|--------|
| 100              | 2.0    | 0.25   |
| 10,000           | 4.0    | 0.50   |
| 1,000,000        | 6.0    | 0.75   |
| 50,000,000       | 7.7    | 0.96   |
| 100,000,000+     | 8.0+   | 1.00   |

---

## 4. Worked Examples

### Example 1: Critical Direct Dependency (lodash CVE in next.js)

```
CVSS_Base = 9.8
Depth_Factor = 1.00 (direct dependency)
Context_Multiplier = 1.00 (runtime)
Popularity_Factor = 0.96 (next.js: ~50M weekly downloads)

Score = min(10.0, 9.8 × 1.00 × 1.00 × 0.96) = min(10.0, 9.41) = 9.41
Tier = Critical
```

### Example 2: High Severity, Deep Transitive, Dev Only

```
CVSS_Base = 8.1
Depth_Factor = 0.55 (depth 4)
Context_Multiplier = 0.50 (devDependency)
Popularity_Factor = 0.75 (1M weekly downloads)

Score = min(10.0, 8.1 × 0.55 × 0.50 × 0.75) = min(10.0, 1.67) = 1.67
Tier = Low
```

### Example 3: Medium Severity, Transitive Runtime

```
CVSS_Base = 6.5
Depth_Factor = 0.85 (depth 2)
Context_Multiplier = 1.00 (runtime)
Popularity_Factor = 0.50 (10K weekly downloads)

Score = min(10.0, 6.5 × 0.85 × 1.00 × 0.50) = min(10.0, 2.76) = 2.76
Tier = Low
```

---

## 5. Score Decomposition Storage

Each scored record stores all intermediate factors for auditability and debugging:

```sql
-- affected_repositories table fields:
cvss_base               DECIMAL(3,1),    -- Raw CVSS score from CVE
depth_factor            DECIMAL(4,3),    -- 0.400 – 1.000
context_multiplier      DECIMAL(4,3),    -- 0.300 – 1.000
popularity_factor       DECIMAL(4,3),    -- 0.100 – 1.000
context_score           DECIMAL(4,2),    -- Final score: 0.10 – 10.00
severity_tier           VARCHAR(10)      -- Critical | High | Medium | Low
```

---

## 6. Score Recalculation Triggers

The score is recalculated when any input changes:

| Trigger                          | Affected Records                       |
|----------------------------------|----------------------------------------|
| CVSS score updated by NVD        | All repos affected by that CVE         |
| Package download count updated   | All repos using that package           |
| Dependency context type corrected| That specific repo-CVE record          |
| Dependency depth recalculated    | That specific repo-CVE record          |

Recalculation is triggered by:
1. A Kafka event from the ingestion service (CVE updated)
2. A daily batch job for download count refresh
3. Manual trigger via API for specific records

---

## 7. Future Enhancements (Post-MVP)

### 7.1 Call-Graph Reachability (Phase 2)

For npm packages, static analysis can determine if the vulnerable function is actually called in the dependent project.

```
Reachability_Factor:
  - Reachable:     1.0 (vulnerable function in call graph)
  - Unreachable:   0.1 (vulnerable function never called)
  - Unknown:       0.7 (default — no analysis available)
```

Tools: CodeQL (GitHub), Semgrep, or custom AST walker.

### 7.2 Exploit Availability Factor (Phase 2)

Adjust score upward if a public exploit or PoC exists for the CVE.

```
Exploit_Factor:
  - Weaponized/in-the-wild: 1.5 (capped at max score 10)
  - PoC published:           1.2
  - No public exploit:       1.0 (default)
```

Source: EPSS (Exploit Prediction Scoring System) from FIRST.org.

### 7.3 Repository Activity Factor (Phase 2)

Actively maintained repos are more likely to patch quickly; deprioritize abandoned repos.

```
Activity_Factor:
  - Last commit < 30 days:   1.0
  - Last commit 30-90 days:  0.9
  - Last commit 90-365 days: 0.7
  - Last commit > 365 days:  0.4
  - Archived:                0.2
```

---

## 8. Implementation

### 8.1 Python Module (`libs/scoring-engine`)

```python
# libs/scoring-engine/odepm_scoring/calculator.py

from dataclasses import dataclass
from .factors import depth_factor, context_multiplier, popularity_factor

@dataclass
class ScoringInput:
    cvss_base: float
    dependency_depth: int
    context_type: str  # runtime | dev | peer | test | optional
    weekly_downloads: int

@dataclass
class ScoringResult:
    context_score: float
    severity_tier: str
    cvss_base: float
    depth_factor: float
    context_multiplier: float
    popularity_factor: float

def compute_score(input: ScoringInput) -> ScoringResult:
    df = depth_factor(input.dependency_depth)
    cm = context_multiplier(input.context_type)
    pf = popularity_factor(input.weekly_downloads)
    
    raw_score = input.cvss_base * df * cm * pf
    final_score = round(min(10.0, raw_score), 2)
    
    return ScoringResult(
        context_score=final_score,
        severity_tier=_score_to_tier(final_score),
        cvss_base=input.cvss_base,
        depth_factor=df,
        context_multiplier=cm,
        popularity_factor=pf,
    )

def _score_to_tier(score: float) -> str:
    if score >= 9.0:
        return "Critical"
    elif score >= 7.0:
        return "High"
    elif score >= 4.0:
        return "Medium"
    else:
        return "Low"
```

### 8.2 Unit Tests

```python
# libs/scoring-engine/tests/test_calculator.py

def test_critical_direct_runtime_popular():
    result = compute_score(ScoringInput(
        cvss_base=9.8, dependency_depth=1,
        context_type="runtime", weekly_downloads=50_000_000
    ))
    assert result.severity_tier == "Critical"
    assert result.context_score >= 9.0

def test_high_cvss_dev_dep_scores_low():
    result = compute_score(ScoringInput(
        cvss_base=8.1, dependency_depth=4,
        context_type="dev", weekly_downloads=100_000
    ))
    assert result.severity_tier == "Low"
    assert result.context_score < 4.0

def test_score_capped_at_ten():
    result = compute_score(ScoringInput(
        cvss_base=10.0, dependency_depth=1,
        context_type="runtime", weekly_downloads=100_000_000
    ))
    assert result.context_score == 10.0

def test_zero_downloads_uses_minimum_factor():
    result = compute_score(ScoringInput(
        cvss_base=9.8, dependency_depth=1,
        context_type="runtime", weekly_downloads=0
    ))
    assert result.popularity_factor == 0.1
```

---

## 9. Calibration & Validation

To validate the scoring model:

1. **Historical CVE dataset:** Select 20 well-known CVEs (log4j, lodash, requests, etc.)
2. **Expert scoring:** Have 3 security engineers manually score 50 repo-CVE pairs
3. **Model comparison:** Compute correlation (Pearson r) between model scores and expert scores
4. **Target:** r ≥ 0.85 before launch
5. **Ongoing calibration:** Quarterly review of expert-vs-model divergence; adjust factors if needed

---

*Last updated: 2026-04-18*
