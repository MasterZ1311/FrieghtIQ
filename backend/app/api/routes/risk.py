from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.db.session import get_db
from app.repositories.risk_repo import RiskRepository
from app.repositories.port_repo import PortRepository
from app.repositories.vessel_repo import VesselRepository
from app.repositories.cargo_repo import CargoRepository
from app.models.risk import RiskEvent, PortCongestion, WeatherObservation, TidalWindow
from app.models.enums import (
    RiskType,
    RiskSeverity,
    RiskStatus,
    DataStatusType,
    TidalWindowStatus,
    CongestionIndicator,
)
from app.schemas.risk import (
    RiskEventSchema,
    RiskEventCreate,
    UnifiedRiskSummaryResponse,
    PortRiskEvaluationResponse,
    VoyageRiskEvaluationRequest,
    VoyageRiskEvaluationResponse,
    WeatherObservationSchema,
    WeatherEvaluationResponse,
    TidalWindowSchema,
    TidalEvaluationRequest,
    TidalEvaluationResponse,
    PortCongestionSchema,
    CongestionEvaluationResponse,
)
from app.services.risk import (
    WeatherRiskService,
    TidalGateScheduler,
    CongestionRiskService,
    RiskEngine,
    RiskAggregationService,
)

# ----------------------------------------------------
# Routers
# ----------------------------------------------------
risk_router = APIRouter(prefix="/risk", tags=["Operational Risk Intelligence"])
congestion_router = APIRouter(prefix="/congestion", tags=["Port Congestion Intelligence"])
weather_router = APIRouter(prefix="/weather", tags=["Weather Risk Intelligence"])
tidal_router = APIRouter(prefix="/tidal", tags=["Tidal Gate Scheduler"])


# ====================================================
# UNIFIED RISK CENTER ENDPOINTS
# ====================================================

@risk_router.get("", response_model=UnifiedRiskSummaryResponse)
def get_risk_summary(db: Session = Depends(get_db)):
    """
    Returns aggregated risk center telemetry across all monitored ports, voyages, and vessels.
    """
    repo = RiskRepository(db)
    events = repo.get_risk_events(limit=200)

    # Active events
    active_events = [e for e in events if e.status in [RiskStatus.ACTIVE, RiskStatus.MONITORED]]

    crit_count = sum(1 for e in active_events if e.severity == RiskSeverity.CRITICAL)
    high_count = sum(1 for e in active_events if e.severity == RiskSeverity.HIGH)
    med_count = sum(1 for e in active_events if e.severity == RiskSeverity.MEDIUM)
    low_count = sum(1 for e in active_events if e.severity == RiskSeverity.LOW)

    severities = [e.severity.value for e in active_events]
    overall_severity = RiskAggregationService.determine_overall_severity(severities)

    total_exposure = sum(float(e.financial_exposure_usd or 0.0) for e in active_events)
    total_delay = sum(float(e.delay_hours_estimate or 0.0) for e in active_events)

    # Top risk ports
    port_event_counts: Dict[str, Dict[str, Any]] = {}
    for e in active_events:
        if e.port_name or e.port_id:
            p_name = e.port_name or e.port_id or "Unknown"
            if p_name not in port_event_counts:
                port_event_counts[p_name] = {"port_name": p_name, "port_id": e.port_id, "count": 0, "max_severity": e.severity.value}
            port_event_counts[p_name]["count"] += 1

    top_ports = sorted(list(port_event_counts.values()), key=lambda x: x["count"], reverse=True)[:5]

    # Provenance counts
    provenance: Dict[str, int] = {}
    for e in events:
        src = e.data_status.value if hasattr(e.data_status, "value") else str(e.data_status)
        provenance[src] = provenance.get(src, 0) + 1

    return {
        "total_active_events": len(active_events),
        "critical_events_count": crit_count,
        "high_events_count": high_count,
        "medium_events_count": med_count,
        "low_events_count": low_count,
        "overall_operational_severity": overall_severity,
        "total_financial_exposure_usd": round(total_exposure, 2),
        "total_delay_hours": round(total_delay, 1),
        "events": events,
        "top_risk_ports": top_ports,
        "provenance_breakdown": provenance,
    }


