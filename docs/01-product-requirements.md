# 01 — Product Requirements Document
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0 | **Status:** Approved | **Date:** 2026-04-18

---

## 1. Problem Statement

When a CVE is published for an open-source library, thousands of downstream projects are affected but most maintainers don't know. The gap between vulnerability disclosure and remediation averages **47 days** across the open-source ecosystem. This system closes that gap by:

1. Automatically detecting newly published CVEs
2. Tracing transitive dependency trees to find every affected downstream project
3. Estimating exposure severity based on usage context
4. Drafting and delivering patch-request issues to maintainers automatically

---

## 2. Strategic Context

### 2.1 Market Problem
- **Dependency depth:** Modern applications average 5–10 levels of transitive dependencies
- **Blind spots:** Only ~15% of affected projects patch within 30 days of CVE publication
- **Scale:** A single CVE in a foundational library (e.g., log4j, lodash, requests) can affect millions of projects

### 2.2 Target Market
- Primary: Enterprise DevSecOps teams managing large project portfolios
- Secondary: Open-source maintainers seeking automated vulnerability monitoring
- Tertiary: Security researchers studying supply-chain attack propagation

---

## 3. Product Goals

### 3.1 Primary Goals (MVP — 14 weeks)

| ID  | Goal                                                                           | Metric                          |
|-----|--------------------------------------------------------------------------------|---------------------------------|
| G1  | CVE ingestion within 15 minutes of NVD/OSV publication                        | Ingestion latency ≤ 15 min      |
| G2  | Transitive dependency resolution for npm, PyPI, Maven                          | Coverage ≥ 95% of top packages  |
| G3  | Identify affected public GitHub repositories                                   | ≥ 100 repos per major CVE       |
| G4  | Contextual severity scoring per affected project                               | Score accuracy vs. expert: ≥85% |
| G5  | Automated patch-request issue generation and dispatch                          | Issue created within 45 min     |
| G6  | Analyst dashboard for CVE and impact visualization                             | DAU ≥ 500 at launch             |

### 3.2 Secondary Goals (3-month horizon)

- Self-service maintainer registration and opt-in
- API access for enterprise security toolchain integration
- SBOM (Software Bill of Materials) export per repository
- Trend analytics: time-to-patch by ecosystem, severity, project type

---

## 4. Non-Goals

| Item                             | Rationale                                        |
|----------------------------------|--------------------------------------------------|
| Private repository scanning      | Requires auth; planned for enterprise tier       |
| Automated code fixes / PRs       | Higher complexity; Phase 2                       |
| Container / binary scanning      | Out of scope for dependency manifest approach    |
| Go modules, Cargo, NuGet         | Phase 2 ecosystem expansion                      |
| SAST / DAST integration          | Separate security domain                         |
| On-premise deployment            | SaaS-first MVP                                   |

---

## 5. User Personas

### P1: Alex — Security Analyst
- **Company type:** Mid-size tech company (500–5,000 engineers)
- **Daily tools:** Jira, GitHub, Snyk, Dependabot
- **Goal:** Immediately assess organizational exposure to new CVEs
- **Frustration:** Manual dependency auditing is slow; no cross-project view
- **Key workflow:** Searches CVE → sees affected internal repos → exports report for management

### P2: Maya — Open-Source Maintainer
- **Background:** Maintains 3–5 libraries in spare time
- **Tools:** GitHub, npm/pip publish workflows
- **Goal:** Keep projects secure without constant monitoring
- **Frustration:** Only discovers vulnerabilities via sporadic PRs from users
- **Key workflow:** Receives GitHub issue → reads dependency path → updates dependency → closes issue

### P3: David — Enterprise CISO
- **Company type:** Large enterprise (10,000+ engineers, hundreds of repos)
- **Goal:** Executive-level supply-chain risk posture
- **Need:** Aggregated risk reports, SLA metrics on remediation time, API integration with internal GRC tools
- **Key workflow:** Weekly digest of unpatched Critical/High CVEs across org portfolio

