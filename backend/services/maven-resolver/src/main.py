import os
import asyncio
import logging
from dep_mapper_shared.kafka import KafkaConsumerWrapper, KafkaProducerWrapper
from dep_mapper_shared.neo4j_client import Neo4jClient
from dep_mapper_shared.redis_client import RedisClient
from api_clients import MavenCentralClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9094")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "propex_password")

neo4j_client = Neo4jClient(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
redis_client = RedisClient(host=REDIS_HOST, port=6379)
producer = KafkaProducerWrapper(KAFKA_BROKER)

def resolve_maven_dependencies(cve_data: dict):
    if cve_data.get("affected_packages"):
        for pkg in cve_data["affected_packages"]:
            if pkg.get("ecosystem", "").lower() == "maven":
                asyncio.run(process_package(cve_data["cve_id"], pkg))

async def process_package(cve_id: str, pkg: dict):
    pkg_name = pkg["name"]
    logger.info(f"Resolving Maven package {pkg_name} for CVE {cve_id}")
    
    # Split group_id and artifact_id typically colons
    parts = pkg_name.split(":")
    group_id = parts[0] if len(parts) > 0 else pkg_name
    artifact_id = parts[1] if len(parts) > 1 else ""

    if redis_client.check_rate_limit(f"rate:maven:{pkg_name}", limit=100, window_seconds=60):
        try:
            # 1. Fetch info
            deps = await MavenCentralClient.search_dependencies(group_id, artifact_id)
            
            # 2. Write Graph
            for dep in deps:
                child_name = dep.get("id", "unknown:unknown")
                neo4j_client.add_package_dependency("maven", child_name, "latest", "maven", pkg_name, "latest")
            
            # 3. Write CVE Connection
            neo4j_client.mark_cve_affected(cve_id, 0.0, "maven", pkg_name, pkg.get("versions_affected", []))
            
            # 4. Record to Kafka
            producer.publish("dependency.resolved", {
                "cve_id": cve_id,
                "affected_package_ecosystem": "maven",
                "affected_package_name": pkg_name,
                "resolutions_found": len(deps),
                "status": "resolved"
            })
            logger.info(f"Resolved {len(deps)} dependents for Maven artifact {pkg_name}")
            
        except Exception as e:
            logger.error(f"Error processing {pkg_name}: {e}")

if __name__ == "__main__":
    logger.info("Starting Maven Resolver Service...")
    neo4j_client.create_indexes()
    consumer = KafkaConsumerWrapper(KAFKA_BROKER, "maven-resolver-group", ["cve.raw"])
    consumer.consume_loop(resolve_maven_dependencies)
