import logging
import asyncio
from typing import List, Set, Dict, Any
from ..clients.npm_client import NpmClient
from ..clients.libraries_client import LibrariesIoClient
from .version_checker import VersionChecker
from .graph_writer import GraphWriter

logger = logging.getLogger(__name__)

class NpmResolver:
    def __init__(
        self, 
        npm_client: NpmClient, 
        libs_client: LibrariesIoClient,
        graph_writer: GraphWriter,
        max_depth: int = 10
    ):
        self.npm_client = npm_client
        self.libs_client = libs_client
        self.graph_writer = graph_writer
        self.max_depth = max_depth

    async def resolve_propagation(self, cve_id: str, package_name: str, vulnerable_ranges: List[str]):
        """
        Main entry point to resolve propagation of a CVE through npm ecosystem.
        """
        logger.info(f"Starting propagation resolution for {cve_id} in {package_name}")
        
        # 1. Mark the initial package as affected
        await self.graph_writer.mark_affected(cve_id, "npm", package_name)
        
        # 2. Start BFS traversal
        queue = [(package_name, 0)]
        visited = {package_name}
        
        while queue:
            current_pkg, depth = queue.pop(0)
            
            if depth >= self.max_depth:
                logger.debug(f"Reached max depth {self.max_depth} for {current_pkg}")
                continue
                
            logger.info(f"Resolving dependents for {current_pkg} (depth {depth})")
            
            # Fetch dependents from libraries.io
            dependents = await self.libs_client.get_dependents("npm", current_pkg)
            
            for dep in dependents:
                dep_name = dep.get("name")
                if not dep_name or dep_name in visited:
                    continue
                
                # In a real implementation, we would check the version constraint
                # to see if the dependent uses a vulnerable version.
                # For Phase 1, we'll mark it and continue the BFS.
                
                await self.graph_writer.create_dependency(dep_name, current_pkg, "npm", "unknown")
                await self.graph_writer.mark_affected(cve_id, "npm", dep_name)
                
                visited.add(dep_name)
                queue.append((dep_name, depth + 1))
                
                # Small sleep to respect rate limits
                await asyncio.sleep(0.1)

        logger.info(f"Finished propagation resolution for {cve_id}. Found {len(visited)} affected packages.")
