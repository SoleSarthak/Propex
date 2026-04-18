import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, String, Float, Integer, DateTime, select
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

Base = declarative_base()

class AffectedRepository(Base):
    __tablename__ = "affected_repositories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cve_id = Column(String, index=True, nullable=False)
    repository_url = Column(String, index=True, nullable=False)
    target_package = Column(String, nullable=False)
    
    # 4 Factors
    dependency_depth = Column(Integer, nullable=False)
    context_type = Column(String, nullable=False)
    popularity_stars = Column(Integer, nullable=False)
    download_count = Column(Integer, nullable=False)
    
    # Final ML Score
    propex_score = Column(Float, nullable=False)
    
    # Audit
    scored_at = Column(DateTime(timezone=True), server_default=func.now())

class Database:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def persist_score(self, data: dict):
        """
        Save the calculated score and its factors to the PostgreSQL database.
        """
        async with self.SessionLocal() as session:
            try:
                record = AffectedRepository(
                    cve_id=data["cve_id"],
                    repository_url=data.get("repository_url", "unknown"),
                    target_package=data["target"],
                    dependency_depth=data["depth"],
                    context_type=data["context"],
                    popularity_stars=data["popularity"],
                    download_count=data["downloads"],
                    propex_score=data["propex_score"]
                )
                session.add(record)
                await session.commit()
                logger.info(f"Persisted score {data['propex_score']} for {data['cve_id']} to DB.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to persist score to DB: {e}")

    async def close(self):
        await self.engine.dispose()