### P4: Raj — CVE Researcher
- **Background:** Security researcher studying vulnerability propagation
- **Goal:** Understand blast radius of newly discovered vulnerabilities
- **Need:** Detailed graph visualization of dependency propagation paths
- **Key workflow:** Searches specific CVE → explores dependency graph → exports data for analysis

---

## 6. User Stories (Abbreviated — see `02-user-stories.md` for full list)

| ID     | Story                                                                                              | Priority |
|--------|----------------------------------------------------------------------------------------------------|----------|
| US-001 | As Alex, I want to see new CVEs within 15 minutes so I can begin triage immediately               | P0       |
| US-002 | As Alex, I want to filter CVEs by ecosystem and severity so I can focus my attention              | P0       |
| US-003 | As Alex, I want to see every repo affected by a CVE and its severity score                        | P0       |
| US-004 | As Maya, I want to receive a GitHub issue with clear dependency path and remediation steps        | P0       |
| US-005 | As Maya, I want to opt out of automated issues so I control my repo                               | P0       |
| US-006 | As David, I want to export a CSV of all Critical CVEs affecting my org's repos                    | P1       |
| US-007 | As Raj, I want to explore the dependency propagation graph interactively                          | P1       |
| US-008 | As Alex, I want to mark a finding as "false positive" or "patched" in the dashboard               | P2       |

---

## 7. Functional Requirements

### 7.1 CVE Ingestion

| ID     | Requirement                                                              | Priority |
|--------|--------------------------------------------------------------------------|----------|
| FR-001 | Ingest CVEs from NVD (`/rest/json/cves/2.0`) every 15 minutes           | P0       |
| FR-002 | Subscribe to OSV advisory webhook feed                                   | P0       |
| FR-003 | Parse GitHub Security Advisory feed every 30 minutes                    | P1       |
| FR-004 | Normalize to canonical CVE schema with CVSS, affected packages, versions | P0       |
| FR-005 | Deduplicate CVEs across sources (same CVE-ID from multiple sources)     | P0       |
| FR-006 | Persist raw source response to object storage for replay                 | P1       |
| FR-007 | Support manual CVE submission via API for unlisted CVEs                  | P2       |

### 7.2 Dependency Resolution

| ID     | Requirement                                                              | Priority |
|--------|--------------------------------------------------------------------------|----------|
| FR-008 | Resolve npm transitive dependency tree via npm Registry API              | P0       |
| FR-009 | Resolve PyPI transitive dependency tree via PyPI JSON API                | P0       |
| FR-010 | Resolve Maven transitive dependency tree via Maven Central API           | P0       |
| FR-011 | Traverse to unlimited transitive depth                                   | P0       |
| FR-012 | Store dependency graph in Neo4j as directed graph                        | P0       |
| FR-013 | Cache resolved trees with TTL; invalidate on new package version         | P1       |
| FR-014 | Identify reverse dependencies (who depends on affected package)          | P0       |

### 7.3 Repository Identification

| ID     | Requirement                                                              | Priority |
|--------|--------------------------------------------------------------------------|----------|
| FR-015 | Search GitHub for repos containing dependency files with affected package | P0       |
| FR-016 | Support: package.json, requirements.txt, setup.py, pom.xml, build.gradle | P0       |
| FR-017 | Extract dependency version specification from manifest files             | P0       |
| FR-018 | Determine if version spec is vulnerable (overlap with CVE version range) | P0       |

### 7.4 Severity Scoring

| ID     | Requirement                                                              | Priority |
|--------|--------------------------------------------------------------------------|----------|
| FR-019 | Compute contextual severity score (1.0–10.0) per repo-CVE pair          | P0       |
| FR-020 | Factor in: CVSS base score, dependency depth, runtime/dev context        | P0       |
| FR-021 | Factor in: package weekly download volume (popularity proxy)             | P1       |
| FR-022 | Assign severity tier: Critical / High / Medium / Low                     | P0       |
| FR-023 | Re-score when CVSS is updated by NVD                                     | P2       |

### 7.5 Patch Request Generation

