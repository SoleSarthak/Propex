# 02 — User Stories & Acceptance Criteria
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Date:** 2026-04-18

---

## Epic 1: CVE Discovery & Ingestion

### US-101: Real-Time CVE Ingestion
**As** a security analyst,
**I want** newly published CVEs to appear in the system within 15 minutes of NVD publication,
**So that** I can begin impact assessment as soon as possible.

**Acceptance Criteria:**
- [ ] AC-101-1: System polls NVD API every 15 minutes and stores new CVEs
- [ ] AC-101-2: CVEs from OSV webhook appear in the system within 2 minutes of OSV publication
- [ ] AC-101-3: Each CVE record contains: CVE ID, CVSS score, affected packages, description, source
- [ ] AC-101-4: Duplicate CVEs (same ID from multiple sources) are deduplicated; canonical record kept
- [ ] AC-101-5: Ingestion failures are logged and retried; alert fires if lag exceeds 20 minutes

---

### US-102: CVE Filtering and Search
**As** a security analyst,
**I want** to filter and search CVEs by ecosystem, severity, date, and package name,
**So that** I can focus on CVEs relevant to my technology stack.

**Acceptance Criteria:**
- [ ] AC-102-1: Dashboard shows paginated CVE list, 25 per page, sorted by published date descending
- [ ] AC-102-2: Filter by ecosystem: npm, PyPI, Maven (multi-select)
- [ ] AC-102-3: Filter by severity tier: Critical, High, Medium, Low (multi-select)
- [ ] AC-102-4: Filter by date range (published after / before)
- [ ] AC-102-5: Free-text search matches CVE ID, package name, and description
- [ ] AC-102-6: Filters are combinable and reflected in URL for shareability
- [ ] AC-102-7: Results update within 500ms of filter change

---

### US-103: CVE Detail View
**As** a security analyst,
**I want** to see full details for a specific CVE including all affected packages and repositories,
**So that** I can understand the full blast radius.

**Acceptance Criteria:**
- [ ] AC-103-1: CVE detail page shows: ID, description, CVSS score/vector, published date, source links
- [ ] AC-103-2: Lists all affected packages with version ranges and fixed version
- [ ] AC-103-3: Shows count of affected repositories by severity tier
- [ ] AC-103-4: Links to affected repository list (paginated, sortable by score)
- [ ] AC-103-5: Page loads within 2 seconds for CVEs with up to 10,000 affected repos

---

### US-104: Manual CVE Submission
**As** a security researcher,
**I want** to manually submit a CVE that hasn't appeared in NVD/OSV yet,
**So that** I can analyze propagation of zero-day or pre-publication vulnerabilities.

**Acceptance Criteria:**
- [ ] AC-104-1: API endpoint `POST /api/v1/cves` accepts CVE data in canonical format
- [ ] AC-104-2: Requires authentication (API key)
- [ ] AC-104-3: Triggers dependency resolution pipeline immediately upon submission
- [ ] AC-104-4: Returns 201 with created CVE record; returns 409 if CVE ID already exists
- [ ] AC-104-5: Manually submitted CVEs are tagged with source: "manual"

---

## Epic 2: Dependency Resolution

### US-201: npm Dependency Tree Resolution
**As** a security analyst,
**I want** the system to resolve the full transitive dependency tree for affected npm packages,
**So that** I can understand which npm packages and projects are downstream of a vulnerability.

**Acceptance Criteria:**
- [ ] AC-201-1: Given a vulnerable npm package and version range, system identifies all npm packages that depend on it (directly or transitively)
- [ ] AC-201-2: Resolution covers all published versions of the affected package
- [ ] AC-201-3: Dependency depth is recorded for each edge in the graph
- [ ] AC-201-4: devDependencies are distinguished from runtime dependencies
- [ ] AC-201-5: Resolution completes within 60 seconds for packages with < 1,000 direct dependents (P95)
- [ ] AC-201-6: Results are cached; cache invalidated when a new package version is published

---

### US-202: PyPI Dependency Tree Resolution
**As** a security analyst,
**I want** the system to resolve transitive dependencies for affected PyPI packages,
**So that** I can identify downstream Python projects at risk.

