# 07 — Monorepo Structure
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. Repository Strategy

ODEPM uses a **monorepo** approach managed with a workspace-aware tool. This enables:
- Shared tooling (linting, testing, CI configs)
- Atomic commits across service boundaries
- Simplified dependency management across packages
- Consistent coding standards enforced at root level

**Tooling:** `pnpm` workspaces for JS/TS packages; `poetry` workspaces for Python services; `Gradle` multi-project for Maven resolver.

---

## 2. Top-Level Directory Layout

```
odepm/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                      # PR checks: lint, test, build
│   │   ├── cd-staging.yml              # Auto-deploy to staging on main merge
│   │   ├── cd-production.yml           # Manual-approve deploy to production
│   │   ├── security-scan.yml           # Trivy + Bandit scans
│   │   └── dependency-update.yml       # Dependabot auto-update
│   ├── CODEOWNERS                      # Code review ownership
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
│
├── .devcontainer/
│   └── devcontainer.json               # VS Code Dev Container config
│
├── docker/
│   ├── docker-compose.yml              # Local development stack
│   ├── docker-compose.test.yml         # Integration test environment
│   └── nginx/
│       └── nginx.conf
│
├── k8s/
│   ├── base/                           # Kustomize base manifests
│   │   ├── namespaces.yaml
│   │   ├── configmaps/
│   │   ├── secrets/                    # Sealed secrets (Bitnami)
│   │   └── services/
│   ├── overlays/
│   │   ├── staging/
│   │   └── production/
│   └── helm/
│       └── odepm/                      # Helm chart for full stack
│
├── services/
│   ├── cve-ingestion/                  # Python service
│   ├── dependency-coordinator/         # Python service
│   ├── npm-resolver/                   # Node.js service
│   ├── pypi-resolver/                  # Python service
│   ├── maven-resolver/                 # Java service
│   ├── impact-analyzer/                # Python service
│   ├── patch-drafter/                  # Python service
│   ├── issue-creator/                  # Python service
│   └── api-gateway/                    # Python service
│
├── apps/
│   └── web-dashboard/                  # React TypeScript app
│
├── packages/
│   ├── shared-types/                   # TypeScript shared types
│   ├── ui-components/                  # Shared React component library
│   └── api-client/                     # Generated API client (OpenAPI)
│
├── libs/
│   ├── python-shared/                  # Shared Python utilities
│   │   ├── odepm_common/
│   │   │   ├── models/                 # Pydantic models
│   │   │   ├── kafka/                  # Kafka producer/consumer helpers
│   │   │   ├── db/                     # SQLAlchemy base + session
│   │   │   ├── cache/                  # Redis client wrapper
│   │   │   ├── auth/                   # Auth middleware
│   │   │   └── observability/          # OpenTelemetry setup
│   │   ├── pyproject.toml
│   │   └── README.md
│   └── scoring-engine/                 # Pure Python scoring library (no I/O)
│       ├── odepm_scoring/
│       │   ├── calculator.py
│       │   ├── factors.py
│       │   └── tiers.py
│       ├── tests/
│       └── pyproject.toml
│
├── docs/
│   ├── 01-product-requirements.md
│   ├── 02-user-stories-and-acceptance-criteria.md
│   ├── 03-information-architecture.md
│   ├── 04-system-architecture.md
│   ├── 05-database-schema.md
│   ├── 06-api-contracts.md
│   ├── 07-monorepo-structure.md
│   ├── 08-scoring-engine-spec.md
│   ├── 09-engineering-scope-definition.md
│   ├── 10-development-phases.md
│   ├── 11-environment-and-devops.md
│   └── 12-testing-strategy.md
│
├── scripts/
│   ├── setup-dev.sh                    # Developer onboarding script
│   ├── seed-db.py                      # Seed local DB with sample data
│   ├── run-migrations.sh               # Run Alembic migrations
│   └── generate-api-client.sh          # Regenerate TypeScript API client
│
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       └── 20240315_initial_schema.py
│
├── pyproject.toml                      # Root Python workspace config (Poetry)
├── pnpm-workspace.yaml                 # pnpm workspace config
├── package.json                        # Root package.json (workspace root)
├── .eslintrc.json                      # Shared ESLint config
├── .prettierrc                         # Shared Prettier config
├── .editorconfig
├── Makefile                            # Common dev commands
└── README.md
```

---

## 3. Service Directory Structure (Python Services)

Each Python service follows the same internal structure:

