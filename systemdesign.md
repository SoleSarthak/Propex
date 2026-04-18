# System Design Document
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. System Overview

ODEPM is an event-driven distributed system that continuously tracks CVE publications and maps their propagation through open-source dependency trees to affected downstream repositories. It then scores exposure severity and dispatches automated, context-aware patch-request issues to maintainers.

---

## 2. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            DATA SOURCES                                  │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│  │ NVD API  │  │ OSV Feed │  │ GitHub Advisory │  │ npm/PyPI/Maven   │ │
│  └────┬─────┘  └────┬─────┘  └────────┬────────┘  └────────┬─────────┘ │
└───────┼─────────────┼─────────────────┼───────────────────┼────────────┘
        │             │                 │                   │
┌───────▼─────────────▼─────────────────▼───────────────────▼────────────┐
│                    INGESTION LAYER                                        │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │          CVE Ingestion Service (Python / FastAPI)                │    │
│  │  - Polls NVD every 15 min    - Consumes OSV webhooks            │    │
│  │  - Deduplicates CVEs         - Normalizes to canonical schema    │    │
│  └──────────────────────────────┬───────────────────────────────────┘    │
└─────────────────────────────────┼──────────────────────────────────────  ┘
                                  │  Kafka Topic: cve.raw
┌─────────────────────────────────▼────────────────────────────────────────┐
│                    RESOLUTION LAYER                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │  npm Resolver   │  │  PyPI Resolver  │  │    Maven Resolver       │   │
│  │  (Node.js)      │  │  (Python)       │  │    (Java/Spring)        │   │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────────┘   │
│           └───────────────────┬┘                      │                  │
│                               └──────────┬────────────┘                  │
└──────────────────────────────────────────┼───────────────────────────────┘
                                           │  Neo4j Graph DB
┌──────────────────────────────────────────▼───────────────────────────────┐
│                    ANALYSIS LAYER                                          │
│  ┌──────────────────────────────────────────────────────────────────┐     │
│  │              Impact Analyzer / Scoring Engine (Python)           │     │
│  │  - CVSS-adjusted contextual scoring                              │     │
│  │  - Depth, runtime context, popularity factors                    │     │
│  │  - Ranks affected repos by severity tier                         │     │
│  └──────────────────────────────┬───────────────────────────────────┘     │
└─────────────────────────────────┼──────────────────────────────────────── ┘
                                  │  Kafka Topic: impact.scored
┌─────────────────────────────────▼────────────────────────────────────────┐
│                    NOTIFICATION LAYER                                      │
│  ┌──────────────────────────┐  ┌──────────────────────────────────────┐   │
│  │   LLM Patch Drafter      │  │   GitHub Issue Creator               │   │
│  │   (LangChain + GPT-4o)   │  │   (REST API + Rate Limiter)         │   │
│  └──────────────────────────┘  └──────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────────┐
│                    API & PRESENTATION LAYER                                │
│  ┌──────────────────────────┐  ┌──────────────────────────────────────┐   │
│  │   REST API Gateway       │  │   React Dashboard                    │   │
│  │   (FastAPI)              │  │   (Cytoscape.js + shadcn/ui)        │   │
│  └──────────────────────────┘  └──────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Deep Dives

### 3.1 CVE Ingestion Service

**Design decisions:**
- APScheduler for cron-like polling (lightweight, no Airflow needed in MVP)
- Webhook endpoint for OSV push notifications reduces ingestion latency to near-zero
- Canonical CVE schema eliminates downstream parsing complexity

**Failure handling:**
- NVD API is unreliable; implement retry with exponential backoff
- Store raw responses in S3 for replay capability
- Dead-letter queue (DLQ) for malformed CVE payloads

### 3.2 Dependency Resolution

**npm Strategy:**
- Use `GET https://registry.npmjs.org/{pkg}` to get all version metadata
- Identify reverse dependencies (who depends on this package) via:
  1. npm `dependents` search API (limited)
  2. Pre-built reverse-dependency index from libraries.io (preferred)
  3. GitHub code search API for `package.json` files containing the package

