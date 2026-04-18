# 10 — Development Phases
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. Overview

ODEPM development is organized into **6 phases** across 14 weeks (2-week sprints), followed by ongoing post-MVP iterations. Each phase has clear deliverables, acceptance criteria, and team assignments.

---

## 2. Phase Timeline

```
Week 1-2   │ Phase 0: Foundation
Week 3-4   │ Phase 1: CVE Ingestion + npm Resolver
Week 5-6   │ Phase 2: PyPI + Maven Resolvers + Graph DB
Week 7-8   │ Phase 3: Scoring Engine + Repository Discovery
Week 9-10  │ Phase 4: LLM Patch Drafter + Issue Creator
Week 11-12 │ Phase 5: Dashboard MVP + Public API
Week 13-14 │ Phase 6: Beta Launch + Hardening
```

---

## 3. Phase 0: Foundation (Weeks 1–2)

### 3.1 Goals
- Development environment working for all engineers
- Core infrastructure provisioned
- Shared libraries scaffolded
- CI/CD pipeline operational

### 3.2 Deliverables

#### Platform Team
- [ ] AWS EKS cluster provisioned (staging)
- [ ] Kafka topics created (all 4 topics per schema in `04-system-architecture.md`)
- [ ] PostgreSQL RDS instance running with initial schema
- [ ] Redis ElastiCache cluster running
- [ ] Neo4j AuraDB instance running
- [ ] AWS S3 buckets created with correct policies
- [ ] GitHub Actions CI pipeline: lint → test → build → push ECR
- [ ] ArgoCD connected to staging namespace
- [ ] Secrets Manager configured with placeholder secrets
- [ ] Local `docker-compose.yml` working for all services

#### Backend Team Lead
- [ ] `libs/python-shared` scaffolded with:
  - Pydantic models (CveRecord, AffectedPackage, KafkaEvents)
  - Kafka producer/consumer base classes
  - SQLAlchemy async session factory
  - Redis async client
  - OpenTelemetry setup
  - Auth middleware (JWT + API key)
- [ ] `libs/scoring-engine` scaffolded with scoring formula implementation
- [ ] Database migrations: Alembic setup + initial schema (`05-database-schema.md`)
- [ ] Monorepo structure initialized (Poetry workspaces, pnpm workspace)

#### Frontend Team
- [ ] React app scaffolded with Vite
- [ ] Design system initialized (shadcn/ui + Tailwind + custom tokens)
- [ ] React Router + Zustand + TanStack Query configured
- [ ] Mock API server (MSW) configured for local development
- [ ] Figma design review completed for key pages

### 3.3 Acceptance Criteria
- `make docker-up` starts all services without errors
- `make test` runs (with 0 tests passing is acceptable at this stage)
- CI pipeline runs on PRs and succeeds on a trivial change
- ArgoCD deploys to staging namespace successfully
- All engineers can access Neo4j, PostgreSQL, Redis, and Kafka locally

---

## 4. Phase 1: CVE Ingestion + npm Resolver (Weeks 3–4)

### 4.1 Goals
- First end-to-end pipeline working: NVD → Kafka → npm dependency tree → Neo4j
- System can ingest real CVEs from NVD

### 4.2 Deliverables

#### Backend Team
- [ ] CVE Ingestion Service (complete):
  - NVD polling with APScheduler
  - OSV webhook endpoint
  - CVE normalization + deduplication
  - Kafka publish to `cve.raw`
  - S3 raw response archival
  - Health check endpoints
- [ ] npm Resolver Service (complete):
  - Kafka consumer for `cve.raw`
  - npm Registry API client (with rate limiting)
  - libraries.io reverse dependency lookup
  - BFS dependency tree traversal (depth 1–10)
  - semver version range overlap detection
  - Neo4j graph writer (Package nodes + DEPENDS_ON edges)
  - Repository discovery via GitHub code search API
  - Redis caching for package trees (24h TTL)
  - Kafka publish to `dependency.resolved`
- [ ] Dependency Coordinator Service (complete)

