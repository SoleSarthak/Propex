from confluent_kafka import Producer, Consumer, KafkaError
import json
import logging

logger = logging.getLogger(__name__)

class KafkaProducerWrapper:
    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def publish(self, topic: str, data: dict):
        self.producer.produce(
            topic,
            value=json.dumps(data).encode('utf-8'),
            callback=self.delivery_report
        )
        self.producer.poll(0)
    
    def flush(self):
        self.producer.flush()

class KafkaConsumerWrapper:
    def __init__(self, bootstrap_servers: str, group_id: str, topics: list[str]):
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe(topics)

    def consume_loop(self, message_handler_callback):
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        break
                
                try:
                    payload = json.loads(msg.value().decode('utf-8'))
                    message_handler_callback(payload)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
        finally:
            self.consumer.close()
