# Product Requirements Document (PRD)
## Open-Source Dependency Exploit Propagation Mapper (ODEPM)

**Version:** 1.0  
**Date:** 2026-04-18  
**Status:** Draft  
**Owner:** Product Team  

---

## 1. Executive Summary

### 1.1 Problem Statement

When a CVE (Common Vulnerability and Exposure) is published for an open-source library, thousands of downstream projects that depend on it — directly or transitively — are immediately at risk. The majority of project maintainers:

- **Do not know** their project is affected
- **Cannot efficiently audit** their full transitive dependency tree
- **Lack prioritization** — they don't know whether the vulnerable function is actually reachable from their code
- **Have no automated pathway** to receive patch guidance

The current status quo leaves a critical security gap between vulnerability disclosure and remediation, often measured in months.

### 1.2 Solution

ODEPM is a SaaS platform that:
1. Continuously monitors CVE feeds across major vulnerability databases
2. Resolves full transitive dependency trees for affected packages across npm, PyPI, and Maven
3. Identifies every public repository affected
4. Scores exposure severity using usage context
5. Drafts and sends personalized patch-request issues to maintainers

---

## 2. Goals & Non-Goals

### 2.1 Goals (MVP)

| ID  | Goal                                                                                         |
|-----|----------------------------------------------------------------------------------------------|
| G1  | Ingest CVEs from NVD, OSV, and GitHub Security Advisories within 15 minutes of publication  |
| G2  | Resolve transitive dependency trees for npm, PyPI, and Maven ecosystems                      |
| G3  | Identify affected public GitHub/GitLab repositories                                          |
| G4  | Score each affected project with a contextual severity score (1–10)                          |
| G5  | Auto-generate patch-request issue text using LLM                                             |
| G6  | Allow maintainers to opt in/out of automated issue creation                                  |
| G7  | Provide a searchable dashboard for security analysts                                          |

### 2.2 Non-Goals (MVP)

- Private repository scanning (future premium tier)
- Automated pull request / code fix generation (future phase)
- Binary / container image scanning
- SAST / DAST integration
- Support for Go modules, Cargo, NuGet (future phase)

---

## 3. User Personas

### Persona 1: Security Analyst (Alex)
- **Role:** Security engineer at a mid-size company
- **Goal:** Quickly identify if their projects are affected by a newly published CVE
- **Pain Point:** Manually tracking transitive dependencies is time-consuming and error-prone
- **Needs:** Dashboard showing affected projects, severity scores, and one-click remediation guidance

### Persona 2: Open-Source Maintainer (Maya)
- **Role:** Maintains 3–5 open-source libraries on GitHub
- **Goal:** Keep projects secure with minimal effort
- **Pain Point:** Often unaware of vulnerabilities in dependencies for weeks/months
- **Needs:** Automated notifications with clear context and actionable patch instructions

### Persona 3: Enterprise Security Officer (David)
- **Role:** CISO at a large organization
- **Goal:** Audit supply chain risk across hundreds of internal projects
- **Pain Point:** No consolidated view of transitive dependency vulnerabilities
- **Needs:** API access, CSV/SBOM exports, executive risk summary reports

---

## 4. User Stories

### 4.1 CVE Discovery

- **US-001:** As a security analyst, I want to see newly published CVEs within 15 minutes so that I can begin impact assessment immediately.
- **US-002:** As a security analyst, I want to filter CVEs by ecosystem (npm/PyPI/Maven) so that I can focus on relevant technologies.
- **US-003:** As a security analyst, I want to see the full transitive dependency tree for a CVE-affected package so that I understand the blast radius.

### 4.2 Impact Assessment

- **US-004:** As a security analyst, I want each affected project to have a contextual severity score so that I can prioritize remediation efforts.
- **US-005:** As a security analyst, I want to see whether the vulnerability is in a direct or transitive dependency so that I can assess actual risk.
- **US-006:** As a security analyst, I want to filter affected projects by download count so that I can identify high-impact targets first.

### 4.3 Automated Notifications

- **US-007:** As an open-source maintainer, I want to receive a GitHub issue when my project is affected by a CVE so that I am promptly informed.
- **US-008:** As a maintainer, I want the issue text to include the specific dependency path, CVE details, and suggested fix so that I can act immediately.
- **US-009:** As a maintainer, I want to opt out of automated issues so that I maintain control over my repository.

### 4.4 Dashboard

- **US-010:** As a security analyst, I want a searchable list of CVEs with affected project counts so that I can triage at scale.
- **US-011:** As a security analyst, I want an interactive graph visualization of dependency chains so that I can understand propagation paths.
- **US-012:** As a security officer, I want to export affected project data as CSV/JSON/SBOM so that I can feed it into internal tools.

---

## 5. Functional Requirements

### 5.1 CVE Ingestion

