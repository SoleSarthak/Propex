import logging
import os
import asyncio
from fastapi import FastAPI

from .services.consumer import MavenCveConsumer
from .services.resolver import MavenResolverService
from .services.graph_writer import GraphWriter
from .services.pom_parser import PomParser
from .clients.maven_client import MavenCentralClient
from odepm_common.kafka.producer import KafkaProducerBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maven Resolver Service")

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "propex_password")

# Initialize components
maven_client = MavenCentralClient()
pom_parser = PomParser()
graph_writer = GraphWriter(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
kafka_producer = KafkaProducerBase(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

resolver_service = MavenResolverService(
    maven_client=maven_client,
    pom_parser=pom_parser,
    graph_writer=graph_writer,
    kafka_producer=kafka_producer
)

consumer = MavenCveConsumer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id="maven-resolver-group",
    resolver_service=resolver_service
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consumer.start())
    logger.info("Kafka consumer started for Maven Resolver")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    consumer.stop()
    await maven_client.close()
    await graph_writer.close()
    kafka_producer.close()
