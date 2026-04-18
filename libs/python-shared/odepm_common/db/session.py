import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://propex:propex_password@localhost:5432/propex_db",
)

Base = declarative_base()


def get_async_engine():
    return create_async_engine(DATABASE_URL, echo=True)


def get_async_sessionmaker(engine=None):
    if engine is None:
        engine = get_async_engine()
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

def get_db_session_factory(db_url: str = None):
    """Alias for get_async_sessionmaker that accepts a custom DB URL"""
    engine = create_async_engine(db_url or DATABASE_URL, echo=True)
    return get_async_sessionmaker(engine)



# For backward compatibility if needed, but better to use the functions
# AsyncSessionLocal = get_async_sessionmaker()


async def get_db():
    session_maker = get_async_sessionmaker()
    async with session_maker() as session:
        yield session
