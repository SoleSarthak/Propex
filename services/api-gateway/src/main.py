import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
db = Database(DATABASE_URL)

# Need to import router after db is defined to avoid circular dependency
from .routers.scoring import router as scoring_router
app.include_router(scoring_router)

@app.on_event("shutdown")
async def shutdown_event():
    await db.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
