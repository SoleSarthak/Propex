import logging
import os
import asyncio
from fastapi import FastAPI
from .services.drafter import PatchDrafterService
from .consumer import PatchDrafterConsumer
from odepm_common.kafka.producer import KafkaProducerBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Patch Drafter Service")

# Config
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://propex:propex_password@postgres:5432/propex_db")

# Components
drafter = PatchDrafterService(
    gemini_api_key=GEMINI_API_KEY,
    redis_url=REDIS_URL,
    database_url=DATABASE_URL
)
kafka_producer = KafkaProducerBase(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

consumer = PatchDrafterConsumer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id="patch-drafter-group",
    drafter=drafter,
    producer=kafka_producer
)

@app.on_event("startup")
async def startup_event():
    await drafter.init_db()
    asyncio.create_task(consumer.start())
    logger.info("Patch Drafter Service started. Listening to 'impact.scored'...")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    consumer.stop()
    await drafter.close()
    kafka_producer.close()
