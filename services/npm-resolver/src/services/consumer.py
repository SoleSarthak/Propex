import logging
import os
import json
import asyncio
from typing import Dict, Any
from odepm_common.kafka.consumer import KafkaConsumerBase
from .resolver import NpmResolver

logger = logging.getLogger(__name__)

class CveConsumer(KafkaConsumerBase):
    def __init__(self, bootstrap_servers: str, group_id: str, resolver: NpmResolver):
        super().__init__(bootstrap_servers, group_id, topics=["cve.raw"])
        self.resolver = resolver

    async def process_message(self, message_data: Dict[str, Any]):
        """
        Process a message from the cve.raw topic.
        """
        cve_id = message_data.get("cve_id")
        source = message_data.get("source")
        
        # We only care about npm related CVEs or all CVEs if we want to cross-check
        # For now, let's look for affected packages in the record
        affected_packages = message_data.get("affected_packages", [])
        
        # If the record doesn't have affected packages (NVD often doesn't specify ecosystem clearly)
        # we might need a separate service to classify them. 
        # For this MVP, we'll look for any packages tagged as 'npm'.
        
        for pkg in affected_packages:
            if pkg.get("ecosystem") == "npm":
                package_name = pkg.get("name")
                vulnerable_ranges = pkg.get("versions_affected", [])
                
                await self.resolver.resolve_propagation(
                    cve_id=cve_id,
                    package_name=package_name,
                    vulnerable_ranges=vulnerable_ranges
                )
