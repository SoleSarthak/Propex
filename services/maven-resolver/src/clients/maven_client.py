import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MavenCentralClient:
    def __init__(self, base_url: str = "https://search.maven.org/solrsearch/select", repo_url: str = "https://repo1.maven.org/maven2"):
        self.base_url = base_url
        self.repo_url = repo_url
        self.client = httpx.AsyncClient(timeout=15.0)

    async def get_package_versions(self, group_id: str, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Search Maven Central to get all available versions for a given group and artifact.
        """
        params = {
            "q": f"g:\"{group_id}\" AND a:\"{artifact_id}\"",
            "core": "gav",
            "rows": 100,
            "wt": "json"
        }
        
        try:
            response = await self.client.get(self.base_url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch {group_id}:{artifact_id} metadata: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Exception fetching {group_id}:{artifact_id} metadata: {e}")
            return None

    async def get_pom_xml(self, group_id: str, artifact_id: str, version: str) -> Optional[str]:
        """
        Fetch the actual POM XML file from the Maven Central repository.
        """
        group_path = group_id.replace('.', '/')
        url = f"{self.repo_url}/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                logger.warning(f"POM not found at {url}")
                return None
            else:
                logger.error(f"Failed to fetch POM from {url}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Exception fetching POM from {url}: {e}")
            return None

    async def close(self):
        await self.client.aclose()