| ID     | Requirement                                                                              | Priority |
|--------|------------------------------------------------------------------------------------------|----------|
| FR-001 | System shall poll NVD API for new CVEs every 15 minutes                                  | P0       |
| FR-002 | System shall ingest OSV advisory feed in real-time via webhook                           | P0       |
| FR-003 | System shall normalize CVEs into a canonical schema (CVSS, affected packages, versions)  | P0       |
| FR-004 | System shall deduplicate CVEs across sources                                              | P1       |
| FR-005 | System shall support manual CVE submission via API                                        | P2       |

### 5.2 Dependency Resolution

| ID     | Requirement                                                                              | Priority |
|--------|------------------------------------------------------------------------------------------|----------|
| FR-006 | System shall resolve npm package trees via npm Registry API                               | P0       |
| FR-007 | System shall resolve PyPI package trees via PyPI JSON API                                 | P0       |
| FR-008 | System shall resolve Maven package trees via Maven Central REST API                       | P0       |
| FR-009 | System shall traverse transitive dependencies to unlimited depth                          | P0       |
| FR-010 | System shall cache resolved trees and invalidate on new package versions                  | P1       |

### 5.3 Affected Repository Identification

| ID     | Requirement                                                                              | Priority |
|--------|------------------------------------------------------------------------------------------|----------|
| FR-011 | System shall identify GitHub repositories using affected package via dependency files     | P0       |
| FR-012 | System shall support package.json, requirements.txt, setup.py, pom.xml, build.gradle     | P0       |
| FR-013 | System shall rank affected repositories by download/install count                        | P1       |

### 5.4 Severity Scoring

| ID     | Requirement                                                                              | Priority |
|--------|------------------------------------------------------------------------------------------|----------|
| FR-014 | System shall compute a contextual severity score (1–10) per affected project             | P0       |
| FR-015 | Score shall factor: CVSS base score, dependency depth, runtime vs. dev context           | P0       |
| FR-016 | Score shall factor: package download volume, reachability (where determinable)           | P1       |

### 5.5 Patch Request Generation

| ID     | Requirement                                                                              | Priority |
|--------|------------------------------------------------------------------------------------------|----------|
| FR-017 | System shall generate patch-request issue text using LLM                                  | P0       |
| FR-018 | Issue text shall include: CVE ID, CVSS score, dependency path, recommended version fix   | P0       |
| FR-019 | System shall create GitHub issues via GitHub REST API                                     | P0       |
| FR-020 | System shall respect repository opt-out list                                              | P0       |
| FR-021 | System shall not create duplicate issues for the same CVE + repository pair               | P0       |

---

## 6. Non-Functional Requirements

| ID      | Requirement                                                                   | Target        |
|---------|-------------------------------------------------------------------------------|---------------|
| NFR-001 | CVE ingestion latency from publication to system awareness                    | ≤ 15 minutes  |
| NFR-002 | Dependency tree resolution time per package (P95)                             | ≤ 30 seconds  |
| NFR-003 | Dashboard page load time                                                       | ≤ 2 seconds   |
| NFR-004 | API availability (SLA)                                                         | 99.5%         |
| NFR-005 | GitHub issue creation rate compliance                                          | ≤ 5000/hour   |
| NFR-006 | Data retention for CVE records                                                 | 5 years       |
| NFR-007 | All stored tokens and secrets must be encrypted at rest                        | AES-256       |

---

## 7. Success Metrics

| Metric                                      | MVP Target        | 6-Month Target     |
|---------------------------------------------|-------------------|--------------------|
| CVEs processed per day                      | 500               | 2,000              |
| Packages with resolved dependency trees     | 10,000            | 100,000            |
| Affected repositories identified per CVE    | ≥ 100             | ≥ 1,000            |
| Issue open rate by maintainers              | ≥ 30%             | ≥ 50%              |
| Mean time to patch (vs. control group)      | 40% reduction     | 60% reduction      |
| Dashboard DAU                               | 500               | 5,000              |

---

## 8. Release Milestones

| Milestone | Description                                          | Target Date |
|-----------|------------------------------------------------------|-------------|
| M0        | Infrastructure setup, CI/CD, databases               | Week 2      |
| M1        | CVE ingestion + npm dependency resolver              | Week 4      |
| M2        | PyPI + Maven resolvers + Neo4j graph                 | Week 6      |
| M3        | Scoring engine + affected repo identification        | Week 8      |
| M4        | LLM patch drafter + GitHub issue creator             | Week 10     |
| M5        | Dashboard MVP + public API                           | Week 12     |
| M6        | Beta launch + performance optimization               | Week 14     |

---

## 9. Assumptions & Constraints

- Public GitHub repositories are the initial target (no private repo access)
- npm, PyPI, and Maven APIs are available and have sufficient rate limits for our use
- LLM API (GPT-4o or Gemini) costs are factored into pricing model
- OSV and NVD data is freely available and accurate

---

*Last updated: 2026-04-18*
jkl