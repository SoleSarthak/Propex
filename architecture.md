# Architecture Overview
## Open-Source Dependency Exploit Propagation Mapper

---

## 1. System Vision

The Open-Source Dependency Exploit Propagation Mapper (ODEPM) is a distributed platform designed to:

1. **Ingest** newly published CVEs from NVD, OSV, and GitHub Advisory databases.
2. **Resolve** transitive dependency trees across npm, PyPI, and Maven ecosystems.
3. **Map** affected downstream projects by crawling public repository metadata.
4. **Score** exposure severity using usage context (direct vs. transitive, runtime vs. devDependency, call-graph analysis).
5. **Generate** and dispatch automated patch-request issues to affected repository maintainers.

---

## 2. Architectural Style

| Concern              | Pattern                                   |
|----------------------|-------------------------------------------|
| Overall              | Event-Driven Microservices                |
| Data Ingestion       | Pipeline / ETL with streaming             |
| Dependency Analysis  | Graph Database (Neo4j) + Worker Queues    |
| API Layer            | REST + GraphQL (BFF pattern)              |
| Frontend             | React SPA with Server-Side rendering      |
| Deployment           | Kubernetes on GCP / AWS                   |
| Communication        | Apache Kafka (async), gRPC (sync RPC)     |

---

## 3. High-Level Component Map

```
┌──────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SOURCES                         │
│  NVD API │ OSV API │ GitHub Advisories │ npm Registry │ PyPI │ Maven │
└──────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   CVE INGESTION    │
                    │   SERVICE          │
                    │  (Kafka Producer)  │
                    └─────────┬──────────┘
                              │ Kafka Topic: cve.raw
                    ┌─────────▼──────────┐
                    │  DEPENDENCY        │
                    │  RESOLVER SERVICE  │
                    │  (Graph Builder)   │
                    └─────────┬──────────┘
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  npm     │  │  PyPI    │  │  Maven   │
        │  Resolver│  │  Resolver│  │  Resolver│
        └──────┬───┘  └──────┬───┘  └──────┬───┘
               └──────────────┼──────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   NEO4J GRAPH DB   │
                    │  (Dependency Graph)│
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  IMPACT ANALYZER   │
                    │  (Scoring Engine)  │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  NOTIFICATION &    │
                    │  PATCH DRAFTER     │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   GITHUB / GITLAB  │
                    │   ISSUE CREATOR    │
                    └────────────────────┘
```

---

## 4. Core Services

### 4.1 CVE Ingestion Service
- Polls NVD (National Vulnerability Database) API every 15 minutes
- Subscribes to OSV (Open Source Vulnerabilities) webhook feed
- Normalizes CVE data into canonical format
- Publishes to Kafka topic `cve.raw`

### 4.2 Dependency Resolver Service
- Consumes from `cve.raw` Kafka topic
- For each affected package, resolves the full transitive dependency tree
- Queries npm Registry API, PyPI JSON API, Maven Central REST API
- Builds and stores dependency graph nodes/edges in Neo4j
- Publishes resolved graph to `dependency.resolved` Kafka topic

### 4.3 Impact Analyzer (Scoring Engine)
- Consumes `dependency.resolved` events
- Runs CVSS-adjusted scoring with contextual multipliers:
  - Direct vs. transitive dependency depth
  - Runtime vs. devDependency context
  - Download volume / ecosystem popularity
  - Static call-graph reachability (where available)
- Stores scored results in PostgreSQL + caches in Redis

### 4.4 Notification & Patch Drafter
- Consumes high-severity findings from `impact.scored` topic
- Uses LLM (GPT-4o / Gemini) to generate personalized patch-request issue text
- Respects rate limits and maintainer preferences
- Dispatches via GitHub REST API

### 4.5 API Gateway
- REST endpoints for CVE lookup, project impact queries
- GraphQL BFF for the dashboard frontend
- OAuth2 authentication (GitHub OAuth for maintainer actions)

### 4.6 Frontend Dashboard
- React + TypeScript SPA
- Real-time updates via WebSocket / SSE
- Interactive dependency graph visualization (D3.js / Cytoscape.js)
- CVE impact leaderboard and per-project drill-down

---

## 5. Data Stores

| Store        | Technology   | Purpose                                          |
|--------------|--------------|--------------------------------------------------|
| Graph DB     | Neo4j        | Dependency relationship graph                    |
| Relational   | PostgreSQL   | CVE records, projects, scores, users             |
| Cache        | Redis        | Hot CVE lookups, rate-limit counters             |
| Object Store | S3 / GCS     | Raw CVE dumps, SBOM exports, issue templates     |
| Search       | Elasticsearch| Full-text search on CVE descriptions, projects   |
| Message Bus  | Apache Kafka | Async event streaming between services           |

---

## 6. Security Architecture

- All inter-service communication over mTLS
- GitHub tokens stored in HashiCorp Vault / AWS Secrets Manager
- Rate limiting at API Gateway (Kong / Nginx)
- RBAC: read-only analysts vs. write-enabled responders
- Audit log for every automated issue creation action

---

## 7. Scalability Considerations

- Dependency resolver workers are horizontally scalable (stateless)
- Neo4j cluster with read replicas for graph query load
- Kafka partitioned by ecosystem (npm / PyPI / Maven)
- Redis cluster for sub-millisecond cache hits
- CDN for dashboard static assets

---

## 8. Technology Stack Summary

| Layer              | Technology                                    |
|--------------------|-----------------------------------------------|
| Language (Backend) | Python 3.12, Go 1.22                          |
| Language (Frontend)| TypeScript 5, React 18                        |
| Graph DB           | Neo4j 5.x                                     |
| Relational DB      | PostgreSQL 16                                 |
| Cache              | Redis 7                                       |
| Message Bus        | Apache Kafka 3.7                              |
| Container Orch.    | Kubernetes 1.30                               |
| CI/CD              | GitHub Actions + ArgoCD                       |
| Observability      | OpenTelemetry + Grafana + Prometheus + Jaeger  |
| LLM Integration    | OpenAI GPT-4o / Google Gemini 1.5 Pro         |

---

*Last updated: 2026-04-18*
