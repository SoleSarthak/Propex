# MVP Technical Document
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. MVP Scope

End-to-end pipeline: `CVE Published → Ingested → Dependencies Resolved → Affected Repos Found → Scored → Issue Created`

### In Scope
- CVE ingestion from NVD API + OSV Feed
- npm, PyPI, Maven transitive dependency resolution
- Affected GitHub repository discovery
- Contextual severity scoring engine
- LLM-generated patch-request issue text (GPT-4o-mini)
- GitHub issue creation via REST API
- Read-only analyst dashboard (React SPA)
- REST API for query access
- Opt-out registry for maintainers

### Out of Scope
- GitLab, private repos, automated PRs, Go/Cargo/NuGet, SAST/DAST

---

## 2. Tech Stack

### Backend Services

| Service               | Language | Framework       |
|-----------------------|----------|-----------------|
| CVE Ingestion         | Python   | FastAPI + APScheduler |
| npm Resolver          | Node.js  | Express         |
| PyPI Resolver         | Python   | FastAPI         |
| Maven Resolver        | Java 21  | Spring Boot     |
| Scoring Engine        | Python   | Celery          |
| Patch Drafter         | Python   | FastAPI + LangChain |
| API Gateway           | Python   | FastAPI         |

### Data Layer

| Component      | Technology   | Hosted          |
|----------------|--------------|-----------------|
| Graph DB       | Neo4j 5.18   | Neo4j AuraDB    |
| Relational DB  | PostgreSQL 16| AWS RDS         |
| Cache          | Redis 7.2    | ElastiCache     |
| Message Bus    | Kafka 3.7    | Confluent Cloud |
| Object Storage | AWS S3       | AWS             |

### Frontend
React 18 + TypeScript 5, Vite, Zustand, TanStack Query, Cytoscape.js, shadcn/ui, Tailwind CSS

---

## 3. Service Specifications

### 3.1 CVE Ingestion Service

Polls NVD API every 15 min, consumes OSV webhooks, parses GitHub Advisory feed.

**Output Schema (Kafka: `cve.raw`):**
```json
{
  "cve_id": "CVE-2024-12345",
  "source": "nvd|osv|ghsa",
  "published_at": "2024-03-15T10:00:00Z",
  "cvss_score": 9.8,
  "affected_packages": [
    { "ecosystem": "npm", "name": "lodash", "versions_affected": ["<4.17.21"], "fixed_version": "4.17.21" }
  ],
  "description": "Prototype pollution vulnerability..."
}
```

### 3.2 Dependency Resolver (All Ecosystems)

**Algorithm:**
1. Receive affected package from Kafka
2. Fetch all versions from registry API
3. BFS/DFS traverse dependency tree
4. Write nodes + edges to Neo4j
5. Publish to `dependency.resolved` topic

**Neo4j Data Model:**
```cypher
(:Package {name, ecosystem, version}) -[:DEPENDS_ON {depth: 2}]-> (:Package)
(:Repository {url, owner}) -[:USES {version_spec: "^4.17.0"}]-> (:Package)
(:CVE {id, cvss}) -[:AFFECTS {versions: ["<4.17.21"]}]-> (:Package)
```

### 3.3 Scoring Engine

```
Score = CVSS_Base × Depth_Factor × Context_Multiplier × Popularity_Factor

Depth_Factor:      1.0 (direct) | 0.8 (depth 2) | 0.6 (depth 3) | 0.4 (depth 4+)
Context_Multiplier: 1.0 (runtime) | 0.5 (devDependency)
Popularity_Factor:  log10(weekly_downloads) / 10  [capped at 1.0]
Final Score:        min(10.0, Score)
```

| Score Range | Tier     | Action                       |
|-------------|----------|------------------------------|
| 8.0–10.0    | Critical | Immediate issue creation     |
| 6.0–7.9     | High     | Issue within 1 hour          |
| 4.0–5.9     | Medium   | Issue within 24 hours        |
| 1.0–3.9     | Low      | Dashboard notification only  |

### 3.4 LLM Patch Drafter

- Model: `gpt-4o-mini`, Temperature: 0.3, Max tokens: 800
- Fallback: Template-based generation if LLM unavailable
- Generates issue with: CVE ID, CVSS, dependency chain, remediation steps

### 3.5 GitHub Issue Creator

- Rate limit: 5,000 req/hr (authenticated), token rotation pool
- Duplicate prevention via `issued_notifications` table lookup
- Labels applied: `security`, `vulnerability`, `auto-generated`, severity tier

---

## 4. API Endpoints (MVP)

```
GET  /api/v1/cves                             # List CVEs
GET  /api/v1/cves/{cve_id}                    # CVE details
GET  /api/v1/cves/{cve_id}/affected-repos     # Repos affected
GET  /api/v1/packages/{ecosystem}/{name}/dependents
GET  /api/v1/repos/{owner}/{name}/vulnerabilities
POST /api/v1/opt-out                          # Opt out of auto-issues
GET  /api/v1/notifications                    # Notification history
```

---

## 5. Key Database Tables

```sql
CREATE TABLE cves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cve_id VARCHAR(20) UNIQUE NOT NULL,
    source VARCHAR(10), published_at TIMESTAMPTZ,
    cvss_score DECIMAL(3,1), description TEXT, raw_data JSONB
);

CREATE TABLE affected_repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cve_affected_package_id UUID,
    repo_url TEXT, repo_owner TEXT,
    dependency_depth INTEGER, dependency_path TEXT[],
    context_type VARCHAR(20), context_score DECIMAL(3,1),
    notification_status VARCHAR(20) DEFAULT 'pending',
    issue_url TEXT
);

CREATE TABLE opt_out_registry (
    id UUID PRIMARY KEY, repo_url TEXT NOT NULL,
    opted_out_at TIMESTAMPTZ DEFAULT NOW(), reason TEXT
);
```

---

## 6. Dev Environment Setup

```bash
git clone https://github.com/org/odepm && cd odepm
docker-compose up -d

# Endpoints:
# API Gateway:   http://localhost:8000
# Dashboard:     http://localhost:3000
# Neo4j:         http://localhost:7474
# Kafka UI:      http://localhost:8080
```

---

## 7. MVP Acceptance Criteria

| Criterion                                    | Pass Condition                        |
|----------------------------------------------|---------------------------------------|
| NVD CVE ingestion                            | Appears in DB within 15 min           |
| npm transitive resolution (lodash)           | Returns 500+ dependent packages       |
| Context score computed                       | Score 1–10, matches formula           |
| LLM issue text generated                     | Coherent, includes CVE + dep path     |
| GitHub issue created                         | Visible on GitHub within 2 min        |
| Dashboard renders CVE list                   | No errors, accurate data              |
| Opt-out prevents issue creation              | No issue after opt-out registered     |

---

*Last updated: 2026-04-18*
