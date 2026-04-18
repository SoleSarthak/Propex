# 09 — Engineering Scope Definition
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. Overview

This document defines the precise engineering scope for the ODEPM MVP, breaking down what each team is responsible for building, estimated effort, and explicit in/out-of-scope boundaries for each component.

---

## 2. Team Structure

| Team             | Responsibility                                        | Size |
|------------------|-------------------------------------------------------|------|
| Platform Team    | Infrastructure, K8s, CI/CD, observability             | 2 SRE + 1 DevOps |
| Backend Team     | All Python/Java/Node.js services, Kafka, databases    | 4 BE engineers |
| Frontend Team    | React dashboard, design system                        | 2 FE engineers |
| ML/AI Team       | Scoring engine, LLM prompt engineering                | 1 engineer |
| Security Team    | Auth, secrets management, audit logging               | 1 engineer |

---

## 3. Component-Level Scope

### 3.1 CVE Ingestion Service

**Owner:** Backend Team
**Effort Estimate:** 5 engineering days

#### In Scope
- Poll NVD API (`/rest/json/cves/2.0`) with configurable interval (default 15 min)
- Receive OSV advisory webhooks via FastAPI endpoint
- Parse GitHub Security Advisory GraphQL feed
- Normalize all sources to canonical `CveRecord` Pydantic model
- Deduplicate CVEs by CVE ID (upsert pattern in PostgreSQL)
- Publish valid CVE events to Kafka topic `cve.raw`
- Store raw API responses to S3 for replay
- Health check and readiness endpoints
- Dead-letter queue (DLQ) handling for malformed events
- Structured logging + OpenTelemetry tracing

#### Out of Scope
- OVAL / CVRF / CVSS format parsing (use NIST-normalized data only)
- MITRE CVE List direct parsing
- CVE enrichment with exploit data (Phase 2)
- Custom CVE feed plugin system (Phase 2)

---

### 3.2 Dependency Coordinator Service

**Owner:** Backend Team
**Effort Estimate:** 2 engineering days

#### In Scope
- Consume events from `cve.raw` Kafka topic
- Route each affected package to the appropriate ecosystem resolver (npm/PyPI/Maven)
- Track resolution status per CVE in PostgreSQL
- Aggregate completion across all ecosystem resolvers
- Publish summary event when all ecosystems resolved

#### Out of Scope
- Resolution logic itself (each resolver service owns that)
- Priority queue management (use Kafka partition ordering)

---

### 3.3 npm Resolver Service

**Owner:** Backend Team
**Effort Estimate:** 8 engineering days

#### In Scope
- Consume from `cve.raw` Kafka topic (npm packages only)
- Fetch reverse dependency index from libraries.io API (who depends on this package)
- For each dependent, fetch `package.json` and identify dependency context
- BFS traversal of dependency tree up to depth 10
- Version range overlap checking (semver)
- Write package nodes and `DEPENDS_ON` / `USES` edges to Neo4j
- Cache resolved package trees in Redis (TTL: 24 hours)
- Handle npm Registry rate limits (exponential backoff, token auth)
- Publish resolved events to `dependency.resolved` Kafka topic

#### Out of Scope
- npm audit API integration (uses registry metadata only)
- Yarn/pnpm lock file parsing (Phase 2)
- Private npm registry support (Phase 2)
- `node_modules` directory analysis (Phase 2)

---

### 3.4 PyPI Resolver Service

**Owner:** Backend Team
**Effort Estimate:** 7 engineering days

#### In Scope
- Consume from `cve.raw` Kafka topic (PyPI packages only)
- Fetch reverse dependency data from PyPI JSON API + libraries.io
- Parse `install_requires`, `extras_require`, `tests_require` from `setup.py` / `pyproject.toml`
- Handle PEP 508 version specifiers (e.g., `requests>=2.0,<3.0`)
- BFS traversal of dependency tree up to depth 10
- Write to Neo4j (same schema as npm resolver)
- Cache and rate limit handling (same pattern as npm)
- Publish to `dependency.resolved`

#### Out of Scope
- Conda / conda-forge packages
- `requirements.in` (pip-tools source) compilation
- Virtual environment scanning

---

### 3.5 Maven Resolver Service

