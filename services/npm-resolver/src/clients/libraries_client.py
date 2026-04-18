import logging
from typing import List, Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LibrariesIoClient:
    BASE_URL = "https://libraries.io/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=20.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_dependents(self, ecosystem: str, package_name: str) -> List[Dict[str, Any]]:
        """
        Fetch dependents for a package from libraries.io.
        Ecosystem mapping: npm -> NPM, pypi -> Pypi, etc.
        """
        # Libraries.io uses capitalized ecosystem names
        lib_ecosystem = ecosystem.upper() if ecosystem != "pypi" else "Pypi"
        
        url = f"{self.BASE_URL}/{lib_ecosystem}/{package_name}/dependents"
        params = {"api_key": self.api_key}
        
        logger.debug(f"Fetching dependents for {package_name} from libraries.io")
        
        response = await self.client.get(url, params=params)
        if response.status_code == 404:
            return []
            
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
