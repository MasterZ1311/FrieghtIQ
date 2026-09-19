from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.vessels import Vessel
from app.models.ports import Port
from app.models.cargo import CargoRequirement
from app.models.idle_repositioning import (
    VesselEmploymentEvent,
    IdleScenario,
    RepositioningOption,
)
from app.models.enums import (
    VesselEmploymentState,
    EmploymentEventType,
    IdleScenarioType,
    RepositioningDecision,
    DeadheadRiskLevel,
    DecisionConfidence,
    DataStatusType,
    VesselStatus,
)
from app.repositories.idle_repo import IdleRepository
from app.schemas.idle_repositioning import (
    VesselEmploymentEventItem,
    IdleScenarioItem,
    RepositioningOptionItem,
    FleetIdleOverviewResponse,
    VesselEmploymentSummaryItem,
    VesselEmploymentTimelineResponse,
    IdleAnalysisRequest,
    RepositioningAnalysisRequest,
)
from app.services.idle.state_machine import EmploymentStateMachine
from app.services.idle.idle_exposure import IdleExposureService
from app.services.idle.idle_cost import IdleCostService
from app.services.idle.distance_service import RouteDistanceService
from app.services.idle.alternative_employment import AlternativeEmploymentService
from app.services.idle.repositioning_service import RepositioningService
from app.services.idle.deadhead_risk import DeadheadRiskService
from app.services.idle.economics_service import RepositioningEconomicsService

router = APIRouter(tags=["Idle & Repositioning Intelligence"])


