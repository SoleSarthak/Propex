"""
NuGet (C#/.NET) resolver service.
Uses the NuGet v3 API — free, no auth required.
"""
import logging
import httpx
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

NUGET_INDEX_URL = "https://api.nuget.org/v3/index.json"
NUGET_SEARCH_URL = "https://azuresearch-usnc.nuget.org/query"
NUGET_FLATCONTAINER = "https://api.nuget.org/v3-flatcontainer"

class NuGetClient:
    """
    Resolves .NET package dependency trees via the NuGet v3 REST API.
    Completely free, no authentication required.
    """
    
    async def get_package_versions(self, package_id: str) -> List[str]:
        """List all available versions of a NuGet package."""
        url = f"{NUGET_FLATCONTAINER}/{package_id.lower()}/index.json"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("versions", [])
                logger.warning(f"NuGet returned {resp.status_code} for {package_id}")
            except Exception as e:
                logger.error(f"NuGet version fetch failed for {package_id}: {e}")
        return []

    async def get_package_manifest(self, package_id: str, version: str) -> Optional[str]:
        """
        Download the .nuspec XML manifest for a package version.
        This contains all <dependency> elements.
        """
        url = f"{NUGET_FLATCONTAINER}/{package_id.lower()}/{version}/{package_id.lower()}.nuspec"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.text
            except Exception as e:
                logger.error(f"nuspec fetch failed: {e}")
        return None

    def parse_nuspec(self, nuspec_xml: str) -> List[Dict[str, str]]:
        """
        Parse a .nuspec XML file and extract all <dependency> elements.
        Returns list of {id, version, target_framework}
        """
        import xml.etree.ElementTree as ET
        deps = []
        
        try:
            root = ET.fromstring(nuspec_xml)
            ns = {"ns": "http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"}
            
            for dep_group in root.findall(".//ns:group", ns):
                target_fw = dep_group.get("targetFramework", "any")
                for dep in dep_group.findall("ns:dependency", ns):
                    deps.append({
                        "id": dep.get("id", ""),
                        "version": dep.get("version", ""),
                        "target_framework": target_fw,
                        "exclude": dep.get("exclude", "")
                    })
            
            # Also handle ungrouped dependencies
            for dep in root.findall(".//ns:dependencies/ns:dependency", ns):
                deps.append({
                    "id": dep.get("id", ""),
                    "version": dep.get("version", ""),
                    "target_framework": "any",
                    "exclude": dep.get("exclude", "")
                })
        except ET.ParseError as e:
            logger.error(f"nuspec XML parse error: {e}")
        
        return deps

    async def search_packages(self, query: str, prerelease: bool = False) -> List[Dict]:
        """Search NuGet for packages matching a query."""
        params = {"q": query, "prerelease": str(prerelease).lower(), "take": 20}
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(NUGET_SEARCH_URL, params=params)
                if resp.status_code == 200:
                    return resp.json().get("data", [])
            except Exception as e:
                logger.error(f"NuGet search failed: {e}")
        return []