| ID     | Requirement                                                              | Priority |
|--------|--------------------------------------------------------------------------|----------|
| FR-024 | Generate patch-request issue text via LLM (GPT-4o-mini)                 | P0       |
| FR-025 | Issue text includes: CVE ID, CVSS, dep path, fixed version, remediation  | P0       |
| FR-026 | Create GitHub issue via REST API for Critical/High repos                  | P0       |
| FR-027 | Respect opt-out registry; never issue to opted-out repos                 | P0       |
| FR-028 | Prevent duplicate issues (same CVE + repo pair)                          | P0       |
| FR-029 | Apply standard labels: security, vulnerability, auto-generated, tier     | P0       |
| FR-030 | Batch dispatch Medium/Low issues at low-traffic hours                    | P1       |

### 7.6 Dashboard & API

| ID     | Requirement                                                              | Priority |
|--------|--------------------------------------------------------------------------|----------|
| FR-031 | Searchable, paginated CVE list with filters (ecosystem, severity, date)  | P0       |
| FR-032 | Per-CVE detail page with affected repo list and scores                   | P0       |
| FR-033 | Interactive dependency graph visualization                               | P1       |
| FR-034 | Per-repo page showing all CVEs affecting that repo                       | P1       |
| FR-035 | CSV / JSON export of CVE + affected repo data                            | P1       |
| FR-036 | REST API with authentication for programmatic access                     | P0       |
| FR-037 | Maintainer opt-out self-service page                                     | P0       |

---

## 8. Non-Functional Requirements

| ID       | Requirement                                          | Target          |
|----------|------------------------------------------------------|-----------------|
| NFR-001  | CVE ingestion latency from NVD publication           | ≤ 15 min        |
| NFR-002  | Dependency tree resolution time (P95, per package)   | ≤ 30 sec        |
| NFR-003  | End-to-end: CVE → first GitHub issue created         | ≤ 45 min        |
| NFR-004  | Dashboard page load time (P95)                       | ≤ 2 sec         |
| NFR-005  | API response time (P95, read endpoints)              | ≤ 500 ms        |
| NFR-006  | System availability (SLA)                            | ≥ 99.5%         |
| NFR-007  | Maximum GitHub issues dispatched per hour            | ≤ 4,800/hr      |
| NFR-008  | Data retention for CVE and impact records            | 5 years         |
| NFR-009  | All API tokens / secrets encrypted at rest           | AES-256         |
| NFR-010  | GDPR compliance for any EU maintainer data           | Required        |

---

## 9. Success Metrics

### 9.1 Leading Indicators (First 30 Days)
- CVEs processed per day: **≥ 200**
- Dependency trees resolved: **≥ 50,000 packages**
- GitHub issues created: **≥ 1,000**
- Dashboard registered users: **≥ 500**

### 9.2 Lagging Indicators (90 Days)
- Issue open rate by maintainers: **≥ 30%**
- Median time-to-patch for notified vs. control: **40% faster**
- Repeat visitors to dashboard: **≥ 60% monthly retention**
- API integrations by enterprise users: **≥ 10**

---

## 10. Constraints & Assumptions

| Item                          | Detail                                                   |
|-------------------------------|----------------------------------------------------------|
| Public repos only             | GitHub API code search limited to public repositories    |
| API rate limits               | npm: ~1K/min; PyPI: ~600/min; GitHub: 5K/hr              |
| LLM cost                      | GPT-4o-mini: ~$0.008/issue; budget $100/day = ~12K/day  |
| OSV data quality              | Assumed accurate; cross-validated with NVD               |
| Repo maintainer availability  | Not all maintainers active; issue delivery ≠ issue action|

---

## 11. Risks

| Risk                                      | Probability | Impact | Mitigation                              |
|-------------------------------------------|-------------|--------|-----------------------------------------|
| NVD API downtime                          | Medium      | High   | OSV + GHSA as fallback sources          |
| GitHub rate limit exhaustion              | High        | Medium | Token rotation pool, batching           |
| LLM generates inaccurate issue text       | Low         | High   | Human review for Critical CVEs          |
| Dependency resolver misses transitive dep | Medium      | High   | Test suite with known CVE propagations  |
| Maintainer community backlash (spam)      | Low         | High   | Opt-out registry, rate limiting, clear branding |

---

*Last updated: 2026-04-18*