#### ML/AI Team
- [ ] `libs/scoring-engine` unit tests written and passing (>90% coverage)
- [ ] Scoring formula validated against manual expert scores (r ≥ 0.85)

#### Platform Team
- [ ] Prometheus + Grafana dashboards configured for CVE ingestion lag
- [ ] Alert: page on-call if CVE ingestion lag > 20 min

### 4.3 Milestone Demo
> **Demo:** Trigger a manual CVE publication; watch it appear in the database, trigger npm dependency resolution, and see affected repositories appear in Neo4j browser within 5 minutes.

### 4.4 Acceptance Criteria
- System ingests CVE-2021-44228 (log4j) from NVD within 15 minutes of restart
- npm dependency tree for `lodash@<4.17.21` resolves with > 1,000 affected repositories
- Neo4j contains correct `Package`, `Repository`, `DEPENDS_ON`, `USES` nodes/edges
- `dependency.resolved` event published to Kafka

---

## 5. Phase 2: PyPI + Maven Resolvers + Graph Enrichment (Weeks 5–6)

### 5.1 Goals
- Full ecosystem coverage: npm + PyPI + Maven all resolving
- Dependency graph in Neo4j is comprehensive and queryable
- Repository discovery working for all three ecosystems

### 5.2 Deliverables

#### Backend Team
- [ ] PyPI Resolver Service (complete):
  - PyPI JSON API client
  - libraries.io PyPI reverse dependency lookup
  - PEP 508 version specifier parsing
  - `setup.py` / `pyproject.toml` / `requirements.txt` parsing
  - Neo4j graph writer
  - Redis caching
  - Kafka publish
- [ ] Maven Resolver Service (complete):
  - Maven Central Search API client
  - POM XML parser (dependencies + dependency management + BOM)
  - Maven version range parser
  - Dependency scope handling (compile/runtime/test/provided)
  - Neo4j graph writer
  - Redis caching
  - Kafka publish
- [ ] Repository Discovery Enhancement:
  - Support `requirements.txt`, `setup.py`, `pom.xml`, `build.gradle`
  - Version spec verification (overlap with CVE affected range)
  - GitHub repository metadata enrichment (stars, language, fork status)

#### Platform Team
- [ ] Neo4j read replica added for query load separation
- [ ] Neo4j indexes created for `pkg_lookup`, `repo_url`, `cve_id`

### 5.3 Milestone Demo
> **Demo:** For CVE-2022-42969 (py library), show full PyPI dependency tree with affected repositories. For a known Maven CVE, show affected Java repositories.

### 5.4 Acceptance Criteria
- PyPI resolver resolves `requests@<2.32.0` with > 500 affected repositories
- Maven resolver resolves a known log4j CVE with > 200 affected repositories
- All three ecosystem resolvers complete within 60 seconds for packages with < 1,000 direct dependents (P95)
- Neo4j graph query returns correct dependency paths for known repo-CVE pairs

---

## 6. Phase 3: Scoring Engine + Impact Analysis (Weeks 7–8)

### 6.1 Goals
- Every affected repository has a contextual severity score
- Score decomposition (all factors) stored for auditability
- High-severity repositories identified and queued for notification

### 6.2 Deliverables

#### Backend Team + ML/AI Team
- [ ] Impact Analyzer Service (complete):
  - Kafka consumer for `dependency.resolved`
  - Neo4j path query for dependency depth
  - Context type extraction from dependency manifest
  - Download count fetching from Redis/registry APIs
  - Scoring Engine integration
  - Score persistence to `affected_repositories` table
  - Redis score cache (1h TTL)
  - Kafka publish to `impact.scored` (Critical + High only)
  - Batch scheduler for Medium/Low (nightly job)
- [ ] Score recalculation job (runs when CVSS updated)
- [ ] API endpoint: `GET /cves/{cve_id}/affected-repos` (paginated, sortable by score)
- [ ] Basic admin API to trigger manual re-scoring

