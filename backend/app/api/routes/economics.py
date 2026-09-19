from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.economics_repo import VoyageEconomicsRepository
from app.repositories.port_repo import PortRepository
from app.repositories.vessel_repo import VesselRepository
from app.schemas.economics import (
    VoyageEconomicsAnalysisRequest,
    VoyageEconomicsAnalysisResponse,
    CostComponentItem,
    SpeedScenarioItem,
    VoyageScenarioItem,
    BunkerCalculationRequest,
    BunkerCalculationResponse,
    BunkerPriceResponse,
    SpeedAnalysisRequest,
    SpeedBreakEvenResponse,
    SensitivityAnalysisRequest,
    SensitivityAnalysisResponse,
)
from app.services.economics import (
    VoyageEconomicsService,
    BunkerPriceProvider,
    BunkerCostService,
    SpeedScenarioService,
    SpeedBreakEvenService,
    SensitivityService,
)

# ----------------------------------------------------
# Routers
# ----------------------------------------------------
economics_router = APIRouter(prefix="/voyage-economics", tags=["Voyage Financial Economics"])
bunker_router = APIRouter(prefix="/bunker", tags=["Bunker Fuel Economics"])
speed_router = APIRouter(prefix="/speed", tags=["Speed & Fuel Optimization"])


# ====================================================
# VOYAGE ECONOMICS ENDPOINTS
# ====================================================

