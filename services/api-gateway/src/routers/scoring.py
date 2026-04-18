import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from ..db.database import Database
from ..models.schemas import AffectedRepositoryResponse, MaintainerStatusUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["scoring"])

# Dependency to get DB instance (would be injected via app state in main.py)
def get_db():
    from ..main import db
    return db

@router.get("/cves/{cve_id}/affected-repos", response_model=List[AffectedRepositoryResponse])
async def get_affected_repos(
    cve_id: str = Path(..., description="The ID of the CVE"),
    skip: int = Query(0, description="Pagination offset"),
    limit: int = Query(50, description="Pagination limit"),
    db: Database = Depends(get_db)
):
    """
    Get a paginated list of repositories affected by a specific CVE, sorted by highest Propex score.
    """
    repos = await db.get_affected_repos(cve_id, skip, limit)
    return repos

@router.get("/repos/{owner}/{name}/vulnerabilities", response_model=List[AffectedRepositoryResponse])
async def get_repo_vulnerabilities(
    owner: str = Path(..., description="Repository owner (e.g., org name)"),
    name: str = Path(..., description="Repository name"),
    db: Database = Depends(get_db)
):
    """
    Get all vulnerabilities affecting a specific repository, sorted by highest Propex score.
    """
    # Assuming repository_url is stored as "https://github.com/owner/name"
    repo_url = f"https://github.com/{owner}/{name}"
    vulns = await db.get_repo_vulnerabilities(repo_url)
    return vulns

@router.patch("/repos/{owner}/{name}/vulnerabilities/{cve_id}", response_model=dict)
async def update_maintainer_status(
    status_update: MaintainerStatusUpdate,
    owner: str = Path(...),
    name: str = Path(...),
    cve_id: str = Path(...),
    db: Database = Depends(get_db)
):
    """
    Update the maintainer status (e.g., 'patched', 'investigating', 'false_positive') for a specific vulnerability in a repo.
    """
    repo_url = f"https://github.com/{owner}/{name}"
    success = await db.update_maintainer_status(repo_url, cve_id, status_update.status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Vulnerability mapping not found for this repository")
        
    return {"message": f"Status updated to '{status_update.status}' successfully"}