@risk_router.get("/events", response_model=List[RiskEventSchema])
def list_risk_events(
    severity: Optional[str] = Query(None),
    risk_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    port_id: Optional[str] = Query(None),
    vessel_id: Optional[str] = Query(None),
    voyage_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    repo = RiskRepository(db)
    return repo.get_risk_events(
        severity=severity,
        risk_type=risk_type,
        status=status,
        port_id=port_id,
        vessel_id=vessel_id,
        voyage_id=voyage_id,
        limit=limit
    )


@risk_router.get("/events/{event_id}", response_model=RiskEventSchema)
def get_risk_event(event_id: str, db: Session = Depends(get_db)):
    repo = RiskRepository(db)
    ev = repo.get_risk_event_by_id(event_id)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Risk event {event_id} not found")
    return ev


@risk_router.post("/events", response_model=RiskEventSchema)
def create_risk_event(payload: RiskEventCreate, db: Session = Depends(get_db)):
    repo = RiskRepository(db)
    now = datetime.now(timezone.utc)
    ev = RiskEvent(
        id=f"RISK-{uuid.uuid4().hex[:8].upper()}",
        risk_type=payload.risk_type,
        severity=payload.severity,
        status=payload.status,
        port_id=payload.port_id,
        port_name=payload.port_name,
        berth_id=payload.berth_id,
        vessel_id=payload.vessel_id,
        vessel_name=payload.vessel_name,
        voyage_id=payload.voyage_id,
        title=payload.title,
        description=payload.description,
        trigger_source=payload.trigger_source,
        occurred_at=payload.occurred_at or now,
        expires_at=payload.expires_at,
        financial_exposure_usd=payload.financial_exposure_usd,
        delay_hours_estimate=payload.delay_hours_estimate,
        mitigation_action=payload.mitigation_action,
        data_status=payload.data_status,
        created_at=now,
    )
    return repo.create_risk_event(ev)


@risk_router.patch("/events/{event_id}/status", response_model=RiskEventSchema)
def update_risk_event_status(
    event_id: str,
    new_status: RiskStatus = Query(...),
    db: Session = Depends(get_db)
):
    repo = RiskRepository(db)
    ev = repo.update_risk_event_status(event_id, new_status)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Risk event {event_id} not found")
    return ev


@risk_router.post("/analyze/port", response_model=PortRiskEvaluationResponse)
def analyze_port_risk(
    port_id: str = Query(...),
    port_name: Optional[str] = Query(None),
    vessel_draft_m: Optional[float] = Query(None),
    berth_draft_m: Optional[float] = Query(None),
    cargo_type: Optional[str] = Query("COKING_COAL"),
    vessel_class: Optional[str] = Query("PANAMAX"),
    db: Session = Depends(get_db)
):
    # Resolve port name if missing
    p_repo = PortRepository(db)
    port = p_repo.get_port_by_id(port_id)
    if port and not port_name:
        port_name = port.name
    if port and berth_draft_m is None and port.max_draft:
        berth_draft_m = float(port.max_draft)

    engine = RiskEngine()
    result = engine.evaluate_port_risk(
        port_id=port_id,
        port_name=port_name,
        vessel_draft_m=vessel_draft_m,
        berth_draft_m=berth_draft_m,
        cargo_type=cargo_type,
        vessel_class=vessel_class
    )
    return result


@risk_router.post("/analyze/voyage", response_model=VoyageRiskEvaluationResponse)
def analyze_voyage_risk(payload: VoyageRiskEvaluationRequest, db: Session = Depends(get_db)):
    p_repo = PortRepository(db)
    v_repo = VesselRepository(db)

    orig_port = p_repo.get_port_by_id(payload.origin_port_id)
    dest_port = p_repo.get_port_by_id(payload.destination_port_id)

    orig_name = payload.origin_port_name or (orig_port.name if orig_port else payload.origin_port_id)
    dest_name = payload.destination_port_name or (dest_port.name if dest_port else payload.destination_port_id)

    orig_berth_draft = payload.origin_berth_draft_m or (float(orig_port.max_draft) if orig_port and orig_port.max_draft else None)
    dest_berth_draft = payload.destination_berth_draft_m or (float(dest_port.max_draft) if dest_port and dest_port.max_draft else None)

    vessel_draft = payload.vessel_draft_m
    vessel_name = payload.vessel_name
    vessel_class = payload.vessel_class

    if payload.vessel_id:
        vessel = v_repo.get_vessel_by_id(payload.vessel_id)
        if vessel:
            vessel_name = vessel_name or vessel.name
            vessel_class = vessel_class or vessel.vessel_class.value
            if vessel_draft is None and vessel.particulars and vessel.particulars.max_draft_m:
                vessel_draft = float(vessel.particulars.max_draft_m)

    engine = RiskEngine()
    result = engine.evaluate_voyage_risk(
        origin_port_id=payload.origin_port_id,
        origin_port_name=orig_name,
        destination_port_id=payload.destination_port_id,
        destination_port_name=dest_name,
        vessel_name=vessel_name,
        vessel_class=vessel_class,
        vessel_draft_m=vessel_draft,
        origin_berth_draft_m=orig_berth_draft,
        destination_berth_draft_m=dest_berth_draft,
        cargo_type=payload.cargo_type,
        eta_origin=payload.eta_origin,
        laycan_from=payload.laycan_from,
        laycan_to=payload.laycan_to,
        charter_hire_usd_per_day=payload.charter_hire_usd_per_day
    )
    return result


# ====================================================
# CONGESTION INTELLIGENCE ENDPOINTS
# ====================================================

@congestion_router.get("/ports", response_model=List[PortCongestionSchema])
def get_all_port_congestions(db: Session = Depends(get_db)):
    repo = RiskRepository(db)
    records = repo.get_all_latest_port_congestions()
    return records


@congestion_router.get("/ports/{port_id}", response_model=CongestionEvaluationResponse)
def get_port_congestion_detail(
    port_id: str,
    vessel_class: Optional[str] = Query("PANAMAX"),
    laytime_hours: float = Query(48.0),
    demurrage_rate: float = Query(18000.0),
    db: Session = Depends(get_db)
):
    p_repo = PortRepository(db)
    port = p_repo.get_port_by_id(port_id)
    port_name = port.name if port else port_id

    service = CongestionRiskService()
    return service.evaluate_congestion_risk(
        port_id=port_id,
        port_name=port_name,
        vessel_class=vessel_class,
        laytime_allowed_hours=laytime_hours,
        demurrage_rate_usd_per_day=demurrage_rate
    )


@congestion_router.post("/analyze", response_model=CongestionEvaluationResponse)
def analyze_congestion(
    port_id: str = Query(...),
    port_name: Optional[str] = Query(None),
    vessel_class: Optional[str] = Query("PANAMAX"),
    laytime_allowed_hours: float = Query(48.0),
    demurrage_rate_usd_per_day: float = Query(18000.0),
    db: Session = Depends(get_db)
):
    service = CongestionRiskService()
    return service.evaluate_congestion_risk(
        port_id=port_id,
        port_name=port_name,
        vessel_class=vessel_class,
        laytime_allowed_hours=laytime_allowed_hours,
        demurrage_rate_usd_per_day=demurrage_rate_usd_per_day
    )


# ====================================================
# WEATHER RISK INTELLIGENCE ENDPOINTS
# ====================================================

@weather_router.get("/ports/{port_id}", response_model=WeatherEvaluationResponse)
def get_port_weather(
    port_id: str,
    cargo_type: Optional[str] = Query("COKING_COAL"),
    db: Session = Depends(get_db)
):
    p_repo = PortRepository(db)
    port = p_repo.get_port_by_id(port_id)
    port_name = port.name if port else port_id

    service = WeatherRiskService()
    return service.evaluate_weather_risk(
        port_id=port_id,
        port_name=port_name,
        cargo_type=cargo_type
    )


@weather_router.post("/analyze", response_model=WeatherEvaluationResponse)
def analyze_weather(
    port_id: str = Query(...),
    port_name: Optional[str] = Query(None),
    cargo_type: Optional[str] = Query("COKING_COAL")
):
    service = WeatherRiskService()
    return service.evaluate_weather_risk(
        port_id=port_id,
        port_name=port_name,
        cargo_type=cargo_type
    )


# ====================================================
# TIDAL GATE SCHEDULER ENDPOINTS
# ====================================================

@tidal_router.get("/ports/{port_id}", response_model=List[TidalWindowSchema])
def get_port_tidal_windows(port_id: str, db: Session = Depends(get_db)):
    repo = RiskRepository(db)
    windows = repo.get_tidal_windows_for_port(port_id)
    if not windows:
        # Generate synthetic scheduled windows for next 48h
        p_repo = PortRepository(db)
        port = p_repo.get_port_by_id(port_id)
        port_name = port.name if port else port_id
        berth_draft = float(port.max_draft) if port and port.max_draft else 14.0
        
        now = datetime.now(timezone.utc)
        synthetic_slots = TidalGateScheduler.generate_tidal_windows(
            port_id=port_id,
            start_time=now,
            days=3,
            port_name=port_name,
            berth_draft=berth_draft
        )
        saved = []
        for s in synthetic_slots:
            tw = TidalWindow(
                id=f"TW-{uuid.uuid4().hex[:8].upper()}",
                port_id=port_id,
                port_name=port_name,
                window_start=datetime.fromisoformat(s["window_start"]),
                window_end=datetime.fromisoformat(s["window_end"]),
                peak_water_time=datetime.fromisoformat(s["peak_water_time"]),
                predicted_tide_height_m=s["predicted_tide_height_m"],
                berth_depth_cd_m=berth_draft,
                total_available_depth_m=s["total_available_depth_m"],
                required_ukc_m=0.5,
                status=TidalWindowStatus.PASS if s["event_type"] == "HIGH_WATER" else TidalWindowStatus.CONDITIONAL,
                explanation=f"{s['event_type']} tide slot at {port_name} (Height: +{s['predicted_tide_height_m']}m CD).",
                data_source="SYNTHETIC_HARMONIC",
                created_at=now
            )
            saved.append(repo.save_tidal_window(tw))
        return saved
    return windows


@tidal_router.get("/berths/{berth_id}", response_model=List[TidalWindowSchema])
def get_berth_tidal_windows(berth_id: str, db: Session = Depends(get_db)):
    repo = RiskRepository(db)
    return repo.get_tidal_windows_for_berth(berth_id)


@tidal_router.post("/evaluate", response_model=TidalEvaluationResponse)
def evaluate_tidal_feasibility(
    payload: TidalEvaluationRequest,
    db: Session = Depends(get_db)
):
    p_repo = PortRepository(db)
    port = p_repo.get_port_by_id(payload.port_id)
    port_name = payload.port_name or (port.name if port else payload.port_id)
    berth_draft = payload.berth_draft_m or (float(port.max_draft) if port and port.max_draft else None)

    return TidalGateScheduler.evaluate_ukc_feasibility(
        vessel_draft_m=payload.vessel_draft_m,
        berth_draft_m=berth_draft,
        port_id=payload.port_id,
        arrival_time=payload.arrival_time,
        required_ukc_m=payload.required_ukc_m,
        port_name=port_name,
        channel_draft_m=payload.channel_draft_m
    )
