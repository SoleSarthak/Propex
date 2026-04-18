import logging
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class NpmClient:
    BASE_URL = "https://registry.npmjs.org"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_package_metadata(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full metadata for a package from the npm registry.
        """
        url = f"{self.BASE_URL}/{package_name}"
        logger.debug(f"Fetching npm metadata for {package_name}")
        
        response = await self.client.get(url)
        if response.status_code == 404:
            logger.warning(f"Package {package_name} not found in npm registry")
            return None
            
        response.raise_for_status()
        return response.json()

    async def get_package_dependencies(self, package_name: str, version: str = "latest") -> Dict[str, str]:
        """
        Fetch dependencies for a specific version of a package.
        """
        metadata = await self.get_package_metadata(package_name)
        if not metadata:
            return {}

        versions = metadata.get("versions", {})
        
        # Resolve 'latest' tag if needed
        if version == "latest":
            version = metadata.get("dist-tags", {}).get("latest")
            if not version:
                return {}

        target_version_data = versions.get(version)
        if not target_version_data:
            # Fallback to latest if specific version not found
            latest = metadata.get("dist-tags", {}).get("latest")
            target_version_data = versions.get(latest, {})

        return target_version_data.get("dependencies", {})

    async def close(self):
        await self.client.aclose()
