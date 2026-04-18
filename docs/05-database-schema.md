# 05 — Database Schema
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. PostgreSQL Schema

### 1.1 Schema Overview

```
odepm_db
├── cves                         # Canonical CVE records
├── cve_affected_packages        # Packages affected by each CVE
├── packages                     # Package metadata cache
├── repositories                 # Repository metadata cache
├── affected_repositories        # Repo-CVE impact records
├── issued_notifications         # Notification dispatch history
├── opt_out_registry             # Maintainer opt-out registry
├── users                        # Dashboard user accounts
├── api_keys                     # API authentication keys
└── audit_log                    # Immutable action audit trail
```

---

### 1.2 Full DDL

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For GIN indexes on arrays

-- ============================================================
-- CVE TABLES
-- ============================================================

CREATE TABLE cves (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cve_id              VARCHAR(25) UNIQUE NOT NULL,        -- e.g. CVE-2024-12345
    source              VARCHAR(10) NOT NULL                -- nvd | osv | ghsa | manual
                        CHECK (source IN ('nvd', 'osv', 'ghsa', 'manual')),
    published_at        TIMESTAMPTZ NOT NULL,
    last_modified_at    TIMESTAMPTZ,
    cvss_score          DECIMAL(3,1),                       -- 0.0 - 10.0
    cvss_version        VARCHAR(5),                         -- 3.0 | 3.1 | 4.0
    cvss_vector         TEXT,
    severity_tier       VARCHAR(10)                         -- Critical | High | Medium | Low
                        GENERATED ALWAYS AS (
                            CASE
                                WHEN cvss_score >= 9.0 THEN 'Critical'
                                WHEN cvss_score >= 7.0 THEN 'High'
                                WHEN cvss_score >= 4.0 THEN 'Medium'
                                ELSE 'Low'
                            END
                        ) STORED,
    description         TEXT,
    raw_data            JSONB,                              -- Original source response
    resolution_status   VARCHAR(20) DEFAULT 'pending'      -- pending | resolving | resolved | failed
                        CHECK (resolution_status IN ('pending', 'resolving', 'resolved', 'failed')),
    resolved_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cves_published_at ON cves (published_at DESC);
CREATE INDEX idx_cves_severity_tier ON cves (severity_tier);
CREATE INDEX idx_cves_resolution_status ON cves (resolution_status);
CREATE INDEX idx_cves_description_gin ON cves USING GIN (to_tsvector('english', description));

-- ------------------------------------------------------------

CREATE TABLE cve_affected_packages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cve_id          UUID NOT NULL REFERENCES cves(id) ON DELETE CASCADE,
    ecosystem       VARCHAR(10) NOT NULL
                    CHECK (ecosystem IN ('npm', 'pypi', 'maven')),
    package_name    VARCHAR(300) NOT NULL,
    versions_affected TEXT[] NOT NULL,                     -- e.g. [">=4.0.0", "<4.17.21"]
    fixed_version   VARCHAR(100),
    purl            TEXT,                                  -- Package URL (PURL) standard
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (cve_id, ecosystem, package_name)
);

CREATE INDEX idx_cap_cve_id ON cve_affected_packages (cve_id);
CREATE INDEX idx_cap_ecosystem_name ON cve_affected_packages (ecosystem, package_name);

-- ============================================================
-- PACKAGE & REPOSITORY TABLES
-- ============================================================

CREATE TABLE packages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ecosystem           VARCHAR(10) NOT NULL
                        CHECK (ecosystem IN ('npm', 'pypi', 'maven')),
    name                VARCHAR(300) NOT NULL,
    latest_version      VARCHAR(100),
    weekly_downloads    BIGINT DEFAULT 0,
    total_dependents    INTEGER DEFAULT 0,                 -- # of packages depending on this
    homepage_url        TEXT,
    repository_url      TEXT,
    description         TEXT,
    metadata_fetched_at TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (ecosystem, name)
);

CREATE INDEX idx_packages_eco_name ON packages (ecosystem, name);
CREATE INDEX idx_packages_downloads ON packages (weekly_downloads DESC);

-- ------------------------------------------------------------

