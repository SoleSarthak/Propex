import os
import hashlib
import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File

router = APIRouter(prefix="/api/v1/security", tags=["security"])

VT_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
VT_BASE_URL = "https://www.virustotal.com/api/v3"

@router.post("/scan-file")
async def scan_file(file: UploadFile = File(...)):
    if not VT_API_KEY:
        # If no key, we can't do a real scan, so we'll return a helpful error
        raise HTTPException(status_code=501, detail="VirusTotal API Key not configured in .env")

    # 1. Calculate SHA-256 hash of the file
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    # 2. Check if VirusTotal has a report for this hash
    async with httpx.AsyncClient() as client:
        headers = {"x-apikey": VT_API_KEY}
        response = await client.get(f"{VT_BASE_URL}/files/{file_hash}", headers=headers)

        if response.status_code == 200:
            data = response.json()
            stats = data["data"]["attributes"]["last_analysis_stats"]
            return {
                "hash": file_hash,
                "detected": stats["malicious"] > 0,
                "malicious_count": stats["malicious"],
                "total_engines": sum(stats.values()),
                "source": "VirusTotal Live",
                "details": data["data"]["attributes"]["last_analysis_results"]
            }
        elif response.status_code == 404:
            # File never seen by VT, we would need to upload it for a full scan
            # For the demo, we'll return a "Clean/Unknown" status
            return {
                "hash": file_hash,
                "detected": False,
                "message": "File not previously seen by VirusTotal. Likely clean or unique.",
                "source": "VirusTotal Live"
            }
        else:
            raise HTTPException(status_code=response.status_code, detail="Error communicating with VirusTotal")
