import logging
import asyncio
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

class GitHubClient:
    """
    GitHub REST API client for creating security issues on affected repositories.
    Implements token pool rotation and rate limit management.
    """
    BASE_URL = "https://api.github.com"

    def __init__(self, tokens: list[str]):
        if not tokens:
            raise ValueError("At least one GitHub token is required.")
        self._tokens = [t for t in tokens if t]  # Filter empty strings
        self._current_idx = 0

    def _get_token(self) -> str:
        """Round-robin token rotation across all available GitHub accounts."""
        token = self._tokens[self._current_idx % len(self._tokens)]
        self._current_idx += 1
        return token

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def search_existing_issues(self, owner: str, repo: str, cve_id: str) -> bool:
        """
        Check if a security issue for this CVE already exists on the repository.
        Returns True if a duplicate is found.
        """
        query = f"{cve_id} repo:{owner}/{repo} is:issue"
        url = f"{self.BASE_URL}/search/issues"
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params={"q": query}, headers=self._get_headers(), timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("total_count", 0) > 0
                logger.warning(f"GitHub issue search returned {resp.status_code}")
            except Exception as e:
                logger.error(f"Failed to search existing issues: {e}")
        return False

    async def create_issue(self, owner: str, repo: str, title: str, body: str, labels: list[str] = None, retries: int = 3) -> Optional[str]:
        """
        Create a GitHub issue with exponential backoff retry logic.
        Returns the URL of the created issue, or None on failure.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        payload = {
            "title": title,
            "body": body,
            "labels": labels or ["security", "vulnerability", "propex"]
        }
        
        for attempt in range(retries):
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(url, json=payload, headers=self._get_headers(), timeout=15.0)
                    
                    # Handle rate limiting
                    if resp.status_code == 429 or resp.status_code == 403:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        remaining = resp.headers.get("X-RateLimit-Remaining", "?")
                        logger.warning(f"GitHub rate limit hit. Remaining: {remaining}. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    if resp.status_code == 201:
                        issue_url = resp.json().get("html_url")
                        logger.info(f"GitHub issue created: {issue_url}")
                        return issue_url
                    else:
                        logger.error(f"GitHub issue creation failed (attempt {attempt+1}): {resp.status_code} {resp.text}")
                        
                except Exception as e:
                    logger.error(f"GitHub API error (attempt {attempt+1}): {e}")
                
                # Exponential backoff
                wait = 2 ** attempt
                logger.info(f"Retrying in {wait}s...")
                await asyncio.sleep(wait)
        
        return None
