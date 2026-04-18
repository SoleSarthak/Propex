# 12 — Testing Strategy
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. Testing Philosophy

ODEPM follows the **Testing Trophy** approach (Kent C. Dodds), emphasizing:
1. **Integration tests** as the primary quality signal — test real service interactions
2. **Unit tests** for pure business logic (scoring engine, normalizers, parsers)
3. **E2E tests** for critical user flows
4. **Avoid mocking at the boundary** — prefer real external services in integration tests

**Coverage Targets:**

| Test Level    | Target Coverage | Tool                         |
|---------------|-----------------|------------------------------|
| Unit          | ≥ 90%           | pytest, Jest, JUnit          |
| Integration   | ≥ 75%           | pytest, Testcontainers       |
| E2E           | Critical paths  | Playwright                   |
| Performance   | Key endpoints   | k6                           |
| Security      | OWASP Top 10    | OWASP ZAP, Bandit, Trivy     |

---

## 2. Unit Tests

### 2.1 Python Services (pytest)

**Framework:** pytest 8.x + pytest-asyncio + pytest-cov + hypothesis

**Location:** `services/{service}/tests/unit/`

**Key test suites:**

#### Scoring Engine (`libs/scoring-engine`)
```python
# tests/test_calculator.py

@pytest.mark.parametrize("depth,expected", [
    (1, 1.00), (2, 0.85), (3, 0.70), (4, 0.55), (5, 0.40), (10, 0.40)
])
def test_depth_factor(depth, expected):
    assert depth_factor(depth) == expected

@pytest.mark.parametrize("context,expected", [
    ("runtime", 1.00), ("dev", 0.50), ("test", 0.30), ("peer", 0.90)
])
def test_context_multiplier(context, expected):
    assert context_multiplier(context) == expected

@pytest.mark.parametrize("downloads,expected_min,expected_max", [
    (0, 0.0, 0.2),
    (100, 0.2, 0.4),
    (1_000_000, 0.6, 0.8),
    (100_000_000, 0.95, 1.0),
])
def test_popularity_factor_range(downloads, expected_min, expected_max):
    f = popularity_factor(downloads)
    assert expected_min <= f <= expected_max

def test_score_never_exceeds_ten():
    result = compute_score(ScoringInput(
        cvss_base=10.0, dependency_depth=1,
        context_type="runtime", weekly_downloads=999_999_999
    ))
    assert result.context_score <= 10.0

# Property-based test with Hypothesis
@given(
    cvss=st.floats(min_value=0.0, max_value=10.0),
    depth=st.integers(min_value=1, max_value=20),
    downloads=st.integers(min_value=0, max_value=100_000_000)
)
def test_score_always_valid(cvss, depth, downloads):
    result = compute_score(ScoringInput(
        cvss_base=cvss, dependency_depth=depth,
        context_type="runtime", weekly_downloads=downloads
    ))
    assert 0.0 <= result.context_score <= 10.0
    assert result.severity_tier in ("Critical", "High", "Medium", "Low")
```

#### CVE Normalizer (`services/cve-ingestion`)
```python
# tests/unit/test_normalizer.py

def test_nvd_cve_normalized_correctly():
    raw_nvd = load_fixture("nvd_cve_sample.json")
    result = NvdNormalizer().normalize(raw_nvd)
    
    assert result.cve_id == "CVE-2024-12345"
    assert result.source == "nvd"
    assert 0.0 <= result.cvss_score <= 10.0
    assert len(result.affected_packages) > 0
    assert all(p.ecosystem in ("npm", "pypi", "maven") for p in result.affected_packages)

def test_deduplication_prefers_newer_source():
    existing = CveRecord(cve_id="CVE-2024-12345", source="nvd", published_at=datetime(2024,1,1))
    incoming = CveRecord(cve_id="CVE-2024-12345", source="osv", published_at=datetime(2024,1,2))
    
    result = dedup_cve(existing, incoming)
    assert result.source == "nvd"          # nvd takes precedence
    assert result.last_modified_at is not None

def test_cvss_missing_defaults_to_medium():
    raw = {"cveId": "CVE-2024-99999", "metrics": {}}
    result = NvdNormalizer().normalize(raw)
    assert result.cvss_score == 5.0
```

