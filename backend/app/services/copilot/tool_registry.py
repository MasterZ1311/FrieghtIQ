from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.schemas.copilot import ToolDefinitionSchema


class CopilotToolRegistry:
    """
    Central registry for all analytical tools accessible to the AI Chartering Copilot.
    Defines tools, schemas, operational permissions, timeouts, and required inputs.
    Strictly enforces READ and ANALYZE permissions; rejects destructive WRITE actions.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinitionSchema] = {}
        self._register_default_tools()

    def register_tool(self, tool: ToolDefinitionSchema):
        self._tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[ToolDefinitionSchema]:
        return self._tools.get(tool_name)

    def list_tools(self) -> List[ToolDefinitionSchema]:
        return list(self._tools.values())

    def validate_permission(self, tool_name: str) -> bool:
        """
        Ensures the tool does not violate Phase 12 read/analyze security boundaries.
        Returns False if the tool is registered as a WRITE action.
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return False
        return tool.permission in ["READ", "ANALYZE"]

    def _register_default_tools(self):
        # 1. CARGO TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="get_cargo_requirement",
            description="Retrieve cargo requirement particulars (commodity, quantity, laycan, load/discharge ports).",
            input_schema={"cargo_id": "Optional[str] (e.g. CR-2026-001 or UUID)"},
            output_schema={"cargo": "CargoRequirement details", "status": "DataStatusType"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["cargo_id or active session cargo"],
            source="CARGO_REPOSITORY",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="create_cargo_requirement",
            description="Simulate/preview a cargo requirement. (Restricted in Phase 12; non-persistent preview only).",
            input_schema={"title": "str", "cargo_type": "str", "quantity_mt": "float", "load_port_id": "str", "discharge_port_id": "str"},
            output_schema={"preview": "CargoRequirement preview", "status": "DEMO"},
            permission="WRITE", # Explicitly marked WRITE to test/enforce permission blocker
            timeout_sec=5,
            data_requirements=["cargo particulars"],
            source="CARGO_REPOSITORY",
        ))

        # 2. VESSEL TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="search_vessels",
            description="Query active and snapshot fleet vessels matching vessel class, status, or DWT range.",
            input_schema={"vessel_class": "Optional[str]", "status": "Optional[str]", "limit": "int"},
            output_schema={"vessels": "List of vessels", "total": "int"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["fleet database"],
            source="VESSEL_REPOSITORY",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_vessel",
            description="Retrieve detailed vessel particulars, capacity, speed-consumption benchmarks, and status.",
            input_schema={"vessel_id": "str (UUID or IMO)"},
            output_schema={"vessel": "Vessel details", "particulars": "VesselParticulars"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["vessel_id"],
            source="VESSEL_REPOSITORY",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="match_vessels",
            description="Run deterministic vessel matching engine for a cargo requirement against available tonnage.",
            input_schema={"cargo_id": "str", "top_n": "int"},
            output_schema={"candidates": "List of scored vessels", "rules_evaluated": "List of rule outcomes"},
            permission="ANALYZE",
            timeout_sec=10,
            data_requirements=["cargo_id"],
            source="VESSEL_MATCHING_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_vessel_employment",
            description="Retrieve vessel employment history, current status, and next scheduled commitment.",
            input_schema={"vessel_id": "str"},
            output_schema={"events": "List of employment events", "current_state": "VesselEmploymentState"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["vessel_id"],
            source="IDLE_REPOSITIONING_REPOSITORY",
        ))

        # 3. PORT TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="get_port",
            description="Retrieve port master record, UN/LOCODE, coordinates, and tidal regime.",
            input_schema={"port_id_or_code": "str (UUID or UN/LOCODE e.g. INPRT, AUNCL)"},
            output_schema={"port": "Port details", "berths_count": "int"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["port_id or unlocode"],
            source="PORT_REPOSITORY",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_port_constraints",
            description="Retrieve physical constraints (max draft, max beam, max LOA, air draft, tidal window) for a port.",
            input_schema={"port_id": "str"},
            output_schema={"constraints": "List of PortConstraints"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["port_id"],
            source="PORT_REPOSITORY",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_port_berths",
            description="Retrieve berths and berth-specific limitations for a discharge/load port.",
            input_schema={"port_id": "str"},
            output_schema={"berths": "List of Berths and constraints"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["port_id"],
            source="PORT_REPOSITORY",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="evaluate_vessel_port",
            description="Evaluate combinatorial vessel-port geometric compatibility (draft, LOA, beam, DWT limits).",
            input_schema={"vessel_id": "str", "port_id": "str", "cargo_quantity_mt": "Optional[float]"},
            output_schema={"status": "FEASIBLE | CONDITIONAL | INFEASIBLE", "rule_evaluations": "List"},
            permission="ANALYZE",
            timeout_sec=10,
            data_requirements=["vessel_id", "port_id"],
            source="VESSEL_PORT_OPTIMIZER_SERVICE",
        ))

        # 4. FREIGHT TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="get_freight_forecast",
            description="Retrieve multi-horizon probabilistic freight rate forecast (P10, P50, P90 in USD/MT).",
            input_schema={"origin_port_id": "str", "destination_port_id": "str", "horizon_days": "Optional[int]"},
            output_schema={"p10": "float", "p50": "float", "p90": "float", "model_version": "str", "data_status": "DataStatusType"},
            permission="READ",
            timeout_sec=8,
            data_requirements=["origin_port_id", "destination_port_id"],
            source="FREIGHT_FORECAST_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_freight_backtest",
            description="Retrieve backtesting validation metrics (MAE, RMSE, MAPE) for the freight forecasting model.",
            input_schema={"origin_port_id": "str", "destination_port_id": "str"},
            output_schema={"metrics": "Dict of error metrics", "walk_forward_window": "str"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["origin_port_id", "destination_port_id"],
            source="FREIGHT_REPOSITORY",
        ))

        # 5. REGIME TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="get_market_regime",
            description="Retrieve current Gaussian Hidden Markov Model (HMM) market regime and state probabilities.",
            input_schema={"route_id": "Optional[str]"},
            output_schema={"current_regime": "BEAR | BASE | BULL", "probabilities": "Dict", "alignment": "ForecastRegimeAlignment"},
            permission="READ",
            timeout_sec=6,
            data_requirements=["market regime model"],
            source="MARKET_REGIME_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_regime_history",
            description="Retrieve historical market regime sequence and regime transition matrix.",
            input_schema={"limit": "int"},
            output_schema={"history": "List of regime points", "transitions": "Dict"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["regime history"],
            source="MARKET_REGIME_SERVICE",
        ))

        # 6. WAIT/FIX TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="analyze_wait_fix",
            description="Run Wait vs Fix decision engine analyzing expected market evolution, waiting cost, and option value.",
            input_schema={"cargo_id": "str", "vessel_id": "Optional[str]"},
            output_schema={"decision": "WAIT | FIX_NOW | MONITOR", "confidence": "DecisionConfidence", "expected_savings_usd": "float"},
            permission="ANALYZE",
            timeout_sec=10,
            data_requirements=["cargo_id"],
            source="WAIT_FIX_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_wait_fix_scenarios",
            description="Retrieve discretized LOW, CENTRAL, and HIGH scenario outcomes from the latest Wait/Fix run.",
            input_schema={"analysis_id": "Optional[str]"},
            output_schema={"scenarios": "List of scenario outcomes"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["analysis_id or latest"],
            source="WAIT_FIX_SERVICE",
        ))

        # 7. CONTRACT TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="analyze_contract_strategy",
            description="Evaluate SPOT vs SHORT_TERM_MULTIPLE_VOYAGE vs MEDIUM_TERM charter party contract structures.",
            input_schema={"cargo_id": "str", "volume_mt": "Optional[float]"},
            output_schema={"recommended_strategy": "ContractStrategyType", "expected_total_expenditure_usd": "float"},
            permission="ANALYZE",
            timeout_sec=10,
            data_requirements=["cargo_id or volume"],
            source="CONTRACT_STRATEGY_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_contract_comparison",
            description="Retrieve side-by-side risk-adjusted cost comparison across chartering contract structures.",
            input_schema={"strategy_id": "Optional[str]"},
            output_schema={"comparison": "List of contract strategy options"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["strategy_id or latest"],
            source="CONTRACT_STRATEGY_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_contract_break_even",
            description="Calculate freight rate break-even threshold between spot chartering and multi-voyage commitment.",
            input_schema={"spot_rate": "float", "forward_rate": "float", "duration_days": "float"},
            output_schema={"break_even_rate_usd_pmt": "float", "indifference_horizon_days": "float"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["spot_rate", "forward_rate"],
            source="CONTRACT_STRATEGY_SERVICE",
        ))

        # 8. IDLE TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="analyze_idle",
            description="Calculate idle exposure, holding cost, and alternative employment evaluation for waiting vessels.",
            input_schema={"vessel_id": "str", "days_idle": "float"},
            output_schema={"daily_idle_cost_usd": "float", "total_idle_cost_usd": "float"},
            permission="ANALYZE",
            timeout_sec=8,
            data_requirements=["vessel_id"],
            source="IDLE_REPOSITIONING_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="analyze_repositioning",
            description="Analyze ballast repositioning economics (deadhead distance, fuel cost, opportunity loss).",
            input_schema={"vessel_id": "str", "current_port_id": "str", "target_port_id": "str"},
            output_schema={"decision": "REPOSITION | DO_NOT_REPOSITION", "ballast_distance_nm": "float", "repositioning_cost_usd": "float"},
            permission="ANALYZE",
            timeout_sec=10,
            data_requirements=["vessel_id", "ports"],
            source="IDLE_REPOSITIONING_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_employment_timeline",
            description="Retrieve operational and commercial timeline events for a vessel.",
            input_schema={"vessel_id": "str"},
            output_schema={"timeline": "List of employment events"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["vessel_id"],
            source="IDLE_REPOSITIONING_SERVICE",
        ))

        # 9. RISK TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="get_voyage_risk",
            description="Retrieve unified voyage operational risk summary (congestion, weather, tidal, timing risks).",
            input_schema={"origin_port_id": "str", "destination_port_id": "str", "vessel_id": "Optional[str]"},
            output_schema={"overall_severity": "RiskSeverity", "active_risks_count": "int", "events": "List"},
            permission="READ",
            timeout_sec=6,
            data_requirements=["ports"],
            source="OPERATIONAL_RISK_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="analyze_weather",
            description="Analyze severe weather exposure, Beaufort wind force, wave heights, and port stoppage risk.",
            input_schema={"port_id": "str"},
            output_schema={"weather_severity": "RiskSeverity", "wind_speed_knots": "float", "wave_height_m": "float"},
            permission="ANALYZE",
            timeout_sec=6,
            data_requirements=["port_id"],
            source="OPERATIONAL_RISK_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="analyze_congestion",
            description="Analyze port congestion, queue count, average waiting days, and expected demurrage exposure.",
            input_schema={"port_id": "str"},
            output_schema={"congestion_indicator": "CongestionIndicator", "queue_vessel_count": "int", "avg_waiting_days": "float"},
            permission="ANALYZE",
            timeout_sec=6,
            data_requirements=["port_id"],
            source="OPERATIONAL_RISK_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="evaluate_tidal",
            description="Evaluate tidal gate clearance, under-keel clearance (UKC), and tide restriction windows.",
            input_schema={"port_id": "str", "vessel_draft_m": "float"},
            output_schema={"tidal_status": "TidalWindowStatus", "max_safe_draft_m": "float", "next_gate_hours": "float"},
            permission="ANALYZE",
            timeout_sec=6,
            data_requirements=["port_id", "draft"],
            source="OPERATIONAL_RISK_SERVICE",
        ))

        # 10. ECONOMICS TOOLS
        self.register_tool(ToolDefinitionSchema(
            name="analyze_voyage_economics",
            description="Compute itemized voyage economics: freight, bunker, port dues, time charter, demurrage, $/MT.",
            input_schema={"origin_port_id": "str", "destination_port_id": "str", "cargo_quantity_mt": "float", "vessel_id": "Optional[str]"},
            output_schema={"total_voyage_cost_usd": "float", "cost_per_mt": "float", "breakdown": "Dict", "data_status": "DataStatusType"},
            permission="ANALYZE",
            timeout_sec=12,
            data_requirements=["ports", "cargo_quantity"],
            source="VOYAGE_ECONOMICS_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="analyze_speed",
            description="Generate hydrodynamic cubic speed scenarios (8-14 kts) and identify economically preferred speed.",
            input_schema={"vessel_id": "Optional[str]", "distance_nm": "float", "hire_rate_usd_day": "Optional[float]", "bunker_price_usd_mt": "Optional[float]"},
            output_schema={"preferred_speed_knots": "Optional[float]", "scenarios": "List", "verdict": "str"},
            permission="ANALYZE",
            timeout_sec=8,
            data_requirements=["distance_nm"],
            source="SPEED_SCENARIO_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="analyze_sensitivity",
            description="Evaluate economic sensitivity to bunker price, freight rate, vessel speed, and port delay swings.",
            input_schema={"analysis_id": "Optional[str]", "bunker_delta_pct": "Optional[float]", "freight_delta_pct": "Optional[float]"},
            output_schema={"adjusted_cost_usd": "float", "adjusted_cost_per_mt": "float", "elasticity": "Dict"},
            permission="ANALYZE",
            timeout_sec=8,
            data_requirements=["analysis_id or base economics"],
            source="SENSITIVITY_SERVICE",
        ))

        self.register_tool(ToolDefinitionSchema(
            name="get_speed_scenarios",
            description="Retrieve evaluated speed scenarios and Admiralty formula calculations for a voyage analysis.",
            input_schema={"analysis_id": "str"},
            output_schema={"speed_scenarios": "List of evaluated speed points"},
            permission="READ",
            timeout_sec=5,
            data_requirements=["analysis_id"],
            source="VOYAGE_ECONOMICS_REPOSITORY",
        ))
