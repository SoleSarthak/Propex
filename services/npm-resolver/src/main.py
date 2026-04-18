import logging
import os
import asyncio
from fastapi import FastAPI
from .clients.npm_client import NpmClient
from .clients.libraries_client import LibrariesIoClient
from .services.graph_writer import GraphWriter
from .services.resolver import NpmResolver
from .services.consumer import CveConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="npm Resolver Service")

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "propex_password")
LIBRARIES_IO_API_KEY = os.getenv("LIBRARIES_IO_API_KEY", "")

# Initialize components
npm_client = NpmClient()
libs_client = LibrariesIoClient(api_key=LIBRARIES_IO_API_KEY)
graph_writer = GraphWriter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
resolver = NpmResolver(npm_client, libs_client, graph_writer)

consumer = CveConsumer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id="npm-resolver-group",
    resolver=resolver
)

@app.on_event("startup")
async def startup_event():
    # Start Kafka consumer in the background
    asyncio.create_task(consumer.start())
    logger.info("Kafka consumer started for npm-resolver")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    consumer.stop()
    await npm_client.close()
    await libs_client.close()
    await graph_writer.close()
