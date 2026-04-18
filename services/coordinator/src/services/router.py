import json
import logging
from typing import List, Dict, Any
from odepm_common.kafka.producer import KafkaProducerBase
from odepm_common.models.cve import CveRecord

logger = logging.getLogger(__name__)

class CoordinatorRouter(KafkaProducerBase):
    def __init__(self, bootstrap_servers: str):
        super().__init__(bootstrap_servers)
        self.topic_map = {
            "npm": "resolver.npm",
            "pypi": "resolver.pypi",
            "maven": "resolver.maven"
        }

    async def route_cve(self, record: CveRecord):
        """
        Route a CVE to appropriate ecosystem-specific resolver topics.
        """
        affected_packages = record.affected_packages
        
        if not affected_packages:
            logger.info(f"No affected packages listed for {record.cve_id}, skipping routing.")
            return

        for pkg in affected_packages:
            ecosystem = pkg.ecosystem.lower()
            topic = self.topic_map.get(ecosystem)
            
            if topic:
                logger.info(f"Routing {record.cve_id} to {topic} for package {pkg.name}")
                message = record.model_dump()
                message["target_package"] = pkg.name
                
                # Convert datetime objects to string for JSON serialization
                self.produce(topic, key=record.cve_id, value=json.dumps(message, default=str))
            else:
                logger.warning(f"Unsupported ecosystem '{ecosystem}' for CVE {record.cve_id}")
