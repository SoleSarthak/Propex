import logging
import json
from typing import Dict, Any
from odepm_common.kafka.producer import KafkaConsumerBase, KafkaProducerBase

logger = logging.getLogger(__name__)

class ImpactAnalyzerConsumer(KafkaConsumerBase):
    def __init__(self, bootstrap_servers: str, group_id: str, analyzer_service, db, producer: KafkaProducerBase, job_queue):
        super().__init__(bootstrap_servers, group_id, topics=["dependency.resolved"])
        self.analyzer_service = analyzer_service
        self.db = db
        self.producer = producer
        self.job_queue = job_queue

    async def process_message(self, message_data: Dict[str, Any]):
        """
        Listens to the 'dependency.resolved' topic. 
        When a resolver finishes mapping a blast radius, this kicks off the scoring.
        """
        try:
            cve_id = message_data.get("cve_id")
            root_package = message_data.get("root_package")
            ecosystem = message_data.get("ecosystem")
            
            # In a full flow, we'd iterate over all repos found by the manifest detector.
            # For this MVP step, we will score the root package impact on a generic "test-repo".
            logger.info(f"Received resolved dependency tree for {cve_id} on {root_package}. Starting ML Impact Analysis...")
            
            # Simulate fetching repo data (this would be queried from DB)
            repo_url = f"https://github.com/example/{root_package}-dependent"
            
            # Extract CVSS score (usually passed in message or fetched from DB)
            cvss_score = float(message_data.get("cvss_score", 7.5))
            
            # 1. Compute Score
            score_data = await self.analyzer_service.analyze_and_score(
                cve_id=cve_id,
                package_name=root_package,
                cvss_score=cvss_score,
                repo_stars=150, # Stubbed GitHub enricher data
                manifest_type="package.json",
                scope="runtime"
            )
            score_data["repository_url"] = repo_url
            
            # 2. Persist to DB
            await self.db.persist_score(score_data)
            
            # 3. Routing based on severity
            propex_score = score_data["propex_score"]
            if propex_score >= 7.0:
                logger.warning(f"CRITICAL/HIGH impact detected ({propex_score}). Immediate publish to impact.scored.")
                self.producer.produce("impact.scored", key=cve_id, value=score_data)
            else:
                logger.info(f"MEDIUM/LOW impact detected ({propex_score}). Queuing for nightly batch.")
                # We would normally schedule this with APScheduler
                self.job_queue.append(score_data)
                
        except Exception as e:
            logger.error(f"Failed to process dependency.resolved message: {e}")
