import os
import asyncio
import logging
from odepm_common.kafka.producer import KafkaConsumerWrapper, KafkaProducerWrapper
from odepm_common.db.neo4j_client import Neo4jClient
from odepm_common.cache.redis_client import RedisClient
from api_clients import LibrariesIoClient

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


def resolve_pypi_dependencies(cve_data: dict):
    """
    Parses a CVE raw event, extracts PyPI packages, and resolves.
    """
    if cve_data.get("affected_packages"):
        for pkg in cve_data["affected_packages"]:
            if pkg.get("ecosystem", "").lower() == "pypi":
                asyncio.run(process_package(cve_data["cve_id"], pkg))


async def process_package(cve_id: str, pkg: dict):
    pkg_name = pkg["name"]
    logger.info(f"Resolving PyPI package {pkg_name} for CVE {cve_id}")

    # Optional caching logic for package info
    if redis_client.check_rate_limit(
        f"rate:pypi:{pkg_name}", limit=100, window_seconds=60
    ):
        try:
            # 1. Fetch package info (dummy call usage)
            # pypi_data = await PyPIClient.get_package_json(pkg_name)

            # 2. Get dependents from libraries.io
            deps = await LibrariesIoClient.get_reverse_dependencies("pypi", pkg_name)

            # 3. Write Graph
            for dep in deps:
                child_name = dep.get("name")
                neo4j_client.add_package_dependency(
                    "pypi", child_name, "latest", "pypi", pkg_name, "latest"
                )

            # 4. Write Cve connection
            neo4j_client.mark_cve_affected(
                cve_id, 0.0, "pypi", pkg_name, pkg.get("versions_affected", [])
            )

            # Publish resolved
            producer.publish(
                "dependency.resolved",
                {
                    "cve_id": cve_id,
                    "affected_package_ecosystem": "pypi",
                    "affected_package_name": pkg_name,
                    "resolutions_found": len(deps),
                    "status": "resolved",
                },
            )
            logger.info(f"Resolved {len(deps)} dependents for {pkg_name}")

        except Exception as e:
            logger.error(f"Error processing {pkg_name}: {e}")


if __name__ == "__main__":
    logger.info("Starting PyPI Resolver Service...")
    neo4j_client.create_indexes()
    consumer = KafkaConsumerWrapper(KAFKA_BROKER, "pypi-resolver-group", ["cve.raw"])
    consumer.consume_loop(resolve_pypi_dependencies)
