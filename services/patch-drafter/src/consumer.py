import logging
import json
from typing import Dict, Any
from odepm_common.kafka.producer import KafkaConsumerBase, KafkaProducerBase
from .drafter import PatchDrafterService

logger = logging.getLogger(__name__)

class PatchDrafterConsumer(KafkaConsumerBase):
    def __init__(self, bootstrap_servers: str, group_id: str, drafter: PatchDrafterService, producer: KafkaProducerBase):
        super().__init__(bootstrap_servers, group_id, topics=["impact.scored"])
        self.drafter = drafter
        self.producer = producer

    async def process_message(self, message_data: Dict[str, Any]):
        """
        Listens to 'impact.scored' topic (Critical + High only, from the Impact Analyzer).
        Drafts a patch using Gemini and publishes the result to 'notifications.out'.
        """
        try:
            cve_id = message_data.get("cve_id")
            target_pkg = message_data.get("target")
            ecosystem = message_data.get("ecosystem", "npm")
            repo_url = message_data.get("repository_url", "unknown")
            propex_score = float(message_data.get("propex_score", 0.0))
            depth = int(message_data.get("depth", 1))
            
            logger.info(f"Drafting patch for CVE {cve_id} in {target_pkg} (score: {propex_score})...")
            
            patch_text = await self.drafter.draft_patch(
                cve_id=cve_id,
                package_name=target_pkg,
                ecosystem=ecosystem,
                repo_url=repo_url,
                propex_score=propex_score,
                depth=depth,
                version_range=message_data.get("version_range", "unknown"),
                fix_version=message_data.get("fix_version", "latest")
            )
            
            # Publish the drafted patch to the notifications topic for the Issue Creator
            notification_payload = {
                "cve_id": cve_id,
                "package_name": target_pkg,
                "ecosystem": ecosystem,
                "repository_url": repo_url,
                "propex_score": propex_score,
                "patch_draft": patch_text
            }
            
            self.producer.produce("notifications.out", key=cve_id, value=notification_payload)
            logger.info(f"Patch for {cve_id}/{target_pkg} published to 'notifications.out'.")
            
        except Exception as e:
            logger.error(f"Failed to process impact.scored message: {e}")
