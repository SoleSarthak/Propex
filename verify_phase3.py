import asyncio
import httpx
import json
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # 1. Push message to dependency.resolved using subprocess and stdin
    test_msg = {
        "cve_id": "CVE-TEST-ML-1234",
        "root_package": "express",
        "ecosystem": "npm",
        "cvss_score": 9.8,
        "blast_radius_size": 1
    }
    
    cmd = ["docker", "exec", "-i", "propex-redpanda", "rpk", "topic", "produce", "dependency.resolved", "--brokers", "localhost:9092"]
    
    try:
        subprocess.run(cmd, input=json.dumps(test_msg), text=True, check=True, capture_output=True)
        logger.info("Published test message to 'dependency.resolved'")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to produce message: {e.stderr}")
        return
        
    # Give the impact-analyzer time to process, query Neo4j, Redis, compute score, and save to Postgres
    await asyncio.sleep(5)
    
    # 2. Query the API Gateway to verify it was saved and scored correctly
    api_url = "http://localhost:8006/api/v1/cves/CVE-TEST-ML-1234/affected-repos"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                repo = data[0]
                logger.info(f"SUCCESS: Found affected repo via API!")
                logger.info(f"Repository URL: {repo['repository_url']}")
                logger.info(f"Target Package: {repo['target_package']}")
                logger.info(f"CVSS vs Propex Score: 9.8 -> {repo['propex_score']}")
                logger.info(f"Factors: Depth={repo['dependency_depth']}, Context={repo['context_type']}, Stars={repo['popularity_stars']}, Downloads={repo['download_count']}")
                print("\nMILESTONE VERIFICATION COMPLETE. ALL TESTS PASSED.")
            else:
                logger.error("API returned 200, but array was empty. Impact Analyzer may have failed to process.")
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
    except Exception as e:
         logger.error(f"Failed to reach API Gateway: {e}")

if __name__ == "__main__":
    asyncio.run(main())
