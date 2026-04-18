import logging
import json
from typing import Dict, Any, Optional
import redis.asyncio as redis
from odepm_scoring.engine import ScoringEngine
from .neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

class ImpactAnalyzerService:
    def __init__(self, neo4j_client: Neo4jClient, redis_url: str):
        self.neo4j_client = neo4j_client
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def get_download_count(self, package_name: str) -> int:
        """
        Fetch download count from Redis.
        If missing, defaults to 0 for the MVP.
        """
        try:
            count = await self.redis.get(f"downloads:{package_name}")
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Failed to fetch download count for {package_name}: {e}")
            return 0

    def extract_context_type(self, manifest_type: str, scope: str = None) -> str:
        """
        Determine if the dependency is runtime or development based on the manifest and scope.
        """
        # Default to runtime unless explicitly dev
        if scope in ["test", "dev", "provided"]:
            return "dev"
        
        # In a real scenario, this would parse the actual package.json or pom.xml structure
        # to see if it's under devDependencies or dependencies.
        return "runtime"

    async def analyze_and_score(self, cve_id: str, package_name: str, cvss_score: float, repo_stars: int = 10, manifest_type: str = "package.json", scope: str = None) -> Dict[str, Any]:
        """
        Core pipeline to gather the 4 scoring factors and compute the final Propex Score.
        """
        # 1. Dependency Depth
        depth = await self.neo4j_client.get_dependency_depth(cve_id, package_name)
        if depth == -1:
            depth = 1 # Default fallback
            
        # 2. Context Type (Runtime vs Dev)
        context = self.extract_context_type(manifest_type, scope)
        
        # 3. Popularity (from GitHub stars, passed in, or fetched if repo)
        # Assuming repo_stars represents the popularity factor for the affected repository
        
        # 4. Usage/Downloads
        downloads = await self.get_download_count(package_name)

        # 5. Compute Final Score using the internal ML/Scoring engine library
        final_score = ScoringEngine.compute_score(
            cvss_base=cvss_score,
            depth=depth,
            context=context,
            popularity=repo_stars,
            downloads=downloads
        )
        
        result = {
            "cve_id": cve_id,
            "target": package_name,
            "depth": depth,
            "context": context,
            "popularity": repo_stars,
            "downloads": downloads,
            "propex_score": final_score
        }
        
        # Cache score for 1 hour
        cache_key = f"score:{cve_id}:{package_name}"
        await self.redis.set(cache_key, json.dumps(result), ex=3600)
        logger.info(f"Computed Propex Score {final_score} for {package_name} against {cve_id}")
        
        return result

    async def close(self):
        await self.redis.close()
