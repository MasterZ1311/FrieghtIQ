"""
FreightIQ — FastAPI Backend Entry Point
=======================================
Intelligent freight forecasting and vessel chartering decision-support platform.

⚠ DEMO MODE: All predictions and data are synthetic. Not real market data.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, SessionLocal
from app.seed.seeder import seed_database
from app.ml.model import get_model
from app.routers import (
    forecast_router,
    vessels_router,
    ports_router,
    economics_router,
    market_entry_router,
    risk_router,
    contracts_router,
    scenarios_router,
    dashboard_router,
    workflow_router,
    regime_router,
    options_router,
    copilot_router,
)



logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, "INFO"))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, seed demo data, warm up ML model."""
    logger.info("FreightIQ starting up...")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

    # Seed demo data
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    # Warm up ML model (trains if not already trained)
    from app.services.forecast_service import ensure_model_trained
    db = SessionLocal()
    try:
        ensure_model_trained(db)
    except Exception as e:
        logger.warning(f"ML warm-up failed (non-critical): {e}")
    finally:
        db.close()

    logger.info("FreightIQ ready.")
    yield
    logger.info("FreightIQ shutting down.")


app = FastAPI(
    title="FreightIQ API",
    description=(
        "Intelligent freight forecasting and vessel chartering decision-support platform. "
        "⚠ All data is SYNTHETIC / DEMO — not real market data."
    ),
    version="1.0.0-hackathon",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],  # permissive for hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(dashboard_router)
app.include_router(forecast_router)
app.include_router(vessels_router)
app.include_router(ports_router)
app.include_router(economics_router)
app.include_router(market_entry_router)
app.include_router(risk_router)
app.include_router(contracts_router)
app.include_router(scenarios_router)
app.include_router(workflow_router)
app.include_router(regime_router)
app.include_router(options_router)
app.include_router(copilot_router)




@app.get("/", tags=["Health"])
def root():
    return {
        "service": "FreightIQ API",
        "version": "1.0.0-hackathon",
        "status": "operational",
        "disclaimer": "[DEMO] All predictions and data are synthetic. Not real market data.",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "service": "FreightIQ API",
        "version": "1.0.0",
        "disclaimer": "[DEMO] All predictions and data are synthetic. Not real market data.",
    }

