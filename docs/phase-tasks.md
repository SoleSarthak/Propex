# ODEPM — Phase Tasks
## Open-Source Dependency Exploit Propagation Mapper

> **Free-Stack Edition** — All tools used are free, open-source, or have generous free tiers.

---

## Free Stack Reference

| Category | Free Tool Used |
|---|---|
| **Containerization** | Docker + Docker Compose |
| **SQL Database** | PostgreSQL (Docker container) |
| **Cache / Queue** | Redis (Docker container) |
| **Graph Database** | Neo4j Community Edition (Docker) |
| **Message Broker** | Redpanda (Kafka-compatible, Docker) |
| **Object Storage** | MinIO (self-hosted S3-compatible, Docker) |
| **CI/CD** | GitHub Actions (free tier) |
| **Container Registry** | GitHub Container Registry (GHCR) — free |
| **Migrations** | Alembic (Python, free) |
| **LLM (AI)** | Google Gemini API (free tier — 1M tokens/month) |
| **Monitoring** | Prometheus + Grafana (Docker, free) |
| **Tracing** | Jaeger (Docker, free) |
| **Error Tracking** | GlitchTip (self-hosted, free) or Sentry free tier |
| **Analytics** | Umami (self-hosted, free) |
| **Uptime Alerts** | UptimeRobot (free tier — email/Slack alerts) |
| **Frontend Hosting** | Vercel free tier / Cloudflare Pages |
| **Backend Hosting** | Render free tier / Railway free tier / Fly.io free tier |
| **Secrets Management** | `.env` files + `python-dotenv` / GitHub Actions Secrets |
| **CDN** | Cloudflare (free tier) |

---

## PHASE 0: Foundation (COMPLETED)

### Platform / DevOps
- [x] Install Docker Desktop and verify Docker Compose works locally
- [x] Create `docker-compose.yml` with all services:
  - [x] PostgreSQL 16 container (port 5432)
  - [x] Redis 7 container (port 6379)
  - [x] Neo4j Community 5.x container (ports 7474, 7687)
  - [x] Redpanda (Kafka-compatible) container (port 9092) + Redpanda Console UI
  - [x] MinIO container (port 9000) for object storage
  - [x] Prometheus + Grafana containers (ports 9090, 3000)
  - [x] Jaeger all-in-one container (port 16686)
- [x] Create `.env.example` with all required environment variables (no real secrets)
- [x] Set up GitHub Actions CI pipeline (lint → test → build → push to GHCR)
- [x] Configure basic Prometheus scrape targets for all services
- [x] Import Grafana community dashboards (Redis, PostgreSQL, Node Exporter)
- [x] Set up UptimeRobot (free) to monitor local-exposed or hosted endpoints

### Backend Team Lead
- [x] Initialize monorepo structure (`poetry` workspaces + `pnpm` workspace)
- [x] Scaffold `libs/python-shared`:
  - [x] Pydantic models: `CveRecord`, `AffectedPackage`, Kafka event schemas
  - [x] Kafka producer/consumer base classes (using `confluent-kafka` Python client)
  - [x] SQLAlchemy async session factory (connect to local PostgreSQL)
  - [x] Redis async client wrapper (`redis-py`)
  - [x] Auth middleware (JWT + API key, using `python-jose`)
  - [x] OpenTelemetry setup helper (free, CNCF project)
- [x] Scaffold `libs/scoring-engine` with formula stub
- [x] Set up Alembic + write initial migration (all tables from `05-database-schema.md`)
- [x] Write `Makefile` with all standard dev commands
- [x] Write developer onboarding `scripts/setup-dev.sh` (installs Python/Node, starts Docker Compose)
- [x] Write `scripts/seed-db.py` with 4 real CVE seeds

### Frontend Team
- [x] Scaffold React app with Vite + TypeScript
- [x] Install and configure: shadcn/ui, Tailwind CSS, Zustand, TanStack Query, React Router v6
- [x] Configure MSW (Mock Service Worker) for local API mocking
- [x] Set up Playwright for E2E tests (free, open-source)
- [x] Create design tokens (colors, typography, spacing) in `styles/theme.css`
- [x] Build `TopNav`, `Sidebar`, `PageWrapper` layout components
- [x] Build `LoadingSpinner`, `EmptyState`, `Pagination` common components

