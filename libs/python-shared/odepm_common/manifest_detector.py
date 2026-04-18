import logging
from typing import Dict, List
from .github_client import GitHubClient

logger = logging.getLogger(__name__)

class ManifestDetector:
    def __init__(self, github_client: GitHubClient):
        self.github_client = github_client
        
        # Mapping of ecosystem to typical manifest file names
        self.manifest_map = {
            "npm": ["package.json"],
            "pypi": ["requirements.txt", "setup.py", "pyproject.toml"],
            "maven": ["pom.xml", "build.gradle"]
        }

    async def detect_manifests(self, package_name: str, ecosystem: str) -> List[Dict[str, str]]:
        """
        Use GitHub Search API to find repositories containing manifest files 
        that reference the given vulnerable package.
        """
        manifest_files = self.manifest_map.get(ecosystem.lower(), [])
        if not manifest_files:
            logger.warning(f"No manifest files configured for ecosystem: {ecosystem}")
            return []

        results = []
        for manifest in manifest_files:
            # E.g., query: "requests" filename:requirements.txt
            query = f'"{package_name}" filename:{manifest}'
            logger.info(f"Searching GitHub for: {query}")
            
            search_results = await self.github_client.search_code(query)
            
            for item in search_results:
                repo_info = item.get("repository", {})
                results.append({
                    "repo_full_name": repo_info.get("full_name"),
                    "repo_url": repo_info.get("html_url"),
                    "file_path": item.get("path"),
                    "manifest_type": manifest
                })
                
        # Deduplicate by repo_url
        unique_repos = {r["repo_url"]: r for r in results}.values()
        return list(unique_repos)
