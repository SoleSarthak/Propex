# 04 — System Architecture
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. Architecture Overview

ODEPM follows an **event-driven microservices** architecture. Components communicate asynchronously via Apache Kafka, with synchronous gRPC for latency-sensitive inter-service calls. All services are containerized and orchestrated on Kubernetes.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SOURCES                                │
│  NVD API │ OSV Webhook │ GitHub Advisory │ npm Registry │ PyPI │ Maven Central│
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
               ┌─────────────────▼──────────────────┐
               │        CVE INGESTION SERVICE         │
               │   (Python/FastAPI + APScheduler)     │
               │  • Polls NVD every 15 min            │
               │  • Consumes OSV webhooks             │
               │  • Normalizes + deduplicates         │
               └─────────────────┬──────────────────┘
                                 │ Kafka: cve.raw
               ┌─────────────────▼──────────────────┐
               │     DEPENDENCY RESOLVER SERVICE      │
               │         (Coordinator)               │
               └──────┬────────────┬───────────┬─────┘
                      │            │            │
          ┌───────────▼──┐ ┌───────▼──┐ ┌──────▼───────┐
          │ npm Resolver │ │   PyPI   │ │    Maven     │
          │  (Node.js)   │ │ Resolver │ │   Resolver   │
          │              │ │ (Python) │ │   (Java)     │
          └───────────┬──┘ └───────┬──┘ └──────┬───────┘
                      └──────────┬─┘           │
                                 │◄────────────┘
                      ┌──────────▼──────────────┐
                      │       NEO4J GRAPH DB      │
                      │  (Dependency + Impact     │
                      │   Graph Storage)          │
                      └──────────┬───────────────┘
                                 │ Kafka: dependency.resolved
               ┌─────────────────▼──────────────────┐
               │         IMPACT ANALYZER              │
               │      (Scoring Engine, Python)        │
               │  • CVSS × Depth × Context × Pop     │
               │  • Stores scores in PostgreSQL       │
               │  • Caches hot scores in Redis        │
               └─────────────────┬──────────────────┘
                                 │ Kafka: impact.scored
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼────────┐   ┌──────────▼──────────┐  ┌────────▼───────────┐
│  LLM PATCH      │   │  GITHUB ISSUE        │  │  NOTIFICATION      │
│  DRAFTER        │   │  CREATOR             │  │  TRACKER           │
│ (LangChain/GPT) │   │ (REST API + RateLimit)│  │ (PostgreSQL write) │
└─────────────────┘   └─────────────────────┘  └────────────────────┘
                                 │
               ┌─────────────────▼──────────────────┐
               │           API GATEWAY                │
               │        (Python/FastAPI)              │
               │  REST + GraphQL BFF                  │
               └─────────────────┬──────────────────┘
                                 │
               ┌─────────────────▼──────────────────┐
               │        REACT DASHBOARD               │
               │  (TypeScript, Cytoscape.js)          │
               └────────────────────────────────────┘