### 6.3 Milestone Demo
> **Demo:** For CVE-2024-12345 (a test CVE), show a ranked table of affected repositories with scores, severity tiers, and factor breakdown.

### 6.4 Acceptance Criteria
- Score computed for all affected repos within 10 minutes of dependency resolution
- Score formula matches spec in `08-scoring-engine-spec.md` (validated with 20 test cases)
- All 4 scoring factors stored per record
- `impact.scored` events published for all Critical and High repos
- API endpoint returns correct paginated results sorted by score

---

## 7. Phase 4: LLM Patch Drafter + Issue Creator (Weeks 9–10)

### 7.1 Goals
- End-to-end automated patch request: scored CVE → LLM issue text → GitHub issue created
- Opt-out registry functional
- Duplicate prevention working

### 7.2 Deliverables

#### ML/AI Team
- [ ] Patch Drafter Service (complete):
  - Kafka consumer for `impact.scored`
  - LangChain GPT-4o-mini integration
  - System prompt + user prompt templates (per ecosystem variant)
  - Few-shot examples for consistent formatting
  - Generated text validation (must contain CVE ID, dep path, remediation)
  - Caching by (CVE ID + dep path hash) — 7-day TTL
  - Fallback template system (used when LLM unavailable or invalid output)
  - Cost tracking per issue in structured logs
  - Kafka publish to `notifications.out`

#### Backend Team
- [ ] Issue Creator Service (complete):
  - Kafka consumer for `notifications.out`
  - Opt-out registry check (Redis cache + PostgreSQL fallback)
  - Duplicate check (`issued_notifications` table + GitHub issue search)
  - GitHub REST API client with token pool (up to 10 tokens)
  - Rate limit management: honor `X-RateLimit-*` headers
  - Retry logic with exponential backoff (max 3 retries per issue)
  - `issued_notifications` table write on success/failure
  - Audit log entry per issue creation
  - DLQ handling for persistent failures
- [ ] Opt-out API endpoints (`POST /opt-out`, `DELETE /opt-out`, `GET /opt-out`)
- [ ] GitHub OAuth 2.0 flow in API Gateway (for opt-out authentication)

### 7.3 Milestone Demo
> **Demo:** End-to-end: manually trigger a CVE, watch it resolve, score, generate issue text, and appear as a GitHub issue on a test repository within 45 minutes.

### 7.4 Acceptance Criteria
- LLM-generated issue text includes: CVE ID, dependency path, CVSS score, fixed version, remediation command
- Issue created on GitHub test repo within 45 minutes of CVE ingestion
- Opted-out repositories receive no issues (verified with 3 test repos)
- No duplicate issues created for same CVE + repo pair (tested with 5 retry attempts)
- Audit log records every issue creation with user, timestamp, and issue URL

---

## 8. Phase 5: Dashboard MVP + Public API (Weeks 11–12)

### 8.1 Goals
- Analyst dashboard fully functional with all key views
- Public REST API live with authentication and rate limiting
- Data export working

### 8.2 Deliverables

#### Frontend Team
- [ ] All pages implemented:
  - Home / Landing Page
  - Dashboard (auth required)
  - CVE List + Filters
  - CVE Detail + Affected Repos Table
  - Dependency Graph Visualization (Cytoscape.js)
  - Package Detail page
  - Repository Detail + Vulnerability History
  - Notification History
  - Opt-Out Page (with GitHub OAuth)
  - API Key Management
- [ ] Dark mode support
- [ ] Responsive layout (desktop + tablet)
- [ ] SSE real-time CVE feed on dashboard
- [ ] Error boundaries + loading states on all pages
- [ ] Accessibility: WCAG 2.1 AA for core flows

#### Backend Team
- [ ] All API Gateway endpoints complete (per `06-api-contracts.md`)
- [ ] API key management: create, list, revoke
- [ ] Rate limiting: Redis counter per API key per hour
- [ ] Data export: CSV + JSON, async for large datasets (S3 pre-signed URL)
- [ ] OpenAPI spec published at `/api/docs`
- [ ] SSE endpoint for real-time CVE feed

