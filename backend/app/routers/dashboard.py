"""Dashboard summary router — aggregates key metrics for the executive dashboard."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.forecast_service import forecast, get_history

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

DEFAULT_ROUTES = [
    {"origin": "Australia", "destination": "Paradip", "vessel_class": "Panamax", "commodity": "Coal"},
    {"origin": "Indonesia", "destination": "Visakhapatnam", "vessel_class": "Supramax", "commodity": "Coal"},
    {"origin": "Mozambique", "destination": "Gangavaram", "vessel_class": "Capesize", "commodity": "Coal"},
    {"origin": "United States", "destination": "Haldia", "vessel_class": "Panamax", "commodity": "Coal"},
]


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    """Returns key rate snapshots and trend summaries for the dashboard."""
    snapshots = []
    for route in DEFAULT_ROUTES:
        try:
            fc = forecast(db, **route, horizon_days=30)
            snapshots.append({
                "route": f"{route['origin']} → {route['destination']}",
                "vessel_class": route["vessel_class"],
                "current_rate": fc["current_rate_usd_per_mt"],
                "predicted_rate": fc["predicted_rate_usd_per_mt"],
                "trend": fc["trend"],
                "confidence_pct": fc["confidence_pct"],
                "tce": fc["tce_estimate_usd_per_day"],
            })
        except Exception as e:
            snapshots.append({"route": f"{route['origin']} → {route['destination']}", "error": str(e)})

    return {
        "rate_snapshots": snapshots,
        "disclaimer": "[DEMO] All rates are synthetic demo data.",
    }


@router.get("/chart-data")
def chart_data(
    origin: str = Query(default="Australia"),
    destination: str = Query(default="Paradip"),
    vessel_class: str = Query(default="Panamax"),
    db: Session = Depends(get_db),
):
    history = get_history(db, origin, destination, vessel_class)
    return {"data": history, "disclaimer": "[DEMO] Synthetic historical data."}