#### Version Range Checker (`services/npm-resolver`)
```typescript
// tests/unit/versionRangeChecker.test.ts

describe("isVersionVulnerable", () => {
  it("returns true when version is within vulnerable range", () => {
    expect(isVersionVulnerable("4.16.0", ["<4.17.21"])).toBe(true);
  });

  it("returns false when version is fixed", () => {
    expect(isVersionVulnerable("4.17.21", ["<4.17.21"])).toBe(false);
  });

  it("handles complex range with lower bound", () => {
    expect(isVersionVulnerable("4.5.0", [">=4.0.0", "<4.17.21"])).toBe(true);
    expect(isVersionVulnerable("3.99.0", [">=4.0.0", "<4.17.21"])).toBe(false);
  });

  it("handles wildcard specs", () => {
    expect(isVersionVulnerable("1.2.3", ["*"])).toBe(true);
  });
});
```

---

## 3. Integration Tests

### 3.1 Strategy

Integration tests run against **real infrastructure** via Testcontainers (Python/Java) or Docker Compose (Node.js). They test:
- Service → database interactions
- Service → Kafka interactions (produce + consume)
- Service → external API interactions (mocked with WireMock / MSW)

**Location:** `services/{service}/tests/integration/`

### 3.2 CVE Ingestion Integration Tests

```python
# tests/integration/test_nvd_ingestion.py

@pytest.mark.integration
class TestNvdIngestion:
    
    async def test_polls_nvd_and_persists_new_cve(
        self, db_session, kafka_consumer, mock_nvd_api
    ):
        # Arrange: mock NVD returns 1 new CVE
        mock_nvd_api.return_value = load_fixture("nvd_single_cve.json")
        
        # Act: trigger polling job
        await run_nvd_poll_job()
        
        # Assert: CVE in PostgreSQL
        cve = await db_session.execute(
            select(CVE).where(CVE.cve_id == "CVE-2024-12345")
        )
        assert cve is not None
        assert cve.cvss_score == 9.8
        
        # Assert: event published to Kafka
        message = await kafka_consumer.poll(timeout=5.0)
        assert message is not None
        assert message.value["cve_id"] == "CVE-2024-12345"

    async def test_duplicate_cve_is_not_republished(
        self, db_session, kafka_consumer, mock_nvd_api
    ):
        # Pre-seed: CVE already exists
        await db_session.add(CVE(cve_id="CVE-2024-12345", source="nvd"))
        
        # Run poll twice
        await run_nvd_poll_job()
        await run_nvd_poll_job()
        
        # Only 1 Kafka message
        messages = await kafka_consumer.poll_all(timeout=3.0)
        assert len(messages) == 1
```

### 3.3 npm Resolver Integration Tests

```typescript
// tests/integration/npmRegistryClient.test.ts

describe("npmRegistryClient integration", () => {
  it("resolves direct dependents of lodash", async () => {
    // Uses WireMock stub of npm registry
    const client = new NpmRegistryClient();
    const dependents = await client.getDirectDependents("lodash", "4.17.20");
    
    expect(dependents.length).toBeGreaterThan(10);
    expect(dependents).toContainEqual(
      expect.objectContaining({ name: "express" })
    );
  });

  it("writes package graph to Neo4j", async () => {
    const writer = new GraphWriter(testNeo4jDriver);
    await writer.writePackageDependency({
      from: "express@4.18.0",
      to: "lodash@4.16.6",
      depth: 1,
      type: "runtime"
    });
    
    const result = await testNeo4jDriver.session().run(
      "MATCH (a:Package)-[r:DEPENDS_ON]->(b:Package) RETURN r.depth",
      {}
    );
    expect(result.records[0].get("r.depth")).toBe(1);
  });
});
```

### 3.4 Scoring Engine Integration Tests

```python
@pytest.mark.integration
async def test_full_scoring_pipeline(
    db_session, neo4j_session, redis_client, kafka_consumer
):
    # Arrange: seed CVE + resolution data
    cve = await seed_cve(db_session, cvss=9.8, ecosystem="npm", package="lodash")
    await seed_neo4j_graph(neo4j_session, repo="github.com/vercel/next.js", depth=2)
    await redis_client.set("pkg:downloads:npm:lodash", "50000000")
    
    # Act: run impact analyzer
    await run_impact_analyzer_for_cve(cve.cve_id)
    
    # Assert: score stored in DB
    record = await db_session.execute(
        select(AffectedRepository)
        .where(AffectedRepository.repo_url == "https://github.com/vercel/next.js")
    )
    assert record.context_score > 0
    assert record.severity_tier in ("Critical", "High", "Medium", "Low")
    assert record.depth_factor is not None
    
    # Assert: Kafka event published for High+ repos
    if record.severity_tier in ("Critical", "High"):
        msg = await kafka_consumer.poll(timeout=5.0, topic="impact.scored")
        assert msg.value["repo_url"] == "https://github.com/vercel/next.js"
```

