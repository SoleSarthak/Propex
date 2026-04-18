# 06 — API Contracts
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18  
**Base URL:** `https://api.odepm.io/api/v1`  
**Spec Format:** OpenAPI 3.1

---

## 1. Authentication

All API endpoints (except public read-only ones) require authentication via Bearer token.

```http
Authorization: Bearer odepm_sk_xxxxxxxxxxxxxxxxxxxx
```

**Public Endpoints (no auth required):**
- `GET /cves`
- `GET /cves/{cve_id}`
- `GET /packages/{ecosystem}/{name}`

**Authenticated Endpoints:** All POST/PUT/DELETE plus export and notification endpoints.

---

## 2. Common Response Formats

### 2.1 Paginated List Response
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 1234,
    "total_pages": 50,
    "has_next": true,
    "has_prev": false
  }
}
```

### 2.2 Error Response
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "CVE with ID CVE-2024-99999 was not found",
    "details": {}
  }
}
```

### 2.3 Error Codes

| HTTP Status | Code                    | Description                        |
|-------------|-------------------------|------------------------------------|
| 400         | VALIDATION_ERROR        | Invalid request parameters          |
| 401         | UNAUTHORIZED            | Missing or invalid auth token       |
| 403         | FORBIDDEN               | Insufficient permissions            |
| 404         | RESOURCE_NOT_FOUND      | Resource does not exist             |
| 409         | CONFLICT                | Resource already exists             |
| 422         | UNPROCESSABLE_ENTITY    | Business logic validation failure   |
| 429         | RATE_LIMIT_EXCEEDED     | Too many requests                   |
| 500         | INTERNAL_ERROR          | Unexpected server error             |
| 503         | SERVICE_UNAVAILABLE     | Dependency unavailable              |

---

## 3. CVE Endpoints

### `GET /cves` — List CVEs

**Query Parameters:**

| Parameter    | Type    | Required | Description                                      |
|--------------|---------|----------|--------------------------------------------------|
| page         | integer | No       | Page number (default: 1)                         |
| per_page     | integer | No       | Results per page (default: 25, max: 100)         |
| ecosystem    | string  | No       | Filter by: `npm`, `pypi`, `maven` (comma-sep)    |
| severity     | string  | No       | Filter by: `Critical`, `High`, `Medium`, `Low`   |
| published_after | string | No    | ISO8601 date                                     |
| published_before | string | No   | ISO8601 date                                     |
| q            | string  | No       | Full-text search (CVE ID, package, description)  |
| sort         | string  | No       | `published_at` (default), `cvss_score`, `affected_count` |
| order        | string  | No       | `desc` (default), `asc`                          |

