"""
System and per-ecosystem prompt templates for the Gemini Patch Drafter.
"""

SYSTEM_PROMPT = """You are an expert security researcher specializing in open-source dependency vulnerabilities.
Your task is to draft a clear, actionable, and professional security patch recommendation.

Follow these rules strictly:
1. Always reference the exact CVE ID provided.
2. Show the exact dependency path (e.g., my-app → vulnerable-lib → sub-dep).
3. Provide a concise description of the vulnerability's impact.
4. Give a clear remediation step with the exact fixed version to upgrade to.
5. Include a code snippet showing the fix (package.json, requirements.txt, or pom.xml).
6. Keep the tone professional and non-alarming.
7. Always end with a section titled "Affected Versions" listing the vulnerable version range.

Your response MUST include all of the following sections:
- ## Summary
- ## Dependency Path
- ## Remediation
- ## Code Fix
- ## Affected Versions
"""


NPM_TEMPLATE = """
**CVE ID**: {cve_id}
**Ecosystem**: npm
**Vulnerable Package**: `{package_name}` (versions {version_range})
**Repository**: {repo_url}
**Dependency Depth**: {depth} ({"direct" if {depth} == 1 else "transitive"})
**Propex Risk Score**: {propex_score}/10

Please draft a security patch recommendation for this repository.
The repository uses `{package_name}` which is affected by {cve_id}.
The fix version is `{fix_version}`.
"""

PYPI_TEMPLATE = """
**CVE ID**: {cve_id}
**Ecosystem**: PyPI (Python)
**Vulnerable Package**: `{package_name}` (versions {version_range})
**Repository**: {repo_url}
**Dependency Depth**: {depth}
**Propex Risk Score**: {propex_score}/10

Please draft a security patch recommendation for this Python project.
The project uses `{package_name}` which is affected by {cve_id}.
The fix version is `{fix_version}`. Show a requirements.txt snippet.
"""

MAVEN_TEMPLATE = """
**CVE ID**: {cve_id}
**Ecosystem**: Maven (Java)
**Vulnerable Package**: `{package_name}` (versions {version_range})
**Repository**: {repo_url}
**Dependency Depth**: {depth}
**Propex Risk Score**: {propex_score}/10

Please draft a security patch recommendation for this Java/Maven project.
The project uses `{package_name}` which is affected by {cve_id}.
The fix version is `{fix_version}`. Show a pom.xml <dependency> snippet.
"""

FALLBACK_TEMPLATES = {
    "npm": """
## Summary
A critical vulnerability {cve_id} has been detected in `{package_name}` used by your repository.

## Dependency Path
{repo_url} → `{package_name}` ({version_range})

## Remediation
Upgrade `{package_name}` to version `{fix_version}` or later immediately.

## Code Fix
```json
"dependencies": {{
  "{package_name}": "^{fix_version}"
}}
```

## Affected Versions
All versions below `{fix_version}` are affected.
""",
    "pypi": """
## Summary
A critical vulnerability {cve_id} has been detected in `{package_name}` used by your repository.

## Dependency Path
{repo_url} → `{package_name}` ({version_range})

## Remediation
Upgrade `{package_name}` to version `{fix_version}` or later immediately.

## Code Fix
```
# requirements.txt
{package_name}>={fix_version}
```

## Affected Versions
All versions below `{fix_version}` are affected.
""",
    "maven": """
## Summary
A critical vulnerability {cve_id} has been detected in `{package_name}` used by your repository.

## Dependency Path
{repo_url} → `{package_name}` ({version_range})

## Remediation
Upgrade `{package_name}` to version `{fix_version}` or later in your `pom.xml`.

## Code Fix
```xml
<dependency>
  <groupId>{group_id}</groupId>
  <artifactId>{artifact_id}</artifactId>
  <version>{fix_version}</version>
</dependency>
```

## Affected Versions
All versions below `{fix_version}` are affected.
""",
}


def get_user_prompt(ecosystem: str, **kwargs) -> str:
    templates = {
        "npm": NPM_TEMPLATE,
        "pypi": PYPI_TEMPLATE,
        "maven": MAVEN_TEMPLATE,
    }
    template = templates.get(ecosystem.lower(), NPM_TEMPLATE)
    return template.format(**kwargs)


def get_fallback_patch(ecosystem: str, **kwargs) -> str:
    template = FALLBACK_TEMPLATES.get(ecosystem.lower(), FALLBACK_TEMPLATES["npm"])
    # For maven: split groupId:artifactId
    if ecosystem.lower() == "maven":
        pkg = kwargs.get("package_name", ":")
        parts = pkg.split(":")
        kwargs.setdefault("group_id", parts[0] if len(parts) > 0 else "com.example")
        kwargs.setdefault("artifact_id", parts[1] if len(parts) > 1 else pkg)
    return template.format(**kwargs)
