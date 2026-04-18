import logging
import os
import asyncio
from fastapi import FastAPI
from .services.github_client import GitHubClient
from .services.database import Database
from .consumer import IssueCreatorConsumer
from odepm_common.kafka.producer import KafkaProducerBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Issue Creator Service")

# Config
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://propex:propex_password@postgres:5432/propex_db")

# Support up to 5 GitHub tokens for round-robin rotation
GITHUB_TOKENS = [
    t for t in [
        os.getenv("GITHUB_TOKEN_1", os.getenv("GITHUB_TOKEN", "")),
        os.getenv("GITHUB_TOKEN_2", ""),
        os.getenv("GITHUB_TOKEN_3", ""),
        os.getenv("GITHUB_TOKEN_4", ""),
        os.getenv("GITHUB_TOKEN_5", ""),
    ] if t
]

# Components
github = GitHubClient(tokens=GITHUB_TOKENS if GITHUB_TOKENS else ["placeholder"])
db = Database(DATABASE_URL)
kafka_producer = KafkaProducerBase(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

consumer = IssueCreatorConsumer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id="issue-creator-group",
    github=github,
    db=db,
    producer=kafka_producer,
    redis_url=REDIS_URL
)

@app.on_event("startup")
async def startup_event():
    await db.init_db()
    asyncio.create_task(consumer.start())
    logger.info("Issue Creator Service started. Listening to 'notifications.out'...")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    consumer.stop()
    await consumer.close()
    await db.close()
    kafka_producer.close()
