from confluent_kafka import Producer, Consumer, KafkaError
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class KafkaProducerBase:
    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def produce(self, topic: str, key: str, value: Any):
        """
        Produce a message to a Kafka topic.
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        self.producer.produce(
            topic, 
            key=key,
            value=value.encode("utf-8") if isinstance(value, str) else value,
            callback=self.delivery_report
        )
        self.producer.poll(0)

    def flush(self):
        self.producer.flush()

    def close(self):
        self.flush()

# Alias for backward compatibility
KafkaProducerWrapper = KafkaProducerBase


class KafkaConsumerBase:
    def __init__(self, bootstrap_servers: str, group_id: str, topics: List[str]):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True
        })
        self.consumer.subscribe(topics)
        self._running = False

    async def start(self):
        """
        Start the consumption loop.
        """
        self._running = True
        logger.info(f"Starting Kafka consumer for topics: {self.topics}")
        
        try:
            while self._running:
                # Run poll in a thread to avoid blocking the event loop
                msg = await asyncio.to_thread(self.consumer.poll, 1.0)
                
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        break

                try:
                    payload = json.loads(msg.value().decode("utf-8"))
                    await self.process_message(payload)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        finally:
            self.close()

    async def process_message(self, message_data: Dict[str, Any]):
        """
        Override this method in subclasses to handle messages.
        """
        raise NotImplementedError("Subclasses must implement process_message")

    def stop(self):
        self._running = False

    def close(self):
        self.consumer.close()

# Alias for backward compatibility
KafkaConsumerWrapper = KafkaConsumerBase
