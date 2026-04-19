"""
GitLab Issue Creator — extends issue creation to support GitLab repositories.
Uses GitLab REST API v4 (free for all GitLab.com users).
"""
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

GITLAB_API_URL = "https://gitlab.com/api/v4"

class GitLabIssueClient:
    """
    Creates security issues on GitLab repositories via the GitLab v4 REST API.
    Mirrors the GitHub IssueCreator pipeline for GitLab-hosted projects.
    """
    
    def __init__(self, access_token: str):
        self.headers = {
            "PRIVATE-TOKEN": access_token,
            "Content-Type": "application/json"
        }

    def _parse_gitlab_path(self, repo_url: str) -> Optional[str]:
        """Extract encoded namespace/project path from a GitLab URL."""
        import urllib.parse
        # https://gitlab.com/owner/repo or https://gitlab.com/org/group/repo
        url = repo_url.rstrip("/")
        if "gitlab.com/" not in url:
            return None
        path = url.split("gitlab.com/", 1)[1]
        return urllib.parse.quote(path, safe="")

    async def search_existing_issues(self, repo_url: str, cve_id: str) -> bool:
        """Check if a security issue for this CVE already exists on GitLab."""
        encoded_path = self._parse_gitlab_path(repo_url)
        if not encoded_path:
            return False
        
        url = f"{GITLAB_API_URL}/projects/{encoded_path}/issues"
        params = {"search": cve_id, "scope": "all", "state": "all"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, params=params, headers=self.headers)
                if resp.status_code == 200:
                    return len(resp.json()) > 0
            except Exception as e:
                logger.error(f"GitLab issue search failed: {e}")
        return False

    async def create_issue(self, repo_url: str, title: str, description: str, 
                           labels: list[str] = None) -> Optional[str]:
        """
        Create a GitLab issue and return the web URL.
        GitLab uses 'description' instead of 'body'.
        """
        encoded_path = self._parse_gitlab_path(repo_url)
        if not encoded_path:
            logger.error(f"Cannot parse GitLab path from URL: {repo_url}")
            return None
        
        url = f"{GITLAB_API_URL}/projects/{encoded_path}/issues"
        payload = {
            "title": title,
            "description": description,
            "labels": ",".join(labels or ["security", "vulnerability", "propex"])
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url, json=payload, headers=self.headers)
                if resp.status_code == 201:
                    issue_url = resp.json().get("web_url")
                    logger.info(f"GitLab issue created: {issue_url}")
                    return issue_url
                logger.error(f"GitLab issue creation failed: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"GitLab API error: {e}")
        return None
