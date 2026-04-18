import logging
import os
import json
import asyncio
from typing import Dict, Any
from fastapi import FastAPI
from odepm_common.kafka.consumer import KafkaConsumerBase
from odepm_common.db.session import get_db_session_factory
from odepm_common.models.cve import CveRecord
from .services.router import CoordinatorRouter
from .services.status_tracker import StatusTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dependency Coordinator")

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize components
router = CoordinatorRouter(KAFKA_BOOTSTRAP_SERVERS)
session_factory = get_db_session_factory(DATABASE_URL)

class CoordinatorConsumer(KafkaConsumerBase):
    async def process_message(self, message_data: Dict[str, Any]):
        """
        Process a message from the cve.raw topic and route it.
        """
        try:
            record = CveRecord(**message_data)
            logger.info(f"Received CVE for coordination: {record.cve_id}")
            
            # 1. Update status to 'resolving'
            async with session_factory() as session:
                tracker = StatusTracker(session)
                await tracker.update_status(record.cve_id, "resolving")
            
            # 2. Route to appropriate resolvers
            await router.route_cve(record)
            
        except Exception as e:
            logger.error(f"Failed to process coordination for message: {e}")

consumer = CoordinatorConsumer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id="coordinator-group",
    topics=["cve.raw"]
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consumer.start())
    logger.info("Kafka consumer started for Dependency Coordinator")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    consumer.stop()
    await router.close()