### All Teams
- [x] Verify `make docker-up` starts all services without errors
- [x] Verify all engineers can access Neo4j (localhost:7474), PostgreSQL, Redis, Redpanda locally
- [x] Set up pre-commit hooks (`black`, `flake8`, `mypy`, `eslint`) — all free
- [x] Write team coding standards doc in `docs/contributing.md`

---

## PHASE 1: CVE Ingestion + npm Resolver (Weeks 3–4)

### CVE Ingestion Service (Backend)
- [x] Implement NVD API client (`services/cve_ingestion/services/nvd_client.py`)
  - [x] `GET /rest/json/cves/2.0` with `lastModStartDate` filter (NVD API is free)
  - [x] Pagination handling (NVD returns 2,000 per page)
  - [x] Retry with exponential backoff on 503/429
- [x] Implement OSV webhook endpoint (`POST /webhooks/osv`) — OSV is free and open
- [x] Implement GitHub Advisory GraphQL feed parser (uses free GitHub token)
- [x] Implement CVE normalizer (NVD → `CveRecord`)
- [x] Implement deduplication logic (upsert by `cve_id`)
- [x] Implement Redpanda/Kafka producer (publish to `cve.raw` topic)
- [x] Implement MinIO archival of raw API responses (replaces S3)
- [x] Set up APScheduler jobs (NVD: 15 min, GHSA: 30 min) — free library
- [x] Add health check + readiness endpoints
- [x] Write unit tests (normalizer, deduplication, version parser) — target 90% coverage
- [x] Write integration tests (NVD poll → PostgreSQL → Redpanda)
- [x] Write `Dockerfile` + `docker-compose` service entry

### npm Resolver Service (Backend)
- [x] Implement Redpanda consumer for `cve.raw` topic (npm filter)
- [x] Implement npm Registry API client (free, no auth needed for public packages)
- [x] Implement libraries.io reverse dependency lookup (free API tier: 60 req/min)
- [x] Implement BFS dependency tree traversal (max depth 10)
- [x] Implement semver version range overlap checker (use `semver` Python library)
- [x] Implement GitHub code search API client (free GitHub token, 30 req/min)
- [x] Implement Neo4j graph writer (Package, Repository nodes + DEPENDS_ON, USES, AFFECTS edges)
- [x] Implement Redis cache for package trees (24h TTL)
- [x] Implement Redpanda producer (publish to `dependency.resolved`)
- [x] Write unit tests (semver checker, BFS traversal) — 90% coverage
- [x] Write integration tests (npm registry → Neo4j write → Redpanda publish)
- [x] Write `Dockerfile` + `docker-compose` service entry

### Dependency Coordinator (Backend)
- [x] Implement Redpanda consumer for `cve.raw`
- [x] Route packages to npm/PyPI/Maven resolver topics
- [x] Track resolution status per CVE in PostgreSQL
- [x] Write unit + integration tests

### Scoring Engine Library (ML/AI)
- [x] Implement `depth_factor()`, `context_multiplier()`, `popularity_factor()` functions
- [x] Implement `compute_score()` with full formula
- [x] Implement `_score_to_tier()` classification
- [x] Write 20+ unit tests including property-based tests (`hypothesis` — free)
- [x] Validate against 20 manual expert-scored CVE-repo pairs (target r ≥ 0.85)

### Monitoring
- [x] Add Grafana alert rule: CVE ingestion lag > 20 min → email (via UptimeRobot or SMTP)
- [x] Add Grafana panel: Redpanda `cve.raw` consumer lag

### Phase 1 Milestone Verification
- [x] Manually trigger NVD poll; CVE appears in DB within 15 min
- [x] `lodash@<4.17.21` resolves with > 1,000 affected repos in Neo4j
- [x] `dependency.resolved` event appears in Redpanda

