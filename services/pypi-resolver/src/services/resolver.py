import logging
import asyncio
from typing import List, Set, Dict, Any

from ..clients.pypi_client import PyPiClient
from ..clients.libraries_client import LibrariesIoClient
from .graph_writer import GraphWriter
from odepm_common.kafka.producer import KafkaProducerBase

logger = logging.getLogger(__name__)

class PyPiResolverService:
    def __init__(
        self, 
        pypi_client: PyPiClient, 
        libs_client: LibrariesIoClient,
        graph_writer: GraphWriter,
        kafka_producer: KafkaProducerBase,
        max_depth: int = 5
    ):
        self.pypi_client = pypi_client
        self.libs_client = libs_client
        self.graph_writer = graph_writer
        self.kafka_producer = kafka_producer
        self.max_depth = max_depth

    async def resolve(self, cve_id: str, package_name: str, message_data: Dict[str, Any]):
        """
        Resolve propagation of a CVE through the PyPI ecosystem via BFS traversal.
        """
        logger.info(f"Starting PyPI propagation resolution for {cve_id} in {package_name}")
        
        # Mark initial package as affected
        await self.graph_writer.mark_affected(cve_id, "pypi", package_name)
        
        queue = [(package_name, 0)]
        visited: Set[str] = {package_name}
        
        while queue:
            current_pkg, depth = queue.pop(0)
            
            if depth >= self.max_depth:
                logger.debug(f"Reached max depth {self.max_depth} for {current_pkg}")
                continue
                
            logger.info(f"Resolving PyPI dependents for {current_pkg} (depth {depth})")
            
            # Fetch reverse dependencies (who depends on current_pkg)
            dependents = await self.libs_client.get_dependents(current_pkg, platform="pypi")
            
            for dep in dependents:
                dep_name = dep.get("name")
                if not dep_name or dep_name in visited:
                    continue
                
                # In a robust implementation, we'd check the PEP 508 version requirement constraints
                # For this milestone, we map the structural blast radius
                await self.graph_writer.create_dependency(dep_name, current_pkg, "pypi", "*")
                await self.graph_writer.mark_affected(cve_id, "pypi", dep_name)
                
                visited.add(dep_name)
                queue.append((dep_name, depth + 1))
                
                # Sleep to respect rate limits of Libraries.io (60 req/min free tier)
                await asyncio.sleep(1.0) 

        logger.info(f"Finished PyPI resolution for {cve_id}. Found {len(visited)} affected packages.")
        
        # Publish completion event
        resolved_event = {
            "cve_id": cve_id,
            "ecosystem": "pypi",
            "root_package": package_name,
            "blast_radius_size": len(visited)
        }
        self.kafka_producer.produce("dependency.resolved", key=cve_id, value=resolved_event)
        logger.info(f"Published resolution event for {cve_id} to dependency.resolved")