**Owner:** Backend Team
**Effort Estimate:** 10 engineering days (Java complexity)

#### In Scope
- Consume from `cve.raw` Kafka topic (Maven artifacts only)
- Query Maven Central Search API for dependent artifacts
- Parse `pom.xml` dependency declarations (groupId:artifactId:version)
- Handle Maven version ranges and properties (`${version}`)
- Handle BOM (Bill of Materials) imports
- Resolve dependency scopes: compile, runtime, test, provided, import
- BFS traversal up to depth 10
- Write to Neo4j
- Cache and rate limit handling
- Publish to `dependency.resolved`

#### Out of Scope
- Gradle build script parsing (Phase 2)
- Kotlin DSL (build.gradle.kts) support (Phase 2)
- SBT (Scala Build Tool) (Phase 2)
- Private Artifactory / Nexus repositories (Phase 2)

---

### 3.6 Impact Analyzer (Scoring Engine)

**Owner:** Backend Team + ML/AI Team
**Effort Estimate:** 6 engineering days

#### In Scope
- Consume from `dependency.resolved` Kafka topic
- For each affected repository, retrieve:
  - CVSS score from PostgreSQL
  - Dependency depth and context type from Neo4j
  - Weekly downloads from Redis cache (populated by resolvers)
- Compute contextual severity score using scoring library (`libs/scoring-engine`)
- Store all scoring factors + final score to `affected_repositories` table
- Cache scores in Redis (TTL: 1 hour)
- Emit high-priority notifications to `impact.scored` Kafka topic for Critical/High repos
- Batch processing for Medium/Low repos (scheduled job, 2 AM UTC)

#### Out of Scope
- Call-graph / reachability analysis (Phase 2)
- EPSS integration (Phase 2)
- ML-based score prediction (Phase 2)
- Repository activity scoring (Phase 2)

---

### 3.7 Patch Drafter Service

**Owner:** ML/AI Team
**Effort Estimate:** 5 engineering days

#### In Scope
- Consume from `impact.scored` Kafka topic (Critical + High tiers)
- Generate issue text via OpenAI GPT-4o-mini API
- Implement prompt template system (system prompt + user prompt)
- Cache generated text by (CVE ID + dependency path hash) — same path = reuse text
- Fallback template system when LLM API unavailable
- Validate generated text: must contain CVE ID, dependency path, remediation steps
- Publish finalized issue payloads to `notifications.out` Kafka topic
- Track cost per issue in structured logs

#### Out of Scope
- PR generation (automated code fix) — Phase 2
- Multi-language issue text (English only for MVP)
- Custom user-defined issue templates (Phase 2)
- Slack/email notification channels (Phase 2)

---

### 3.8 Issue Creator Service

**Owner:** Backend Team
**Effort Estimate:** 6 engineering days

#### In Scope
- Consume from `notifications.out` Kafka topic
- Check opt-out registry before creating any issue
- Check `issued_notifications` table for duplicates
- Create GitHub issues via GitHub REST API
- Manage GitHub token pool (up to 10 tokens, round-robin rotation)
- Respect GitHub rate limits (5,000/hr per token); parse `Retry-After` headers
- Apply standard labels to created issues
- Record all issued notifications in `issued_notifications` table
- DLQ handling: failed issues go to `notifications.dlq`, retried after 1 hour
- Audit log entry for every issue created

#### Out of Scope
- GitLab issue creation (Phase 2)
- Jira ticket creation (Phase 2)
- Email notifications (Phase 2)
- Slack notifications (Phase 2)
- Bulk close / update previously created issues

---

### 3.9 API Gateway

**Owner:** Backend Team
**Effort Estimate:** 8 engineering days

#### In Scope
- All REST endpoints defined in `06-api-contracts.md`
- GitHub OAuth 2.0 authentication flow
- API key authentication (Bearer token)
- JWT session management (HTTP-only cookie for dashboard)
- RBAC enforcement (viewer/analyst/admin roles)
- Rate limiting per API key (1,000 req/hr) via Redis counter
- OpenAPI 3.1 spec auto-generated from FastAPI routes
- Pagination, filtering, and sorting for all list endpoints
- Export job creation and status polling
- Opt-out registration endpoints
- Response caching for frequently accessed CVE data (Redis, 5-min TTL)

