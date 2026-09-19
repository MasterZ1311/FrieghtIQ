import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from app.models.enums import (
    ContractStrategyType, MarketScenarioType, DecisionConfidence, DataStatusType,
    FeasibilityStatus
)
from app.services.contracts.voyage_planning import VoyagePlanningService, VoyagePlanningResult
from app.services.contracts.spot_model import SpotContractCostModel, SpotCostResult
from app.services.contracts.multiple_voyage_model import MultipleVoyageCostModel, MultipleVoyageCostResult
from app.services.contracts.hybrid_strategy import HybridContractStrategy, CoverageTierResult
from app.services.contracts.flexibility import FlexibilityCostModel, FlexibilityEvaluation
from app.services.contracts.market_exposure import MarketExposureModel, MarketExposureEvaluation
from app.services.contracts.risk_adjusted_cost import RiskAdjustedCostService, RiskAdjustedCostBreakdown
from app.services.contracts.break_even import BreakEvenService, BreakEvenAnalysisResult

class StrategyScenarioItem(BaseModel):
    scenario_name: str # "BEAR", "BASE", "BULL"
    market_assumption: str
    rate: float
    quantity: float
    cost: float
    probability: float

class StrategyDetail(BaseModel):
    id: Optional[str] = None
    strategy_type: ContractStrategyType
    strategy_label: str
    contract_duration: str
    voyage_count: int
    total_quantity: float
    contracted_quantity: float
    spot_quantity: float
    reference_rate: Optional[float]
    expected_rate: float
    expected_cost: float
    p10_cost: float
    p50_cost: float
    p90_cost: float
    market_exposure: float
    flexibility_measure: float
    risk_adjusted_cost: float
    break_even_rate: Optional[float]
    decision_confidence: DecisionConfidence
    scenarios: List[StrategyScenarioItem]
    why_this_fits: List[str]
    key_trade_off: str
    data_status: DataStatusType = DataStatusType.SYNTHETIC

class ScenarioMatrixCell(BaseModel):
    strategy_type: ContractStrategyType
    scenario_name: str
    freight_rate_usd_pmt: float
    freight_cost_usd: float
    market_assumption: str

class ContractEngineAnalysisResult(BaseModel):
    cargo_request_id: Optional[str]
    trade_lane: str
    origin_port_id: str
    destination_port_id: str
    cargo_type: str
    total_requirement_mt: float
    parcel_size_mt: float
    vessel_class: str
    planning_horizon_days: int
    voyage_plan: VoyagePlanningResult
    strategies: Dict[str, StrategyDetail] # "SPOT", "SHORT_TERM_MULTIPLE_VOYAGE", "MEDIUM_TERM_MULTIPLE_VOYAGE"
    scenario_matrix: List[ScenarioMatrixCell]
    break_even_analysis: BreakEvenAnalysisResult
    coverage_spectrum: List[CoverageTierResult]
    port_feasibility_status: str
    data_provenance: Dict[str, Any]
    decision_confidence: DecisionConfidence
    created_at: str

