import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from database import check_database, configure_engine, initialize_database
from routers.analysis import router as analysis_router
from routers.projects import router as projects_router

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_engine()
    initialize_database()
    logger.info("Database initialized successfully")
    yield


app = FastAPI(
    title="Failure Prediction AI",
    description="Milestone 1 — Data Collection and Market Intelligence",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {"message": "Failure Prediction AI Backend Running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    if not check_database():
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if not check_database():
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ready"}


app.include_router(projects_router)
app.include_router(analysis_router)