```
services/cve-ingestion/
├── Dockerfile
├── pyproject.toml
├── .env.example
├── README.md
├── src/
│   └── cve_ingestion/
│       ├── __init__.py
│       ├── main.py                     # FastAPI app entry point
│       ├── config.py                   # Pydantic settings from env vars
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── health.py               # GET /health, GET /ready
│       │   └── webhooks.py             # OSV webhook receiver
│       ├── services/
│       │   ├── __init__.py
│       │   ├── nvd_client.py           # NVD API client
│       │   ├── osv_client.py           # OSV API client
│       │   ├── ghsa_client.py          # GitHub Advisory client
│       │   ├── normalizer.py           # CVE normalization logic
│       │   └── publisher.py            # Kafka producer
│       ├── models/
│       │   ├── __init__.py
│       │   ├── cve.py                  # Pydantic models
│       │   └── kafka_events.py
│       ├── scheduler/
│       │   ├── __init__.py
│       │   └── jobs.py                 # APScheduler job definitions
│       └── utils/
│           ├── __init__.py
│           ├── dedup.py
│           └── version_parser.py
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_normalizer.py
    │   ├── test_nvd_client.py
    │   └── test_dedup.py
    └── integration/
        ├── test_nvd_ingestion.py
        └── test_kafka_publish.py
```

---

## 4. Service Directory Structure (Node.js — npm Resolver)

```
services/npm-resolver/
├── Dockerfile
├── package.json
├── tsconfig.json
├── .env.example
├── README.md
├── src/
│   ├── index.ts                        # Service entry point + Kafka consumer
│   ├── config.ts                       # Environment config (zod validation)
│   ├── resolvers/
│   │   ├── npmRegistryClient.ts        # npm Registry API wrapper
│   │   ├── dependencyTreeResolver.ts   # BFS/DFS tree resolution
│   │   ├── reverseIndexLookup.ts       # Who depends on package X
│   │   └── versionRangeChecker.ts      # semver range overlap checking
│   ├── graph/
│   │   ├── neo4jClient.ts              # Neo4j driver wrapper
│   │   └── graphWriter.ts              # Write nodes/edges to Neo4j
│   ├── kafka/
│   │   ├── consumer.ts                 # Consume cve.raw topic
│   │   └── producer.ts                 # Publish dependency.resolved topic
│   ├── models/
│   │   └── types.ts                    # TypeScript interfaces
│   └── utils/
│       ├── cache.ts                    # Redis caching helpers
│       ├── rateLimiter.ts              # npm API rate limiter
│       └── logger.ts                   # Pino structured logger
└── tests/
    ├── unit/
    │   ├── dependencyTreeResolver.test.ts
    │   └── versionRangeChecker.test.ts
    └── integration/
        └── npmRegistryClient.test.ts
```

---

## 5. Service Directory Structure (Java — Maven Resolver)

```
services/maven-resolver/
├── Dockerfile
├── build.gradle
├── settings.gradle
├── gradle.properties
├── .env.example
├── README.md
└── src/
    ├── main/
    │   └── java/io/odepm/maven/
    │       ├── MavenResolverApplication.java
    │       ├── config/
    │       │   ├── AppConfig.java
    │       │   └── KafkaConfig.java
    │       ├── consumer/
    │       │   └── CveEventConsumer.java
    │       ├── producer/
    │       │   └── DependencyResolvedProducer.java
    │       ├── resolver/
    │       │   ├── MavenCentralClient.java
    │       │   ├── PomParser.java
    │       │   └── DependencyTreeResolver.java
    │       ├── graph/
    │       │   └── Neo4jGraphWriter.java
    │       └── model/
    │           ├── CveEvent.java
    │           └── DependencyNode.java
    └── test/
        └── java/io/odepm/maven/
            ├── PomParserTest.java
            └── DependencyTreeResolverTest.java
```

---

## 6. Web Dashboard Structure

