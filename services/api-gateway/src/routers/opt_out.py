import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import redis.asyncio as redis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/opt-out", tags=["opt-out"])

OPT_OUT_PREFIX = "optout:"

# --- Schemas ---
class OptOutRequest(BaseModel):
    repository_url: str
    reason: Optional[str] = None

# --- Dependency ---
def get_redis(request: Request):
    return request.app.state.redis

@router.post("", status_code=201)
async def register_opt_out(body: OptOutRequest, r: redis.Redis = Depends(get_redis)):
    """
    Register a repository opt-out. Requires GitHub OAuth (stubbed here).
    The repo will not receive any Propex issue notifications.
    """
    key = f"{OPT_OUT_PREFIX}{body.repository_url}"
    await r.set(key, "1")
    logger.info(f"Opt-out registered: {body.repository_url}")
    return {"message": f"Repository '{body.repository_url}' has been opted out successfully."}

@router.delete("")
async def reverse_opt_out(repository_url: str, r: redis.Redis = Depends(get_redis)):
    """Remove a repository from the opt-out registry."""
    key = f"{OPT_OUT_PREFIX}{repository_url}"
    deleted = await r.delete(key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Repository was not in the opt-out registry.")
    logger.info(f"Opt-out removed: {repository_url}")
    return {"message": f"Repository '{repository_url}' opt-out has been reversed."}

@router.get("")
async def list_opt_outs(r: redis.Redis = Depends(get_redis)):
    """List all repositories currently in the opt-out registry."""
    keys = await r.keys(f"{OPT_OUT_PREFIX}*")
    repos = [k.replace(OPT_OUT_PREFIX, "") for k in keys]
    return {"opted_out_repositories": repos, "count": len(repos)}