@economics_router.post("/analyze", response_model=VoyageEconomicsAnalysisResponse)
def analyze_voyage_economics(
    payload: VoyageEconomicsAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Computes end-to-end transparent voyage economics across freight, bunker,
    port tariffs, vessel time, expected delay/demurrage, and repositioning expenses.
    """
    service = VoyageEconomicsService(db=db)
    result = service.analyze_voyage_economics(
        origin_port_id=payload.origin_port_id,
        destination_port_id=payload.destination_port_id,
        cargo_quantity_mt=payload.cargo_quantity_mt,
        cargo_type=payload.cargo_type,
        vessel_id=payload.vessel_id,
        cargo_request_id=payload.cargo_request_id,
        voyage_id=payload.voyage_id,
        custom_speed_knots=payload.custom_speed_knots,
        custom_freight_rate_usd_per_mt=payload.custom_freight_rate_usd_per_mt,
        custom_bunker_price_usd_per_mt=payload.custom_bunker_price_usd_per_mt,
        custom_daily_hire_usd=payload.custom_daily_hire_usd,
        congestion_delay_hours=payload.congestion_delay_hours,
        weather_delay_hours=payload.weather_delay_hours,
        tidal_delay_hours=payload.tidal_delay_hours,
        laytime_allowed_hours=payload.laytime_allowed_hours,
        demurrage_rate_usd_per_day=payload.demurrage_rate_usd_per_day,
        ballast_distance_nm=payload.ballast_distance_nm,
        idle_days=payload.idle_days,
        persist=True
    )
    return result


@economics_router.get("/latest", response_model=VoyageEconomicsAnalysisResponse)
def get_latest_analysis(db: Session = Depends(get_db)):
    """
    Returns the most recently evaluated voyage financial economic analysis.
    If none exists in DB, triggers an analysis for the SAIL benchmark route.
    """
    latest = VoyageEconomicsRepository.get_latest(db)
    service = VoyageEconomicsService(db=db)
    if not latest:
        # Default Newcastle -> Paradip benchmark
        ports = PortRepository.get_all_ports(db)
        ncy = next((p for p in ports if p.unlocode == "AUNCY" or "Newcastle" in p.name), ports[0] if ports else None)
        prt = next((p for p in ports if p.unlocode == "INPRT" or "Paradip" in p.name), ports[1] if len(ports) > 1 else None)
        vessels = VesselRepository.get_all(db)
        vessel = vessels[0] if vessels else None

        result = service.analyze_voyage_economics(
            origin_port_id=ncy.id if ncy else "newcastle-au",
            destination_port_id=prt.id if prt else "paradip-in",
            cargo_quantity_mt=75000.0,
            vessel_id=vessel.id if vessel else None,
            persist=True
        )
        return result

    # Re-evaluate live representation for rich sub-engines
    return service.analyze_voyage_economics(
        origin_port_id=latest.origin_port_id,
        destination_port_id=latest.destination_port_id,
        cargo_quantity_mt=latest.cargo_quantity_mt,
        vessel_id=latest.vessel_id,
        cargo_request_id=latest.cargo_request_id,
        voyage_id=latest.voyage_id,
        persist=False
    )


@economics_router.get("/{analysis_id}", response_model=VoyageEconomicsAnalysisResponse)
def get_analysis_by_id(analysis_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a specific voyage economics evaluation by ID.
    """
    rec = VoyageEconomicsRepository.get_by_id(db, analysis_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Voyage analysis {analysis_id} not found.")

    service = VoyageEconomicsService(db=db)
    return service.analyze_voyage_economics(
        origin_port_id=rec.origin_port_id,
        destination_port_id=rec.destination_port_id,
        cargo_quantity_mt=rec.cargo_quantity_mt,
        vessel_id=rec.vessel_id,
        cargo_request_id=rec.cargo_request_id,
        voyage_id=rec.voyage_id,
        persist=False
    )


@economics_router.get("/{analysis_id}/components", response_model=List[CostComponentItem])
def get_analysis_components(analysis_id: str, db: Session = Depends(get_db)):
    """
    Retrieves itemized cost components for a specific voyage economics record.
    """
    comps = VoyageEconomicsRepository.get_components(db, analysis_id)
    return comps


@economics_router.get("/{analysis_id}/scenarios", response_model=List[VoyageScenarioItem])
def get_analysis_scenarios(analysis_id: str, db: Session = Depends(get_db)):
    """
    Retrieves scenario comparisons (BASE, LOW_COST, HIGH_COST, DELAY, etc.) for a voyage analysis.
    """
    scens = VoyageEconomicsRepository.get_scenarios(db, analysis_id)
    return scens


@economics_router.get("/{analysis_id}/speed-scenarios", response_model=List[SpeedScenarioItem])
def get_analysis_speed_scenarios(analysis_id: str, db: Session = Depends(get_db)):
    """
    Retrieves evaluated speed scenarios for a voyage analysis.
    """
    speeds = VoyageEconomicsRepository.get_speed_scenarios(db, analysis_id)
    return speeds


@economics_router.post("/sensitivity", response_model=SensitivityAnalysisResponse)
def analyze_sensitivity(payload: SensitivityAnalysisRequest):
    """
    Calculates multidimensional economic sensitivity and elasticity curves across
    bunker prices, freight rates, speeds, delays, cargo quantities, and hire rates.
    """
    res = SensitivityService.calculate_sensitivities(
        distance_nm=payload.distance_nm,
        base_cargo_quantity_mt=payload.base_cargo_quantity_mt,
        base_freight_rate_usd_per_mt=payload.base_freight_rate_usd_per_mt,
        base_bunker_price_usd_per_mt=payload.base_bunker_price_usd_per_mt,
        base_speed_knots=payload.base_speed_knots,
        base_daily_charter_rate_usd=payload.base_daily_charter_rate_usd,
        base_port_cost_usd=payload.base_port_cost_usd,
        base_port_delay_hours=payload.base_port_delay_hours,
        baseline_consumption_mtpd=payload.baseline_consumption_mtpd,
        baseline_speed_knots=payload.baseline_speed_knots,
        laytime_allowed_hours=payload.laytime_allowed_hours,
        demurrage_rate_usd_per_day=payload.demurrage_rate_usd_per_day,
    )
    return res


@economics_router.post("/speed", response_model=Dict[str, Any])
def analyze_speed_options(payload: SpeedAnalysisRequest):
    """
    Evaluates candidate speeds across the hydrodynamic cubic fuel consumption curve.
    """
    res = SpeedScenarioService.evaluate_speed_scenarios(
        distance_nm=payload.distance_nm,
        cargo_quantity_mt=payload.cargo_quantity_mt,
        baseline_speed_knots=payload.baseline_speed_knots,
        baseline_consumption_mtpd=payload.baseline_consumption_mtpd,
        bunker_price_usd_per_mt=payload.bunker_price_usd_per_mt,
        daily_charter_rate_usd=payload.daily_charter_rate_usd,
        port_cost_usd=payload.port_cost_usd,
        candidate_speeds=payload.candidate_speeds
    )
    return res


# ====================================================
# BUNKER FUEL ENDPOINTS
# ====================================================

@bunker_router.post("/calculate", response_model=BunkerCalculationResponse)
def calculate_bunker_consumption(payload: BunkerCalculationRequest):
    """
    Calculates nautical fuel consumption and total bunker cost from physical inputs.
    """
    res = BunkerCostService.calculate_bunker_cost(
        distance_nm=payload.distance_nm,
        speed_knots=payload.speed_knots,
        consumption_mtpd=payload.consumption_mtpd,
        bunker_price_usd_per_mt=payload.bunker_price_usd_per_mt,
        port_days=payload.port_days,
        port_consumption_mtpd=payload.port_consumption_mtpd,
        fuel_grade=payload.fuel_grade,
        hub_location=payload.hub_location
    )
    return res


@bunker_router.get("/prices", response_model=List[BunkerPriceResponse])
def get_bunker_price_benchmarks():
    """
    Returns live and recent bunker fuel price benchmarks across key global bunkering hubs.
    """
    return BunkerPriceProvider.get_prices()


# ====================================================
# SPEED OPTIMIZATION ENDPOINTS
# ====================================================

@speed_router.post("/analyze", response_model=Dict[str, Any])
def analyze_speed_curve(payload: SpeedAnalysisRequest):
    """
    Runs hydrodynamic cubic Admiralty curve analysis across speeds.
    """
    return SpeedScenarioService.evaluate_speed_scenarios(
        distance_nm=payload.distance_nm,
        cargo_quantity_mt=payload.cargo_quantity_mt,
        baseline_speed_knots=payload.baseline_speed_knots,
        baseline_consumption_mtpd=payload.baseline_consumption_mtpd,
        bunker_price_usd_per_mt=payload.bunker_price_usd_per_mt,
        daily_charter_rate_usd=payload.daily_charter_rate_usd,
        port_cost_usd=payload.port_cost_usd,
        candidate_speeds=payload.candidate_speeds
    )


@speed_router.post("/break-even", response_model=SpeedBreakEvenResponse)
def calculate_speed_break_even(payload: SpeedAnalysisRequest):
    """
    Performs marginal break-even analysis: marginal bunker cost vs marginal charter time savings.
    """
    return SpeedBreakEvenService.calculate_break_even(
        distance_nm=payload.distance_nm,
        baseline_consumption_mtpd=payload.baseline_consumption_mtpd,
        baseline_speed_knots=payload.baseline_speed_knots,
        bunker_price_usd_per_mt=payload.bunker_price_usd_per_mt,
        daily_charter_rate_usd=payload.daily_charter_rate_usd,
        cargo_quantity_mt=payload.cargo_quantity_mt
    )
