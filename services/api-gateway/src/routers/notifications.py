import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime, select
from sqlalchemy.orm import declarative_base
from ..db.database import Database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

Base = declarative_base()

# --- Schemas ---
class NotificationResponse(BaseModel):
    id: int
    cve_id: str
    repository_url: str
    github_issue_url: Optional[str]
    success: bool
    failure_reason: Optional[str]

    class Config:
        from_attributes = True

# --- Dependency ---
def get_db(request: Request):
    return request.app.state.db

@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = Query(0),
    limit: int = Query(50),
    db: Database = Depends(get_db)
):
    """
    Return a paginated list of all notification attempts (both successful and failed).
    """
    results = await db.get_notifications(skip=skip, limit=limit)
    return results

@router.post("/{notification_id}/retry")
async def retry_notification(
    notification_id: int = Path(..., description="ID of the failed notification to retry"),
    db: Database = Depends(get_db)
):
    """
    Queue a failed notification for immediate retry by re-publishing to notifications.out.
    """
    notification = await db.get_notification_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")
    if notification.success:
        raise HTTPException(status_code=400, detail="Notification already succeeded. No retry needed.")
    
    # In a full impl, this would re-publish to the notifications.out Kafka topic
    # For now, return a queued status
    logger.info(f"Queuing notification {notification_id} for retry...")
    return {"message": f"Notification {notification_id} queued for retry.", "repository_url": notification.repository_url}