#### Out of Scope
- GraphQL API (Phase 2)
- Webhook delivery system (Phase 2)
- SAML/SSO integration (Phase 2)
- Per-organization API key scoping (Phase 2)

---

### 3.10 Web Dashboard

**Owner:** Frontend Team
**Effort Estimate:** 12 engineering days

#### In Scope
- All pages defined in `03-information-architecture.md`
- GitHub OAuth login/logout flow
- CVE list with filtering, sorting, pagination
- CVE detail page with affected repo table
- Interactive dependency graph (Cytoscape.js) on CVE detail
- Package and repository detail pages
- Notification history page
- Opt-out self-service page
- CSV/JSON export trigger + status polling
- API key management page
- Responsive layout (desktop + tablet; mobile read-only)
- Real-time CVE counter updates via SSE (Server-Sent Events)
- Dark mode support

#### Out of Scope
- Native mobile app (Phase 2)
- SBOM visualizer (Phase 2)
- Embeddable badge/widget (Phase 2)
- White-label theming (Phase 2)

---

### 3.11 Infrastructure & Platform

**Owner:** Platform Team
**Effort Estimate:** 8 engineering days

#### In Scope
- Kubernetes cluster setup (AWS EKS)
- Namespace and RBAC configuration
- Helm chart for full platform deployment
- Kustomize overlays for staging and production
- GitHub Actions CI pipeline (lint, test, build, security scan)
- ArgoCD GitOps deployment setup
- AWS RDS PostgreSQL provisioning + automated backups
- AWS ElastiCache Redis cluster setup
- Confluent Cloud Kafka setup (topics, partitions, retention)
- Neo4j AuraDB provisioning
- AWS S3 bucket setup with lifecycle policies
- Prometheus + Grafana dashboards
- Jaeger distributed tracing
- OpenSearch log aggregation
- PagerDuty alert integration
- AWS Secrets Manager configuration
- TLS certificate automation (cert-manager + Let's Encrypt)
- Nginx Ingress with rate limiting

#### Out of Scope
- Multi-region deployment (Phase 2)
- Disaster recovery runbooks (Phase 2)
- SOC2 compliance controls (post-launch)
- Custom VPC design (use default AWS VPC for MVP)

---

## 4. Shared Libraries

### `libs/python-shared`

**Owner:** Backend Team Lead
**Effort Estimate:** 3 engineering days

Covers: Pydantic models, Kafka helpers, SQLAlchemy session factory, Redis client, auth middleware, OpenTelemetry setup.

### `libs/scoring-engine`

**Owner:** ML/AI Team
**Effort Estimate:** 2 engineering days

Pure Python library, no I/O. Implements the scoring formula from `08-scoring-engine-spec.md`.

---

## 5. Total Effort Summary

| Component                  | Engineering Days |
|----------------------------|-----------------|
| CVE Ingestion              | 5               |
| Dependency Coordinator     | 2               |
| npm Resolver               | 8               |
| PyPI Resolver              | 7               |
| Maven Resolver             | 10              |
| Impact Analyzer            | 6               |
| Patch Drafter              | 5               |
| Issue Creator              | 6               |
| API Gateway                | 8               |
| Web Dashboard              | 12              |
| Infrastructure             | 8               |
| Shared Libraries           | 5               |
| QA & Integration Testing   | 8               |
| **TOTAL**                  | **90 days**     |

With a team of 9 engineers: ~10 working days × 2 sprints = **~14 weeks** to MVP (accounting for coordination overhead).

---

## 6. Dependencies & Blockers

| Component        | Depends On                               | Risk                              |
|------------------|------------------------------------------|-----------------------------------|
| npm Resolver     | libraries.io API access                  | Rate limits may require paid plan |
| Patch Drafter    | OpenAI API key                           | Cost control needed               |
| Issue Creator    | GitHub token pool (10 tokens)            | Requires 10 GitHub test accounts  |
| API Gateway      | PostgreSQL schema stabilized             | DB migrations must run first      |
| Web Dashboard    | API Gateway endpoints finalized          | Can mock with OpenAPI mocks       |
| All services     | Kafka topics created                     | Platform team blocker             |
| All services     | `libs/python-shared` published           | Backend team blocker              |

---

*Last updated: 2026-04-18*
