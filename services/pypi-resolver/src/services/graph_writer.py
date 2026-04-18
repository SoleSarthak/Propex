import logging
from typing import Dict, Any, List
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

class GraphWriter:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self):
        await self.driver.close()

    async def upsert_package(self, ecosystem: str, name: str, version: str):
        """
        Upsert a Package node.
        """
        query = """
        MERGE (p:Package {ecosystem: $ecosystem, name: $name})
        SET p.latest_version = $version, p.updated_at = timestamp()
        RETURN p
        """
        async with self.driver.session() as session:
            await session.run(query, ecosystem=ecosystem, name=name, version=version)

    async def create_dependency(self, parent_name: str, child_name: str, ecosystem: str, version_req: str):
        """
        Create a DEPENDS_ON relationship between packages.
        """
        query = """
        MERGE (p1:Package {ecosystem: $ecosystem, name: $parent_name})
        MERGE (p2:Package {ecosystem: $ecosystem, name: $child_name})
        MERGE (p1)-[r:DEPENDS_ON]->(p2)
        SET r.version_requirement = $version_req, r.updated_at = timestamp()
        """
        async with self.driver.session() as session:
            await session.run(query, ecosystem=ecosystem, parent_name=parent_name, child_name=child_name, version_req=version_req)

    async def mark_affected(self, cve_id: str, ecosystem: str, package_name: str):
        """
        Create an AFFECTS relationship between a CVE and a Package.
        """
        query = """
        MERGE (c:Cve {cve_id: $cve_id})
        MERGE (p:Package {ecosystem: $ecosystem, name: $package_name})
        MERGE (c)-[r:AFFECTS]->(p)
        SET r.detected_at = timestamp()
        """
        async with self.driver.session() as session:
            await session.run(query, cve_id=cve_id, ecosystem=ecosystem, package_name=package_name)
