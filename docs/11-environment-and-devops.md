# 11 — Environment & DevOps
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. Environment Strategy

ODEPM uses three environments with strict promotion gates:

| Environment | Purpose                           | Deploy Trigger        | Approval   |
|-------------|-----------------------------------|-----------------------|------------|
| Local       | Developer inner loop              | Manual (`make dev`)   | None       |
| Staging     | Integration + QA validation       | Auto on `main` merge  | None       |
| Production  | Live service                      | Tagged release        | Manual (2 approvers) |

---

## 2. Local Development Environment

### 2.1 Prerequisites

```
- Docker Desktop 4.x (with WSL2 on Windows)
- Node.js 20 LTS
- Python 3.12 (via pyenv or mise)
- Java 21 (via SDKMAN or mise)
- kubectl 1.30
- helm 3.x
- pnpm 9.x
- poetry 1.8.x
- make (via Git for Windows on Windows)
```

### 2.2 Developer Onboarding

```bash
# 1. Clone repo
git clone https://github.com/odepm-org/odepm
cd odepm

# 2. Run setup script (installs deps, configures pre-commit hooks)
make setup

# 3. Copy environment files
cp .env.example .env.local
# Edit .env.local with your local secrets (see .env.example comments)

# 4. Start all infrastructure services
make docker-up

# 5. Run database migrations
make migrate

# 6. Seed local database with sample CVE data
make db-seed

# 7. Start all services in watch mode (hot reload)
make dev

# Dashboard available at: http://localhost:3000
# API available at:       http://localhost:8000
# API Docs:               http://localhost:8000/api/docs
# Neo4j Browser:          http://localhost:7474
# Kafka UI:               http://localhost:8080
# Grafana:                http://localhost:3001 (admin/admin)
# Jaeger:                 http://localhost:16686
```

### 2.3 Local docker-compose.yml Services

| Service         | Port      | Image                            |
|-----------------|-----------|----------------------------------|
| PostgreSQL      | 5432      | postgres:16-alpine               |
| Redis           | 6379      | redis:7-alpine                   |
| Neo4j           | 7474/7687 | neo4j:5.18-community             |
| Kafka + Zookeeper | 9092    | confluentinc/cp-kafka:7.7        |
| Kafka UI        | 8080      | provectuslabs/kafka-ui           |
| LocalStack (S3) | 4566      | localstack/localstack            |
| Jaeger          | 16686     | jaegertracing/all-in-one:latest  |
| Grafana         | 3001      | grafana/grafana:latest           |
| Prometheus      | 9090      | prom/prometheus:latest           |

### 2.4 Pre-commit Hooks

Configured via `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-json
      - id: detect-private-key

  - repo: https://github.com/psf/black
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy

  - repo: https://github.com/pre-commit/mirrors-eslint
    hooks:
      - id: eslint
        files: \.(ts|tsx)$
```

---

## 3. Staging Environment

### 3.1 Infrastructure

| Component     | Spec                         | Provider           |
|---------------|------------------------------|--------------------|
| Kubernetes    | EKS 1.30, 3 nodes (t3.medium)| AWS                |
| PostgreSQL    | RDS db.t3.medium, Multi-AZ   | AWS RDS            |
| Redis         | ElastiCache t3.micro, 1 shard| AWS ElastiCache    |
| Neo4j         | AuraDB Free tier             | Neo4j AuraDB       |
| Kafka         | Confluent Basic (1 broker)   | Confluent Cloud    |
| S3            | Standard storage class       | AWS S3             |

### 3.2 Deployment to Staging

**Trigger:** Any merge to `main` branch.

```yaml
# .github/workflows/cd-staging.yml
name: Deploy to Staging
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push images
        run: make docker-build docker-push TAG=${{ github.sha }}
      - name: Update ArgoCD image tags
        run: |
          # Updates kustomize image tag in k8s/overlays/staging/
          ./scripts/update-image-tags.sh ${{ github.sha }}
          git commit -am "chore: update staging image tags to ${{ github.sha }}"
          git push
      - name: Wait for ArgoCD sync
        run: argocd app wait odepm-staging --timeout 300
      - name: Run smoke tests
        run: make smoke-test ENV=staging
```

---

## 4. Production Environment

### 4.1 Infrastructure

