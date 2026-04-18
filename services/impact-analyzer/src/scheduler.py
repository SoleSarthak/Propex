import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from odepm_common.kafka.producer import KafkaProducerBase

logger = logging.getLogger(__name__)

class BatchJobScheduler:
    def __init__(self, job_queue: list, producer: KafkaProducerBase):
        self.scheduler = AsyncIOScheduler()
        self.job_queue = job_queue
        self.producer = producer

    def start(self):
        # Schedule nightly at 2 AM UTC
        self.scheduler.add_job(
            self.process_batch,
            CronTrigger(hour=2, minute=0, timezone='UTC'),
            id='nightly_medium_low_publish',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("APScheduler started: Nightly batch job for Medium/Low impacts scheduled for 2:00 AM UTC.")

    async def process_batch(self):
        """
        Process the queue of Medium and Low impact scores that were held back from immediate publishing.
        """
        if not self.job_queue:
            logger.info("Nightly batch: No pending impact scores to publish.")
            return

        logger.info(f"Nightly batch: Publishing {len(self.job_queue)} Medium/Low impact scores to Redpanda...")
        
        while self.job_queue:
            score_data = self.job_queue.pop(0)
            cve_id = score_data.get("cve_id")
            
            self.producer.produce("impact.scored", key=cve_id, value=score_data)
            
        logger.info("Nightly batch processing complete.")

    def stop(self):
        self.scheduler.shutdown()