---

## PHASE 2: PyPI + Maven Resolvers + Graph Enrichment (Weeks 5–6)

### PyPI Resolver Service (Backend)
- [x] Implement Redpanda consumer for `cve.raw` (PyPI filter)
- [x] Implement PyPI JSON API client (`/pypi/{package}/json`) — free, no auth
- [x] Implement libraries.io PyPI reverse dependency lookup (free tier)
- [x] Implement PEP 508 version specifier parser (`packaging` library — free)
- [x] Implement `setup.py` / `pyproject.toml` / `requirements.txt` parser
- [x] Handle `extras_require` and `tests_require` dependency types
- [x] Implement Neo4j graph writer (reuse shared pattern)
- [x] Implement Redis cache + rate limiting
- [x] Implement Redpanda publish to `dependency.resolved`
- [ ] Write unit tests (PEP 508 parser edge cases) — 90% coverage
- [ ] Write integration tests
- [x] Write `Dockerfile` + `docker-compose` service entry

### Maven Resolver Service (Backend / Java)
- [x] Implement Redpanda consumer (use `kafka-python` or Java Kafka client)
- [x] Implement Maven Central Search API client (free, no auth needed)
- [x] Implement POM XML parser (dependencies + dependencyManagement + BOM imports)
- [x] Implement Maven version range parser (e.g., `[1.0,2.0)`)
- [x] Handle all dependency scopes: compile, runtime, test, provided, import
- [x] Implement Neo4j graph writer
- [x] Implement Redis caching
- [x] Implement Redpanda publish to `dependency.resolved`
- [ ] Write unit tests — 90% coverage
- [ ] Write integration tests (use `testcontainers` — free, open-source)
- [x] Write `Dockerfile` + `docker-compose` service entry

### Repository Discovery Enhancement (Backend)
- [x] Support manifest file detection for `requirements.txt`, `setup.py`, `pom.xml`, `build.gradle`
- [x] Implement version spec overlap verification for PyPI specs
- [x] Implement version spec overlap verification for Maven ranges
- [x] Enrich repository metadata from GitHub API (stars, language, archive status, fork) — free token
- [x] Update `repositories` table with enriched metadata
- [x] Handle GitHub search API pagination (date windowing to bypass 1,000 result limit)

### Monitoring
- [x] Create Neo4j indexes: `pkg_lookup`, `repo_url`, `cve_id`
- [x] Add Grafana panels: resolution time P95 per ecosystem

### Phase 2 Milestone Verification
- [x] `requests@<2.32.0` (PyPI) resolves with > 500 affected repos
- [x] Log4j Maven CVE resolves with > 200 affected Java repos
- [x] All 3 resolvers complete in < 60 sec for < 1,000 direct dependents (P95)
- [x] Neo4j path query returns correct chains for known repo-CVE pairs

---

## PHASE 3: Scoring Engine + Impact Analysis (Weeks 7–8)

### Impact Analyzer Service (Backend + ML/AI)
- [ ] Implement Redpanda consumer for `dependency.resolved`
- [ ] Implement Neo4j path query: find dependency depth for each repo-CVE pair
- [ ] Implement context type extraction from dependency manifest (runtime vs. dev)
- [ ] Implement download count fetch from Redis (populated by resolvers)
- [ ] Integrate `libs/scoring-engine` `compute_score()` function
- [ ] Persist all 4 scoring factors + final score to `affected_repositories` table
- [ ] Cache scores in Redis (1h TTL)
- [ ] Publish Critical + High repos to `impact.scored` Redpanda topic (immediate)
- [ ] Schedule batch job for Medium + Low repos (nightly, 2 AM UTC) using APScheduler
- [ ] Implement score recalculation trigger (on CVSS update Kafka event)
- [ ] Write unit tests for each pipeline step
- [ ] Write integration tests (full: Redpanda event → DB record with score)
- [ ] Write `Dockerfile` + `docker-compose` service entry