**Response: `200 OK`**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "cve_id": "CVE-2024-12345",
      "source": "nvd",
      "published_at": "2024-03-15T10:00:00Z",
      "cvss_score": 9.8,
      "severity_tier": "Critical",
      "description": "Prototype pollution vulnerability...",
      "affected_packages": [
        {
          "ecosystem": "npm",
          "name": "lodash",
          "versions_affected": ["<4.17.21"],
          "fixed_version": "4.17.21"
        }
      ],
      "affected_repo_count": 12540,
      "resolution_status": "resolved"
    }
  ],
  "pagination": { "page": 1, "per_page": 25, "total": 847 }
}
```

---

### `GET /cves/{cve_id}` — Get CVE Details

**Path Parameters:** `cve_id` — CVE identifier (e.g., `CVE-2024-12345`)

**Response: `200 OK`**
```json
{
  "id": "uuid",
  "cve_id": "CVE-2024-12345",
  "source": "nvd",
  "published_at": "2024-03-15T10:00:00Z",
  "last_modified_at": "2024-03-16T12:00:00Z",
  "cvss_score": 9.8,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "severity_tier": "Critical",
  "description": "Full description...",
  "affected_packages": [...],
  "affected_repo_counts": {
    "Critical": 234,
    "High": 1205,
    "Medium": 8901,
    "Low": 2200
  },
  "resolution_status": "resolved",
  "resolved_at": "2024-03-15T10:28:00Z",
  "references": [
    "https://nvd.nist.gov/vuln/detail/CVE-2024-12345",
    "https://github.com/lodash/lodash/issues/XXXX"
  ]
}
```

---

### `GET /cves/{cve_id}/affected-repos` — List Affected Repos for CVE

**Query Parameters:** `page`, `per_page`, `severity`, `context_type` (`runtime|dev`), `sort` (`score|downloads|depth`), `order`, `q` (repo name search)

**Response: `200 OK`**
```json
{
  "data": [
    {
      "id": "uuid",
      "repo_url": "https://github.com/facebook/react",
      "repo_owner": "facebook",
      "repo_name": "react",
      "dependency_depth": 2,
      "dependency_path": ["react", "fbjs", "lodash"],
      "dependency_file": "package.json",
      "version_spec": "^4.16.0",
      "context_type": "runtime",
      "context_score": 9.1,
      "severity_tier": "Critical",
      "weekly_downloads": 25000000,
      "notification_status": "sent",
      "issue_url": "https://github.com/facebook/react/issues/99999",
      "notified_at": "2024-03-15T10:45:00Z"
    }
  ],
  "pagination": { "page": 1, "per_page": 25, "total": 12540 }
}
```

---

### `POST /cves` — Submit Manual CVE (Auth Required)

**Request Body:**
```json
{
  "cve_id": "CVE-2024-99999",
  "cvss_score": 8.1,
  "cvss_vector": "CVSS:3.1/...",
  "description": "Description of vulnerability...",
  "affected_packages": [
    {
      "ecosystem": "pypi",
      "name": "requests",
      "versions_affected": ["<2.32.0"],
      "fixed_version": "2.32.0"
    }
  ]
}
```

**Response: `201 Created`**
```json
{ "id": "uuid", "cve_id": "CVE-2024-99999", "status": "processing" }
```

---

## 4. Package Endpoints

### `GET /packages/{ecosystem}/{name}` — Get Package Details

**Path Parameters:** `ecosystem` (`npm|pypi|maven`), `name` (package name)

**Response: `200 OK`**
```json
{
  "id": "uuid",
  "ecosystem": "npm",
  "name": "lodash",
  "latest_version": "4.17.21",
  "weekly_downloads": 50000000,
  "total_dependents": 123456,
  "description": "Lodash modular utilities.",
  "homepage_url": "https://lodash.com",
  "repository_url": "https://github.com/lodash/lodash",
  "active_cves": [
    { "cve_id": "CVE-2024-12345", "cvss_score": 9.8, "fixed_version": "4.17.21" }
  ]
}
```

---

### `GET /packages/{ecosystem}/{name}/dependents` — List Packages Depending On This

**Query Parameters:** `page`, `per_page`, `depth` (filter by exact depth), `sort` (`downloads|depth`)

**Response: `200 OK`**
```json
{
  "data": [
    {
      "ecosystem": "npm",
      "name": "express",
      "version": "4.18.0",
      "depth": 1,
      "dependency_type": "runtime",
      "weekly_downloads": 30000000
    }
  ],
  "pagination": { ... }
}
```

---

### `GET /packages/{ecosystem}/{name}/cves` — List CVEs Affecting Package

**Response: `200 OK`** — Returns paginated list of CVE objects with `versions_affected` and `fixed_version`.

---

## 5. Repository Endpoints

### `GET /repos/{owner}/{name}` — Get Repository Details

**Response: `200 OK`**
```json
{
  "id": "uuid",
  "url": "https://github.com/facebook/react",
  "owner": "facebook",
  "name": "react",
  "stars": 220000,
  "language": "JavaScript",
  "is_archived": false,
  "active_vulnerability_count": 3,
  "critical_count": 1,
  "high_count": 2,
  "is_opted_out": false
}
```

---

### `GET /repos/{owner}/{name}/vulnerabilities` — List CVEs Affecting Repo

**Query Parameters:** `page`, `per_page`, `severity`, `status` (`pending|sent|patched`)

**Response: `200 OK`**
```json
{
  "data": [
    {
      "cve_id": "CVE-2024-12345",
      "cvss_score": 9.8,
      "severity_tier": "Critical",
      "package_name": "lodash",
      "dependency_path": ["my-app", "express", "lodash"],
      "context_score": 8.7,
      "notification_status": "sent",
      "issue_url": "https://github.com/owner/repo/issues/42",
      "maintainer_status": null
    }
  ],
  "pagination": { ... }
}
```

---

### `PATCH /repos/{owner}/{name}/vulnerabilities/{cve_id}` — Update Maintainer Status (Auth Required)

**Request Body:**
```json
{
  "maintainer_status": "patched | not_affected | wont_fix"
}
```

**Response: `200 OK`**
```json
{ "cve_id": "CVE-2024-12345", "maintainer_status": "patched", "updated_at": "2024-03-16T09:00:00Z" }
```

---

## 6. Notification Endpoints

### `GET /notifications` — List All Notifications (Auth Required)

**Query Parameters:** `page`, `per_page`, `status` (`created|failed|skipped`), `cve_id`, `start_date`, `end_date`

**Response: `200 OK`**
```json
{
  "data": [
    {
      "id": "uuid",
      "cve_id": "CVE-2024-12345",
      "repo_url": "https://github.com/owner/repo",
      "issue_url": "https://github.com/owner/repo/issues/42",
      "status": "created",
      "generation_method": "llm",
      "sent_at": "2024-03-15T10:45:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

### `POST /notifications/{id}/retry` — Retry Failed Notification (Auth Required)

**Response: `202 Accepted`**
```json
{ "id": "uuid", "status": "queued", "message": "Notification queued for retry." }
```

---

## 7. Opt-Out Endpoints

### `POST /opt-out` — Register Opt-Out (Requires GitHub OAuth)

**Request Body:**
```json
{
  "scope_type": "repo | org",
  "scope_value": "https://github.com/owner/repo | org_name",
  "reason": "Optional reason text"
}
```

**Response: `201 Created`**
```json
{ "id": "uuid", "scope_type": "repo", "scope_value": "...", "is_active": true }
```

---

### `DELETE /opt-out` — Reverse Opt-Out (Requires GitHub OAuth)

**Request Body:** `{ "scope_type": "repo", "scope_value": "..." }`

**Response: `200 OK`**
```json
{ "message": "Opt-out reversed. You will receive future notifications." }
```

---

### `GET /opt-out` — List Opt-Outs for Authenticated User (Requires GitHub OAuth)

**Response: `200 OK`**
```json
{
  "data": [
    { "scope_type": "repo", "scope_value": "https://github.com/me/my-lib", "opted_out_at": "..." }
  ]
}
```

---

## 8. Export Endpoints

### `POST /exports` — Request Data Export (Auth Required)

**Request Body:**
```json
{
  "export_type": "cve_list | affected_repos",
  "format": "csv | json",
  "filters": {
    "cve_id": "CVE-2024-12345",
    "severity": ["Critical", "High"],
    "ecosystem": ["npm"]
  }
}
```

**Response: `202 Accepted`**
```json
{ "export_id": "uuid", "status": "processing", "estimated_ready_in_seconds": 30 }
```

---

### `GET /exports/{export_id}` — Check Export Status & Get Download URL (Auth Required)

**Response: `200 OK`**
```json
{
  "export_id": "uuid",
  "status": "ready | processing | failed",
  "download_url": "https://s3.amazonaws.com/odepm-data/exports/...?presigned...",
  "download_expires_at": "2024-03-16T10:00:00Z",
  "row_count": 12540
}
```

---

## 9. API Keys Endpoints

### `POST /api-keys` — Create API Key (Auth Required)

**Request Body:** `{ "name": "My Integration Key" }`

**Response: `201 Created`**
```json
{
  "id": "uuid",
  "name": "My Integration Key",
  "key": "odepm_sk_xxxxxxxxxxxxxxxxxxxx",  // Only shown ONCE
  "prefix": "odepm_sk",
  "created_at": "2024-03-15T10:00:00Z",
  "expires_at": null
}
```

---

### `GET /api-keys` — List API Keys (Auth Required)

Returns all keys for the authenticated user. The `key` field is never returned after creation (only `prefix`).

---

### `DELETE /api-keys/{key_id}` — Revoke API Key (Auth Required)

**Response: `200 OK`** `{ "message": "API key revoked." }`

---

## 10. Rate Limits

| Endpoint Group            | Limit          | Window    |
|---------------------------|----------------|-----------|
| Public read endpoints     | 100 requests   | 1 minute  |
| Authenticated read        | 1,000 requests | 1 hour    |
| Authenticated write       | 100 requests   | 1 hour    |
| Export requests           | 10 requests    | 1 hour    |
| Manual CVE submission     | 20 requests    | 1 day     |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1710508800
```

---

## 11. Webhooks (Future — Phase 2)

ODEPM will support outbound webhooks to notify enterprise users of new CVE impacts.

**Planned Events:**
- `cve.new` — New CVE ingested
- `cve.impact_scored` — Impact scoring complete for a CVE
- `notification.sent` — Issue created on a repository
- `repo.patched` — Maintainer marks finding as patched

---

*Last updated: 2026-04-18*
