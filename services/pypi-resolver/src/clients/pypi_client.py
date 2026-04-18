import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PyPiClient:
    def __init__(self, base_url: str = "https://pypi.org/pypi"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_package_info(self, package_name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch package information from PyPI JSON API.
        If version is provided, fetches specific version info, otherwise fetches latest.
        """
        try:
            if version:
                url = f"{self.base_url}/{package_name}/{version}/json"
            else:
                url = f"{self.base_url}/{package_name}/json"
                
            response = await self.client.get(url)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Package {package_name} (version: {version}) not found on PyPI.")
                return None
            else:
                logger.error(f"Failed to fetch {package_name} from PyPI: HTTP {response.status_code}")
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Exception fetching {package_name} from PyPI: {e}")
            return None

    async def close(self):
        await self.client.aclose()