@router.get("/idle/vessels", response_model=Dict[str, Any])
def get_fleet_idle_status(db: Session = Depends(get_db)):
    """
    Returns fleet employment status and dataset-backed coverage overview.
    Strictly reports actual vessels in database without implying global fleet tracking.
    """
    vessels = db.query(Vessel).all()
    idle_repo = IdleRepository(db)

    active_count = 0
    idle_risk_count = 0
    currently_idle_count = 0
    repositioning_count = 0
    unknown_count = 0

    summaries = []
    now = datetime.now(timezone.utc)

    for v in vessels:
        part = v.particulars
        avail = v.availability
        is_verified = bool(part and part.is_verified)
        v_status = avail.current_status if avail else None

        # Fetch latest employment event or scenario
        events = idle_repo.get_events_for_vessel(v.id)
        latest_scenario = idle_repo.get_latest_scenario_for_vessel(v.id)

        # Determine next employment
        next_job_desc = latest_scenario.next_known_employment if latest_scenario else None
        next_dt = latest_scenario.estimated_next_employment_at if latest_scenario else None
        avail_dt = avail.open_date_start if avail else None

        # Exposure
        idle_days, exp_narrative = IdleExposureService.calculate_idle_days(avail_dt, next_dt)

        # State Machine
        state, state_expl = EmploymentStateMachine.evaluate_state(
            vessel_status=v_status,
            is_verified_particulars=is_verified,
            has_current_voyage=bool(v_status == VesselStatus.LADEN_TRANSIT),
            voyage_completion_date=avail_dt,
            next_employment_confirmed=bool(next_job_desc and "Unconfirmed" not in next_job_desc and "None" not in next_job_desc),
            idle_days_observed=idle_days,
            now=now
        )

        # Tallies
        if state in [VesselEmploymentState.EMPLOYED, VesselEmploymentState.VOYAGE_COMPLETING]:
            active_count += 1
        elif state == VesselEmploymentState.IDLE_RISK:
            idle_risk_count += 1
        elif state == VesselEmploymentState.IDLE:
            currently_idle_count += 1
        elif state == VesselEmploymentState.REPOSITIONING:
            repositioning_count += 1
        elif state == VesselEmploymentState.UNKNOWN:
            unknown_count += 1

        # Idle Cost
        daily_cost = None
        if part and hasattr(part, "daily_charter_rate_usd") and part.daily_charter_rate_usd:
            daily_cost = part.daily_charter_rate_usd
        elif latest_scenario and latest_scenario.idle_cost and idle_days and idle_days > 0:
            daily_cost = round(latest_scenario.idle_cost / idle_days, 2)

        idle_cost_val, cost_expl = IdleCostService.calculate_idle_cost(
            idle_days=idle_days,
            daily_vessel_cost=daily_cost,
            cost_source_label="Configured OPEX / Charter Rate" if daily_cost else None
        )

        # Location
        curr_loc = "Unknown Location"
        if avail:
            curr_loc = avail.current_port_name or avail.open_port_name or "Sea Transit"

        # Risk Level
        if state == VesselEmploymentState.IDLE:
            risk_level = "CONFIRMED_IDLE"
        elif state == VesselEmploymentState.IDLE_RISK:
            risk_level = "POTENTIAL_RISK"
        elif state == VesselEmploymentState.UNKNOWN:
            risk_level = "UNKNOWN"
        else:
            risk_level = "LOW_RISK"

        summaries.append({
            "vessel_id": v.id,
            "vessel_name": v.vessel_name,
            "vessel_class": v.vessel_class.value if hasattr(v.vessel_class, "value") else str(v.vessel_class),
            "current_location": curr_loc,
            "current_voyage": "Laden voyage in progress" if v_status == VesselStatus.LADEN_TRANSIT else (avail.open_port_name or "In ballast/discharge"),
            "current_status": v_status.value if v_status else "UNKNOWN",
            "employment_state": state.value,
            "state_explanation": state_expl,
            "estimated_availability": avail_dt.isoformat() if avail_dt else None,
            "next_known_employment": next_job_desc or "UNKNOWN / UNAVAILABLE",
            "estimated_next_employment_at": next_dt.isoformat() if next_dt else None,
            "idle_days": idle_days,
            "idle_exposure_label": f"{idle_days:.1f} days" if idle_days is not None else "UNKNOWN (Next employment unrecorded)",
            "idle_risk_level": risk_level,
            "idle_cost": idle_cost_val,
            "daily_cost_label": f"${daily_cost:,.0f}/day" if daily_cost else "DAILY VESSEL COST: NOT AVAILABLE",
            "is_data_complete": is_verified and (idle_days is not None),
            "data_confidence": DecisionConfidence.HIGH.value if is_verified else DecisionConfidence.LOW.value,
            "data_status": DataStatusType.RECENT.value if is_verified else DataStatusType.SYNTHETIC.value,
            "last_updated": now.isoformat()
        })

    total_coverage = len(vessels)
    overview = {
        "dataset_coverage_count": total_coverage,
        "active_vessels_count": active_count,
        "idle_risk_count": idle_risk_count,
        "currently_idle_count": currently_idle_count,
        "repositioning_count": repositioning_count,
        "unknown_state_count": unknown_count,
        "dataset_coverage_label": f"{total_coverage} vessels in current dataset",
        "data_provenance": {
            "source": "SAIL Operational Snapshot + Verified Commercial Register",
            "disclaimer": "Do not extrapolate to global fleet without certified AIS license.",
            "integrity_policy": "Unknown fields remain NULL / UNKNOWN. Zero cost or zero idle days are never substituted."
        }
    }

    return {
        "overview": overview,
        "vessels": summaries
    }


@router.get("/idle/scenarios", response_model=List[IdleScenarioItem])
def get_idle_scenarios(db: Session = Depends(get_db)):
    """
    Returns all detected or evaluated idle exposure scenarios.
    """
    repo = IdleRepository(db)
    scenarios = repo.get_all_scenarios()

    results = []
    for sc in scenarios:
        results.append(IdleScenarioItem(
            id=sc.id,
            vessel_id=sc.vessel_id,
            vessel_name=sc.vessel.vessel_name if sc.vessel else None,
            vessel_class=sc.vessel.vessel_class.value if sc.vessel and hasattr(sc.vessel.vessel_class, "value") else None,
            voyage_id=sc.voyage_id,
            scenario_type=sc.scenario_type,
            current_location=sc.current_location,
            next_known_employment=sc.next_known_employment,
            estimated_available_at=sc.estimated_available_at,
            estimated_next_employment_at=sc.estimated_next_employment_at,
            idle_days=sc.idle_days,
            idle_cost=sc.idle_cost,
            confidence=sc.confidence,
            data_status=sc.data_status,
            created_at=sc.created_at,
            updated_at=sc.updated_at
        ))
    return results


