# 03 — Information Architecture
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## 1. Site Map

```
ODEPM Platform
│
├── / (Home / Landing Page)
│   ├── Hero: Platform overview + CTA
│   ├── Stats: CVEs tracked, repos protected, issues sent
│   └── Recent CVE feed (public, no auth)
│
├── /dashboard (Analyst Dashboard) ← Requires Auth
│   ├── Overview widgets
│   │   ├── CVEs in last 24h
│   │   ├── Critical findings unaddressed
│   │   └── Issues sent today
│   ├── Recent CVE feed
│   └── Quick search
│
├── /cves (CVE Explorer)
│   ├── CVE List (paginated, filterable)
│   └── /cves/:cve-id (CVE Detail)
│       ├── Summary + CVSS
│       ├── Affected Packages
│       ├── Affected Repositories (paginated, sortable)
│       └── Dependency Graph Visualization
│
├── /packages (Package Explorer)
│   ├── Package Search
│   └── /packages/:ecosystem/:name (Package Detail)
│       ├── CVEs affecting this package
│       ├── Dependents list
│       └── Version timeline
│
├── /repos (Repository Explorer)
│   ├── Repository Search
│   └── /repos/:owner/:name (Repo Detail)
│       ├── CVE exposure history
│       ├── Dependency tree
│       └── Notification history
│
├── /notifications (Notification Center) ← Requires Auth
│   ├── All notifications sent (paginated)
│   ├── Filter by status, CVE, date
│   └── Retry failed notifications
│
├── /opt-out (Maintainer Opt-Out)
│   ├── GitHub OAuth login
│   ├── Repository list
│   └── Toggle opt-out per repo / per org
│
├── /api-keys (API Key Management) ← Requires Auth
│   ├── Create API key
│   ├── List active keys
│   └── Revoke key
│
├── /docs (Documentation)
│   ├── Getting Started
│   ├── API Reference (OpenAPI UI)
│   ├── How Scoring Works
│   └── Opt-Out Guide
│
└── /settings (Account Settings) ← Requires Auth
    ├── Profile (GitHub OAuth info)
    ├── Notification preferences
    └── Export data
```

---

## 2. Navigation Structure

### 2.1 Primary Navigation (Top Bar)

| Item             | Route              | Auth Required | Persona         |
|------------------|--------------------|---------------|-----------------|
| Dashboard        | /dashboard         | Yes           | Analyst, CISO   |
| CVEs             | /cves              | No            | All             |
| Packages         | /packages          | No            | All             |
| Repositories     | /repos             | No            | All             |
| Notifications    | /notifications     | Yes           | Analyst         |
| Docs             | /docs              | No            | All             |

### 2.2 Secondary Navigation (Sidebar / User Menu)

| Item             | Route              | Auth Required |
|------------------|--------------------|---------------|
| API Keys         | /api-keys          | Yes           |
| Opt-Out          | /opt-out           | GitHub OAuth  |
| Settings         | /settings          | Yes           |
| Sign Out         | /auth/logout       | Yes           |

---

## 3. Content Model

### 3.1 CVE Object

| Field             | Type          | Display                                 |
|-------------------|---------------|-----------------------------------------|
| cve_id            | string        | Badge (CVE-2024-12345)                  |
| title             | string        | Derived from description (first sentence)|
| description       | text          | Full text on detail page                |
| cvss_score        | decimal       | Color-coded score badge                 |
| cvss_vector       | string        | Expandable technical detail             |
| severity_tier     | enum          | Critical/High/Medium/Low label          |
| published_at      | datetime      | "2 hours ago" + tooltip with full date  |
| source            | enum          | NVD / OSV / GHSA badge                  |
| affected_packages | array         | Inline chips on list; full table on detail |
| affected_repo_count | integer     | Number shown on list card               |

### 3.2 Affected Repository Object

| Field              | Type     | Display                                  |
|--------------------|----------|------------------------------------------|
| repo_url           | string   | Clickable link                           |
| repo_name          | string   | Bold primary label                       |
| repo_owner         | string   | Secondary label with avatar              |
| context_score      | decimal  | Progress bar + number                    |
| severity_tier      | enum     | Color label                              |
| dependency_depth   | integer  | "Direct" or "Depth: 3"                  |
| dependency_path    | array    | Breadcrumb chain                         |
| context_type       | enum     | Runtime / Dev badge                      |
| notification_status| enum     | Pending / Sent / Skipped / Failed badge  |
| issue_url          | string   | GitHub link if created                   |
| weekly_downloads   | integer  | Formatted (1.2M, 50K, etc.)              |

### 3.3 Package Object

| Field            | Type     | Display                                  |
|------------------|----------|------------------------------------------|
| ecosystem        | enum     | npm / PyPI / Maven badge                 |
| name             | string   | Primary label                            |
| latest_version   | string   | Secondary label                          |
| weekly_downloads | integer  | Popularity bar                           |
| cve_count        | integer  | Warning badge if > 0                     |
| dependent_count  | integer  | Number of packages depending on this     |

