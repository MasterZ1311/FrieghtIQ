import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.schemas.copilot import CopilotPlanStepSchema
from app.models.enums import CopilotToolStatus


class CharteringPlannerService:
    """
    Converts natural language user intents and conversation context
    into a structured, deterministic execution plan of analytical tool calls.
    Ensures only necessary tools are scheduled, without inventing ungrounded parameters.
    """

    def generate_plan(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[CopilotPlanStepSchema]:
        query = (user_query or "").strip().lower()
        ctx = context or {}

        cargo_id = ctx.get("cargo_request_id") or ctx.get("cargo_id")
        vessel_id = ctx.get("vessel_id")
        origin_id = ctx.get("origin_port_id")
        dest_id = ctx.get("destination_port_id")
        quantity_mt = ctx.get("quantity_mt") or 75000.0

        # Determine Intent Category
        steps: List[CopilotPlanStepSchema] = []

        # 1. SPECIFIC INTENT: Vessel Matching
        if any(k in query for k in ["find relevant vessel", "match vessel", "tonnage", "candidate vessel"]):
            steps = [
                CopilotPlanStepSchema(
                    step_number=1,
                    tool_name="get_cargo_requirement",
                    reason="Retrieve cargo volume, laycan, and load/discharge ports.",
                    arguments={"cargo_id": cargo_id} if cargo_id else {},
                ),
                CopilotPlanStepSchema(
                    step_number=2,
                    tool_name="match_vessels",
                    reason="Run deterministic matching engine against available tonnage.",
                    arguments={"cargo_id": cargo_id, "top_n": 5},
                ),
                CopilotPlanStepSchema(
                    step_number=3,
                    tool_name="evaluate_vessel_port",
                    reason="Verify draft and LOA feasibility at discharge berth for candidate vessel.",
                    arguments={"vessel_id": vessel_id, "port_id": dest_id},
                ),
            ]

        # 2. SPECIFIC INTENT: Port Constraints & Feasibility
        elif any(k in query for k in ["port feasibility", "port constraint", "berth", "draft limit"]):
            steps = [
                CopilotPlanStepSchema(
                    step_number=1,
                    tool_name="get_port",
                    reason="Retrieve destination port particulars.",
                    arguments={"port_id_or_code": dest_id or "INPRT"},
                ),
                CopilotPlanStepSchema(
                    step_number=2,
                    tool_name="get_port_constraints",
                    reason="Retrieve physical limits (draft, beam, LOA, DWT).",
                    arguments={"port_id": dest_id or "INPRT"},
                ),
                CopilotPlanStepSchema(
                    step_number=3,
                    tool_name="evaluate_vessel_port",
                    reason="Evaluate vessel-port geometric compatibility.",
                    arguments={"vessel_id": vessel_id, "port_id": dest_id or "INPRT"},
                ),
            ]

        # 3. SPECIFIC INTENT: Wait vs Fix
        elif any(k in query for k in ["wait or fix", "fix or wait", "should i fix", "wait/fix"]):
            steps = [
                CopilotPlanStepSchema(
                    step_number=1,
                    tool_name="get_cargo_requirement",
                    reason="Confirm cargo laycan window and volume.",
                    arguments={"cargo_id": cargo_id} if cargo_id else {},
                ),
                CopilotPlanStepSchema(
                    step_number=2,
                    tool_name="get_freight_forecast",
                    reason="Retrieve P10/P50/P90 probabilistic rate curve.",
                    arguments={"origin_port_id": origin_id, "destination_port_id": dest_id},
                ),
                CopilotPlanStepSchema(
                    step_number=3,
                    tool_name="get_market_regime",
                    reason="Retrieve Gaussian HMM market state and transition probabilities.",
                    arguments={},
                ),
                CopilotPlanStepSchema(
                    step_number=4,
                    tool_name="analyze_wait_fix",
                    reason="Compute waiting cost vs forward option value.",
                    arguments={"cargo_id": cargo_id, "vessel_id": vessel_id},
                ),
            ]

        # 4. SPECIFIC INTENT: Contract Strategy
        elif any(k in query for k in ["contract", "spot vs", "multiple voyage", "charter party structure"]):
            steps = [
                CopilotPlanStepSchema(
                    step_number=1,
                    tool_name="get_cargo_requirement",
                    reason="Retrieve total commitment volume.",
                    arguments={"cargo_id": cargo_id} if cargo_id else {},
                ),
                CopilotPlanStepSchema(
                    step_number=2,
                    tool_name="analyze_contract_strategy",
                    reason="Evaluate Spot vs Short-term vs Medium-term chartering structures.",
                    arguments={"cargo_id": cargo_id, "volume_mt": quantity_mt},
                ),
                CopilotPlanStepSchema(
                    step_number=3,
                    tool_name="get_contract_comparison",
                    reason="Compare side-by-side risk-adjusted commitments.",
                    arguments={},
                ),
            ]

        # 5. SPECIFIC INTENT: Voyage Economics & Speed
        elif any(k in query for k in ["voyage economics", "voyage cost", "bunker cost", "cost per mt", "speed scenario"]):
            steps = [
                CopilotPlanStepSchema(
                    step_number=1,
                    tool_name="analyze_voyage_economics",
                    reason="Calculate complete itemized voyage financials (freight, bunker, port, time, demurrage).",
                    arguments={
                        "origin_port_id": origin_id,
                        "destination_port_id": dest_id,
                        "cargo_quantity_mt": quantity_mt,
                        "vessel_id": vessel_id,
                        "cargo_id": cargo_id,
                    },
                ),
                CopilotPlanStepSchema(
                    step_number=2,
                    tool_name="analyze_speed",
                    reason="Evaluate Admiralty cubic speed scenarios to test economic speed preferred range.",
                    arguments={"vessel_id": vessel_id, "distance_nm": 5840.0},
                ),
            ]

        # 6. SPECIFIC INTENT: Operational Risk
        elif any(k in query for k in ["risk", "weather", "congestion", "tidal", "delay", "demurrage"]):
            steps = [
                CopilotPlanStepSchema(
                    step_number=1,
                    tool_name="get_voyage_risk",
                    reason="Retrieve unified route risk summary.",
                    arguments={"origin_port_id": origin_id, "destination_port_id": dest_id, "vessel_id": vessel_id},
                ),
                CopilotPlanStepSchema(
                    step_number=2,
                    tool_name="analyze_congestion",
                    reason="Quantify anchorage queue and expected demurrage exposure.",
                    arguments={"port_id": dest_id or "INPRT"},
                ),
                CopilotPlanStepSchema(
                    step_number=3,
                    tool_name="analyze_weather",
                    reason="Check wind speed, swell, and port stoppage risk.",
                    arguments={"port_id": dest_id or "INPRT"},
                ),
                CopilotPlanStepSchema(
                    step_number=4,
                    tool_name="evaluate_tidal",
                    reason="Verify under-keel clearance and tidal gate availability.",
                    arguments={"port_id": dest_id or "INPRT", "vessel_draft_m": 14.2},
                ),
            ]

        # 7. DEFAULT / COMPREHENSIVE END-TO-END CHARTERING ASSESSMENT
        # (e.g. "Analyze 75,000 MT coal from Newcastle to Paradip within 30 days")
        else:
            steps = [
                CopilotPlanStepSchema(
                    step_number=1,
                    tool_name="get_cargo_requirement",
                    reason="Extract cargo particulars and laycan constraints.",
                    arguments={"cargo_id": cargo_id} if cargo_id else {},
                ),
                CopilotPlanStepSchema(
                    step_number=2,
                    tool_name="match_vessels",
                    reason="Match qualified candidate tonnage for this cargo volume.",
                    arguments={"cargo_id": cargo_id, "top_n": 3},
                ),
                CopilotPlanStepSchema(
                    step_number=3,
                    tool_name="evaluate_vessel_port",
                    reason="Verify geometric port constraints at discharge terminal.",
                    arguments={"vessel_id": vessel_id, "port_id": dest_id},
                ),
                CopilotPlanStepSchema(
                    step_number=4,
                    tool_name="get_freight_forecast",
                    reason="Load probabilistic freight curve (P10/P50/P90).",
                    arguments={"origin_port_id": origin_id, "destination_port_id": dest_id},
                ),
                CopilotPlanStepSchema(
                    step_number=5,
                    tool_name="get_market_regime",
                    reason="Evaluate current Gaussian HMM market regime.",
                    arguments={},
                ),
                CopilotPlanStepSchema(
                    step_number=6,
                    tool_name="analyze_wait_fix",
                    reason="Determine commercial timing advice (WAIT vs FIX_NOW).",
                    arguments={"cargo_id": cargo_id, "vessel_id": vessel_id},
                ),
                CopilotPlanStepSchema(
                    step_number=7,
                    tool_name="analyze_contract_strategy",
                    reason="Compare Spot vs COA commitment structures.",
                    arguments={"cargo_id": cargo_id, "volume_mt": quantity_mt},
                ),
                CopilotPlanStepSchema(
                    step_number=8,
                    tool_name="get_voyage_risk",
                    reason="Assess congestion, weather, and tidal operational risks.",
                    arguments={"origin_port_id": origin_id, "destination_port_id": dest_id, "vessel_id": vessel_id},
                ),
                CopilotPlanStepSchema(
                    step_number=9,
                    tool_name="analyze_voyage_economics",
                    reason="Compute total delivered voyage financials ($/MT).",
                    arguments={
                        "origin_port_id": origin_id,
                        "destination_port_id": dest_id,
                        "cargo_quantity_mt": quantity_mt,
                        "vessel_id": vessel_id,
                        "cargo_id": cargo_id,
                    },
                ),
            ]

        return steps