CREATE TABLE repositories (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url                 TEXT UNIQUE NOT NULL,               -- https://github.com/owner/repo
    owner               VARCHAR(200) NOT NULL,
    name                VARCHAR(200) NOT NULL,
    full_name           VARCHAR(400) GENERATED ALWAYS AS (owner || '/' || name) STORED,
    default_branch      VARCHAR(100) DEFAULT 'main',
    stars               INTEGER DEFAULT 0,
    forks               INTEGER DEFAULT 0,
    language            VARCHAR(50),
    is_archived         BOOLEAN DEFAULT FALSE,
    is_fork             BOOLEAN DEFAULT FALSE,
    weekly_downloads    BIGINT DEFAULT 0,                   -- From package registry if library
    metadata_fetched_at TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_repos_url ON repositories (url);
CREATE INDEX idx_repos_owner ON repositories (owner);
CREATE INDEX idx_repos_stars ON repositories (stars DESC);

-- ============================================================
-- IMPACT RECORDS
-- ============================================================

CREATE TABLE affected_repositories (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cve_affected_package_id     UUID NOT NULL REFERENCES cve_affected_packages(id) ON DELETE CASCADE,
    repository_id               UUID REFERENCES repositories(id),
    repo_url                    TEXT NOT NULL,
    repo_owner                  TEXT NOT NULL,
    repo_name                   TEXT NOT NULL,

    -- Dependency context
    dependency_depth            INTEGER NOT NULL DEFAULT 1, -- 1 = direct
    dependency_path             TEXT[] NOT NULL,            -- ["my-app", "express", "lodash"]
    dependency_file             TEXT,                       -- "package.json", "requirements.txt"
    version_spec                TEXT,                       -- "^4.16.0"
    context_type                VARCHAR(20)                 -- runtime | dev | peer | test | optional
                                CHECK (context_type IN ('runtime', 'dev', 'peer', 'test', 'optional', 'unknown')),

    -- Scoring
    cvss_base                   DECIMAL(3,1),
    depth_factor                DECIMAL(4,3),
    context_multiplier          DECIMAL(4,3),
    popularity_factor           DECIMAL(4,3),
    context_score               DECIMAL(4,2),               -- 1.0 - 10.0
    severity_tier               VARCHAR(10)                 -- Critical | High | Medium | Low
                                CHECK (severity_tier IN ('Critical', 'High', 'Medium', 'Low')),

    -- Notification
    notification_status         VARCHAR(20) DEFAULT 'pending'
                                CHECK (notification_status IN ('pending', 'queued', 'sent', 'skipped_opt_out', 'skipped_duplicate', 'failed')),
    issue_url                   TEXT,
    notified_at                 TIMESTAMPTZ,

    -- Maintainer feedback
    maintainer_status           VARCHAR(20)                 -- null | patched | not_affected | wont_fix
                                CHECK (maintainer_status IN (NULL, 'patched', 'not_affected', 'wont_fix')),
    maintainer_updated_at       TIMESTAMPTZ,

    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (cve_affected_package_id, repo_url)
);

CREATE INDEX idx_ar_cap_id ON affected_repositories (cve_affected_package_id);
CREATE INDEX idx_ar_repo_url ON affected_repositories (repo_url);
CREATE INDEX idx_ar_severity ON affected_repositories (severity_tier);
CREATE INDEX idx_ar_notification_status ON affected_repositories (notification_status);
CREATE INDEX idx_ar_context_score ON affected_repositories (context_score DESC);
CREATE INDEX idx_ar_dep_path_gin ON affected_repositories USING GIN (dependency_path);

-- ============================================================
-- NOTIFICATION TABLES
-- ============================================================

CREATE TABLE issued_notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cve_id          VARCHAR(25) NOT NULL,
    repo_url        TEXT NOT NULL,
    issue_url       TEXT,
    issue_number    INTEGER,
    github_repo     TEXT,                                   -- owner/repo

    issue_title     TEXT,
    issue_body      TEXT,                                   -- Full generated text
    issue_labels    TEXT[],

    generation_method VARCHAR(20)                           -- llm | template
                    CHECK (generation_method IN ('llm', 'template')),
    llm_model       VARCHAR(50),                            -- gpt-4o-mini, etc.

    status          VARCHAR(20) NOT NULL DEFAULT 'created'
                    CHECK (status IN ('draft', 'created', 'failed', 'skipped')),
    retry_count     INTEGER DEFAULT 0,
    error_message   TEXT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at         TIMESTAMPTZ,

    UNIQUE (cve_id, repo_url)
);

