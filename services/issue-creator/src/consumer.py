import logging
import json
from typing import Dict, Any
import redis.asyncio as redis
from odepm_common.kafka.producer import KafkaConsumerBase, KafkaProducerBase
from .services.github_client import GitHubClient
from .services.database import Database

logger = logging.getLogger(__name__)

OPT_OUT_CACHE_PREFIX = "optout:"

class IssueCreatorConsumer(KafkaConsumerBase):
    def __init__(self, bootstrap_servers: str, group_id: str, github: GitHubClient, db: Database, producer: KafkaProducerBase, redis_url: str):
        super().__init__(bootstrap_servers, group_id, topics=["notifications.out"])
        self.github = github
        self.db = db
        self.producer = producer
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def _is_opted_out(self, repo_url: str) -> bool:
        """Check opt-out registry: Redis cache first, Postgres fallback."""
        cache_key = f"{OPT_OUT_CACHE_PREFIX}{repo_url}"
        cached = await self.redis.get(cache_key)
        if cached is not None:
            return cached == "1"
        # Fallback: in a full impl, query Postgres opt_out_registry table
        # For now, assume not opted out
        return False

    async def process_message(self, message_data: Dict[str, Any]):
        """
        Listens to 'notifications.out'. For each patch draft:
        1. Opt-out check
        2. Duplicate check (DB + GitHub search)
        3. Create GitHub issue
        4. Record in DB + audit log
        5. On failure: publish to DLQ
        """
        cve_id = message_data.get("cve_id")
        repo_url = message_data.get("repository_url", "")
        package_name = message_data.get("package_name")
        propex_score = message_data.get("propex_score", 0.0)
        patch_draft = message_data.get("patch_draft", "")

        logger.info(f"Processing notification: {cve_id} for {repo_url}")

        # Parse owner/repo from URL
        try:
            parts = repo_url.rstrip("/").split("/")
            owner, repo = parts[-2], parts[-1]
        except (IndexError, ValueError):
            logger.error(f"Cannot parse owner/repo from URL: {repo_url}")
            return

        # 1. Opt-out check
        if await self._is_opted_out(repo_url):
            logger.info(f"Repository {repo_url} has opted out. Skipping.")
            await self.db.write_audit_log(cve_id, repo_url, "SKIPPED_OPT_OUT")
            return

        # 2. Duplicate check — DB first
        if await self.db.is_duplicate(cve_id, repo_url):
            logger.info(f"Duplicate detected in DB for {cve_id}/{repo_url}. Skipping.")
            await self.db.write_audit_log(cve_id, repo_url, "SKIPPED_DUPLICATE_DB")
            return

        # 3. Duplicate check — GitHub search
        if await self.github.search_existing_issues(owner, repo, cve_id):
            logger.info(f"Duplicate issue found on GitHub for {cve_id}. Skipping.")
            await self.db.write_audit_log(cve_id, repo_url, "SKIPPED_DUPLICATE_GITHUB")
            await self.db.record_notification(cve_id, repo_url, None, success=False, reason="Duplicate found on GitHub")
            return

        # 4. Create GitHub issue
        title = f"[Security] {cve_id} — Vulnerability in `{package_name}` (Propex Score: {propex_score}/10)"
        issue_url = await self.github.create_issue(
            owner=owner,
            repo=repo,
            title=title,
            body=patch_draft,
            labels=["security", "vulnerability", "propex-alert"]
        )

        # 5. Record result
        if issue_url:
            await self.db.record_notification(cve_id, repo_url, issue_url, success=True)
            await self.db.write_audit_log(cve_id, repo_url, "CREATED", detail=issue_url)
            logger.info(f"Issue created successfully: {issue_url}")
        else:
            # Publish to DLQ for retry after 1 hour
            await self.db.record_notification(cve_id, repo_url, None, success=False, reason="All retries exhausted")
            await self.db.write_audit_log(cve_id, repo_url, "FAILED", detail="Max retries reached")
            self.producer.produce("notifications.dlq", key=cve_id, value=message_data)
            logger.error(f"Failed to create issue for {cve_id}/{repo_url}. Published to DLQ.")

    async def close(self):
        await self.redis.aclose()
