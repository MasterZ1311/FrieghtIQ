from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.base import Base
from app.db.session import engine
from app.api.routes import (
    health,
    ports,
    vessels,
    cargo,
    matching,
    optimizer,
    forecasting,
    regime,
    wait_fix,
    contracts,
    idle,
    risk,
    economics,
    copilot,
    decision,
)

# Ensure database tables exist
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing FREIGHT IQ Intelligence Database Engine...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas verified.")
    yield
    logger.info("FREIGHT IQ Engine shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(ports.router, prefix=settings.API_V1_STR)
app.include_router(vessels.router, prefix=settings.API_V1_STR)
app.include_router(cargo.router, prefix=settings.API_V1_STR)
app.include_router(matching.router, prefix=settings.API_V1_STR)
app.include_router(optimizer.router, prefix=settings.API_V1_STR)
app.include_router(forecasting.router, prefix=settings.API_V1_STR)
app.include_router(regime.router, prefix=settings.API_V1_STR)
app.include_router(wait_fix.router, prefix=settings.API_V1_STR)
app.include_router(contracts.router, prefix=settings.API_V1_STR)
app.include_router(idle.router, prefix=settings.API_V1_STR)
app.include_router(risk.risk_router, prefix=settings.API_V1_STR)
app.include_router(risk.congestion_router, prefix=settings.API_V1_STR)
app.include_router(risk.weather_router, prefix=settings.API_V1_STR)
app.include_router(risk.tidal_router, prefix=settings.API_V1_STR)
app.include_router(economics.economics_router, prefix=settings.API_V1_STR)
app.include_router(economics.bunker_router, prefix=settings.API_V1_STR)
app.include_router(economics.speed_router, prefix=settings.API_V1_STR)
app.include_router(copilot.copilot_router, prefix=settings.API_V1_STR)
app.include_router(decision.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "engine": "FREIGHT IQ",
        "system": "Maritime Freight Decision Support & Chartering Intelligence",
        "client": "SAIL / Ministry of Steel (SIH26006)",
        "api_docs": "/docs",
        "health": "/health"
    }