---

## 4. End-to-End Tests

### 4.1 Framework

**Tool:** Playwright 1.44 (TypeScript)  
**Location:** `apps/web-dashboard/tests/e2e/`  
**Environment:** Staging (seeded with known test data)

### 4.2 Critical User Flows

#### Flow 1: Analyst Triage a New CVE

```typescript
// tests/e2e/cve-triage.spec.ts

test("analyst can find and triage a new critical CVE", async ({ page }) => {
  await page.goto("https://staging.odepm.io");
  
  // Login with GitHub (using test account)
  await page.click('[data-testid="login-github-btn"]');
  await githubLogin(page, TEST_GITHUB_CREDENTIALS);
  
  // Navigate to CVEs page
  await page.click('[data-testid="nav-cves"]');
  await expect(page).toHaveURL(/\/cves/);
  
  // Filter to Critical only
  await page.click('[data-testid="filter-severity-critical"]');
  await expect(page.locator('[data-testid="cve-card"]')).toHaveCount(expect.greaterThan(0));
  
  // Click first CVE
  await page.locator('[data-testid="cve-card"]').first().click();
  
  // Verify CVE detail page
  await expect(page.locator('[data-testid="cve-id"]')).toBeVisible();
  await expect(page.locator('[data-testid="cvss-score"]')).toBeVisible();
  await expect(page.locator('[data-testid="affected-repos-table"]')).toBeVisible();
  
  // Export CSV
  await page.click('[data-testid="export-csv-btn"]');
  await expect(page.locator('[data-testid="export-success-toast"]')).toBeVisible();
});
```

#### Flow 2: Maintainer Opts Out

```typescript
test("maintainer can opt out via opt-out page", async ({ page }) => {
  await page.goto("https://staging.odepm.io/opt-out");
  
  await page.click('[data-testid="github-oauth-btn"]');
  await githubLogin(page, TEST_MAINTAINER_CREDENTIALS);
  
  // Select a repo to opt out
  await page.click('[data-testid="repo-toggle-my-test-lib"]');
  await page.click('[data-testid="save-opt-out-btn"]');
  
  await expect(page.locator('[data-testid="opt-out-success"]')).toBeVisible();
  
  // Verify via API
  const response = await fetch(`${API_BASE}/opt-out`, {
    headers: { Authorization: `Bearer ${TEST_API_KEY}` }
  });
  const data = await response.json();
  expect(data.data.some(o => o.scope_value.includes("my-test-lib"))).toBe(true);
});
```

#### Flow 3: API Key Usage

```typescript
test("API key authenticates successfully and respects rate limit", async ({ request }) => {
  const response = await request.get(`${API_BASE}/cves`, {
    headers: { Authorization: `Bearer ${TEST_API_KEY}` }
  });
  expect(response.status()).toBe(200);
  expect(response.headers()["x-ratelimit-limit"]).toBe("1000");
});
```

---

## 5. Performance Tests

### 5.1 Tool: k6

**Location:** `tests/performance/`

### 5.2 Load Test: API Gateway

```javascript
// tests/performance/api-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp to 100 users
    { duration: '5m', target: 1000 },  // Peak: 1000 concurrent users
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
  },
};

export default function () {
  // CVE list (most frequent endpoint)
  const r1 = http.get(`${API_BASE}/api/v1/cves?page=1&per_page=25`, {
    headers: { Authorization: `Bearer ${API_KEY}` }
  });
  check(r1, { 'status 200': (r) => r.status === 200 });
  
  sleep(1);
  
  // CVE detail
  const r2 = http.get(`${API_BASE}/api/v1/cves/${KNOWN_CVE_ID}`, {
    headers: { Authorization: `Bearer ${API_KEY}` }
  });
  check(r2, { 'status 200': (r) => r.status === 200 });
  
  sleep(1);
}
```

### 5.3 Throughput Test: Kafka Pipeline

```python
# tests/performance/test_kafka_throughput.py

def test_pipeline_handles_500k_events_per_day():
    """
    Publish 500K simulated CVE raw events to Kafka.
    Verify all are consumed and scored within 24 hours.
    This test runs in performance environment only.
    """
    events_per_second = 500_000 / 86_400  # ~5.8 events/sec
    
    producer = KafkaProducer(...)
    for i in range(10_000):  # 10K test events (scaled down, 50x)
        producer.send("cve.raw", value=generate_test_cve_event(i))
    
    # Wait for processing (scaled: 10K events should finish in ~30 min)
    wait_for_processing(expected_count=10_000, timeout_minutes=30)
    
    # Assert all records appear in DB
    count = db.execute("SELECT COUNT(*) FROM affected_repositories").scalar()
    assert count >= 10_000
```