### 8.3 Milestone Demo
> **Demo:** Walk through full analyst workflow: login → dashboard → new CVE alert → CVE detail → graph view → affected repo list → export CSV.

### 8.4 Acceptance Criteria
- Dashboard loads within 2 seconds (P95) for CVE list with 1,000 records
- CVE detail page with 10,000 affected repos paginates and sorts correctly
- Dependency graph renders within 3 seconds for 500-node graphs
- API key rate limit enforced: 1,001st request in 1 hour returns 429
- CSV export completes for 10,000 rows within 30 seconds
- All WCAG 2.1 AA accessibility checks pass for login and CVE list pages

---

## 9. Phase 6: Beta Launch + Hardening (Weeks 13–14)

### 9.1 Goals
- Production infrastructure deployed and validated
- Performance and security hardened
- Beta user onboarding
- Monitoring and alerting comprehensive

### 9.2 Deliverables

#### Platform Team
- [ ] Production EKS cluster provisioned
- [ ] Multi-AZ RDS setup with automated failover
- [ ] CloudFront CDN in front of React SPA
- [ ] WAF rules on API Gateway (rate limiting, bot detection)
- [ ] Production Kafka cluster with 7-day retention
- [ ] Full PagerDuty alert integration
- [ ] Runbook documentation for all alerts
- [ ] Disaster recovery drill completed
- [ ] SSL/TLS certificates for all domains

#### Backend Team
- [ ] Load testing: 1,000 concurrent API users, 500K Kafka events/day
- [ ] All P95 latency targets verified (per `01-product-requirements.md` NFR table)
- [ ] PostgreSQL slow query review and index optimization
- [ ] Redis hit rate > 85% for common queries
- [ ] Security audit: OWASP Top 10 review for API Gateway
- [ ] Penetration test on authentication flows

#### ML/AI Team
- [ ] LLM cost monitoring dashboard
- [ ] Hard rate limit: 1,000 LLM calls/day enforced
- [ ] Fallback template coverage: all ecosystems + all severity tiers

#### Frontend Team
- [ ] Performance audit (Lighthouse score ≥ 90)
- [ ] Final SEO meta tags, OG images
- [ ] Error tracking (Sentry) verified working
- [ ] User analytics (privacy-respecting) configured

### 9.3 Beta Launch Checklist
- [ ] 10 beta users onboarded (security analysts + maintainers)
- [ ] Feedback collection mechanism in place (in-app survey)
- [ ] Status page live (`status.odepm.io`)
- [ ] Support email configured
- [ ] Privacy Policy + Terms of Service published

### 9.4 Acceptance Criteria
- Zero Critical severity security findings from pen test
- System handles 500K Kafka events/day without queue buildup
- P95 API response time < 500ms under load
- Dashboard Lighthouse performance score ≥ 90
- 10 beta users onboarded and actively using the platform

---

## 10. Post-MVP Roadmap (Phase 7+)

| Feature                                  | Priority | Target Quarter |
|------------------------------------------|----------|----------------|
| Go modules resolver                      | P1       | Q1 post-launch |
| Cargo (Rust) resolver                    | P1       | Q1 post-launch |
| Call-graph reachability (npm/Python)     | P1       | Q1 post-launch |
| Private repository scanning (OAuth)      | P1       | Q2 post-launch |
| Automated PR generation (Dependabot-like)| P2       | Q2 post-launch |
| Webhook delivery for enterprises         | P2       | Q2 post-launch |
| SBOM export (CycloneDX / SPDX)          | P2       | Q2 post-launch |
| EPSS integration in scoring              | P2       | Q2 post-launch |
| NuGet resolver                           | P3       | Q3 post-launch |
| Enterprise SSO / SAML                   | P3       | Q3 post-launch |
| GitLab support                           | P3       | Q3 post-launch |
| Multi-region deployment                  | P3       | Q3 post-launch |

---

*Last updated: 2026-04-18*
