from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def add_package_dependency(self, parent_ecosystem, parent_name, parent_version, child_ecosystem, child_name, child_version_spec, depth=1):
        query = '''
        MERGE (p1:Package {ecosystem: $parent_eco, name: $parent_name, version: $parent_version})
        MERGE (p2:Package {ecosystem: $child_eco, name: $child_name})
        MERGE (p1)-[r:DEPENDS_ON {version_spec: $child_version_spec}]->(p2)
        ON CREATE SET r.depth = $depth
        '''
        with self.driver.session() as session:
            session.run(query, parent_eco=parent_ecosystem, parent_name=parent_name,
                        parent_version=parent_version, child_eco=child_ecosystem,
                        child_name=child_name, child_version_spec=child_version_spec, depth=depth)

    def add_repository_usage(self, repo_url, repo_owner, package_ecosystem, package_name, version_spec):
        query = '''
        MERGE (r:Repository {url: $repo_url})
        ON CREATE SET r.owner = $repo_owner
        MERGE (p:Package {ecosystem: $package_eco, name: $package_name})
        MERGE (r)-[:USES {version_spec: $version_spec}]->(p)
        '''
        with self.driver.session() as session:
            session.run(query, repo_url=repo_url, repo_owner=repo_owner, 
                        package_eco=package_ecosystem, package_name=package_name, version_spec=version_spec)

    def mark_cve_affected(self, cve_id, cvss_score, package_ecosystem, package_name, versions_affected):
        query = '''
        MERGE (c:CVE {id: $cve_id})
        ON CREATE SET c.cvss = $cvss_score
        MERGE (p:Package {ecosystem: $package_eco, name: $package_name})
        MERGE (c)-[:AFFECTS {versions: $versions_affected}]->(p)
        '''
        with self.driver.session() as session:
            session.run(query, cve_id=cve_id, cvss_score=cvss_score, 
                        package_eco=package_ecosystem, package_name=package_name, versions_affected=versions_affected)

    def create_indexes(self):
        indexes = [
            "CREATE INDEX pkg_lookup IF NOT EXISTS FOR (p:Package) ON (p.name, p.ecosystem, p.version)",
            "CREATE INDEX repo_url IF NOT EXISTS FOR (r:Repository) ON (r.url)",
            "CREATE INDEX cve_id IF NOT EXISTS FOR (c:CVE) ON (c.id)"
        ]
        with self.driver.session() as session:
            for q in indexes:
                session.run(q)
                logger.info(f"Executed indexing: {q}")