**PyPI Strategy:**
- `GET https://pypi.org/pypi/{package}/json` for package metadata
- `GET https://pypi.org/simple/{package}/` for all versions
- Reverse dependency lookup via libraries.io or PyPI dependency index

**Maven Strategy:**
- Maven Central REST API: `GET https://search.maven.org/solrsearch/select?q=...`
- Parse `pom.xml` dependency declarations
- Use `mvn dependency:tree` (via process invocation) for accurate transitive resolution

**Graph Storage in Neo4j:**
- Nodes: `Package`, `Repository`, `CVE`
- Edges: `DEPENDS_ON`, `USES`, `AFFECTS`
- Indexes on `Package.name + Package.ecosystem + Package.version`

### 3.3 Scoring Engine

**Architecture:** Celery workers consuming from `dependency.resolved` Kafka topic

**Score computation pipeline:**
1. Fetch CVSS score from CVE record
2. Determine dependency depth from Neo4j path length
3. Determine context type (runtime vs. dev) from dependency file
4. Fetch weekly download count from package registry
5. Apply formula → store in PostgreSQL, cache in Redis (TTL: 1 hour)

### 3.4 LLM Patch Drafter

**Prompt engineering:**
- System prompt establishes security researcher persona
- Few-shot examples in system prompt for consistent formatting
- Structured output with sections: Summary, Dependency Path, Remediation, References

**Cost control:**
- Use `gpt-4o-mini` for < $0.01 per issue
- Cache identical CVE + dependency_path combos (different repos, same path)
- Hard limit of 1,000 issues/day in MVP

### 3.5 GitHub Issue Creator

**Deduplication strategy:**
1. Check `issued_notifications` table before creating
2. Search existing GitHub issues on target repo for our CVE label
3. Only create if not found in either

**Batch processing:**
- Process high-severity (Critical/High) repos immediately
- Medium/Low batched and dispatched at 2 AM local time (reduced noise)

---

## 4. Data Flow

### 4.1 Happy Path Flow

```
1. NVD publishes CVE-2024-XXXXX at T=0
2. Ingestion service polls at T+15min, discovers CVE
3. Normalizes and publishes to Kafka `cve.raw` at T+15min
4. npm Resolver consumes, fetches dependency tree (T+15 to T+20min)
5. Writes 50,000 affected packages to Neo4j
6. Publishes to `dependency.resolved` at T+20min
7. Scoring Engine consumes, computes scores for 3,000 repos (T+20 to T+25min)
8. 200 repos flagged Critical/High
9. LLM Drafter generates 200 issue texts (T+25 to T+30min)
10. GitHub Issue Creator dispatches (T+30 to T+45min, respecting rate limits)
11. Maintainers begin receiving issues at T+30min
```

### 4.2 Data Partitioning Strategy

| Kafka Topic         | Partition Key  | Partitions |
|---------------------|----------------|------------|
| `cve.raw`           | ecosystem      | 3          |
| `dependency.resolved`| ecosystem     | 3          |
| `impact.scored`     | severity_tier  | 4          |
| `notifications.out` | repo_owner     | 10         |

---

## 5. Scalability Design

### 5.1 Horizontal Scaling

| Component            | Scaling Strategy                      | Max Instances |
|----------------------|---------------------------------------|---------------|
| CVE Ingestion        | Single instance (low volume)          | 1             |
| npm Resolver workers | Add workers per Kafka partition       | 20            |
| Scoring Engine       | Celery autoscale based on queue depth | 50            |
| API Gateway          | K8s HPA based on CPU/RPS             | 10            |
| GitHub Issue Creator | Single instance (rate-limited)        | 1 per token   |

### 5.2 Caching Strategy

