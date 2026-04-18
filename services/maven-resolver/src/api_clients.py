import httpx
from typing import Dict, List


class MavenCentralClient:
    BASE_URL = "https://search.maven.org/solrsearch/select"

    @classmethod
    async def search_dependencies(cls, group_id: str, artifact_id: str) -> List[Dict]:
        """
        Uses Maven Central REST API to find dependents or versions.
        """
        query = f'g:"{group_id}" AND a:"{artifact_id}"'
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                cls.BASE_URL, params={"q": query, "rows": 20, "wt": "json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", {}).get("docs", [])
            return []
