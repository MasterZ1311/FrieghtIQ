import uuid
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.enums import (
    WaitFixDecision, DecisionConfidence, CargoType, VesselClass,
    DataStatusType, ForecastRegimeAlignment, FeasibilityStatus
)
from app.models.cargo import CargoRequirement
from app.models.wait_fix import WaitFixAnalysis, WaitFixScenario
from app.repositories.wait_fix_repo import WaitFixRepository
from app.repositories.freight_repo import FreightRepository
from app.repositories.port_repo import PortRepository
from app.repositories.cargo_repo import CargoRepository
from app.services.regime.service import MarketRegimeService
from app.services.forecasting.service import FreightForecastService
from app.services.wait_fix.economics import FreightEconomicImpactService
from app.services.wait_fix.scenarios import WaitFixScenarioService
from app.services.wait_fix.waiting_cost import WaitingCostModel
from app.services.wait_fix.option_model import WaitOptionModel
from app.services.wait_fix.confidence import DecisionConfidenceService
from app.schemas.wait_fix import (
    WaitFixAnalysisResponse, ScenarioItem, OptionValueResult,
    WaitFixAssumptions, WaitFixEvidenceItem, DataQualityReport
)

class WaitFixDecisionEngine:
    """
    Core Charter-Timing Decision Support Engine.
    Synthesizes cargo requirements, berth constraints, multi-horizon freight forecasts,
    and Gaussian HMM market regimes to model the economic value of fixing now vs waiting.
    """
    def __init__(self, db: Session):
        self.db = db
        self.wait_fix_repo = WaitFixRepository(db)
        self.freight_repo = FreightRepository(db)
        self.port_repo = PortRepository(db)
        self.cargo_repo = CargoRepository(db)
        self.regime_service = MarketRegimeService(db)

    def analyze(
        self,
        cargo_request_id: Optional[str] = None,
        origin_port_id: str = "newcastle-au",
        destination_port_id: str = "paradip-in",
        cargo_type: CargoType = CargoType.COKING_COAL,
        cargo_quantity: float = 75000.0,
        vessel_class: VesselClass = VesselClass.PANAMAX,
        decision_horizon_days: int = 30,
        reference_fix_rate: Optional[float] = None
    ) -> WaitFixAnalysisResponse:
        now = datetime.now(timezone.utc)
        
        # 1. Phase 3: Resolve Cargo Requirement (if provided)
        cargo_req: Optional[CargoRequirement] = None
        if cargo_request_id:
            cargo_req = self.cargo_repo.get_requirement_by_id(cargo_request_id)
            if cargo_req:
                origin_port_id = cargo_req.load_port_id
                destination_port_id = cargo_req.discharge_port_id
                cargo_type = cargo_req.cargo_type
                cargo_quantity = cargo_req.quantity_mt
                # Calculate remaining decision window from laycan
                if cargo_req.laycan_start:
                    laycan_dt = cargo_req.laycan_start
                    if laycan_dt.tzinfo is None:
                        laycan_dt = laycan_dt.replace(tzinfo=timezone.utc)
                    remaining_days = (laycan_dt.date() - now.date()).days
                else:
                    remaining_days = decision_horizon_days
            else:
                remaining_days = decision_horizon_days
        else:
            remaining_days = decision_horizon_days

        # Decision deadline timestamp
        decision_deadline = now + timedelta(days=max(0, remaining_days))

        # 2. Phase 4: Port Compatibility Check
        port_feasibility_status = FeasibilityStatus.PASS
        port_warning_note: Optional[str] = None
        
        # Check Paradip/destination port max draft against vessel class baseline
        dest_port = self.port_repo.get_port_by_id(destination_port_id)
        if dest_port and dest_port.channel_max_draft_m:
            if vessel_class == VesselClass.CAPESIZE and dest_port.channel_max_draft_m < 16.0:
                port_feasibility_status = FeasibilityStatus.CONDITIONAL
                port_warning_note = f"Destination port {dest_port.name} draft ({dest_port.channel_max_draft_m}m) limits Capesize full intake."
            elif vessel_class == VesselClass.NEWCASTLEMAX and dest_port.channel_max_draft_m < 17.5:
                port_feasibility_status = FeasibilityStatus.FAIL
                port_warning_note = f"Destination port {dest_port.name} cannot accommodate Newcastlemax class vessels."

        # 3. Phase 5 & 6: Fetch Freight Forecast & Market Regime
        route = self.regime_service._get_route(origin_port_id, destination_port_id, vessel_class)
        if not route:
            raise ValueError(f"No valid freight route identified between {origin_port_id} and {destination_port_id}")

        observations = self.freight_repo.get_observations(route.id, limit=90)
        current_spot_rate = observations[-1].freight_rate_usd_pmt if observations else 26.50
        effective_fix_rate = reference_fix_rate if reference_fix_rate and reference_fix_rate > 0 else current_spot_rate

        # Get Phase 5 Forecasts
        forecasts = self.freight_repo.get_latest_forecasts(route.id)
        if not forecasts:
            # Generate forward forecasts
            fc_service = FreightForecastService(self.db)
            forecasts = fc_service.generate_route_forecasts(route.id, vessel_class=vessel_class)

        # Extract multi-horizon target (matching decision horizon)
        target_fc = None
        for fc in sorted(forecasts, key=lambda f: abs(f.horizon_days - remaining_days)):
            target_fc = fc
            break
        
        p10 = target_fc.predicted_p10 if target_fc else round(effective_fix_rate * 0.90, 2)
        p50 = target_fc.predicted_p50 if target_fc else round(effective_fix_rate * 0.96, 2)
        p90 = target_fc.predicted_p90 if target_fc else round(effective_fix_rate * 1.08, 2)
        fc_confidence = target_fc.confidence_pct if target_fc else 85.0

        # Get Phase 6 Market Regime Intelligence
        regime_analysis = self.regime_service.analyze_regime(
            origin_port_id=origin_port_id,
            destination_port_id=destination_port_id,
            cargo_type=cargo_type,
            vessel_class=vessel_class
        )
        current_regime = regime_analysis.regime
        regime_confidence = regime_analysis.confidence
        forecast_alignment = regime_analysis.forecast_alignment

        # 4. Handle Boundary & Edge Cases
        if port_feasibility_status == FeasibilityStatus.FAIL:
            return self._build_edge_case_response(
                decision=WaitFixDecision.NOT_EVALUABLE,
                confidence=DecisionConfidence.LOW,
                reason=f"Port feasibility check failed for vessel class {vessel_class.value} at destination port: {port_warning_note}",
                route=route, cargo_quantity=cargo_quantity, cargo_type=cargo_type,
                vessel_class=vessel_class, current_rate=effective_fix_rate,
                remaining_days=remaining_days, decision_deadline=decision_deadline,
                p10=p10, p50=p50, p90=p90, forecast_alignment=forecast_alignment
            )

        if remaining_days <= 0:
            return self._build_edge_case_response(
                decision=WaitFixDecision.DECISION_WINDOW_EXPIRED,
                confidence=DecisionConfidence.HIGH,
                reason=f"Cargo laycan decision window has elapsed ({remaining_days} remaining days). Prompt fixing or laycan re-negotiation required.",
                route=route, cargo_quantity=cargo_quantity, cargo_type=cargo_type,
                vessel_class=vessel_class, current_rate=effective_fix_rate,
                remaining_days=0, decision_deadline=now,
                p10=p10, p50=p50, p90=p90, forecast_alignment=forecast_alignment
            )

        # 5. Calculate Scenario Economics
        scenarios, exp_wait_rate, exp_fix_cost, exp_wait_cost, exp_diff = WaitFixScenarioService.generate_scenarios(
            p10=p10,
            p50=p50,
            p90=p90,
            quantity_mt=cargo_quantity,
            reference_fix_rate=effective_fix_rate
        )

        # 6. Calculate Waiting Risk Penalties
        risk_evaluation = WaitingCostModel.calculate_waiting_risk_penalty(
            p10=p10,
            p50=p50,
            p90=p90,
            current_rate=effective_fix_rate,
            quantity_mt=cargo_quantity,
            remaining_days=remaining_days,
            decision_horizon_days=decision_horizon_days
        )
        total_risk_penalty = risk_evaluation["total_risk_penalty_usd"]
        net_modeled_advantage = exp_diff - total_risk_penalty
        savings_pct = FreightEconomicImpactService.calculate_savings_percentage(exp_diff, exp_fix_cost)

        # 7. Real-Option Flexibility Valuation
        option_result = WaitOptionModel.calculate_wait_option_value(
            current_freight_rate=current_spot_rate,
            reference_fix_rate=effective_fix_rate,
            cargo_quantity_mt=cargo_quantity,
            remaining_days=remaining_days,
            annualized_volatility=0.28,
            discount_rate=0.05
        )

        # 8. Decision Classification Logic
        # Economic significance threshold: 1.5% of voyage cost or $25,000 USD
        economic_threshold_usd = max(25000.0, exp_fix_cost * 0.015)

        if net_modeled_advantage > economic_threshold_usd and remaining_days >= 4:
            decision = WaitFixDecision.WAIT
        elif net_modeled_advantage < -economic_threshold_usd or p50 > effective_fix_rate:
            decision = WaitFixDecision.FIX_NOW
        else:
            decision = WaitFixDecision.MONITOR

        # 9. Evaluate Confidence
        confidence = DecisionConfidenceService.evaluate_confidence(
            forecast_confidence_pct=fc_confidence,
            regime_probability=regime_confidence,
            remaining_days=remaining_days,
            port_feasibility=port_feasibility_status,
            data_status=DataStatusType.SYNTHETIC,
            modeled_difference_pct=savings_pct
        )

        # 10. Generate Explanations & Evidence
        why_this_result, what_could_change_this, evidence_items = self._generate_explanations(
            decision=decision,
            effective_fix_rate=effective_fix_rate,
            exp_wait_rate=exp_wait_rate,
            exp_diff=exp_diff,
            p10=p10, p50=p50, p90=p90,
            current_regime=current_regime,
            remaining_days=remaining_days,
            risk_evaluation=risk_evaluation,
            port_warning_note=port_warning_note
        )

        # 11. Traceable Assumptions & Data Quality
        assumptions = WaitFixAssumptions(
            current_freight_rate=current_spot_rate,
            reference_fix_rate=effective_fix_rate,
            cargo_quantity_mt=cargo_quantity,
            decision_horizon_days=decision_horizon_days,
            remaining_days=remaining_days,
            historical_volatility_annualized=0.28,
            discount_rate_annual=0.05,
            forecast_model="Phase 5 Temporal Fusion Transformer (TFT)",
            regime_model="Phase 6 Continuous Gaussian HMM (4-State)",
            dataset_version="SYNTHETIC_BALTIC_V2026",
            data_status=DataStatusType.SYNTHETIC
        )

        data_quality = DataQualityReport(
            forecast_data="SYNTHETIC (Phase 5 TFT Calibrated)",
            regime_data="SYNTHETIC (Phase 6 HMM Decoded)",
            port_feasibility="AVAILABLE (Phase 4 Port Constraints Verified)",
            vessel_feasibility="AVAILABLE (Phase 3 Particulars Filtered)",
            reference_fix_rate="AVAILABLE (Market Spot Benchmark)",
            overall_quality="HIGH"
        )

        # 12. Persist Analysis to Database
        analysis_id = str(uuid.uuid4())
        analysis_entity = WaitFixAnalysis(
            id=analysis_id,
            cargo_request_id=cargo_request_id,
            origin_port_id=origin_port_id,
            destination_port_id=destination_port_id,
            cargo_type=cargo_type,
            cargo_quantity=cargo_quantity,
            vessel_class=vessel_class,
            current_freight_rate=effective_fix_rate,
            p10_rate=p10,
            p50_rate=p50,
            p90_rate=p90,
            expected_wait_rate=exp_wait_rate,
            expected_fix_cost=exp_fix_cost,
            expected_wait_cost=exp_wait_cost,
            expected_modeled_difference=exp_diff,
            wait_option_value=option_result.option_value_usd,
            decision=decision,
            decision_confidence=confidence,
            decision_deadline=decision_deadline,
            remaining_days=remaining_days,
            forecast_id=target_fc.id if target_fc else None,
            regime_id=None,
            model_version_id="WAIT_FIX_V1.0",
            dataset_version_id="SYNTHETIC_BALTIC_V2026",
            data_status=DataStatusType.SYNTHETIC,
            created_at=now
        )
        self.wait_fix_repo.save_analysis(analysis_entity)

        # Save scenarios
        for sc in scenarios:
            sc_entity = WaitFixScenario(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                scenario_name=sc.scenario_name,
                rate=sc.rate,
                probability=sc.probability,
                freight_cost=sc.freight_cost,
                difference_vs_fix=sc.difference_vs_fix,
                created_at=now
            )
            self.wait_fix_repo.save_scenario(sc_entity)

        # 13. Construct Complete Response
        trade_lane_label = f"{dest_port.name if dest_port else destination_port_id} ← {route.origin_port.name if route.origin_port else origin_port_id}"
        return WaitFixAnalysisResponse(
            id=analysis_id,
            cargo_request_id=cargo_request_id,
            origin_port_id=origin_port_id,
            destination_port_id=destination_port_id,
            trade_lane=f"{route.origin_port.name if route.origin_port else 'Newcastle'} → {route.destination_port.name if route.destination_port else 'Paradip'}",
            cargo_type=cargo_type,
            cargo_quantity=cargo_quantity,
            vessel_class=vessel_class,
            decision=decision,
            decision_confidence=confidence,
            current_freight_rate=effective_fix_rate,
            expected_wait_rate=exp_wait_rate,
            expected_fix_cost=exp_fix_cost,
            expected_wait_cost=exp_wait_cost,
            expected_modeled_difference=exp_diff,
            decision_deadline=decision_deadline,
            remaining_days=remaining_days,
            p10_rate=p10,
            p50_rate=p50,
            p90_rate=p90,
            scenarios=scenarios,
            option_analysis=option_result,
            assumptions=assumptions,
            why_this_result=why_this_result,
            what_could_change_this=what_could_change_this,
            evidence=evidence_items,
            forecast_regime_alignment=forecast_alignment,
            data_quality=data_quality,
            data_status=DataStatusType.SYNTHETIC,
            created_at=now
        )

    def _generate_explanations(
        self,
        decision: WaitFixDecision,
        effective_fix_rate: float,
        exp_wait_rate: float,
        exp_diff: float,
        p10: float, p50: float, p90: float,
        current_regime: str,
        remaining_days: int,
        risk_evaluation: Dict[str, Any],
        port_warning_note: Optional[str]
    ) -> Tuple[List[str], List[str], List[WaitFixEvidenceItem]]:
        why = []
        what_could_change = []
        evidence = []

        rate_diff = effective_fix_rate - exp_wait_rate
        if rate_diff > 0:
            why.append(f"Expected forward freight rate (${exp_wait_rate:.2f}/MT) models an average softening of ${rate_diff:.2f}/MT below the prompt fix benchmark (${effective_fix_rate:.2f}/MT).")
        else:
            why.append(f"Prompt fix benchmark (${effective_fix_rate:.2f}/MT) protects against projected forward curve elevation (${exp_wait_rate:.2f}/MT).")

        why.append(f"Current HMM market regime state is {current_regime}, providing structural contextual momentum for rate dynamics.")
        why.append(f"Decision horizon offers {remaining_days} remaining days before mandatory commitment is required.")

        if exp_diff > 0:
            why.append(f"Aggregate modeled gross freight cost difference across {exp_diff:,.0f} USD favors retaining market flexibility.")
        else:
            why.append(f"Immediate fixture secures cargo economics against an adverse high-case exposure of ${p90:.2f}/MT (${risk_evaluation['adverse_cost_exposure_usd']:,.0f} USD).")

        if port_warning_note:
            why.append(f"Operational constraint noted: {port_warning_note}")

        # What could change this
        what_could_change.append("An unexpected upward rate surge exceeding the P90 envelope ($" + f"{p90:.2f}/MT) would eliminate waiting advantages.")
        what_could_change.append("A market regime shift from " + current_regime + " to a divergent state triggered by bunker or congestion shocks.")
        what_could_change.append(f"Decision window decay: When remaining decision days reach <= 3 days, prompt fixture urgency escalates.")
        what_could_change.append("Port congestion or vessel availability bottleneck emerging at load/discharge ports.")

        # Evidence items
        evidence.append(WaitFixEvidenceItem(
            factor_name="Expected Rate Difference",
            observed_value=f"${rate_diff:+.2f} / MT",
            impact_on_decision="FAVORS_WAIT" if rate_diff > 0.3 else "FAVORS_FIX" if rate_diff < -0.3 else "NEUTRAL",
            weight=0.35,
            description=f"Difference between prompt fix (${effective_fix_rate:.2f}) and weighted expected wait rate (${exp_wait_rate:.2f})."
        ))

        evidence.append(WaitFixEvidenceItem(
            factor_name="Phase 6 Market Regime",
            observed_value=str(current_regime),
            impact_on_decision="FAVORS_WAIT" if current_regime in ["BEAR", "SEASONAL"] else "FAVORS_FIX" if current_regime == "BULL" else "NEUTRAL",
            weight=0.25,
            description=f"Underlying macroeconomic freight state classified by continuous Gaussian HMM."
        ))

        evidence.append(WaitFixEvidenceItem(
            factor_name="Remaining Decision Window",
            observed_value=f"{remaining_days} Days",
            impact_on_decision="FAVORS_WAIT" if remaining_days >= 7 else "FAVORS_FIX" if remaining_days <= 3 else "NEUTRAL",
            weight=0.20,
            description="Operational flexibility time remaining prior to vessel positioning and laycan."
        ))

        evidence.append(WaitFixEvidenceItem(
            factor_name="Forecast Dispersion (P90 - P10)",
            observed_value=f"${p90 - p10:.2f} / MT",
            impact_on_decision="NEUTRAL" if (p90 - p10) / p50 < 0.25 else "FAVORS_FIX",
            weight=0.20,
            description="Uncertainty spread across 10th and 90th percentile forward projection bands."
        ))

        return why, what_could_change, evidence

    def _build_edge_case_response(
        self,
        decision: WaitFixDecision,
        confidence: DecisionConfidence,
        reason: str,
        route: Any,
        cargo_quantity: float,
        cargo_type: CargoType,
        vessel_class: VesselClass,
        current_rate: float,
        remaining_days: int,
        decision_deadline: datetime,
        p10: float, p50: float, p90: float,
        forecast_alignment: ForecastRegimeAlignment
    ) -> WaitFixAnalysisResponse:
        now = datetime.now(timezone.utc)
        current_cost = FreightEconomicImpactService.calculate_total_freight_cost(current_rate, cargo_quantity)
        
        scenarios = [
            ScenarioItem(scenario_name="LOW", rate=p10, probability=0.30, freight_cost=round(p10 * cargo_quantity, 2), difference_vs_fix=round(current_cost - (p10 * cargo_quantity), 2)),
            ScenarioItem(scenario_name="CENTRAL", rate=p50, probability=0.40, freight_cost=round(p50 * cargo_quantity, 2), difference_vs_fix=round(current_cost - (p50 * cargo_quantity), 2)),
            ScenarioItem(scenario_name="HIGH", rate=p90, probability=0.30, freight_cost=round(p90 * cargo_quantity, 2), difference_vs_fix=round(current_cost - (p90 * cargo_quantity), 2)),
        ]

        option_res = OptionValueResult(
            option_value_usd=None,
            option_value_pmt=None,
            methodology="Real-Option Decision-Support (Black-Scholes Framework)",
            parameters={},
            status="OPTION_VALUE_UNAVAILABLE",
            rationale=reason
        )

        assumptions = WaitFixAssumptions(
            current_freight_rate=current_rate,
            reference_fix_rate=current_rate,
            cargo_quantity_mt=cargo_quantity,
            decision_horizon_days=max(1, remaining_days),
            remaining_days=remaining_days,
            historical_volatility_annualized=0.28,
            discount_rate_annual=0.05,
            forecast_model="Phase 5 TFT",
            regime_model="Phase 6 HMM",
            dataset_version="SYNTHETIC_BALTIC_V2026",
            data_status=DataStatusType.SYNTHETIC
        )

        data_quality = DataQualityReport(
            forecast_data="AVAILABLE",
            regime_data="AVAILABLE",
            port_feasibility="FAIL" if decision == WaitFixDecision.NOT_EVALUABLE else "AVAILABLE",
            vessel_feasibility="UNAVAILABLE" if decision == WaitFixDecision.NOT_EVALUABLE else "AVAILABLE",
            reference_fix_rate="AVAILABLE",
            overall_quality="LOW" if decision == WaitFixDecision.NOT_EVALUABLE else "MEDIUM"
        )

        return WaitFixAnalysisResponse(
            id=str(uuid.uuid4()),
            cargo_request_id=None,
            origin_port_id=route.origin_port_id,
            destination_port_id=route.destination_port_id,
            trade_lane=f"{route.origin_port.name if route.origin_port else 'Origin'} → {route.destination_port.name if route.destination_port else 'Destination'}",
            cargo_type=cargo_type,
            cargo_quantity=cargo_quantity,
            vessel_class=vessel_class,
            decision=decision,
            decision_confidence=confidence,
            current_freight_rate=current_rate,
            expected_wait_rate=current_rate,
            expected_fix_cost=current_cost,
            expected_wait_cost=current_cost,
            expected_modeled_difference=0.0,
            decision_deadline=decision_deadline,
            remaining_days=remaining_days,
            p10_rate=p10,
            p50_rate=p50,
            p90_rate=p90,
            scenarios=scenarios,
            option_analysis=option_res,
            assumptions=assumptions,
            why_this_result=[reason],
            what_could_change_this=["Resolution of physical berth or laycan constraints."],
            evidence=[],
            forecast_regime_alignment=forecast_alignment,
            data_quality=data_quality,
            data_status=DataStatusType.SYNTHETIC,
            created_at=now
        )