---

## 6. Security Tests

### 6.1 OWASP ZAP API Scan

Run in CI against staging environment:

```bash
# .github/workflows/security-scan.yml

- name: OWASP ZAP API Scan
  uses: zaproxy/action-api-scan@v0.7
  with:
    target: 'https://staging.odepm.io/api/docs'  # OpenAPI spec URL
    rules_file_name: '.zap/rules.tsv'
    fail_action: true
    cmd_options: '-a'
```

**ZAP rules applied:**
- SQL injection
- XSS (Reflected + Stored)
- SSRF (Server-Side Request Forgery)
- Authentication bypass
- Insecure direct object reference (IDOR)

### 6.2 Bandit Python SAST

```bash
# Run on all Python service code
bandit -r services/ libs/ -ll -f json -o bandit-report.json
```

**Fail CI on:**
- Any HIGH severity finding
- Any MEDIUM finding with HIGH confidence

### 6.3 Trivy Container Scanning

```bash
# Scan all built images
trivy image --severity CRITICAL,HIGH --exit-code 1 \
  odepm/cve-ingestion:$TAG
```

### 6.4 Secret Detection

```bash
# truffleHog scans for accidentally committed secrets
trufflehog git file://. --only-verified
```

### 6.5 Manual Penetration Testing Checklist

Run by security engineer before production launch:

| Test                                   | Tool/Method               | Expected Result        |
|----------------------------------------|---------------------------|------------------------|
| Auth bypass via JWT manipulation       | Burp Suite                | 401 Unauthorized       |
| API key brute force                    | Burp Intruder             | 429 after 10 attempts  |
| SQL injection in CVE ID param          | sqlmap                    | No injection possible  |
| SSRF via repository URL field          | Manual                    | Request blocked         |
| IDOR: access another user's API keys   | Manual                    | 403 Forbidden          |
| GitHub OAuth CSRF                      | Manual state param check  | CSRF token validated   |
| Rate limit bypass (IP rotation)        | Manual                    | Rate limit enforced    |

---

## 7. Test Data Management

### 7.1 Fixtures

**Python fixtures** (`tests/fixtures/`):
- `nvd_cve_sample.json` — Real NVD CVE response (lodash prototype pollution)
- `osv_advisory_sample.json` — Real OSV advisory
- `npm_registry_lodash.json` — Real npm registry response for lodash
- `dependency_graph_small.cypher` — Small 50-node Neo4j graph for unit tests
- `dependency_graph_large.cypher` — 5,000-node graph for performance tests

**TypeScript fixtures** (`apps/web-dashboard/tests/fixtures/`):
- `cve-list-response.json` — Mock API CVE list
- `cve-detail-response.json` — Mock API CVE detail

### 7.2 Test Database Seeding

```python
# scripts/seed-db.py

SEED_CVES = [
    # Real CVEs for realistic testing
    "CVE-2021-44228",  # Log4Shell (log4j) — Critical 10.0
    "CVE-2021-23337",  # lodash prototype pollution
    "CVE-2022-42969",  # py library ReDoS
    "CVE-2023-44270",  # PostCSS line return parsing error
]

async def seed():
    for cve_id in SEED_CVES:
        cve = await fetch_from_nvd(cve_id)
        await db.insert_cve(cve)
        await trigger_resolution(cve)
    
    print(f"Seeded {len(SEED_CVES)} CVEs with dependency resolution")
```

---

## 8. Testing Pyramid Summary

```
                      ┌─────────────────┐
                      │   E2E Tests     │  8 critical user flows
                      │   (Playwright)  │  Run: staging, on-demand
                      └────────┬────────┘
                 ┌─────────────▼──────────────┐
                 │    Integration Tests        │  ~120 tests
                 │  (pytest + Testcontainers)  │  Run: CI + PR
                 └─────────────┬──────────────┘
          ┌──────────────────────▼──────────────────────┐
          │              Unit Tests                      │  ~400 tests
          │  (pytest + Jest + JUnit + Hypothesis)        │  Run: CI + pre-commit
          └──────────────────────────────────────────────┘
```

---

## 9. Test Coverage Reporting

- **Python:** `pytest-cov` → XML report → Codecov
- **TypeScript:** Vitest coverage → LCOV → Codecov
- **Java:** JaCoCo → XML → Codecov
- **Dashboard:** Codecov shows per-file coverage on PR diffs
- **Gate:** PRs to `main` blocked if coverage drops by > 2%

---

*Last updated: 2026-04-18*