| Component     | Spec                                    | Provider        |
|---------------|-----------------------------------------|-----------------|
| Kubernetes    | EKS 1.30, 6 nodes (t3.large + t3.xlarge) | AWS EKS       |
| PostgreSQL    | RDS db.r7g.large, Multi-AZ, PITR       | AWS RDS         |
| Redis         | ElastiCache r7g.medium, cluster mode   | AWS ElastiCache |
| Neo4j         | AuraDB Professional (4 vCPU / 16GB)   | Neo4j AuraDB    |
| Kafka         | Confluent Standard (3 brokers, 7-day)  | Confluent Cloud |
| S3            | Standard + lifecycle to Glacier        | AWS S3          |
| CDN           | CloudFront distribution                | AWS CloudFront  |
| WAF           | AWS WAF with managed rule groups       | AWS WAF         |
| Secrets       | AWS Secrets Manager                    | AWS             |

### 4.2 Deployment to Production

**Trigger:** Manual + tagged release + 2-engineer approval

```yaml
# .github/workflows/cd-production.yml
name: Deploy to Production
on:
  push:
    tags: ['v*.*.*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production          # Requires GitHub environment approval
    steps:
      - uses: actions/checkout@v4
      - name: Build and push images
        run: make docker-build docker-push TAG=${{ github.ref_name }}
      - name: Update ArgoCD image tags (production)
        run: ./scripts/update-image-tags.sh ${{ github.ref_name }} production
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
      - name: Notify PagerDuty of deployment
        run: ./scripts/notify-deployment.sh production ${{ github.ref_name }}
```

### 4.3 Canary Deployment Strategy

For high-risk deployments:
- Deploy new version to 10% of pods (Kubernetes Canary via Argo Rollouts)
- Monitor error rate and P95 latency for 15 minutes
- Auto-promote if metrics within thresholds; auto-rollback on threshold breach

---

## 5. CI Pipeline

### 5.1 Pipeline Stages

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python lint (flake8 + black + mypy)
        run: make lint-python
      - name: TypeScript lint (eslint + tsc)
        run: make lint-typescript
      - name: Java lint (checkstyle)
        run: make lint-java

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_PASSWORD: test }
      redis:
        image: redis:7-alpine
      neo4j:
        image: neo4j:5.18-community
        env: { NEO4J_AUTH: neo4j/testpassword }
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: make test-unit
      - name: Run integration tests
        run: make test-integration
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trivy container scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          severity: CRITICAL,HIGH
      - name: Bandit Python SAST
        run: bandit -r services/ libs/ -ll
      - name: npm audit
        run: pnpm audit --audit-level=high

  build:
    runs-on: ubuntu-latest
    needs: [lint, test, security-scan]
    steps:
      - uses: actions/checkout@v4
      - name: Build all Docker images
        run: make docker-build TAG=${{ github.sha }}
      - name: Push to ECR (staging tag)
        run: make docker-push TAG=${{ github.sha }}-pr
```

### 5.2 PR Requirements

All PRs to `main` require:
- [ ] CI pipeline green (lint + test + security scan + build)
- [ ] Code review from 1 team member (same team) + 1 cross-team member for shared libs
- [ ] Test coverage ≥ 80% for changed files (enforced via Codecov)
- [ ] No new CRITICAL or HIGH security findings (Trivy)
- [ ] OpenAPI spec updated if API changed (checked by CI)

---

## 6. GitOps with ArgoCD

### 6.1 App of Apps Pattern

```
ArgoCD root app → odepm-apps
  ├── odepm-staging (namespace: odepm-*)
  └── odepm-production (namespace: odepm-*)
```

### 6.2 Sync Policy

```yaml
# Staging: auto-sync with self-heal
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true

# Production: manual sync only
syncPolicy:
  syncOptions:
    - CreateNamespace=true
  # No automated: block — manual ArgoCD sync required
```

---

## 7. Secrets Management

### 7.1 Hierarchy

```
AWS Secrets Manager
├── odepm/staging/
│   ├── database_url
│   ├── redis_url
│   ├── neo4j_password
│   ├── kafka_sasl_password
│   ├── openai_api_key
│   ├── github_tokens          (comma-separated pool)
│   └── jwt_secret
└── odepm/production/
    └── (same keys)
```

### 7.2 Secret Injection into Kubernetes

- **Tool:** External Secrets Operator (ESO)
- ESO `ExternalSecret` CRD syncs from AWS Secrets Manager → Kubernetes Secret every 1 hour
- Pods reference `secretKeyRef` in env vars; no secrets in ConfigMaps or YAML files

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: odepm-secrets
  namespace: odepm-api
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: odepm-secrets
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: odepm/production/database_url
```

### 7.3 Secret Rotation

