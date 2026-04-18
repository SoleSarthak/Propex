import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, String, Float, Integer, DateTime, select, update
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()

class AffectedRepository(Base):
    __tablename__ = "affected_repositories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cve_id = Column(String, index=True, nullable=False)
    repository_url = Column(String, index=True, nullable=False)
    target_package = Column(String, nullable=False)
    
    dependency_depth = Column(Integer, nullable=False)
    context_type = Column(String, nullable=False)
    popularity_stars = Column(Integer, nullable=False)
    download_count = Column(Integer, nullable=False)
    propex_score = Column(Float, nullable=False)
    
    # New field for API Gateway PATCH
    maintainer_status = Column(String, default="unacknowledged")

class IssuedNotification(Base):
    """Mirror of the issued_notifications table managed by the Issue Creator service."""
    __tablename__ = "issued_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cve_id = Column(String, nullable=False, index=True)
    repository_url = Column(String, nullable=False, index=True)
    github_issue_url = Column(String, nullable=True)
    success = Column(String, default="false")
    failure_reason = Column(String, nullable=True)

class Database:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def get_affected_repos(self, cve_id: str, skip: int = 0, limit: int = 50) -> List[AffectedRepository]:
        async with self.SessionLocal() as session:
            stmt = select(AffectedRepository).where(AffectedRepository.cve_id == cve_id).order_by(AffectedRepository.propex_score.desc()).offset(skip).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_repo_vulnerabilities(self, repo_url: str) -> List[AffectedRepository]:
        async with self.SessionLocal() as session:
            stmt = select(AffectedRepository).where(AffectedRepository.repository_url == repo_url).order_by(AffectedRepository.propex_score.desc())
            result = await session.execute(stmt)
            return result.scalars().all()

    async def update_maintainer_status(self, repo_url: str, cve_id: str, new_status: str) -> bool:
        async with self.SessionLocal() as session:
            stmt = update(AffectedRepository).where(
                AffectedRepository.repository_url == repo_url,
                AffectedRepository.cve_id == cve_id
            ).values(maintainer_status=new_status)
            
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def get_notifications(self, skip: int = 0, limit: int = 50):
        """Fetch paginated notification history from issued_notifications table."""
        async with self.SessionLocal() as session:
            try:
                stmt = select(IssuedNotification).order_by(IssuedNotification.id.desc()).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
            except Exception:
                return []

    async def get_notification_by_id(self, notification_id: int):
        """Fetch a specific notification by ID."""
        async with self.SessionLocal() as session:
            try:
                stmt = select(IssuedNotification).where(IssuedNotification.id == notification_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception:
                return None

    async def close(self):
        await self.engine.dispose()