### API Gateway — Scoring Endpoints (Backend)
- [ ] `GET /api/v1/cves/{cve_id}/affected-repos` with pagination + sort by score
- [ ] `GET /api/v1/repos/{owner}/{name}/vulnerabilities`
- [ ] `PATCH /api/v1/repos/{owner}/{name}/vulnerabilities/{cve_id}` (maintainer status update)
- [ ] Wire up PostgreSQL queries with SQLAlchemy async
- [ ] Add Redis response caching (5 min TTL for CVE detail)
- [ ] Write integration tests for each endpoint

### Phase 3 Milestone Verification
- [ ] Score computed for all affected repos within 10 min of dependency resolution
- [ ] Formula validated: run 20 test cases from `08-scoring-engine-spec.md`, all pass
- [ ] All 4 scoring factors stored in `affected_repositories` table
- [ ] `impact.scored` events appear in Redpanda for Critical/High repos
- [ ] API returns correctly sorted paginated results

---

## PHASE 4: LLM Patch Drafter + Issue Creator (Weeks 9–10)

### Patch Drafter Service (ML/AI)
- [ ] Implement Redpanda consumer for `impact.scored` (Critical + High)
- [ ] Implement **Google Gemini API** integration (free tier: 1M tokens/month, 1,500 req/day)
  - [ ] Use `google-generativeai` Python SDK (free)
  - [ ] Model: `gemini-2.0-flash` (free tier)
- [ ] Write system prompt (security researcher persona, few-shot examples)
- [ ] Write per-ecosystem user prompt templates (npm/PyPI/Maven variants)
- [ ] Implement output validation (must contain: CVE ID, dep path, remediation, fix version)
- [ ] Implement cache by (CVE ID + dep path hash) — 7-day Redis TTL
- [ ] Implement fallback template system (all ecosystems + all tiers) for when LLM hits rate limits
- [ ] Implement cost/quota tracking (log token usage per call to PostgreSQL)
- [ ] Implement hard rate limit: stay within Gemini free tier (1,500 req/day)
- [ ] Publish to `notifications.out` Redpanda topic
- [ ] Write unit tests for prompt rendering + output validation
- [ ] Write integration tests (Redpanda event → Gemini call → Redpanda publish)
- [ ] Write `Dockerfile` + `docker-compose` service entry

### Issue Creator Service (Backend)
- [ ] Implement Redpanda consumer for `notifications.out`
- [ ] Implement opt-out registry check (Redis cache → PostgreSQL fallback)
- [ ] Implement duplicate check (`issued_notifications` table + GitHub issue search)
- [ ] Implement GitHub REST API client (create issue endpoint, free with personal token)
- [ ] Implement token pool with round-robin rotation (up to 5 free GitHub accounts)
- [ ] Implement rate limit management (parse `X-RateLimit-*` headers, respect `Retry-After`)
- [ ] Implement retry logic: exponential backoff, max 3 retries
- [ ] Implement `issued_notifications` table writes (success + failure)
- [ ] Implement audit log entry per issue creation
- [ ] Implement DLQ handling (failed → `notifications.dlq`, retry after 1h)
- [ ] Write unit tests (duplicate check, rate limit logic)
- [ ] Write integration tests (Redpanda event → GitHub issue created → DB record)
- [ ] Write `Dockerfile` + `docker-compose` service entry

### API Gateway — Opt-Out + Notification Endpoints (Backend)
- [ ] Implement GitHub OAuth 2.0 flow (authorization code) — free GitHub OAuth App
- [ ] `POST /opt-out` — register opt-out (GitHub OAuth required)
- [ ] `DELETE /opt-out` — reverse opt-out
- [ ] `GET /opt-out` — list opt-outs for authenticated user
- [ ] `GET /api/v1/notifications` — paginated notification history
- [ ] `POST /api/v1/notifications/{id}/retry` — queue failed notification for retry
- [ ] Write integration tests for all opt-out + notification endpoints

### Phase 4 Milestone Verification
- [ ] End-to-end: manually trigger CVE → GitHub issue appears within 45 min
- [ ] LLM issue text includes: CVE ID, dep path, CVSS, fix version, remediation command
- [ ] Opted-out test repos receive no issues (test with 3 repos)
- [ ] No duplicate issues after 5 retry attempts to same repo-CVE pair
- [ ] Audit log records each creation with timestamp, repo, issue URL