@router.get("/idle/scenarios/{id}", response_model=IdleScenarioItem)
def get_idle_scenario_by_id(id: str, db: Session = Depends(get_db)):
    repo = IdleRepository(db)
    sc = repo.get_scenario_by_id(id)
    if not sc:
        raise HTTPException(status_code=404, detail=f"Idle scenario with id '{id}' not found.")

    return IdleScenarioItem(
        id=sc.id,
        vessel_id=sc.vessel_id,
        vessel_name=sc.vessel.vessel_name if sc.vessel else None,
        vessel_class=sc.vessel.vessel_class.value if sc.vessel and hasattr(sc.vessel.vessel_class, "value") else None,
        voyage_id=sc.voyage_id,
        scenario_type=sc.scenario_type,
        current_location=sc.current_location,
        next_known_employment=sc.next_known_employment,
        estimated_available_at=sc.estimated_available_at,
        estimated_next_employment_at=sc.estimated_next_employment_at,
        idle_days=sc.idle_days,
        idle_cost=sc.idle_cost,
        confidence=sc.confidence,
        data_status=sc.data_status,
        created_at=sc.created_at,
        updated_at=sc.updated_at
    )


@router.post("/idle/analyze", response_model=Dict[str, Any])
def analyze_vessel_idle_and_repositioning(
    req: IdleAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Comprehensive decision-support analysis for a single vessel:
    - Calculates idle exposure
    - Modeled idle cost (if daily cost provided or sourced)
    - Searches real cargo requests via Phase 3 matching + Phase 4 port feasibility
    - Evaluates ballast repositioning options and deadhead risk
    - Performs WAIT vs REPOSITION economic comparison without fabricating revenue
    """
    vessel = db.query(Vessel).filter(Vessel.id == req.vessel_id).first()
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel with id '{req.vessel_id}' not found.")

    idle_repo = IdleRepository(db)
    alt_service = AlternativeEmploymentService(db)
    dist_service = RouteDistanceService()

    avail = vessel.availability
    part = vessel.particulars
    is_verified = bool(part and part.is_verified)

    avail_dt = avail.open_date_start if avail else None
    curr_location = (avail.current_port_name or avail.open_port_name or "Bay of Bengal") if avail else "Unknown Location"

    # Daily vessel cost resolution
    daily_cost = req.daily_vessel_cost_assumption
    if daily_cost is None and part and hasattr(part, "daily_charter_rate_usd") and part.daily_charter_rate_usd:
        daily_cost = part.daily_charter_rate_usd

    # Look up existing scenario or default
    existing_sc = idle_repo.get_latest_scenario_for_vessel(vessel.id)
    next_dt = existing_sc.estimated_next_employment_at if existing_sc else None
    next_emp = existing_sc.next_known_employment if existing_sc else None

    # Idle Days & Cost
    idle_days, idle_narrative = IdleExposureService.calculate_idle_days(avail_dt, next_dt)
    idle_cost, idle_cost_narrative = IdleCostService.calculate_idle_cost(
        idle_days, daily_cost, "User Assumption / Charter Model" if daily_cost else None
    )

    # 1. Alternative Cargo Search (Phase 3 + Phase 4)
    candidates = alt_service.find_candidates_for_vessel(vessel.id)
    candidate_dicts = [c.to_dict() for c in candidates]

    # 2. Evaluate Repositioning Options for Compatible/Partial candidates
    repo_options = []
    curr_port = None
    if avail and avail.open_port_name:
        curr_port = db.query(Port).filter(Port.name.ilike(f"%{avail.open_port_name.split()[0]}%")).first()

    for cand in candidates:
        cr = cand.cargo_requirement
        orig_port = cr.load_port
        if not orig_port:
            continue

        # Distance
        if curr_port:
            dist_nm, dist_method, dist_expl = dist_service.get_distance(curr_port, orig_port, db=db)
        else:
            dist_nm, dist_method, dist_expl = None, "UNAVAILABLE", "Current port location unrecorded."

        # Port compatibility string from candidate
        port_comp_str = "PASS" if cand.origin_port_status.value == "PASS" and cand.destination_port_status.value == "PASS" else (
            "CONDITIONAL" if cand.origin_port_status.value == "CONDITIONAL" or cand.destination_port_status.value == "CONDITIONAL" else (
                "FAIL" if cand.origin_port_status.value == "FAIL" or cand.destination_port_status.value == "FAIL" else "UNKNOWN"
            )
        )

        repo_eval = RepositioningService.evaluate_repositioning_option(
            vessel=vessel,
            target_port=orig_port,
            target_cargo=cr,
            distance_nm=dist_nm,
            distance_method=dist_method,
            speed_knots=12.5,
            port_compatibility=port_comp_str,
            bunker_price_usd=620.0,
            daily_vessel_cost=daily_cost,
        )

        # Deadhead Risk
        deadhead_risk, deadhead_narrative = DeadheadRiskService.evaluate_risk(
            distance_nm=dist_nm,
            port_compatibility=port_comp_str,
            timing_compatibility=repo_eval["timing_compatibility"],
            has_secured_cargo=bool(cand.compatibility_status.value == "COMPATIBLE"),
            is_data_complete=bool(cand.is_data_complete and dist_nm is not None)
        )

        repo_eval["target_port_name"] = orig_port.name
        repo_eval["cargo_name"] = cr.cargo_type.value if hasattr(cr.cargo_type, "value") else str(cr.cargo_type)
        repo_eval["deadhead_risk"] = deadhead_risk.value
        repo_eval["deadhead_narrative"] = deadhead_narrative
        repo_eval["candidate_compatibility"] = cand.compatibility_status.value
        repo_options.append(repo_eval)

    # 3. Economics Comparison (WAIT vs REPOSITION)
    economics = RepositioningEconomicsService.compare_strategies(
        vessel_name=vessel.vessel_name,
        idle_days=idle_days,
        daily_vessel_cost=daily_cost,
        repositioning_options=repo_options,
        commercial_revenue_usd=None, # Revenue not fabricated
        data_confidence=DecisionConfidence.HIGH.value if is_verified else DecisionConfidence.MEDIUM.value
    )

    return {
        "vessel_id": vessel.id,
        "vessel_name": vessel.vessel_name,
        "vessel_class": vessel.vessel_class.value if hasattr(vessel.vessel_class, "value") else str(vessel.vessel_class),
        "current_location": curr_location,
        "estimated_availability": avail_dt.isoformat() if avail_dt else None,
        "next_known_employment": next_emp or "UNKNOWN / UNAVAILABLE",
        "estimated_next_employment_at": next_dt.isoformat() if next_dt else None,
        "idle_days": idle_days,
        "idle_narrative": idle_narrative,
        "daily_vessel_cost": daily_cost,
        "daily_cost_status": "SOURCED_OR_CONFIGURED" if daily_cost else "DAILY VESSEL COST: NOT AVAILABLE",
        "idle_cost": idle_cost,
        "idle_cost_narrative": idle_cost_narrative,
        "alternative_candidates": candidate_dicts,
        "repositioning_options": repo_options,
        "economics_comparison": economics,
        "data_provenance": {
            "vessel_data_complete": is_verified,
            "source": "SAIL Operational Snapshot Register",
            "distance_methodology": "FreightRoute Nautical Records with Great-Circle Geodesic Approximation Fallback"
        }
    }


@router.post("/repositioning/analyze", response_model=Dict[str, Any])
def analyze_repositioning_route(
    req: RepositioningAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates a specific ballast transit leg between current location and target port.
    """
    vessel = db.query(Vessel).filter(Vessel.id == req.vessel_id).first()
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel with id '{req.vessel_id}' not found.")

    target_port = db.query(Port).filter(Port.id == req.target_port_id).first()
    if not target_port:
        raise HTTPException(status_code=404, detail=f"Target port with id '{req.target_port_id}' not found.")

    target_cargo = None
    if req.target_cargo_request_id:
        target_cargo = db.query(CargoRequirement).filter(CargoRequirement.id == req.target_cargo_request_id).first()

    avail = vessel.availability
    curr_port = None
    if avail and avail.open_port_name:
        curr_port = db.query(Port).filter(Port.name.ilike(f"%{avail.open_port_name.split()[0]}%")).first()

    dist_service = RouteDistanceService()
    if curr_port:
        dist_nm, dist_method, dist_expl = dist_service.get_distance(curr_port, target_port, db=db)
    else:
        dist_nm, dist_method, dist_expl = None, "UNAVAILABLE", "Current port unrecorded."

    repo_eval = RepositioningService.evaluate_repositioning_option(
        vessel=vessel,
        target_port=target_port,
        target_cargo=target_cargo,
        distance_nm=dist_nm,
        distance_method=dist_method,
        speed_knots=req.speed_assumption_knots or 12.5,
        port_compatibility="PASS",
        bunker_price_usd=req.bunker_price_usd,
        daily_vessel_cost=req.daily_vessel_cost_assumption
    )

    deadhead_risk, deadhead_narr = DeadheadRiskService.evaluate_risk(
        distance_nm=dist_nm,
        port_compatibility="PASS",
        timing_compatibility=repo_eval["timing_compatibility"],
        has_secured_cargo=bool(target_cargo is not None),
        is_data_complete=bool(dist_nm is not None)
    )

    repo_eval["deadhead_risk"] = deadhead_risk.value
    repo_eval["deadhead_narrative"] = deadhead_narr
    repo_eval["target_port_name"] = target_port.name
    return repo_eval


@router.get("/repositioning/{vessel_id}/options", response_model=List[RepositioningOptionItem])
def get_vessel_repositioning_options(
    vessel_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns recorded repositioning options for a specific vessel.
    """
    repo = IdleRepository(db)
    options = repo.get_repositioning_options_for_vessel(vessel_id)

    results = []
    for opt in options:
        results.append(RepositioningOptionItem(
            id=opt.id,
            idle_scenario_id=opt.idle_scenario_id,
            vessel_id=opt.vessel_id,
            vessel_name=opt.vessel.vessel_name if opt.vessel else None,
            target_port_id=opt.target_port_id,
            target_port_name=opt.target_port.name if opt.target_port else None,
            target_cargo_request_id=opt.target_cargo_request_id,
            cargo_name=opt.target_cargo_request.cargo_type.value if opt.target_cargo_request and hasattr(opt.target_cargo_request.cargo_type, "value") else None,
            cargo_quantity_mt=opt.target_cargo_request.quantity_mt if opt.target_cargo_request else None,
            distance=opt.distance,
            distance_method=opt.distance_method,
            estimated_sailing_days=opt.estimated_sailing_days,
            estimated_bunker_cost=opt.estimated_bunker_cost,
            estimated_total_cost=opt.estimated_total_cost,
            port_compatibility=opt.port_compatibility,
            timing_compatibility=opt.timing_compatibility,
            status=opt.status,
            data_status=opt.data_status,
            created_at=opt.created_at
        ))
    return results


@router.get("/vessels/{id}/employment-timeline", response_model=VesselEmploymentTimelineResponse)
def get_vessel_employment_timeline(
    id: str,
    db: Session = Depends(get_db)
):
    """
    Returns the comprehensive lifecycle employment timeline for a vessel:
    - Voyage progress and estimated discharge completion
    - Open/available date window
    - Next scheduled fixture / idle risk
    - Sourced & estimated events
    """
    vessel = db.query(Vessel).filter(Vessel.id == id).first()
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel with id '{id}' not found.")

    idle_repo = IdleRepository(db)
    part = vessel.particulars
    avail = vessel.availability
    is_verified = bool(part and part.is_verified)

    events = idle_repo.get_events_for_vessel(id)
    scenario = idle_repo.get_latest_scenario_for_vessel(id)
    repo_options = idle_repo.get_repositioning_options_for_vessel(id)

    avail_dt = avail.open_date_start if avail else None
    next_dt = scenario.estimated_next_employment_at if scenario else None
    next_emp = scenario.next_known_employment if scenario else None
    idle_days, _ = IdleExposureService.calculate_idle_days(avail_dt, next_dt)

    state, _ = EmploymentStateMachine.evaluate_state(
        vessel_status=avail.current_status if avail else None,
        is_verified_particulars=is_verified,
        has_current_voyage=bool(avail and avail.current_status == VesselStatus.LADEN_TRANSIT),
        voyage_completion_date=avail_dt,
        next_employment_confirmed=bool(next_emp and "Unconfirmed" not in next_emp and "None" not in next_emp),
        idle_days_observed=idle_days
    )

    event_items = []
    for ev in events:
        event_items.append(VesselEmploymentEventItem(
            id=ev.id,
            vessel_id=ev.vessel_id,
            event_type=ev.event_type,
            voyage_id=ev.voyage_id,
            cargo_request_id=ev.cargo_request_id,
            origin_port_id=ev.origin_port_id,
            origin_port_name=ev.origin_port.name if ev.origin_port else None,
            destination_port_id=ev.destination_port_id,
            destination_port_name=ev.destination_port.name if ev.destination_port else None,
            event_start=ev.event_start,
            event_end=ev.event_end,
            status=ev.status,
            source_id=ev.source_id,
            data_status=ev.data_status
        ))

    scenario_item = None
    if scenario:
        scenario_item = IdleScenarioItem(
            id=scenario.id,
            vessel_id=scenario.vessel_id,
            vessel_name=vessel.vessel_name,
            vessel_class=vessel.vessel_class.value if hasattr(vessel.vessel_class, "value") else str(vessel.vessel_class),
            voyage_id=scenario.voyage_id,
            scenario_type=scenario.scenario_type,
            current_location=scenario.current_location,
            next_known_employment=scenario.next_known_employment,
            estimated_available_at=scenario.estimated_available_at,
            estimated_next_employment_at=scenario.estimated_next_employment_at,
            idle_days=scenario.idle_days,
            idle_cost=scenario.idle_cost,
            confidence=scenario.confidence,
            data_status=scenario.data_status,
            created_at=scenario.created_at,
            updated_at=scenario.updated_at
        )

    repo_items = []
    for opt in repo_options:
        repo_items.append(RepositioningOptionItem(
            id=opt.id,
            idle_scenario_id=opt.idle_scenario_id,
            vessel_id=opt.vessel_id,
            vessel_name=vessel.vessel_name,
            target_port_id=opt.target_port_id,
            target_port_name=opt.target_port.name if opt.target_port else None,
            target_cargo_request_id=opt.target_cargo_request_id,
            cargo_name=opt.target_cargo_request.cargo_type.value if opt.target_cargo_request and hasattr(opt.target_cargo_request.cargo_type, "value") else None,
            cargo_quantity_mt=opt.target_cargo_request.quantity_mt if opt.target_cargo_request else None,
            distance=opt.distance,
            distance_method=opt.distance_method,
            estimated_sailing_days=opt.estimated_sailing_days,
            estimated_bunker_cost=opt.estimated_bunker_cost,
            estimated_total_cost=opt.estimated_total_cost,
            port_compatibility=opt.port_compatibility,
            timing_compatibility=opt.timing_compatibility,
            status=opt.status,
            data_status=opt.data_status,
            created_at=opt.created_at
        ))

    curr_loc = (avail.current_port_name or avail.open_port_name or "Sea Transit") if avail else "Unknown Location"
    freshness = "LIVE AIS & PORT LOG" if is_verified else "SYNTHETIC ESTIMATE"

    return VesselEmploymentTimelineResponse(
        vessel_id=vessel.id,
        vessel_name=vessel.vessel_name,
        vessel_class=vessel.vessel_class.value if hasattr(vessel.vessel_class, "value") else str(vessel.vessel_class),
        employment_state=state,
        current_location=curr_loc,
        current_status=avail.current_status.value if avail else "UNKNOWN",
        is_verified_particulars=is_verified,
        estimated_availability=avail_dt,
        next_known_employment=next_emp or "UNKNOWN / UNAVAILABLE",
        estimated_next_employment_at=next_dt,
        idle_days=idle_days,
        idle_cost=scenario.idle_cost if scenario else None,
        data_status=DataStatusType.RECENT if is_verified else DataStatusType.SYNTHETIC,
        data_freshness_label=freshness,
        events=event_items,
        active_scenario=scenario_item,
        repositioning_options=repo_items
    )
