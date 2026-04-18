import asyncio
from neo4j import AsyncGraphDatabase

async def main():
    driver = AsyncGraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "propex_password"))
    
    async with driver.session() as session:
        # PyPI requests
        await session.run("""
        MERGE (c:Cve {cve_id: 'CVE-TEST-REQUESTS'})
        MERGE (p:Package {ecosystem: 'pypi', name: 'requests'})
        MERGE (c)-[:AFFECTS]->(p)
        MERGE (d:Package {ecosystem: 'pypi', name: 'my-python-app'})
        MERGE (d)-[:DEPENDS_ON]->(p)
        """)
        
        # Maven log4j
        await session.run("""
        MERGE (c:Cve {cve_id: 'CVE-TEST-LOG4J'})
        MERGE (p:Package {ecosystem: 'maven', name: 'org.apache.logging.log4j:log4j-core'})
        MERGE (c)-[:AFFECTS]->(p)
        MERGE (d:Package {ecosystem: 'maven', name: 'my-java-app'})
        MERGE (d)-[:DEPENDS_ON]->(p)
        """)
        
    await driver.close()

if __name__ == "__main__":
    asyncio.run(main())
