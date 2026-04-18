import os
import httpx
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
            
        self.client = httpx.AsyncClient(timeout=30.0, headers=self.headers)

    async def get_repo_metadata(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Enrich repository metadata from GitHub API (stars, language, archive status, fork)
        """
        if not self.token:
            logger.warning("GITHUB_TOKEN not set. Rate limits will be heavily restricted (60/hr).")

        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "full_name": data.get("full_name"),
                    "stars": data.get("stargazers_count"),
                    "language": data.get("language"),
                    "archived": data.get("archived"),
                    "fork": data.get("fork"),
                    "updated_at": data.get("updated_at")
                }
            elif response.status_code == 404:
                logger.warning(f"Repository {owner}/{repo} not found.")
                return None
            elif response.status_code == 403:
                logger.warning("GitHub API rate limit exceeded.")
                return None
            else:
                logger.error(f"Failed to fetch metadata for {owner}/{repo}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Exception fetching metadata for {owner}/{repo}: {e}")
            return None

    async def search_code(self, query: str, date_from: datetime = None, date_to: datetime = None) -> List[Dict[str, Any]]:
        """
        Search GitHub for code (e.g., manifest files).
        Handles GitHub search API pagination limit (1,000 results) via date windowing.
        """
        results = []
        
        # Base query format
        if date_from and date_to:
            date_str = f" pushed:{date_from.strftime('%Y-%m-%d')}..{date_to.strftime('%Y-%m-%d')}"
            full_query = f"{query}{date_str}"
        else:
            full_query = query
            
        params = {
            "q": full_query,
            "per_page": 100,
            "page": 1
        }
        
        url = f"{self.base_url}/search/code"
        
        while True:
            try:
                response = await self.client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    results.extend(items)
                    
                    if len(items) < 100 or len(results) >= 1000:
                        # Reached end or GitHub 1000 result limit
                        break
                        
                    params["page"] += 1
                    await asyncio.sleep(2.0)  # Respect 30 req/min limit for Search API
                elif response.status_code == 403:
                    logger.warning("GitHub Search API rate limit exceeded. Sleeping for 60s...")
                    await asyncio.sleep(60)
                else:
                    logger.error(f"GitHub search failed: HTTP {response.status_code}")
                    break
                    
            except Exception as e:
                logger.error(f"Exception searching GitHub: {e}")
                break
                
        return results

    async def close(self):
        await self.client.aclose()
