import os
import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class LibrariesIoClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("LIBRARIES_IO_API_KEY")
        self.base_url = "https://libraries.io/api"
        self.client = httpx.AsyncClient(timeout=15.0)

    async def get_dependents(self, package_name: str, platform: str = "pypi", page: int = 1) -> List[Dict[str, Any]]:
        """
        Fetch reverse dependencies (dependents) for a given package on a specific platform.
        """
        if not self.api_key:
            logger.warning("LIBRARIES_IO_API_KEY not set. Dependents lookup will fail or be heavily rate-limited.")
            return []

        url = f"{self.base_url}/{platform}/{package_name}/dependents"
        params = {
            "api_key": self.api_key,
            "page": page,
            "per_page": 100
        }

        try:
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.info(f"No dependents found for {package_name} on {platform}")
                return []
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded for Libraries.io API")
                return []
            else:
                logger.error(f"Failed to fetch dependents for {package_name}: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Exception fetching dependents for {package_name}: {e}")
            return []

    async def close(self):
        await self.client.aclose()