---

## 4. Page Layouts

### 4.1 Dashboard Layout
```
┌─────────────────────────────────────────────────────┐
│  ODEPM  | Dashboard  CVEs  Packages  Repos  Docs    │  ← Top Nav
├─────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ 24h CVEs │ │ Critical │ │ Issues   │ │ Repos  │ │  ← Stat Cards
│  │   47     │ │  Findings│ │  Sent    │ │Affected│ │
│  │          │ │   12     │ │   234    │ │ 1,847  │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│                                                     │
│  ┌──────────────────────────┐ ┌───────────────────┐ │
│  │  Recent High-Severity    │ │  Ecosystem        │ │
│  │  CVEs                    │ │  Breakdown Chart  │ │
│  │  (list)                  │ │  (pie)            │ │
│  └──────────────────────────┘ └───────────────────┘ │
│                                                     │
│  ┌──────────────────────────────────────────────────┐│
│  │  Latest Notifications Sent                       ││  ← Notification Feed
│  └──────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### 4.2 CVE Detail Layout
```
┌─────────────────────────────────────────────────────┐
│  ← Back to CVEs                                     │
│                                                     │
│  CVE-2024-12345                    [Critical] 9.8   │  ← Header
│  Prototype Pollution in lodash < 4.17.21            │
│  Published: 2024-03-15  |  Source: NVD  |  npm     │
│                                                     │
│  ┌────────────────────────────────────────────────┐ │
│  │  Description                                   │ │  ← CVE Details
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  Affected Packages                                  │
│  ┌────────────────────────────────────────────────┐ │
│  │  lodash  <4.17.21  →  Fix: 4.17.21            │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  [Graph View]  [Table View]         [Export CSV]   │  ← Tabs + Actions
│                                                     │
│  ┌────────────────────────────────────────────────┐ │
│  │  Affected Repositories (2,341)                 │ │
│  │  Search: _____________  Filter: [All] ▾        │ │
│  │  ┌──────────────────────────────────────────┐  │ │
│  │  │ facebook/react   9.2 Critical  Depth:1   │  │ │
│  │  │ vercel/next.js   8.9 Critical  Depth:2   │  │ │
│  │  └──────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 5. User Flows

### 5.1 Analyst: New CVE Triage Flow
```
1. Analyst opens Dashboard
2. Sees alert: "New Critical CVE ingested: CVE-2024-XXXXX (9.8)"
3. Clicks through to CVE Detail
4. Reviews affected package + CVSS
5. Switches to Table View → sorted by score
6. Identifies top 10 affected repos in their organization
7. Clicks Export CSV → downloads report
8. Shares with team lead
```

### 5.2 Maintainer: Receives and Acts on Issue
```
1. Maintainer receives GitHub email notification about new issue
2. Opens issue: "[Security] CVE-2024-12345: lodash vulnerability in your dependencies"
3. Reads dependency path: my-app → express → lodash@4.16.0
4. Reads remediation: "Update lodash to 4.17.21 in package.json"
5. Runs: npm install lodash@^4.17.21
6. Pushes update, closes issue with comment
```

### 5.3 Maintainer: Opt-Out Flow
```
1. Maintainer clicks opt-out link in issue footer
2. Redirected to /opt-out
3. Clicks "Login with GitHub"
4. GitHub OAuth consent screen
5. List of their repositories shown
6. Selects repos to opt out
7. Clicks "Opt Out Selected"
8. Confirmation shown; no further issues for selected repos
```

---

## 6. Search & Discovery

### 6.1 Global Search
- Search bar in top navigation (available on all pages)
- Searches across: CVE IDs, package names, repository names
- Autocomplete suggestions with type indicators: [CVE] [pkg] [repo]
- Results page groups by type

### 6.2 CVE Explorer Filters
- Ecosystem: npm | PyPI | Maven (checkbox multi-select)
- Severity: Critical | High | Medium | Low (checkbox multi-select)
- Date Range: Published after / Published before (date pickers)
- Has Affected Repos: Yes / Any (toggle)
- Sort: Published Date | CVSS Score | Affected Repo Count

### 6.3 Affected Repository Filters (on CVE Detail)
- Severity Tier: Critical | High | Medium | Low
- Dependency Type: Direct | Transitive
- Context: Runtime | Dev
- Notification Status: Pending | Sent | Skipped | Failed
- Sort: Score | Download Count | Repo Stars

---

## 7. Notifications & Alerts (In-App)

| Trigger                             | Alert Type  | Location           |
|-------------------------------------|-------------|--------------------|
| New Critical CVE ingested           | Banner      | Dashboard           |
| Issue creation failure (>10 repos)  | Alert card  | Notifications page  |
| Daily digest: unpatched Critical    | Badge       | Nav icon            |
| API key expiring in 7 days          | Warning     | Settings page       |

---

*Last updated: 2026-04-18*
