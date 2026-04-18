# Propex — Hardening Checklist (Phase 6)

## Backend Hardening

### PostgreSQL Performance
- [ ] Enable `pg_stat_statements` extension:
  ```sql
  CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
  ```
- [ ] Run slow query analysis after 24h of traffic:
  ```sql
  SELECT query, calls, mean_exec_time, total_exec_time
  FROM pg_stat_statements
  ORDER BY total_exec_time DESC
  LIMIT 20;
  ```
- [ ] Add composite index for `affected_repositories` hot query path:
  ```sql
  CREATE INDEX CONCURRENTLY idx_affected_repos_cve_score
  ON affected_repositories(cve_id, propex_score DESC);
  
  CREATE INDEX CONCURRENTLY idx_notifications_repo
  ON issued_notifications(repository_url, success);
  ```
- [ ] Verify autovacuum is running: `SELECT schemaname, relname, last_autovacuum FROM pg_stat_user_tables;`

### Redis Cache Verification
- [ ] Check hit rate: `docker exec propex-redis redis-cli INFO stats | grep keyspace`
- [ ] Target: `keyspace_hits / (keyspace_hits + keyspace_misses) > 85%`
- [ ] If cache hit rate < 85%: review TTL values, pre-warm cache for top 100 CVEs

### OWASP ZAP Security Scan
```bash
# Run ZAP baseline scan against API Gateway
docker run -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t http://host.docker.internal:8006 \
  -r zap_report.html

# Fix all HIGH findings before launch. Accept MEDIUM with documented risk.
```

- [ ] No HIGH findings in `zap_report.html`
- [ ] Verify CORS is restricted to dashboard origin in production
- [ ] Verify no sensitive env vars leaked in API responses
- [ ] Verify all POST/PATCH endpoints require Content-Type: application/json

### Rate Limiting (API Gateway)
- [ ] Add Redis rate limiter middleware to `api-gateway/src/main.py`:
  - 1,000 requests/hour per IP (unauthenticated)
  - 5,000 requests/hour per API key (authenticated)
  - Returns `429 Too Many Requests` with `Retry-After` header

---

## Frontend Hardening

### Lighthouse Audit
```bash
npx lighthouse http://localhost:5173 --output=json --output-path=./lighthouse-report.json
# Target: Performance ≥ 90, Accessibility ≥ 90, SEO ≥ 90
```

- [ ] Performance ≥ 90
- [ ] Accessibility ≥ 90
- [ ] Best Practices ≥ 90
- [ ] SEO ≥ 90

### Open Graph Meta Tags
Add to each page's `<head>`:
```html
<meta property="og:title" content="Propex — Open Source Vulnerability Tracker" />
<meta property="og:description" content="Track CVE propagation across npm, PyPI, and Maven dependencies in real-time." />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://propex.dev" />
<meta property="og:image" content="https://propex.dev/og-image.png" />
```

- [ ] Add `public/robots.txt`
- [ ] Add `public/sitemap.xml`

---

## ML/AI Hardening

### Gemini Token Monitoring (Grafana)
- [ ] Add Grafana panel: `SELECT DATE(called_at), SUM(prompt_tokens+output_tokens) FROM gemini_usage_log GROUP BY 1 ORDER BY 1`
- [ ] Configure alert: daily token usage > 800K → send email via UptimeRobot
- [ ] Confirm all 12 fallback templates render correctly:
  ```python
  from src.prompts.templates import get_fallback_patch
  for eco in ["npm", "pypi", "maven"]:
      for score in [9.5, 7.5, 5.0, 2.0]:
          print(get_fallback_patch(eco, cve_id="CVE-TEST", package_name="test", 
                repo_url="https://github.com/a/b", version_range="<1.0", fix_version="1.0"))
  ```

---

## Infrastructure

### UptimeRobot Configuration
Monitor these endpoints every 5 minutes:
| Endpoint | URL | Alert if Down |
|---|---|---|
| API Health | `https://api.propex.dev/health` | Immediately |
| Dashboard | `https://propex.dev` | Immediately |
| Redpanda | Internal only | Via Grafana |
| Neo4j | Internal only | Via Grafana |

### Upptime Status Page
Repository: `github.com/SoleSarthak/propex-status`
- [ ] Create `.github/workflows/uptime.yml` with Upptime action
- [ ] Configure `history/` folder for incident history
- [ ] Link status page in dashboard footer

### Fly.io Deployment Steps
```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login
fly auth login

# 3. Create apps
fly apps create propex-api-gateway
fly apps create propex-impact-analyzer
fly apps create propex-patch-drafter
fly apps create propex-issue-creator

# 4. Set secrets for each app
fly secrets set DATABASE_URL="postgresql://..." -a propex-api-gateway
fly secrets set GEMINI_API_KEY="..." -a propex-patch-drafter
fly secrets set GITHUB_TOKEN="..." -a propex-issue-creator

# 5. Deploy
fly deploy --config infra/fly/fly.api-gateway.toml
fly deploy --config infra/fly/fly.impact-analyzer.toml
```
