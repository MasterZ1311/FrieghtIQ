from app.routers.forecast import router as forecast_router
from app.routers.vessels import router as vessels_router
from app.routers.ports import router as ports_router
from app.routers.economics import router as economics_router
from app.routers.market_entry import router as market_entry_router
from app.routers.risk import router as risk_router
from app.routers.contracts import router as contracts_router
from app.routers.scenarios import router as scenarios_router
from app.routers.dashboard import router as dashboard_router
from app.routers.workflow import router as workflow_router
from app.routers.regime import router as regime_router
from app.routers.options import router as options_router
from app.routers.copilot import router as copilot_router

__all__ = [
    "forecast_router",
    "vessels_router",
    "ports_router",
    "economics_router",
    "market_entry_router",
    "risk_router",
    "contracts_router",
    "scenarios_router",
    "dashboard_router",
    "workflow_router",
    "regime_router",
    "options_router",
    "copilot_router",
]


