import logging
import asyncio
from typing import Dict, Any
from odepm_common.kafka.producer import KafkaConsumerBase

logger = logging.getLogger(__name__)

class PyPiCveConsumer(KafkaConsumerBase):
    def __init__(self, bootstrap_servers: str, group_id: str, resolver_service):
        super().__init__(bootstrap_servers, group_id, topics=["resolver.pypi"])
        self.resolver_service = resolver_service

    async def process_message(self, message_data: Dict[str, Any]):
        """
        Process a message routed to the PyPI resolver.
        """
        try:
            cve_id = message_data.get("cve_id")
            target_package = message_data.get("target_package")
            
            logger.info(f"Received PyPI CVE for resolution: {cve_id} (Package: {target_package})")
            
            if cve_id and target_package:
                # Initiate the resolution process
                # This will involve Neo4j, PyPI Client, and Libraries.io Client
                await self.resolver_service.resolve(cve_id, target_package, message_data)
            else:
                logger.warning(f"Invalid message format: {message_data}")
                
        except Exception as e:
            logger.error(f"Failed to process PyPI coordination message: {e}")
