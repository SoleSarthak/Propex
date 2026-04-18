import logging
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
import redis.asyncio as redis
import google.generativeai as genai
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, text
from sqlalchemy.orm import declarative_base
from ..prompts.templates import SYSTEM_PROMPT, get_user_prompt, get_fallback_patch
from .validator import validate_patch_output

logger = logging.getLogger(__name__)

Base = declarative_base()

class GeminiUsageLog(Base):
    __tablename__ = "gemini_usage_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cve_id = Column(String, nullable=False)
    package_name = Column(String, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    called_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

DAILY_REQUEST_LIMIT = 1500  # Gemini free tier

class PatchDrafterService:
    def __init__(self, gemini_api_key: str, redis_url: str, database_url: str):
        # Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        # Redis
        self.redis = redis.from_url(redis_url, decode_responses=True)
        
        # DB for usage logging
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _make_cache_key(self, cve_id: str, package_name: str, repo_url: str) -> str:
        raw = f"{cve_id}:{package_name}:{repo_url}"
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"patch:{digest}"

    async def _get_daily_count(self) -> int:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        count = await self.redis.get(f"gemini:daily:{today}")
        return int(count) if count else 0

    async def _increment_daily_count(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"gemini:daily:{today}"
        await self.redis.incr(key)
        await self.redis.expire(key, 86400)  # 24h TTL

    async def _log_usage(self, cve_id: str, package_name: str, prompt_tokens: int = 0, output_tokens: int = 0):
        async with self.SessionLocal() as session:
            try:
                log = GeminiUsageLog(
                    cve_id=cve_id,
                    package_name=package_name,
                    prompt_tokens=prompt_tokens,
                    output_tokens=output_tokens
                )
                session.add(log)
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to log Gemini usage: {e}")

    async def draft_patch(
        self,
        cve_id: str,
        package_name: str,
        ecosystem: str,
        repo_url: str,
        propex_score: float,
        depth: int,
        version_range: str = "unknown",
        fix_version: str = "latest"
    ) -> str:
        """
        Core pipeline:
        1. Check Redis cache (7-day TTL)
        2. Check daily rate limit
        3. Call Gemini API
        4. Validate output
        5. Cache + return
        """
        cache_key = self._make_cache_key(cve_id, package_name, repo_url)
        
        # 1. Check Redis cache
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info(f"Cache HIT for {cache_key}. Returning cached patch.")
            return cached
        
        # 2. Check daily rate limit
        daily_count = await self._get_daily_count()
        if daily_count >= DAILY_REQUEST_LIMIT:
            logger.warning(f"Gemini daily rate limit reached ({daily_count}/{DAILY_REQUEST_LIMIT}). Using fallback template.")
            return get_fallback_patch(
                ecosystem=ecosystem,
                cve_id=cve_id,
                package_name=package_name,
                repo_url=repo_url,
                version_range=version_range,
                fix_version=fix_version
            )
        
        # 3. Call Gemini API
        try:
            user_prompt = get_user_prompt(
                ecosystem=ecosystem,
                cve_id=cve_id,
                package_name=package_name,
                repo_url=repo_url,
                propex_score=propex_score,
                depth=depth,
                version_range=version_range,
                fix_version=fix_version
            )
            
            logger.info(f"Calling Gemini gemini-2.0-flash for CVE {cve_id} on {package_name}...")
            response = self.model.generate_content(user_prompt)
            patch_text = response.text
            
            # 4. Validate output
            is_valid, missing = validate_patch_output(patch_text)
            if not is_valid:
                logger.warning(f"Gemini output invalid (missing: {missing}). Using fallback.")
                patch_text = get_fallback_patch(
                    ecosystem=ecosystem,
                    cve_id=cve_id,
                    package_name=package_name,
                    repo_url=repo_url,
                    version_range=version_range,
                    fix_version=fix_version
                )
            
            # 5. Track usage and increment counter
            await self._increment_daily_count()
            usage = response.usage_metadata
            await self._log_usage(
                cve_id=cve_id,
                package_name=package_name,
                prompt_tokens=getattr(usage, 'prompt_token_count', 0),
                output_tokens=getattr(usage, 'candidates_token_count', 0)
            )
            
            # 6. Cache the result for 7 days
            await self.redis.set(cache_key, patch_text, ex=604800)
            logger.info(f"Patch drafted and cached for {cve_id}/{package_name}.")
            return patch_text
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}. Using fallback template.")
            return get_fallback_patch(
                ecosystem=ecosystem,
                cve_id=cve_id,
                package_name=package_name,
                repo_url=repo_url,
                version_range=version_range,
                fix_version=fix_version
            )

    async def close(self):
        await self.redis.aclose()
        await self.engine.dispose()