---

## PHASE 5: Dashboard MVP + Public API (Weeks 11–12)

### Frontend — All Pages (Frontend Team)
- [ ] **Home / Landing Page**: hero, live stats counter, recent CVE feed
- [ ] **Dashboard**: stat cards (CVEs/24h, Critical findings, Issues sent), recent CVEs, SSE feed
- [ ] **CVE List**: paginated table, all filters (ecosystem, severity, date, text search), URL-reflected filters
- [ ] **CVE Detail**: summary, CVSS badge, affected packages, affected repos table (sortable), Export CSV/JSON button
- [ ] **Dependency Graph**: Cytoscape.js visualization (node size = popularity, edge color = dep type), pan/zoom, node click drill-down (Cytoscape.js is free/open-source)
- [ ] **Package Detail**: CVE history, dependents list, version timeline
- [ ] **Repo Detail**: CVE exposure history, notification history, maintainer status toggle
- [ ] **Notification History**: paginated list, filter by status/CVE/date, retry button
- [ ] **Opt-Out Page**: GitHub OAuth flow, repo list, toggle per-repo/per-org
- [ ] **API Key Management**: create, list (with prefix only), revoke
- [ ] **Docs Page**: embed OpenAPI UI (Swagger UI — free/open-source)
- [ ] Implement dark mode (CSS custom property toggle)
- [ ] Implement responsive layout (desktop + tablet)
- [ ] Add SSE connection to dashboard for real-time CVE feed
- [ ] Add error boundaries to all pages
- [ ] Add **GlitchTip** (free, self-hosted Sentry-compatible) SDK for error tracking
- [ ] Add **Umami** (free, self-hosted) for privacy-respecting analytics
- [ ] Run Lighthouse: score ≥ 90 on dashboard and CVE list
- [ ] Deploy frontend to **Vercel free tier** or **Cloudflare Pages** (both free)

### API Gateway — Remaining Endpoints (Backend)
- [ ] `GET /api/v1/cves` with all filters + full-text search
- [ ] `GET /api/v1/cves/{cve_id}` with counts by tier
- [ ] `POST /api/v1/cves` (manual CVE submission, auth required)
- [ ] `GET /api/v1/packages/{ecosystem}/{name}` + dependents + CVEs
- [ ] `GET /api/v1/repos/{owner}/{name}` + vulnerabilities
- [ ] `POST /api/v1/api-keys` — create key (show once)
- [ ] `GET /api/v1/api-keys` — list (prefix only)
- [ ] `DELETE /api/v1/api-keys/{id}` — revoke
- [ ] `POST /api/v1/exports` — async export job creation
- [ ] `GET /api/v1/exports/{id}` — status + MinIO pre-signed URL (replaces S3)
- [ ] SSE endpoint for real-time CVE feed
- [ ] Rate limiting: Redis counter per API key per hour
- [ ] OpenAPI spec auto-generated at `/api/docs` (FastAPI does this for free)
- [ ] Run `make gen-api-client` to generate TypeScript API client for dashboard
- [ ] Deploy backend to **Render free tier** or **Fly.io free tier**

### Phase 5 Milestone Verification
- [ ] Dashboard loads < 2 sec (P95) with 1,000 CVE records
- [ ] CVE detail with 10,000 affected repos paginates and sorts correctly
- [ ] Dependency graph renders < 3 sec for 500-node graph
- [ ] Rate limit: 1,001st API request returns 429
- [ ] CSV export for 10,000 rows completes < 30 sec
- [ ] WCAG 2.1 AA passes for login and CVE list pages

---

## PHASE 6: Beta Launch + Hardening (Weeks 13–14)