| Data             | Cache Key                     | TTL      | Invalidation        |
|------------------|-------------------------------|----------|---------------------|
| Package metadata | `pkg:{ecosystem}:{name}:{ver}`| 24 hours | New version publish |
| CVE details      | `cve:{cve_id}`                | 1 hour   | CVE update event    |
| Severity score   | `score:{repo}:{cve_id}`       | 1 hour   | Score recomputed    |
| LLM issue text   | `issue:{cve_id}:{dep_path}`   | 7 days   | Never (immutable)   |

---

## 6. Reliability & Resilience

### 6.1 Circuit Breakers

Apply circuit breakers on:
- npm Registry API calls
- PyPI API calls
- Maven Central API calls
- GitHub API calls
- LLM API calls (fallback to template)

### 6.2 Retry Policies

| Operation          | Max Retries | Backoff           |
|--------------------|-------------|-------------------|
| NVD API poll       | 5           | Exponential + jitter |
| Package registry   | 3           | 1s, 5s, 30s       |
| Neo4j write        | 3           | 500ms, 2s, 10s    |
| GitHub API         | 3           | Respects Retry-After |
| LLM API            | 2           | 5s, 30s           |

### 6.3 Dead Letter Queues

- `cve.raw.dlq` — failed CVE processing
- `dependency.resolved.dlq` — failed resolution
- `notifications.dlq` — failed issue creation (retry next day)

---

## 7. Security Design

### 7.1 Secrets Management
- All API keys in AWS Secrets Manager
- Rotation every 90 days
- No secrets in environment variables or config files

### 7.2 Authentication & Authorization
- Dashboard: GitHub OAuth2
- API: JWT Bearer tokens, 24-hour expiry
- Internal services: mTLS (cert-manager + Istio)

### 7.3 Data Privacy
- No storage of repository source code
- Only dependency manifest file paths stored
- Maintainer email addresses never stored

---

## 8. Observability

### 8.1 Key Metrics

| Metric                             | Alert Threshold        |
|------------------------------------|------------------------|
| CVE ingestion lag                  | > 20 minutes           |
| Dependency resolution queue depth  | > 10,000 messages      |
| Scoring engine throughput          | < 100 repos/min        |
| GitHub API error rate              | > 5%                   |
| LLM API error rate                 | > 10%                  |

### 8.2 Distributed Tracing
- All services instrument with OpenTelemetry
- Trace ID propagated through Kafka message headers
- Jaeger for trace visualization

### 8.3 Structured Logging
```json
{
  "timestamp": "2024-03-15T10:30:00Z",
  "service": "cve-ingestion",
  "level": "INFO",
  "trace_id": "abc123",
  "event": "cve_ingested",
  "cve_id": "CVE-2024-12345",
  "source": "nvd",
  "latency_ms": 142
}
```

---

## 9. Deployment Architecture

### 9.1 Kubernetes Namespaces
- `odepm-ingestion` — CVE ingestion service
- `odepm-resolution` — npm/PyPI/Maven resolvers
- `odepm-analysis` — Scoring engine
- `odepm-notification` — Patch drafter + Issue creator
- `odepm-api` — API gateway
- `odepm-frontend` — React dashboard
- `odepm-data` — Kafka, databases (or managed services)
- `odepm-monitoring` — Grafana, Prometheus, Jaeger

### 9.2 Resource Requests

| Service             | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------------------|-------------|-----------|----------------|--------------|
| CVE Ingestion       | 100m        | 500m      | 256Mi          | 512Mi        |
| npm Resolver        | 200m        | 1000m     | 512Mi          | 1Gi          |
| PyPI Resolver       | 200m        | 1000m     | 512Mi          | 1Gi          |
| Maven Resolver      | 500m        | 2000m     | 1Gi            | 2Gi          |
| Scoring Engine      | 200m        | 1000m     | 512Mi          | 1Gi          |
| Patch Drafter       | 100m        | 500m      | 256Mi          | 512Mi        |
| API Gateway         | 200m        | 1000m     | 512Mi          | 1Gi          |

---

*Last updated: 2026-04-18*