CREATE INDEX idx_notif_cve_id ON issued_notifications (cve_id);
CREATE INDEX idx_notif_repo_url ON issued_notifications (repo_url);
CREATE INDEX idx_notif_status ON issued_notifications (status);
CREATE INDEX idx_notif_created_at ON issued_notifications (created_at DESC);

-- ============================================================
-- OPT-OUT REGISTRY
-- ============================================================

CREATE TABLE opt_out_registry (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_type      VARCHAR(10) NOT NULL                    -- repo | org
                    CHECK (scope_type IN ('repo', 'org')),
    scope_value     TEXT NOT NULL,                          -- repo URL or org name
    github_user     VARCHAR(200),                           -- Who opted out
    opted_out_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    opted_in_at     TIMESTAMPTZ,                            -- If reversed
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    reason          TEXT,

    UNIQUE (scope_type, scope_value)
);

CREATE INDEX idx_opt_out_scope ON opt_out_registry (scope_type, scope_value) WHERE is_active = TRUE;

-- ============================================================
-- USER MANAGEMENT
-- ============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_id       BIGINT UNIQUE NOT NULL,
    github_login    VARCHAR(200) NOT NULL,
    github_email    TEXT,
    avatar_url      TEXT,
    role            VARCHAR(20) NOT NULL DEFAULT 'viewer'
                    CHECK (role IN ('viewer', 'analyst', 'admin')),
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_github_id ON users (github_id);

-- ------------------------------------------------------------

CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    key_prefix      VARCHAR(8) NOT NULL,                    -- First 8 chars for display
    key_hash        TEXT NOT NULL,                          -- bcrypt hash of full key
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    last_used_at    TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    rate_limit      INTEGER NOT NULL DEFAULT 1000           -- Requests per hour
);

CREATE INDEX idx_api_keys_user_id ON api_keys (user_id);
CREATE INDEX idx_api_keys_prefix ON api_keys (key_prefix) WHERE is_active = TRUE;

-- ============================================================
-- AUDIT LOG
-- ============================================================

CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id),
    service         VARCHAR(50),                            -- 'issue-creator', 'api-gateway', etc.
    action          VARCHAR(100) NOT NULL,                  -- 'create_issue', 'opt_out', etc.
    resource_type   VARCHAR(50),                            -- 'cve', 'repository', 'api_key'
    resource_id     TEXT,
    metadata        JSONB,
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user_id ON audit_log (user_id);
CREATE INDEX idx_audit_action ON audit_log (action);
CREATE INDEX idx_audit_created_at ON audit_log (created_at DESC);
-- Note: No UPDATE or DELETE allowed on this table (enforced via policy)
```

---

## 2. Neo4j Graph Schema

### 2.1 Node Labels & Properties

```cypher
-- Package node
(:Package {
  name: "lodash",
  ecosystem: "npm",
  version: "4.16.0",
  purl: "pkg:npm/lodash@4.16.0",
  weekly_downloads: 50000000,
  is_vulnerable: true,
  created_at: datetime()
})

-- Repository node
(:Repository {
  url: "https://github.com/owner/repo",
  owner: "facebook",
  name: "react",
  stars: 220000,
  weekly_downloads: 25000000,
  language: "JavaScript",
  created_at: datetime()
})

-- CVE node
(:CVE {
  id: "CVE-2024-12345",
  cvss_score: 9.8,
  published_at: datetime("2024-03-15"),
  severity_tier: "Critical"
})
```

### 2.2 Relationship Types & Properties

```cypher
-- Package dependency
(:Package)-[:DEPENDS_ON {
  depth: 2,
  type: "runtime|dev|peer|test",
  version_spec: "^4.16.0",
  resolved_version: "4.16.6"
}]->(:Package)

