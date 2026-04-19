"""
SBOM (Software Bill of Materials) exporter.
Generates CycloneDX 1.5 and SPDX 2.3 format SBOMs for affected repositories.
Both formats are free/open-source standards.
"""
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def generate_cyclonedx_sbom(
    repo_url: str,
    package_name: str,
    ecosystem: str,
    components: List[Dict],
    vulnerabilities: List[Dict]
) -> Dict:
    """
    Generate a CycloneDX 1.5 SBOM document for a repository.
    
    Args:
        repo_url: GitHub repository URL
        package_name: Root package being analyzed
        ecosystem: npm | pypi | maven | go | cargo | nuget
        components: List of {name, version, purl, scope}
        vulnerabilities: List of {cve_id, cvss_score, propex_score, fix_version}
    
    Returns:
        CycloneDX 1.5 JSON document as a dict
    """
    serial_number = f"urn:uuid:{uuid.uuid4()}"
    now = datetime.now(timezone.utc).isoformat()
    
    purl_prefix = {
        "npm": "pkg:npm",
        "pypi": "pkg:pypi",
        "maven": "pkg:maven",
        "go": "pkg:golang",
        "cargo": "pkg:cargo",
        "nuget": "pkg:nuget"
    }.get(ecosystem.lower(), "pkg:generic")

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial_number,
        "version": 1,
        "metadata": {
            "timestamp": now,
            "tools": [
                {
                    "vendor": "Propex",
                    "name": "Propex SBOM Exporter",
                    "version": "1.0.0",
                    "externalReferences": [
                        {"type": "website", "url": "https://github.com/SoleSarthak/Propex"}
                    ]
                }
            ],
            "component": {
                "type": "library",
                "name": package_name,
                "purl": f"{purl_prefix}/{package_name}",
                "bom-ref": f"pkg-root-{package_name}"
            }
        },
        "components": [
            {
                "type": "library",
                "name": comp["name"],
                "version": comp.get("version", "unknown"),
                "purl": f"{purl_prefix}/{comp['name']}@{comp.get('version', '')}",
                "scope": comp.get("scope", "required"),
                "bom-ref": f"pkg-{comp['name']}-{comp.get('version', '')}"
            }
            for comp in components
        ],
        "vulnerabilities": [
            {
                "bom-ref": f"vuln-{vuln['cve_id']}",
                "id": vuln["cve_id"],
                "source": {"name": "NVD", "url": f"https://nvd.nist.gov/vuln/detail/{vuln['cve_id']}"},
                "ratings": [
                    {
                        "source": {"name": "NVD"},
                        "score": vuln.get("cvss_score", 0.0),
                        "severity": _cvss_to_severity(vuln.get("cvss_score", 0.0)),
                        "method": "CVSSv3"
                    },
                    {
                        "source": {"name": "Propex"},
                        "score": vuln.get("propex_score", 0.0),
                        "severity": _cvss_to_severity(vuln.get("propex_score", 0.0)),
                        "method": "other"
                    }
                ],
                "recommendation": f"Upgrade to {vuln.get('fix_version', 'latest')}",
                "affects": [{"ref": f"pkg-root-{package_name}"}]
            }
            for vuln in vulnerabilities
        ]
    }
    
    return sbom


def generate_spdx_sbom(
    repo_url: str,
    package_name: str,
    ecosystem: str,
    components: List[Dict]
) -> Dict:
    """
    Generate an SPDX 2.3 SBOM document.
    """
    doc_namespace = f"https://propex.dev/sbom/{package_name}-{uuid.uuid4()}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    packages = [
        {
            "SPDXID": f"SPDXRef-Package-{comp['name'].replace('/', '-')}",
            "name": comp["name"],
            "versionInfo": comp.get("version", "NOASSERTION"),
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": f"pkg:{ecosystem}/{comp['name']}@{comp.get('version', '')}"
                }
            ]
        }
        for comp in components
    ]
    
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"propex-sbom-{package_name}",
        "documentNamespace": doc_namespace,
        "creationInfo": {
            "created": now,
            "creators": ["Tool: Propex-SBOM-Exporter-1.0"],
            "licenseListVersion": "3.21"
        },
        "packages": packages,
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": f"SPDXRef-Package-{components[0]['name'].replace('/', '-')}"
            }
        ] if components else []
    }


def _cvss_to_severity(score: float) -> str:
    if score >= 9.0: return "critical"
    if score >= 7.0: return "high"
    if score >= 4.0: return "medium"
    return "low"