### Infrastructure (Self-Hosted / Free Tier)
- [ ] Deploy full stack to **Fly.io** (free tier: 3 shared VMs, 3GB volume) or **Render**
- [ ] Configure **Cloudflare** (free tier) as CDN + DNS + TLS for frontend
- [ ] Configure **Cloudflare Tunnel** (free) to expose backend without opening ports
- [ ] Set up SSL/TLS via Cloudflare or Let's Encrypt (both free)
- [ ] Configure **UptimeRobot** (free) for all critical endpoints with email/Slack alerts
- [ ] Set up status page using **Upptime** (free, GitHub-hosted status page)
- [ ] Write runbooks for all critical failure scenarios in `docs/runbooks/`
- [ ] Run disaster recovery drill (simulate DB container restart, verify data integrity)

### Backend Hardening (Backend Team)
- [ ] Run **k6** load test (free, open-source): 100 concurrent API users → all P95 < 500 ms
- [ ] Run k6 throughput test: simulate 50K Kafkua events/day
- [ ] Review PostgreSQL slow query log → add missing indexes (`pg_stat_statements` — free)
- [ ] Verify Redis cache hit rate > 85% (use Redis `INFO stats`)
- [ ] Run **OWASP ZAP** scan (free, open-source) on API → fix all HIGH findings
- [ ] Security pen-test checklist from `12-testing-strategy.md` §6.5
- [ ] Implement hard rate limit on Gemini LLM calls: stay within 1,500 req/day free tier

### Frontend Hardening (Frontend Team)
- [ ] Lighthouse audit: performance, accessibility, SEO — all ≥ 90
- [ ] Add Open Graph meta tags for all pages
- [ ] Add `robots.txt` and `sitemap.xml`
- [ ] Verify GlitchTip integration captures all unhandled errors
- [ ] Verify Umami analytics tracking is working

### ML/AI Hardening (ML/AI Team)
- [ ] Build Gemini token usage monitoring Grafana dashboard (log token counts to PostgreSQL)
- [ ] Alert: daily Gemini token usage > 800K (approaching free tier limit) → email warning
- [ ] Verify fallback template covers all 3 ecosystems × 4 severity tiers = 12 templates
- [ ] A/B test LLM-generated vs. template issues with 5 beta maintainers

### Beta Launch
- [ ] Onboard 10 beta users (5 security analysts + 5 maintainers)
- [ ] Create in-app feedback form (**Tally** free tier or **Google Forms** embed)
- [ ] Set up support email with **Zoho Mail** (free tier) or GitHub Discussions
- [ ] Publish Privacy Policy + Terms of Service (use free policy generators)
- [ ] Create product launch blog post (dev.to / Medium — both free)
- [ ] Submit to Hacker News "Show HN"

### Phase 6 Final Verification
- [ ] Zero Critical security findings from OWASP ZAP scan
- [ ] System handles 50K Redpanda events/day without queue buildup
- [ ] P95 API response < 500 ms under 100 concurrent users (Fly.io/Render free tier limits)
- [ ] Dashboard Lighthouse performance ≥ 90
- [ ] 10 beta users onboarded and active
- [ ] All UptimeRobot alerts verified with a fire drill

---

## POST-MVP BACKLOG (Prioritized)

### Q1 After Launch
- [ ] Go modules resolver (ecosystem parity)
- [ ] Cargo (Rust) resolver
- [ ] EPSS score integration in scoring engine (EPSS API is free)
- [ ] Private repository scanning (GitHub App OAuth)
- [ ] Call-graph reachability for npm (CodeQL — free for open-source)

### Q2 After Launch
- [ ] Automated PR generation (dependency bump)
- [ ] Webhook delivery for enterprise users
- [ ] SBOM export (CycloneDX 1.5 + SPDX 2.3)
- [ ] GitLab issue creator support
- [ ] Multi-language issue text (Spanish, Japanese)

### Q3 After Launch
- [ ] NuGet (C#/.NET) resolver
- [ ] Multi-region deployment (if budget allows, else stay on free tier)
- [ ] Org-level aggregated risk report (PDF export)
- [ ] Slack / Teams notification channel integration (free webhook-based)

---

*Last updated: 2026-04-18 — Free Stack Edition*