```
apps/web-dashboard/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── public/
│   ├── favicon.ico
│   └── og-image.png
└── src/
    ├── main.tsx                        # React app entry point
    ├── App.tsx                         # Root component + router
    ├── router.tsx                      # React Router v6 routes
    │
    ├── pages/
    │   ├── Home/
    │   │   ├── index.tsx
    │   │   └── Hero.tsx
    │   ├── Dashboard/
    │   │   ├── index.tsx
    │   │   ├── StatsCards.tsx
    │   │   └── RecentCveFeed.tsx
    │   ├── CVEs/
    │   │   ├── CveList.tsx
    │   │   ├── CveDetail.tsx
    │   │   └── CveFilters.tsx
    │   ├── Packages/
    │   │   ├── PackageSearch.tsx
    │   │   └── PackageDetail.tsx
    │   ├── Repos/
    │   │   ├── RepoSearch.tsx
    │   │   └── RepoDetail.tsx
    │   ├── Notifications/
    │   │   └── NotificationList.tsx
    │   ├── OptOut/
    │   │   └── OptOutPage.tsx
    │   └── Docs/
    │       └── DocsPage.tsx
    │
    ├── components/
    │   ├── layout/
    │   │   ├── TopNav.tsx
    │   │   ├── Sidebar.tsx
    │   │   └── PageWrapper.tsx
    │   ├── cve/
    │   │   ├── CveCard.tsx
    │   │   ├── CveBadge.tsx
    │   │   └── SeverityChip.tsx
    │   ├── graph/
    │   │   └── DependencyGraph.tsx     # Cytoscape.js wrapper
    │   ├── charts/
    │   │   ├── SeverityBreakdown.tsx
    │   │   └── CveTrend.tsx
    │   └── common/
    │       ├── Pagination.tsx
    │       ├── DataTable.tsx
    │       ├── SearchBar.tsx
    │       ├── LoadingSpinner.tsx
    │       └── EmptyState.tsx
    │
    ├── hooks/
    │   ├── useCves.ts
    │   ├── useCveDetail.ts
    │   ├── useAffectedRepos.ts
    │   └── useOptOut.ts
    │
    ├── store/
    │   ├── authStore.ts                # Zustand auth state
    │   └── filterStore.ts             # Persistent filter state
    │
    ├── api/
    │   ├── client.ts                   # Axios instance + interceptors
    │   ├── cves.ts                     # CVE API calls
    │   ├── packages.ts
    │   ├── repos.ts
    │   └── notifications.ts
    │
    ├── types/
    │   └── index.ts                    # TypeScript type definitions
    │
    └── styles/
        ├── globals.css
        └── theme.css                   # CSS custom properties
```

---

## 7. Shared Libraries

### `libs/python-shared` — Shared Python Utilities

```
libs/python-shared/
├── pyproject.toml
└── odepm_common/
    ├── models/
    │   ├── cve.py                      # Pydantic CVERecord, AffectedPackage
    │   ├── repository.py               # Repository, AffectedRepository
    │   └── kafka_events.py             # CveRawEvent, DependencyResolvedEvent
    ├── kafka/
    │   ├── producer.py                 # KafkaProducer wrapper
    │   ├── consumer.py                 # KafkaConsumer wrapper
    │   └── schemas.py                  # Avro/JSON schema registry
    ├── db/
    │   ├── base.py                     # SQLAlchemy declarative base
    │   ├── session.py                  # Async session factory
    │   └── repositories/              # Data access layer
    ├── cache/
    │   └── redis_client.py             # Redis async client + helpers
    ├── auth/
    │   ├── middleware.py               # FastAPI auth middleware
    │   └── jwt.py                      # JWT encode/decode
    └── observability/
        ├── tracing.py                  # OpenTelemetry setup
        ├── metrics.py                  # Custom metrics
        └── logging.py                  # Structured logging config
```

---

## 8. Makefile Commands

```makefile
# Developer commands
make setup          # Install all dependencies, start Docker services
make dev            # Start all services in watch mode
make test           # Run all tests
make lint           # Run all linters
make type-check     # Run mypy + tsc

# Database
make migrate        # Run pending migrations
make migrate-create name=add_column_x   # Create new migration
make db-seed        # Seed local database

# Docker
make docker-build   # Build all Docker images
make docker-up      # Start docker-compose stack
make docker-down    # Stop docker-compose stack

# Code generation
make gen-api-client     # Regenerate TypeScript API client from OpenAPI spec
make gen-openapi-spec   # Export OpenAPI spec from FastAPI

# CI simulation
make ci             # Run full CI pipeline locally (lint + test + build)
```

---

## 9. Environment Variables

Each service reads configuration exclusively from environment variables, validated with Pydantic Settings (Python) or Zod (TypeScript).

**Common variables across all services:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/odepm_db
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT  # SASL_SSL in production

# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# GitHub
GITHUB_TOKEN=ghp_...
GITHUB_TOKENS=ghp_tok1,ghp_tok2,ghp_tok3  # Pool for rotation

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
SENTRY_DSN=https://...

# App
ENVIRONMENT=development  # development | staging | production
LOG_LEVEL=INFO
SERVICE_NAME=cve-ingestion
```

---

*Last updated: 2026-04-18*
