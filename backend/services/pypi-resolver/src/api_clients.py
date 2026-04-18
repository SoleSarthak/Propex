import httpx
from typing import Dict, Any, List

class PyPIClient:
    BASE_URL = "https://pypi.org/pypi"

    @classmethod
    async def get_package_json(cls, package_name: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{cls.BASE_URL}/{package_name}/json")
            resp.raise_for_status()
            return resp.json()

class LibrariesIoClient:
    BASE_URL = "https://libraries.io/api"

    @classmethod
    async def get_reverse_dependencies(cls, ecosystem: str, package_name: str) -> List[Dict]:
        """
        Uses libraries.io free tier. Max 60 req/min typically.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{cls.BASE_URL}/{ecosystem}/{package_name}/dependents")
            if resp.status_code == 200:
                return resp.json()
            return []
