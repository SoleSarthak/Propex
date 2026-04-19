"""
Automated PR generation service — creates dependency bump pull requests.
Uses GitHub REST API (free with personal token).
"""
import logging
import base64
import httpx
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class PrGeneratorService:
    """
    Automatically creates pull requests that bump a vulnerable dependency
    to its fixed version in the repository's manifest file.
    """
    
    BASE_URL = "https://api.github.com"

    def __init__(self, github_token: str):
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[Dict]:
        """Fetch a file's content and SHA for update operations."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
        return None

    async def create_branch(self, owner: str, repo: str, branch_name: str, from_sha: str) -> bool:
        """Create a new branch from a given commit SHA."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/refs"
        payload = {"ref": f"refs/heads/{branch_name}", "sha": from_sha}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            return resp.status_code == 201

    async def update_file(self, owner: str, repo: str, path: str, branch: str, 
                          content: str, sha: str, commit_message: str) -> bool:
        """Update a file's content on a branch."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        encoded = base64.b64encode(content.encode()).decode()
        payload = {
            "message": commit_message,
            "content": encoded,
            "sha": sha,
            "branch": branch
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.put(url, json=payload, headers=self.headers)
            return resp.status_code in (200, 201)

    async def create_pull_request(self, owner: str, repo: str, title: str, 
                                   body: str, head_branch: str, base_branch: str = "main") -> Optional[str]:
        """Create a pull request and return its URL."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
            "draft": False
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code == 201:
                return resp.json().get("html_url")
            logger.error(f"PR creation failed: {resp.status_code} — {resp.text}")
        return None

    async def generate_bump_pr(self, owner: str, repo: str, package_name: str, 
                                old_version: str, fix_version: str, cve_id: str, 
                                manifest_path: str = "package.json") -> Optional[str]:
        """
        End-to-end: create branch → patch manifest → open PR.
        Returns the PR URL on success.
        """
        # 1. Get current default branch SHA
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            repo_info = await client.get(url, headers=self.headers)
            if repo_info.status_code != 200:
                return None
            default_branch = repo_info.json().get("default_branch", "main")

        branches_url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/ref/heads/{default_branch}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            ref_resp = await client.get(branches_url, headers=self.headers)
            if ref_resp.status_code != 200:
                return None
            base_sha = ref_resp.json()["object"]["sha"]

        # 2. Create branch
        branch_name = f"propex/fix-{cve_id.lower()}-{package_name}"
        if not await self.create_branch(owner, repo, branch_name, base_sha):
            logger.error(f"Failed to create branch {branch_name}")
            return None

        # 3. Fetch + patch the manifest file
        file_info = await self.get_file_content(owner, repo, manifest_path)
        if not file_info:
            logger.error(f"Could not find {manifest_path} in {owner}/{repo}")
            return None

        file_content = base64.b64decode(file_info["content"].replace("\n", "")).decode()
        patched_content = file_content.replace(
            f'"{package_name}": "{old_version}"',
            f'"{package_name}": "^{fix_version}"'
        )
        
        if patched_content == file_content:
            logger.warning(f"Could not find {package_name}@{old_version} in {manifest_path} to patch")
            return None

        commit_msg = f"fix(security): bump {package_name} from {old_version} to {fix_version} [{cve_id}]"
        if not await self.update_file(owner, repo, manifest_path, branch_name, 
                                       patched_content, file_info["sha"], commit_msg):
            return None

        # 4. Create the PR
        pr_title = f"[Security] Bump `{package_name}` to {fix_version} (fixes {cve_id})"
        pr_body = f"""## Security Vulnerability Fix

This PR was automatically generated by **Propex** to remediate [{cve_id}](https://nvd.nist.gov/vuln/detail/{cve_id}).

| | |
|---|---|
| **CVE** | `{cve_id}` |
| **Package** | `{package_name}` |
| **Vulnerable Version** | `{old_version}` |
| **Fixed Version** | `{fix_version}` |
| **Manifest** | `{manifest_path}` |

### What changed
`{package_name}` was pinned to `{old_version}` which contains a known security vulnerability.
This PR bumps it to `^{fix_version}` which resolves the issue.

---
*This PR was auto-generated by [Propex](https://github.com/SoleSarthak/Propex). Please review before merging.*
"""
        return await self.create_pull_request(owner, repo, pr_title, pr_body, branch_name, default_branch)
