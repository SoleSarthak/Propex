"""
Cargo (Rust) resolver service.
Resolves crate dependencies using the crates.io API — free, no auth for read-only.
"""
import logging
import httpx
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

CRATES_IO_API = "https://crates.io/api/v1"
HEADERS = {"User-Agent": "Propex-Resolver/1.0 (github.com/SoleSarthak/Propex)"}  # Required by crates.io

class CargoClient:
    """
    Resolves Rust crate dependency trees via the crates.io REST API.
    crates.io requires a User-Agent header but no auth token.
    """
    
    async def get_crate_info(self, crate_name: str) -> Optional[Dict]:
        """Fetch crate metadata including latest version."""
        url = f"{CRATES_IO_API}/crates/{crate_name}"
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"crates.io returned {resp.status_code} for {crate_name}")
            except Exception as e:
                logger.error(f"crates.io fetch failed for {crate_name}: {e}")
        return None

    async def get_crate_versions(self, crate_name: str) -> List[str]:
        """List all published versions of a crate."""
        url = f"{CRATES_IO_API}/crates/{crate_name}/versions"
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return [v["num"] for v in data.get("versions", [])]
            except Exception as e:
                logger.error(f"Version list failed for {crate_name}: {e}")
        return []

    async def get_dependencies(self, crate_name: str, version: str) -> List[Dict]:
        """
        Fetch the direct dependencies of a specific crate version.
        Returns list of {crate_name, req, kind, optional}
        kind: "normal" | "dev" | "build"
        """
        url = f"{CRATES_IO_API}/crates/{crate_name}/{version}/dependencies"
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "crate_name": dep["crate_id"],
                            "requirement": dep["req"],
                            "kind": dep.get("kind", "normal"),
                            "optional": dep.get("optional", False)
                        }
                        for dep in data.get("dependencies", [])
                    ]
            except Exception as e:
                logger.error(f"Dependency fetch failed for {crate_name}@{version}: {e}")
        return []

    def is_runtime_dependency(self, kind: str) -> bool:
        """Only 'normal' kind dependencies are runtime. 'dev' and 'build' are not."""
        return kind == "normal"
