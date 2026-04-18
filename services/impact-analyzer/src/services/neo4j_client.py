import logging
from typing import Dict, Any, List, Optional
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self):
        await self.driver.close()

    async def get_dependency_depth(self, cve_id: str, dependent_node_name: str, node_type: str = "Package") -> int:
        """
        Find the shortest path length (dependency depth) between a CVE and an affected package/repository.
        0 means direct dependency. >0 means transitive. Returns -1 if not found.
        """
        query = f"""
        MATCH p=shortestPath((c:Cve {{cve_id: $cve_id}})-[:AFFECTS|DEPENDS_ON*]->(t:{node_type} {{name: $node_name}}))
        RETURN length(p) - 1 as depth
        """
        try:
            async with self.driver.session() as session:
                result = await session.run(query, cve_id=cve_id, node_name=dependent_node_name)
                record = await result.single()
                if record:
                    return record["depth"]
        except Exception as e:
            logger.error(f"Error executing Neo4j depth query for {cve_id} -> {dependent_node_name}: {e}")
            
        return -1