```

---

## 2. Service Catalog

| Service Name            | Language    | Framework          | Responsibility                          |
|-------------------------|-------------|--------------------|-----------------------------------------|
| cve-ingestion           | Python 3.12 | FastAPI + APScheduler | Poll NVD, consume OSV, normalize CVEs |
| dependency-coordinator  | Python 3.12 | FastAPI            | Route resolution tasks to ecosystem workers |
| npm-resolver            | Node.js 20  | Express            | Resolve npm dependency trees            |
| pypi-resolver           | Python 3.12 | FastAPI            | Resolve PyPI dependency trees           |
| maven-resolver          | Java 21     | Spring Boot        | Resolve Maven dependency trees          |
| impact-analyzer         | Python 3.12 | Celery + FastAPI   | Score affected repositories             |
| patch-drafter           | Python 3.12 | FastAPI + LangChain| Generate issue text via LLM            |
| issue-creator           | Python 3.12 | FastAPI            | Create GitHub issues, manage rate limits|
| api-gateway             | Python 3.12 | FastAPI            | Unified public API surface              |
| web-dashboard           | TypeScript  | React 18 + Vite    | User interface for analysts             |

---

## 3. Kafka Topics & Event Schemas

### 3.1 Topic: `cve.raw`
**Producer:** cve-ingestion
**Consumers:** dependency-coordinator

```json
{
  "event_id": "uuid",
  "cve_id": "CVE-2024-12345",
  "source": "nvd|osv|ghsa",
  "published_at": "ISO8601",
  "cvss_score": 9.8,
  "cvss_vector": "CVSS:3.1/...",
  "affected_packages": [
    {
      "ecosystem": "npm|pypi|maven",
      "name": "lodash",
      "versions_affected": [">=4.0.0", "<4.17.21"],
      "fixed_version": "4.17.21"
    }
  ],
  "description": "...",
  "references": ["https://..."]
}
```

### 3.2 Topic: `dependency.resolved`
**Producer:** npm/pypi/maven-resolver
**Consumers:** impact-analyzer

```json
{
  "event_id": "uuid",
  "cve_id": "CVE-2024-12345",
  "ecosystem": "npm",
  "package_name": "lodash",
  "resolution_status": "success|partial|failed",
  "affected_repo_count": 12540,
  "graph_written_at": "ISO8601",
  "sample_repos": ["https://github.com/..."]
}
```

### 3.3 Topic: `impact.scored`
**Producer:** impact-analyzer
**Consumers:** patch-drafter, issue-creator

```json
{
  "event_id": "uuid",
  "cve_id": "CVE-2024-12345",
  "repo_url": "https://github.com/owner/repo",
  "context_score": 8.7,
  "severity_tier": "Critical",
  "dependency_depth": 1,
  "context_type": "runtime",
  "dependency_path": ["my-app", "express", "lodash"],
  "weekly_downloads": 1200000,
  "fixed_version": "4.17.21"
}
```

### 3.4 Topic: `notifications.out`
**Producer:** patch-drafter
**Consumers:** issue-creator

```json
{
  "event_id": "uuid",
  "cve_id": "CVE-2024-12345",
  "repo_url": "https://github.com/owner/repo",
  "issue_title": "[Security] CVE-2024-12345...",
  "issue_body": "## Security Vulnerability Detected\n...",
  "severity_tier": "Critical",
  "labels": ["security", "vulnerability", "auto-generated", "critical"],
  "priority": "immediate|batch"
}
```

---

## 4. Data Architecture

### 4.1 Neo4j Graph Model

```
(:CVE {id, cvss, published_at})
  -[:AFFECTS {versions: [...], fixed_version: "4.17.21"}]->
(:Package {name, ecosystem, version})
  -[:DEPENDS_ON {depth: 2, type: "runtime|dev"}]->
(:Package {name, ecosystem, version})

(:Repository {url, owner, name, stars, weekly_downloads})
  -[:USES {version_spec: "^4.16.0", file: "package.json", depth: 1}]->
(:Package {name, ecosystem, version})
```

**Indexes:**
```cypher
CREATE INDEX pkg_lookup FOR (p:Package) ON (p.name, p.ecosystem, p.version);
CREATE INDEX repo_url FOR (r:Repository) ON (r.url);
CREATE INDEX cve_id FOR (c:CVE) ON (c.id);
```

### 4.2 PostgreSQL Schema (Key Tables)

```sql
-- CVE canonical store
cves (id, cve_id, source, published_at, cvss_score, cvss_vector, description, raw_data)

-- Per-package CVE affected range
cve_affected_packages (id, cve_id→cves, ecosystem, package_name, versions_affected[], fixed_version)

-- Per-repo impact record
affected_repositories (id, cve_affected_package_id, repo_url, repo_owner,
                       dependency_depth, dependency_path[], context_type,
                       context_score, severity_tier, weekly_downloads,
                       notification_status, issue_url, created_at)

-- Notification history
issued_notifications (id, cve_id, repo_url, issue_url, status,
                      created_at, retry_count, error_message)

-- Opt-out registry
opt_out_registry (id, repo_url, github_org, opted_out_at, opted_out_by, reason)