| Secret               | Rotation Frequency | Trigger                    |
|----------------------|--------------------|----------------------------|
| GitHub API tokens    | 90 days            | Manual + AWS rotation task |
| OpenAI API key       | 90 days            | Manual                     |
| JWT secret           | 180 days           | Manual (triggers logout)   |
| DB credentials       | 90 days            | AWS RDS automated rotation |
| Redis auth token     | 180 days           | Manual                     |

---

## 8. Observability Setup

### 8.1 Metrics (Prometheus + Grafana)

**Custom metrics per service:**

| Service          | Key Metrics                                              |
|------------------|----------------------------------------------------------|
| cve-ingestion    | `cve_ingest_lag_seconds`, `cve_ingested_total`, `cve_dedup_total` |
| npm-resolver     | `resolution_duration_seconds`, `packages_resolved_total`, `queue_depth` |
| impact-analyzer  | `scores_computed_total`, `score_histogram`, `dlq_depth` |
| patch-drafter    | `llm_calls_total`, `llm_cost_usd_total`, `template_fallbacks_total` |
| issue-creator    | `issues_created_total`, `issues_failed_total`, `github_rate_limit_remaining` |
| api-gateway      | `http_requests_total`, `http_request_duration_seconds`, `rate_limited_total` |

**Grafana Dashboards:**
- `ODEPM Overview` — Key business metrics (CVEs/day, issues sent, repos protected)
- `Pipeline Health` — Kafka lag, queue depth, resolution times
- `API Performance` — Request rate, latency P50/P95/P99, error rate
- `Cost Tracking` — LLM costs, S3 usage, RDS storage
- `Infrastructure` — CPU, memory, pod restarts per service

### 8.2 Alerting

| Alert                                   | Threshold              | Severity   | Channel     |
|-----------------------------------------|------------------------|------------|-------------|
| CVE ingestion lag                       | > 20 minutes           | CRITICAL   | PagerDuty   |
| Kafka consumer lag (any topic)          | > 10,000 messages      | HIGH       | PagerDuty   |
| API error rate                          | > 5% over 5 min        | HIGH       | PagerDuty   |
| GitHub API error rate                   | > 10% over 5 min       | HIGH       | Slack       |
| LLM API error rate                      | > 10% over 5 min       | HIGH       | Slack       |
| Pod crash loop                          | > 3 restarts in 10 min | CRITICAL   | PagerDuty   |
| PostgreSQL CPU                          | > 80% for 5 min        | HIGH       | PagerDuty   |
| Redis memory                            | > 85% used             | HIGH       | Slack       |
| LLM cost per day                        | > $100                 | WARNING    | Slack       |

### 8.3 Distributed Tracing

All services instrument with OpenTelemetry SDK. Trace IDs are propagated:
- Through Kafka message headers (`traceparent`)
- Through HTTP headers (`traceparent`)
- From browser requests through the full backend chain

Jaeger stores traces for 72 hours in staging, 7 days in production.

### 8.4 Structured Logging

All services log in JSON format to stdout, collected by Fluent Bit, stored in OpenSearch.

**Required fields in every log entry:**
```json
{
  "timestamp": "ISO8601",
  "level": "DEBUG|INFO|WARN|ERROR",
  "service": "service-name",
  "trace_id": "otel-trace-id",
  "span_id": "otel-span-id",
  "environment": "staging|production",
  "message": "..."
}
```

---

## 9. Rollback Procedures

### 9.1 Immediate Rollback (< 5 min)

1. In ArgoCD, click "Rollback" to previous successful deployment
2. ArgoCD reverts to previous Helm values + image tags
3. Verify pod health and smoke tests pass

### 9.2 Database Rollback

- Alembic downgrade: `alembic downgrade -1`
- Only available for last 3 migrations (older migrations are forward-only)
- Never run in production without DBA approval

### 9.3 Kafka Event Replay

If an event is incorrectly processed:
1. Use Kafka offset reset to replay from a specific offset
2. Use idempotency keys in all consumers to prevent double-processing

---

## 10. On-Call Runbooks (Index)

| Alert                      | Runbook                                    |
|----------------------------|--------------------------------------------|
| CVE ingestion lag          | `docs/runbooks/cve-ingestion-lag.md`       |
| Kafka consumer lag         | `docs/runbooks/kafka-consumer-lag.md`      |
| API high error rate        | `docs/runbooks/api-high-error-rate.md`     |
| GitHub rate limit exceeded | `docs/runbooks/github-rate-limit.md`       |
| Neo4j connection failure   | `docs/runbooks/neo4j-failure.md`           |
| PostgreSQL high CPU        | `docs/runbooks/postgres-high-cpu.md`       |
| Service pod crash loop     | `docs/runbooks/pod-crash-loop.md`          |

---

*Last updated: 2026-04-18*
