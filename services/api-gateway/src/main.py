import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
from .db.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Propex API Gateway")

# Allow Web Dashboard to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://propex:propex_password@postgres:5432/propex_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
db = Database(DATABASE_URL)

# Need to import router after db is defined to avoid circular dependency
from .routers.scoring import router as scoring_router
from .routers.opt_out import router as opt_out_router
from .routers.notifications import router as notifications_router
app.include_router(scoring_router)
app.include_router(opt_out_router)
app.include_router(notifications_router)

@app.on_event("startup")
async def startup_event():
    app.state.db = db
    app.state.redis = redis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    await db.close()
    await app.state.redis.aclose()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