-- API keys
api_keys (id, user_id, key_hash, name, created_at, expires_at, last_used_at, is_active)
```

### 4.3 Redis Cache Structure

| Key Pattern                          | Data                      | TTL      |
|--------------------------------------|---------------------------|----------|
| `cve:{cve_id}`                       | CVE JSON object           | 1 hour   |
| `pkg:{eco}:{name}:{version}`         | Package metadata JSON     | 24 hours |
| `score:{repo_url}:{cve_id}`          | Decimal score             | 1 hour   |
| `issue_text:{cve_id}:{dep_path_hash}`| LLM-generated text        | 7 days   |
| `rate_limit:github:{token_id}`       | Request count             | 1 hour   |
| `opt_out:{repo_url}`                 | "1" if opted out          | 24 hours |

---

## 5. Authentication & Authorization

### 5.1 Dashboard Auth
- GitHub OAuth 2.0 (Authorization Code Flow)
- Session token stored in HTTP-only cookie
- Token refresh every 24 hours

### 5.2 API Auth
- Bearer token in Authorization header
- Key hashed with bcrypt before storage
- Rate limit: 1,000 req/hr per key

### 5.3 Internal Service Auth
- mTLS with certificates managed by cert-manager (Kubernetes)
- Service accounts per namespace
- No shared secrets between services

### 5.4 RBAC

| Role       | Permissions                                           |
|------------|-------------------------------------------------------|
| Viewer     | Read CVEs, packages, repos, notifications             |
| Analyst    | Viewer + export data, mark findings, submit manual CVEs|
| Admin      | Analyst + manage API keys, access settings, view audit log|

---

## 6. Deployment Architecture

### 6.1 Kubernetes Namespaces

```
odepm-ingestion    → cve-ingestion
odepm-resolution   → dependency-coordinator, npm-resolver, pypi-resolver, maven-resolver
odepm-analysis     → impact-analyzer workers
odepm-notification → patch-drafter, issue-creator
odepm-api          → api-gateway
odepm-frontend     → web-dashboard
odepm-platform     → Kafka, Zookeeper (or use Confluent Cloud)
odepm-data         → PostgreSQL, Redis (or use managed services)
odepm-monitoring   → Prometheus, Grafana, Jaeger, OpenSearch
```

### 6.2 Traffic Flow
```
Internet → CloudFront CDN → Nginx Ingress → API Gateway → Internal Services
Internet → CloudFront CDN → S3/CDN → React SPA (static)
```

### 6.3 Managed Services (Production)

| Service      | Provider           | Why Managed vs. Self-hosted |
|--------------|--------------------|------------------------------|
| Kafka        | Confluent Cloud    | Reduced ops overhead         |
| Neo4j        | Neo4j AuraDB       | Graph-optimized hosting      |
| PostgreSQL   | AWS RDS            | Automated backups, Multi-AZ  |
| Redis        | AWS ElastiCache    | Cluster mode, auto-failover  |
| S3           | AWS S3             | Durable object storage       |
| Secrets      | AWS Secrets Manager| Rotation + audit             |

---

## 7. Observability Stack

| Concern        | Tool           | Details                              |
|----------------|----------------|--------------------------------------|
| Metrics        | Prometheus     | Scraped from all services            |
| Dashboards     | Grafana        | Service health, business KPIs        |
| Alerting       | PagerDuty      | On-call via Grafana alert rules      |
| Tracing        | Jaeger         | OpenTelemetry SDK in all services    |
| Logging        | OpenSearch     | Fluent Bit log shipper from K8s      |
| Error Tracking | Sentry         | Python/Node.js/React SDK             |
| Uptime         | Better Uptime  | External synthetic monitoring        |

---

## 8. CI/CD Pipeline

```
Developer Push
     │
     ▼
GitHub Actions
     ├── Lint (flake8, eslint, checkstyle)
     ├── Unit Tests
     ├── Integration Tests (docker-compose)
     ├── Security Scan (Trivy, Bandit)
     ├── Build Docker Images
     └── Push to ECR
          │
          ▼
ArgoCD (GitOps)
     ├── Staging deployment (auto)
     └── Production deployment (manual approval)
```

---

*Last updated: 2026-04-18*
