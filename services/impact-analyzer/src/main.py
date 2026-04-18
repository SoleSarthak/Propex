import logging
import os
import asyncio
from fastapi import FastAPI

from .db import Database
from .services.neo4j_client import Neo4jClient
from .services.analyzer import ImpactAnalyzerService
from .consumer import ImpactAnalyzerConsumer
from .scheduler import BatchJobScheduler
from odepm_common.kafka.producer import KafkaProducerBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Impact Analyzer Service")

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "propex_password")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://propex:propex_password@postgres:5432/propex_db")

# In-memory queue for batch jobs
job_queue = []

# Initialize components
db = Database(DATABASE_URL)
neo4j_client = Neo4jClient(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
analyzer_service = ImpactAnalyzerService(neo4j_client=neo4j_client, redis_url=REDIS_URL)
kafka_producer = KafkaProducerBase(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

scheduler = BatchJobScheduler(job_queue=job_queue, producer=kafka_producer)

consumer = ImpactAnalyzerConsumer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id="impact-analyzer-group",
    analyzer_service=analyzer_service,
    db=db,
    producer=kafka_producer,
    job_queue=job_queue
)

@app.on_event("startup")
async def startup_event():
    # Initialize DB schema
    await db.init_db()
    
    # Start background tasks
    asyncio.create_task(consumer.start())
    scheduler.start()
    logger.info("Impact Analyzer Service started successfully.")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "queue_size": len(job_queue)}

@app.on_event("shutdown")
async def shutdown_event():
    consumer.stop()
    scheduler.stop()
    await analyzer_service.close()
    await neo4j_client.close()
    await db.close()
    kafka_producer.close()
