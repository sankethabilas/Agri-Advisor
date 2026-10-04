"""FastAPI microservice and scheduler for Outbreak Sentinel Agent.

Endpoints:
  - POST /api/sentinel/scan
  - GET  /api/sentinel/decisions
  - POST /api/sentinel/evaluate
  - POST /api/sentinel/seed-demo
  - GET  /api/sentinel/health
"""

from contextlib import asynccontextmanager
import logging
from typing import Any, Dict, List, Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:
    # Graceful fallback dummy scheduler if apscheduler is not yet installed in environment
    class BackgroundScheduler:
        def __init__(self):
            self.running = False
        def add_job(self, *args, **kwargs):
            pass
        def start(self):
            self.running = True
        def shutdown(self, wait=False):
            self.running = False

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from sentinel_agent.agent import sentinel_agent
from sentinel_agent.config import settings
from sentinel_agent.db import get_connection, init_db
from sentinel_agent.seed import seed_demo_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel_agent.main")

# Setup APScheduler
scheduler = BackgroundScheduler()


def run_scheduled_scan() -> None:
    logger.info("Executing scheduled Outbreak Sentinel scan...")
    try:
        sentinel_agent.scan()
    except Exception as err:
        logger.error("Scheduled scan failed: %s", err)


def run_scheduled_eval() -> None:
    logger.info("Executing scheduled Sentinel past-alerts evaluation...")
    try:
        sentinel_agent.evaluate_past_alerts()
    except Exception as err:
        logger.error("Scheduled evaluation failed: %s", err)


def start_scheduler() -> None:
    """Starts the background scheduler if not already running."""
    if not scheduler.running:
        scheduler.add_job(
            run_scheduled_scan,
            "interval",
            hours=settings.scan_interval_hours,
            id="sentinel_scan_job",
            replace_existing=True,
        )
        scheduler.add_job(
            run_scheduled_eval,
            "interval",
            hours=settings.eval_interval_hours,
            id="sentinel_eval_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            "Sentinel Scheduler started: scan every %dh, eval every %dh",
            settings.scan_interval_hours,
            settings.eval_interval_hours,
        )


def stop_scheduler() -> None:
    """Shuts down the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Sentinel Scheduler shut down.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and start background scheduler
    init_db()
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


# Auto-initialize DB and scheduler on import
try:
    init_db()
    start_scheduler()
except Exception as _err:
    logger.warning("Could not auto-start scheduler on load: %s", _err)


app = FastAPI(
    title="Agri-Advisor Outbreak Sentinel Agent",
    description="Autonomous Agricultural Disease Cluster Surveillance Service",
    version="1.0.0",
    lifespan=lifespan,
)


class SeedDemoRequest(BaseModel):
    district: str = Field(default="Anuradhapura")
    crop: str = Field(default="Rice")
    disease: str = Field(default="Bacterial Leaf Blight")


class DecisionFilter(BaseModel):
    district: Optional[str] = None
    level: Optional[str] = None
    limit: int = 50


@app.get("/api/sentinel/health", tags=["System"])
def get_health() -> Dict[str, Any]:
    """Health check endpoint for Outbreak Sentinel."""
    return {
        "status": "healthy",
        "service": "outbreak_sentinel_agent",
        "scheduler_running": scheduler.running,
        "database": settings.db_path,
    }


@app.post("/api/sentinel/scan", tags=["Sentinel Core"])
def trigger_scan() -> Dict[str, Any]:
    """Manually triggers one complete Sense -> Reason -> Decide -> Act scan cycle."""
    decisions = sentinel_agent.scan()
    return {
        "status": "completed",
        "count": len(decisions),
        "decisions": decisions,
    }


@app.get("/api/sentinel/decisions", tags=["Sentinel Core"])
def list_decisions(
    district: Optional[str] = Query(None, description="Filter by district"),
    level: Optional[str] = Query(None, description="Filter by decision level ('none', 'watch', 'outbreak')"),
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    """Retrieves past sentinel decisions with optional filters."""
    query = "SELECT * FROM sentinel_decisions WHERE 1=1"
    params: List[Any] = []

    if district:
        query += " AND district = ?"
        params.append(district)
    if level:
        query += " AND level = ?"
        params.append(level.lower())

    query += " ORDER BY created_at DESC LIMIT ?;"
    params.append(limit)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        decisions = [dict(row) for row in rows]

    return {
        "total": len(decisions),
        "decisions": decisions,
    }


@app.post("/api/sentinel/evaluate", tags=["Sentinel Core"])
def trigger_evaluation() -> Dict[str, Any]:
    """Manually triggers evaluation of 5-day-old outbreak alerts."""
    evaluations = sentinel_agent.evaluate_past_alerts()
    return {
        "status": "completed",
        "count": len(evaluations),
        "evaluations": evaluations,
    }


@app.post("/api/sentinel/seed-demo", tags=["Demo"])
def seed_demo(payload: Optional[SeedDemoRequest] = None) -> Dict[str, Any]:
    """Seeds simulated diagnosis logs to test outbreak and watch scenarios."""
    req = payload or SeedDemoRequest()
    result = seed_demo_data(
        district=req.district,
        crop=req.crop,
        disease=req.disease,
    )
    return {
        "status": "seeded",
        "details": result,
    }