-- Repository uses package
(:Repository)-[:USES {
  depth: 1,
  type: "runtime|dev",
  version_spec: "^4.16.0",
  resolved_version: "4.16.6",
  manifest_file: "package.json",
  context_score: 8.7,
  severity_tier: "Critical"
}]->(:Package)

-- CVE affects package
(:CVE)-[:AFFECTS {
  versions: [">=4.0.0", "<4.17.21"],
  fixed_version: "4.17.21",
  purl: "pkg:npm/lodash@4.16.0"
}]->(:Package)
```

### 2.3 Key Queries

```cypher
-- Find all repositories affected by a CVE (direct + transitive, up to depth 5)
MATCH (c:CVE {id: $cve_id})-[:AFFECTS]->(p:Package)
MATCH path = (r:Repository)-[:USES*1..5]->(p)
RETURN r.url, r.name, length(path) as depth
ORDER BY depth ASC, r.weekly_downloads DESC
LIMIT 1000;

-- Get dependency path from repo to vulnerable package
MATCH (r:Repository {url: $repo_url})
MATCH path = (r)-[:USES*1..5]->(p:Package)
WHERE (c:CVE {id: $cve_id})-[:AFFECTS]->(p)
RETURN [node in nodes(path) | node.name] as dep_chain
ORDER BY length(path) ASC
LIMIT 1;

-- Count affected repos per CVE by severity tier
MATCH (c:CVE)-[:AFFECTS]->(p:Package)<-[:USES]-(r:Repository)
WHERE c.id = $cve_id
RETURN r.severity_tier, count(r) as repo_count
ORDER BY repo_count DESC;
```

---

## 3. Redis Key Patterns

| Key Pattern                              | Value                     | TTL      | Set By               |
|------------------------------------------|---------------------------|----------|----------------------|
| `cve:{cve_id}`                           | JSON string               | 3600s    | api-gateway          |
| `cve:list:{filter_hash}`                 | JSON array of IDs         | 300s     | api-gateway          |
| `pkg:{eco}:{name}:{ver}`                 | JSON string               | 86400s   | resolvers            |
| `pkg:downloads:{eco}:{name}`             | Integer                   | 86400s   | resolvers            |
| `score:{repo_url_b64}:{cve_id}`          | Float (8.7)               | 3600s    | impact-analyzer      |
| `issue_text:{cve_id}:{dep_path_hash}`    | String (issue markdown)   | 604800s  | patch-drafter        |
| `opt_out:{scope_type}:{scope_val_b64}`   | "1"                       | 86400s   | opt-out-service      |
| `github_ratelimit:{token_id}`            | Integer (remaining)       | 3600s    | issue-creator        |
| `session:{session_id}`                   | JSON user object          | 86400s   | api-gateway          |
| `api_rate:{api_key_prefix}:{hour}`       | Integer (request count)   | 7200s    | api-gateway          |

---

## 4. S3 Bucket Structure

```
s3://odepm-data/
├── raw-cve-responses/
│   ├── nvd/{year}/{month}/{day}/{cve_id}.json
│   ├── osv/{year}/{month}/{day}/{advisory_id}.json
│   └── ghsa/{year}/{month}/{day}/{ghsa_id}.json
│
├── dependency-snapshots/
│   ├── npm/{package_name}/{version}/tree.json
│   ├── pypi/{package_name}/{version}/tree.json
│   └── maven/{group_id}/{artifact_id}/{version}/tree.json
│
├── exports/
│   └── user-exports/{user_id}/{export_id}.{csv|json}
│
├── issue-templates/
│   └── templates/default.md
│
└── sbom-exports/
    └── {repo_owner}/{repo_name}/{cve_id}/sbom.json
```

---

## 5. Database Migrations Strategy

- **Tool:** Alembic (Python) for PostgreSQL migrations
- **Naming:** `{timestamp}_{description}.py` e.g. `20240315_add_severity_tier_to_cves.py`
- **Rules:**
  - All migrations are forward-only in production
  - Backward migrations available for dev/test only
  - Never drop columns (mark as deprecated, remove after 3 releases)
  - All schema changes reviewed by 2 engineers before merge
  - Migrations run automatically in CI/CD before service deployment

---

*Last updated: 2026-04-18*