**Acceptance Criteria:**
- [ ] AC-202-1: Given a vulnerable PyPI package, system resolves full reverse-dependency tree
- [ ] AC-202-2: Handles extras dependencies (`package[extra]` syntax)
- [ ] AC-202-3: Dependency types (install_requires vs. extras_require vs. tests_require) are captured
- [ ] AC-202-4: Resolution completes within 60 seconds for packages with < 500 direct dependents (P95)

---

### US-203: Maven Dependency Tree Resolution
**As** a security analyst,
**I want** the system to resolve transitive dependencies for affected Maven artifacts,
**So that** I can identify downstream Java projects at risk.

**Acceptance Criteria:**
- [ ] AC-203-1: System resolves Maven artifact dependencies including groupId:artifactId:version
- [ ] AC-203-2: Dependency scope (compile, runtime, test, provided) is captured
- [ ] AC-203-3: BOM (Bill of Materials) imports are handled correctly
- [ ] AC-203-4: Resolution completes within 120 seconds for complex dependency trees (P95)

---

### US-204: Dependency Graph Visualization
**As** a security analyst,
**I want** to explore the dependency propagation graph interactively,
**So that** I can visually understand how a vulnerability propagates through the ecosystem.

**Acceptance Criteria:**
- [ ] AC-204-1: Graph shows affected package as root node, dependents as leaf nodes
- [ ] AC-204-2: Node size represents package popularity (download count)
- [ ] AC-204-3: Edge color represents dependency type (runtime: red, dev: grey)
- [ ] AC-204-4: Clicking a node shows package details and its own dependency relationships
- [ ] AC-204-5: Graph can be exported as PNG or SVG
- [ ] AC-204-6: Graph renders within 3 seconds for graphs with up to 500 nodes

---

## Epic 3: Repository Impact Assessment

### US-301: Affected Repository Discovery
**As** a security analyst,
**I want** the system to identify public GitHub repositories using a vulnerable package,
**So that** I know which projects are at risk.

**Acceptance Criteria:**
- [ ] AC-301-1: System discovers repositories containing dependency manifests referencing the vulnerable package
- [ ] AC-301-2: Supported manifest files: package.json, requirements.txt, setup.py, setup.cfg, pom.xml, build.gradle, build.gradle.kts
- [ ] AC-301-3: System verifies that the version specification overlaps with the vulnerable version range
- [ ] AC-301-4: Each affected repository record includes: URL, owner, repo name, dependency file path, version spec
- [ ] AC-301-5: Discovery runs within 30 minutes of dependency resolution completing

---

### US-302: Repository Severity Score
**As** a security analyst,
**I want** each affected repository to have a contextual severity score,
**So that** I can prioritize which maintainers to notify first.

**Acceptance Criteria:**
- [ ] AC-302-1: Severity score is between 1.0 and 10.0
- [ ] AC-302-2: Score factors: CVSS base score, dependency depth, runtime/dev context, download popularity
- [ ] AC-302-3: Score is visible in affected repository list and sortable
- [ ] AC-302-4: Severity tier label (Critical/High/Medium/Low) shown alongside score
- [ ] AC-302-5: Score recomputes if CVSS is updated

---

### US-303: Repository Vulnerability History
**As** a security analyst or maintainer,
**I want** to see all CVEs that have affected a specific repository,
**So that** I can assess its overall security posture.

**Acceptance Criteria:**
- [ ] AC-303-1: Page `/repos/{owner}/{name}` lists all CVEs affecting this repo
- [ ] AC-303-2: Shows CVE ID, score, status (pending/notified/patched), notification date
- [ ] AC-303-3: Shows whether issue was created and links to it if so
- [ ] AC-303-4: Maintainer can mark a finding as "patched" or "not affected"

---

## Epic 4: Patch Request Automation

### US-401: Automated Issue Generation
**As** an open-source maintainer,
**I want** to receive a GitHub issue when my project is affected by a CVE,
**So that** I am informed promptly and have the context to fix it.

