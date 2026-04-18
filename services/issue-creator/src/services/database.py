import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, Integer, String, Boolean, DateTime, select
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)
Base = declarative_base()

class IssuedNotification(Base):
    __tablename__ = "issued_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cve_id = Column(String, nullable=False, index=True)
    repository_url = Column(String, nullable=False, index=True)
    github_issue_url = Column(String, nullable=True)
    success = Column(Boolean, default=False)
    failure_reason = Column(String, nullable=True)
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "issue_creation_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cve_id = Column(String, nullable=False)
    repository_url = Column(String, nullable=False)
    action = Column(String, nullable=False)  # e.g. "CREATED", "SKIPPED_DUPLICATE", "FAILED"
    detail = Column(String, nullable=True)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Database:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def is_duplicate(self, cve_id: str, repo_url: str) -> bool:
        """Check the issued_notifications table for an existing successful notification."""
        async with self.SessionLocal() as session:
            stmt = select(IssuedNotification).where(
                IssuedNotification.cve_id == cve_id,
                IssuedNotification.repository_url == repo_url,
                IssuedNotification.success == True
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def record_notification(self, cve_id: str, repo_url: str, issue_url: Optional[str], success: bool, reason: str = None):
        async with self.SessionLocal() as session:
            record = IssuedNotification(
                cve_id=cve_id,
                repository_url=repo_url,
                github_issue_url=issue_url,
                success=success,
                failure_reason=reason
            )
            session.add(record)
            await session.commit()

    async def write_audit_log(self, cve_id: str, repo_url: str, action: str, detail: str = None):
        async with self.SessionLocal() as session:
            log = AuditLog(cve_id=cve_id, repository_url=repo_url, action=action, detail=detail)
            session.add(log)
            await session.commit()

    async def close(self):
        await self.engine.dispose()
