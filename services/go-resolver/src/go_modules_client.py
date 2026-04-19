"""
Go Modules resolver service.
Resolves Go module dependencies using the Go Module Proxy (proxy.golang.org) — free, no auth.
"""
import logging
import json
import httpx
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

GO_PROXY = "https://proxy.golang.org"
GO_SUM_DB = "https://sum.golang.org"

class GoModulesClient:
    """
    Resolves Go module dependency trees using the public Go Module Proxy.
    No authentication required. Rate limits are generous.
    """
    
    async def get_module_info(self, module_path: str, version: str = "latest") -> Optional[Dict]:
        """Fetch module metadata from Go Module Proxy."""
        url = f"{GO_PROXY}/{module_path}/@v/{version}.info"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"Go proxy returned {resp.status_code} for {module_path}@{version}")
            except Exception as e:
                logger.error(f"Go proxy fetch failed: {e}")
        return None

    async def get_module_versions(self, module_path: str) -> List[str]:
        """List all available versions of a Go module."""
        url = f"{GO_PROXY}/{module_path}/@v/list"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return [v.strip() for v in resp.text.splitlines() if v.strip()]
            except Exception as e:
                logger.error(f"Version list failed for {module_path}: {e}")
        return []

    async def get_go_mod(self, module_path: str, version: str) -> Optional[str]:
        """
        Download the go.mod file for a module version.
        This contains all direct + indirect dependencies.
        """
        url = f"{GO_PROXY}/{module_path}/@v/{version}.mod"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.text
            except Exception as e:
                logger.error(f"go.mod fetch failed: {e}")
        return None

    def parse_go_mod(self, go_mod_content: str) -> List[Dict[str, str]]:
        """
        Parse a go.mod file and extract all require directives.
        Returns list of {module: str, version: str, indirect: bool}
        """
        deps = []
        in_require_block = False
        
        for line in go_mod_content.splitlines():
            stripped = line.strip()
            
            if stripped.startswith("require ("):
                in_require_block = True
                continue
            if in_require_block and stripped == ")":
                in_require_block = False
                continue
            
            if in_require_block or stripped.startswith("require "):
                # Remove "require " prefix for single-line requires
                if stripped.startswith("require "):
                    stripped = stripped[8:]
                
                # Remove inline comments
                if "//" in stripped:
                    comment = stripped[stripped.index("//"):]
                    stripped = stripped[:stripped.index("//")].strip()
                    indirect = "indirect" in comment
                else:
                    indirect = False
                
                parts = stripped.split()
                if len(parts) >= 2:
                    deps.append({
                        "module": parts[0],
                        "version": parts[1],
                        "indirect": indirect
                    })
        
        return deps