class ContractStrategyEngine:
    """
    Master procurement strategy engine for FREIGHT IQ (SIH 2026 #SIH26006).
    Coordinates voyage planning, multi-voyage contract modeling, scenario matrices,
    risk-adjusted cost analysis, and break-even thresholds.
    """

    @classmethod
    def analyze_strategies(
        cls,
        total_requirement_mt: float = 300000.0,
        parcel_size_mt: float = 75000.0,
        origin_port_id: str = "newcastle-au",
        destination_port_id: str = "paradip-in",
        cargo_type: str = "COKING_COAL",
        vessel_class: str = "PANAMAX",
        planning_horizon_days: int = 180,
        reference_contract_rate: Optional[float] = 24.00,
        cargo_request_id: Optional[str] = None,
        # Integrated inputs from Phase 3, 4, 5, 6, 7
        port_feasibility: str = "PASS",
        current_spot_rate: float = 24.50,
        p10_rate: float = 22.80,
        p50_rate: float = 24.10,
        p90_rate: float = 26.50,
        regime_type: str = "BEAR",
        regime_probability: float = 0.65,
        wait_fix_decision: str = "MONITOR",
        volatility_annualized: float = 0.28,
        forecast_id: Optional[str] = None,
        regime_id: Optional[str] = None,
        wait_fix_analysis_id: Optional[str] = None,
    ) -> ContractEngineAnalysisResult:
        if total_requirement_mt <= 0:
            raise ValueError("Total requirement must be strictly positive.")
        if parcel_size_mt <= 0:
            raise ValueError("Voyage parcel size must be strictly positive.")

        # 1. Voyage Planning
        voyage_plan = VoyagePlanningService.plan_voyages(
            total_requirement_mt=total_requirement_mt,
            voyage_parcel_mt=parcel_size_mt,
            planning_horizon_days=planning_horizon_days
        )
        total_voyages = voyage_plan.expected_voyages

        # Check port compatibility gating:
        # If mandatory port validation FAILs, mark overall confidence LOW and add blocking notices
        is_port_blocked = (port_feasibility == "FAIL")
        base_confidence = DecisionConfidence.LOW if is_port_blocked else (
            DecisionConfidence.HIGH if regime_probability >= 0.60 else DecisionConfidence.MEDIUM
        )

        voyage_dict_list = [
            {"voyage_number": item.voyage_number, "parcel_mt": item.parcel_mt, "departure_day": item.estimated_departure_day}
            for item in voyage_plan.schedule
        ]

        # 2. Evaluate Pure SPOT Strategy (100% spot exposure)
        spot_res = SpotContractCostModel.calculate_spot_exposure(
            voyages=voyage_dict_list,
            current_spot_rate=current_spot_rate,
            p10_rate=p10_rate,
            p50_rate=p50_rate,
            p90_rate=p90_rate,
            regime_type=regime_type,
            volatility_annualized=volatility_annualized
        )

        spot_flex = FlexibilityCostModel.evaluate(
            contract_duration_days=0,
            contracted_share=0.0,
            volatility_annualized=volatility_annualized
        )

        spot_exp = MarketExposureModel.evaluate(
            spot_quantity_mt=total_requirement_mt,
            total_quantity_mt=total_requirement_mt,
            expected_spot_rate=spot_res.expected_rate,
            volatility_annualized=volatility_annualized,
            regime_type=regime_type
        )

        spot_risk = RiskAdjustedCostService.calculate_risk_adjusted_cost(
            expected_freight_cost=spot_res.expected_cost,
            total_quantity_mt=total_requirement_mt,
            spot_quantity_mt=total_requirement_mt,
            contracted_quantity_mt=0.0,
            p50_spot_rate=spot_res.p50_rate,
            p90_spot_rate=spot_res.p90_rate,
            contract_duration_days=0
        )

        spot_scenarios = [
            StrategyScenarioItem(
                scenario_name="BEAR",
                market_assumption="Spot freight curve softens by -8% with ample prompt vessel supply",
                rate=spot_res.p10_rate,
                quantity=total_requirement_mt,
                cost=spot_res.p10_cost,
                probability=0.30
            ),
            StrategyScenarioItem(
                scenario_name="BASE",
                market_assumption="TFT baseline forecast trajectory across planned voyage laycans",
                rate=spot_res.p50_rate,
                quantity=total_requirement_mt,
                cost=spot_res.p50_cost,
                probability=0.40
            ),
            StrategyScenarioItem(
                scenario_name="BULL",
                market_assumption="Spot freight curve spikes +12% under regional vessel tightness",
                rate=spot_res.p90_rate,
                quantity=total_requirement_mt,
                cost=spot_res.p90_cost,
                probability=0.30
            ),
        ]

        spot_strategy = StrategyDetail(
            strategy_type=ContractStrategyType.SPOT,
            strategy_label="Spot Single / Repeat Fixtures",
            contract_duration="Prompt Voyage by Voyage",
            voyage_count=total_voyages,
            total_quantity=total_requirement_mt,
            contracted_quantity=0.0,
            spot_quantity=total_requirement_mt,
            reference_rate=current_spot_rate,
            expected_rate=spot_res.expected_rate,
            expected_cost=spot_res.expected_cost,
            p10_cost=spot_res.p10_cost,
            p50_cost=spot_res.p50_cost,
            p90_cost=spot_res.p90_cost,
            market_exposure=spot_exp.exposure_score,
            flexibility_measure=spot_flex.flexibility_score,
            risk_adjusted_cost=spot_risk.total_risk_adjusted_cost,
            break_even_rate=None, # Pure spot is the baseline
            decision_confidence=base_confidence,
            scenarios=spot_scenarios,
            why_this_fits=[
                "Maximum operational agility with zero forward volume penalty or performance liquidated damages.",
                "Enables immediate exploitation if forward freight rates soften under current Bear regime.",
                f"Wait/Fix timing posture ({wait_fix_decision}) indicates prudent monitoring without commitment."
            ],
            key_trade_off="Maximum flexibility in exchange for 100% exposure to upside freight spike volatility."
        )

        # 3. Evaluate SHORT_TERM_MULTIPLE_VOYAGE (50% contracted, e.g. 2 voyages / ~90 days)
        short_cov = 50.0
        short_contract_rate = round(reference_contract_rate * 0.985, 2) if reference_contract_rate else round(current_spot_rate * 0.985, 2)
        short_tier = HybridContractStrategy.evaluate_coverage(
            total_requirement_mt=total_requirement_mt,
            coverage_percentage=short_cov,
            contract_rate=short_contract_rate,
            spot_expected_rate=spot_res.expected_rate,
            spot_p10_rate=spot_res.p10_rate,
            spot_p90_rate=spot_res.p90_rate,
            volatility_annualized=volatility_annualized,
            planning_horizon_days=90
        )

        short_scenarios = [
            StrategyScenarioItem(
                scenario_name="BEAR",
                market_assumption="Contracted volume locked at agreed rate; unhedged 50% captures lower spot rates",
                rate=round((short_tier.contracted_quantity_mt * short_contract_rate + short_tier.spot_quantity_mt * spot_res.p10_rate) / total_requirement_mt, 2),
                quantity=total_requirement_mt,
                cost=round((short_tier.contracted_quantity_mt * short_contract_rate + short_tier.spot_quantity_mt * spot_res.p10_rate), 2),
                probability=0.30
            ),
            StrategyScenarioItem(
                scenario_name="BASE",
                market_assumption="50% volume hedged at contract discount; 50% executed at central forecast baseline",
                rate=short_tier.blended_expected_rate,
                quantity=total_requirement_mt,
                cost=short_tier.expected_cost,
                probability=0.40
            ),
            StrategyScenarioItem(
                scenario_name="BULL",
                market_assumption="Contracted volume limits total cost surge; unhedged 50% absorbs market spike",
                rate=round((short_tier.contracted_quantity_mt * short_contract_rate + short_tier.spot_quantity_mt * spot_res.p90_rate) / total_requirement_mt, 2),
                quantity=total_requirement_mt,
                cost=round((short_tier.contracted_quantity_mt * short_contract_rate + short_tier.spot_quantity_mt * spot_res.p90_rate), 2),
                probability=0.30
            ),
        ]

        short_strategy = StrategyDetail(
            strategy_type=ContractStrategyType.SHORT_TERM_MULTIPLE_VOYAGE,
            strategy_label="Short-Term Multi-Voyage (COA)",
            contract_duration="90 Days (2-3 Voyages)",
            voyage_count=max(2, int(round(total_voyages * 0.5))),
            total_quantity=total_requirement_mt,
            contracted_quantity=short_tier.contracted_quantity_mt,
            spot_quantity=short_tier.spot_quantity_mt,
            reference_rate=short_contract_rate,
            expected_rate=short_tier.blended_expected_rate,
            expected_cost=short_tier.expected_cost,
            p10_cost=short_tier.p10_cost,
            p90_cost=short_tier.p90_cost,
            p50_cost=short_tier.expected_cost,
            market_exposure=short_tier.market_exposure,
            flexibility_measure=short_tier.flexibility_measure,
            risk_adjusted_cost=short_tier.risk_adjusted_cost,
            break_even_rate=short_contract_rate,
            decision_confidence=base_confidence,
            scenarios=short_scenarios,
            why_this_fits=[
                f"Secures vessel availability for 2 guaranteed voyages ({short_tier.contracted_quantity_mt:,.0f} MT) while retaining spot flexibility for remainder.",
                "Captures 1.5% multi-voyage volume concession without committing full semi-annual requirement.",
                "Ideal balance when regime transition probability from Bear to Bull is uncertain."
            ],
            key_trade_off="Half portfolio hedged against spikes; half unhedged allowing downside spot capture."
        )

        # 4. Evaluate MEDIUM_TERM_MULTIPLE_VOYAGE (100% contracted, 4+ voyages / ~180 days)
        med_cov = 100.0
        med_contract_rate = round(reference_contract_rate * 0.970, 2) if reference_contract_rate else round(current_spot_rate * 0.970, 2)
        med_tier = HybridContractStrategy.evaluate_coverage(
            total_requirement_mt=total_requirement_mt,
            coverage_percentage=med_cov,
            contract_rate=med_contract_rate,
            spot_expected_rate=spot_res.expected_rate,
            spot_p10_rate=spot_res.p10_rate,
            spot_p90_rate=spot_res.p90_rate,
            volatility_annualized=volatility_annualized,
            planning_horizon_days=180
        )

        med_scenarios = [
            StrategyScenarioItem(
                scenario_name="BEAR",
                market_assumption="Full tonnage locked at contracted rate; no benefit if spot softens further",
                rate=med_contract_rate,
                quantity=total_requirement_mt,
                cost=med_tier.expected_cost,
                probability=0.30
            ),
            StrategyScenarioItem(
                scenario_name="BASE",
                market_assumption="Full requirement executed at guaranteed 3.0% multi-voyage volume concession",
                rate=med_contract_rate,
                quantity=total_requirement_mt,
                cost=med_tier.expected_cost,
                probability=0.40
            ),
            StrategyScenarioItem(
                scenario_name="BULL",
                market_assumption="Complete insulation from market surges; 100% tonnage protected at fixed rate",
                rate=med_contract_rate,
                quantity=total_requirement_mt,
                cost=med_tier.expected_cost,
                probability=0.30
            ),
        ]

        med_strategy = StrategyDetail(
            strategy_type=ContractStrategyType.MEDIUM_TERM_MULTIPLE_VOYAGE,
            strategy_label="Medium-Term Multi-Voyage (COA)",
            contract_duration="180 Days (4+ Voyages)",
            voyage_count=total_voyages,
            total_quantity=total_requirement_mt,
            contracted_quantity=total_requirement_mt,
            spot_quantity=0.0,
            reference_rate=med_contract_rate,
            expected_rate=med_contract_rate,
            expected_cost=med_tier.expected_cost,
            p10_cost=med_tier.expected_cost,
            p50_cost=med_tier.expected_cost,
            p90_cost=med_tier.expected_cost,
            market_exposure=med_tier.market_exposure,
            flexibility_measure=med_tier.flexibility_measure,
            risk_adjusted_cost=med_tier.risk_adjusted_cost,
            break_even_rate=med_contract_rate,
            decision_confidence=base_confidence,
            scenarios=med_scenarios,
            why_this_fits=[
                f"Full 180-day supply chain certainty for {total_requirement_mt:,.0f} MT with guaranteed vessel scheduling.",
                "Completely eliminates future spot freight volatility and surge exposure.",
                "Commands maximum multi-voyage commitment discount (3.0% below spot benchmark)."
            ],
            key_trade_off="Complete price certainty in exchange for forfeiture of spot softening benefits and laycan rigidity."
        )

        # 5. Scenario Matrix
        scenario_matrix = [
            ScenarioMatrixCell(strategy_type=ContractStrategyType.SPOT, scenario_name="BEAR", freight_rate_usd_pmt=spot_res.p10_rate, freight_cost_usd=spot_res.p10_cost, market_assumption="Spot curve softens -8% with vessel surplus"),
            ScenarioMatrixCell(strategy_type=ContractStrategyType.SPOT, scenario_name="BASE", freight_rate_usd_pmt=spot_res.p50_rate, freight_cost_usd=spot_res.p50_cost, market_assumption="TFT central forecast baseline"),
            ScenarioMatrixCell(strategy_type=ContractStrategyType.SPOT, scenario_name="BULL", freight_rate_usd_pmt=spot_res.p90_rate, freight_cost_usd=spot_res.p90_cost, market_assumption="Spot curve spikes +12% under regional congestion"),
            ScenarioMatrixCell(strategy_type=ContractStrategyType.SHORT_TERM_MULTIPLE_VOYAGE, scenario_name="BEAR", freight_rate_usd_pmt=short_scenarios[0].rate, freight_cost_usd=short_scenarios[0].cost, market_assumption="50% contracted, 50% captures softening spot"),
            ScenarioMatrixCell(strategy_type=ContractStrategyType.SHORT_TERM_MULTIPLE_VOYAGE, scenario_name="BASE", freight_rate_usd_pmt=short_scenarios[1].rate, freight_cost_usd=short_scenarios[1].cost, market_assumption="50% contracted, 50% central forecast"),
            ScenarioMatrixCell(strategy_type=ContractStrategyType.SHORT_TERM_MULTIPLE_VOYAGE, scenario_name="BULL", freight_rate_usd_pmt=short_scenarios[2].rate, freight_cost_usd=short_scenarios[2].cost, market_assumption="50% contracted dampens freight surge"),
            ScenarioMatrixCell(strategy_type=ContractStrategyType.MEDIUM_TERM_MULTIPLE_VOYAGE, scenario_name="BEAR", freight_rate_usd_pmt=med_contract_rate, freight_cost_usd=med_tier.expected_cost, market_assumption="100% contracted locks rate without capturing decline"),
            ScenarioMatrixCell(strategy_type=ContractStrategyType.MEDIUM_TERM_MULTIPLE_VOYAGE, scenario_name="BASE", freight_rate_usd_pmt=med_contract_rate, freight_cost_usd=med_tier.expected_cost, market_assumption="100% contracted captures 3.0% volume discount"),
            ScenarioMatrixCell(strategy_type=ContractStrategyType.MEDIUM_TERM_MULTIPLE_VOYAGE, scenario_name="BULL", freight_rate_usd_pmt=med_contract_rate, freight_cost_usd=med_tier.expected_cost, market_assumption="100% contracted provides complete spike immunity"),
        ]

        # 6. Break-Even Analysis
        break_even = BreakEvenService.calculate_break_even(
            current_spot_rate=current_spot_rate,
            contract_reference_rate=med_contract_rate,
            total_quantity_mt=total_requirement_mt,
            planning_horizon_days=planning_horizon_days
        )

        # 7. Hybrid Coverage Spectrum
        coverage_spectrum = HybridContractStrategy.generate_standard_tiers(
            total_requirement_mt=total_requirement_mt,
            contract_rate=med_contract_rate,
            spot_expected_rate=spot_res.expected_rate,
            spot_p10_rate=spot_res.p10_rate,
            spot_p90_rate=spot_res.p90_rate,
            volatility_annualized=volatility_annualized,
            planning_horizon_days=planning_horizon_days
        )

        # 8. Provenance & Metadata
        provenance = {
            "forecasting_model": "TFT-v1.0.0",
            "market_regime_model": "HMM-Gaussian-v1.0.0",
            "wait_fix_model": "WAIT_FIX_V1.0",
            "dataset_version": "FREIGHT-SYNTH-2026-Q1",
            "contract_strategy_model": "CONTRACT_STRATEGY_V1.0",
            "data_status": DataStatusType.SYNTHETIC,
            "port_validation_status": port_feasibility,
            "reference_contract_rate_status": "AVAILABLE" if reference_contract_rate else "REFERENCE_RATE_UNAVAILABLE"
        }

        return ContractEngineAnalysisResult(
            cargo_request_id=cargo_request_id,
            trade_lane=f"{origin_port_id} -> {destination_port_id}",
            origin_port_id=origin_port_id,
            destination_port_id=destination_port_id,
            cargo_type=cargo_type,
            total_requirement_mt=total_requirement_mt,
            parcel_size_mt=parcel_size_mt,
            vessel_class=vessel_class,
            planning_horizon_days=planning_horizon_days,
            voyage_plan=voyage_plan,
            strategies={
                "SPOT": spot_strategy,
                "SHORT_TERM_MULTIPLE_VOYAGE": short_strategy,
                "MEDIUM_TERM_MULTIPLE_VOYAGE": med_strategy,
            },
            scenario_matrix=scenario_matrix,
            break_even_analysis=break_even,
            coverage_spectrum=coverage_spectrum,
            port_feasibility_status=port_feasibility,
            data_provenance=provenance,
            decision_confidence=base_confidence,
            created_at=datetime.now(timezone.utc).isoformat()
        )