**Acceptance Criteria:**
- [ ] AC-401-1: Issue is created on the affected repository via GitHub REST API
- [ ] AC-401-2: Issue title format: `[Security] CVE-YYYY-NNNNN: {package} vulnerability in your dependencies`
- [ ] AC-401-3: Issue body includes: CVE summary, CVSS score, full dependency path, fixed version, remediation command, links to CVE
- [ ] AC-401-4: Issue is created within 45 minutes of CVE ingestion for Critical severity repos
- [ ] AC-401-5: Issue includes labels: `security`, `vulnerability`, `auto-generated`, and severity tier label
- [ ] AC-401-6: No duplicate issues: system checks before creating; skips if issue already exists for same CVE + repo

---

### US-402: Issue Content Quality
**As** a maintainer,
**I want** the issue text to be clear, professional, and non-alarmist,
**So that** I trust the notification and act on it.

**Acceptance Criteria:**
- [ ] AC-402-1: Issue text is generated by LLM with consistent professional tone
- [ ] AC-402-2: Issue explains why this specific repository is affected (shows dependency path)
- [ ] AC-402-3: Remediation instructions are specific (e.g., `npm install lodash@^4.17.21`)
- [ ] AC-402-4: Issue text is ≤ 600 words
- [ ] AC-402-5: Issue includes a footer noting it was auto-generated with a link to opt-out
- [ ] AC-402-6: If LLM is unavailable, fallback template is used; still meets all content requirements

---

### US-403: Opt-Out Registry
**As** a maintainer,
**I want** to opt out of automated issue creation for my repositories,
**So that** I maintain full control over issue tracking in my projects.

**Acceptance Criteria:**
- [ ] AC-403-1: Self-service opt-out page at `/opt-out`; authenticate via GitHub OAuth
- [ ] AC-403-2: Opt-out can be per-repository or per-GitHub-organization (all repos)
- [ ] AC-403-3: Opt-out takes effect immediately; no further issues created for opted-out repos
- [ ] AC-403-4: Opted-out repos are still visible in the dashboard (flagged as "opted out")
- [ ] AC-403-5: Maintainer can reverse opt-out at any time

---

### US-404: Notification History
**As** a security analyst,
**I want** to see a history of all notifications sent,
**So that** I can audit what has been dispatched and follow up if needed.

**Acceptance Criteria:**
- [ ] AC-404-1: `GET /api/v1/notifications` returns paginated list of all issued notifications
- [ ] AC-404-2: Each record includes: repo, CVE ID, issue URL, created at, status
- [ ] AC-404-3: Filter by: status (sent/failed/skipped), CVE ID, date range
- [ ] AC-404-4: Failed notifications show error reason and retry count

---

## Epic 5: Platform & API

### US-501: REST API Access
**As** an enterprise security engineer,
**I want** programmatic API access to CVE impact data,
**So that** I can integrate ODEPM data into my internal security tooling.

**Acceptance Criteria:**
- [ ] AC-501-1: All read endpoints accessible via authenticated REST API
- [ ] AC-501-2: Authentication via API key (Bearer token in Authorization header)
- [ ] AC-501-3: API keys generated via dashboard self-service
- [ ] AC-501-4: Rate limit: 1,000 requests/hour per API key
- [ ] AC-501-5: OpenAPI 3.1 spec published at `/api/docs`
- [ ] AC-501-6: API versioned under `/api/v1/`

---

### US-502: Data Export
**As** an enterprise security officer,
**I want** to export CVE impact data as CSV or JSON,
**So that** I can use it in spreadsheets, BI tools, or internal reports.

**Acceptance Criteria:**
- [ ] AC-502-1: Export button on CVE list and per-CVE affected-repo list
- [ ] AC-502-2: CSV export includes: CVE ID, package, ecosystem, repo URL, score, tier, notification status
- [ ] AC-502-3: JSON export is valid JSON, formatted per canonical schema
- [ ] AC-502-4: Large exports (>10,000 rows) trigger async job; user notified via email when ready
- [ ] AC-502-5: Exports are available for 24 hours via pre-signed S3 URL

---

*Last updated: 2026-04-18*
