import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.enums import (
    CopilotRole,
    CopilotPlanStatus,
    CopilotToolStatus,
    DataStatusType,
)
from app.models.copilot import CopilotSession, CopilotMessage, CopilotPlan
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotPlanStepSchema,
    ToolResultSchema,
    StructuredCopilotResponse,
)

from app.services.copilot.tool_registry import CopilotToolRegistry
from app.services.copilot.planner import CharteringPlannerService
from app.services.copilot.tool_executor import CopilotToolExecutor
from app.services.copilot.evidence_validator import CopilotEvidenceValidator
from app.services.copilot.grounding import CopilotGroundingService
from app.services.copilot.llm_provider import LLMConfig, LLMProvider, get_llm_provider
from app.repositories.copilot_repo import CopilotRepository
from app.repositories.cargo_repo import CargoRepository

logger = logging.getLogger("freight_iq.copilot.service")


class CopilotService:
    """
    Central orchestration engine for the FREIGHT IQ AI Chartering Copilot.
    Coordinates User Query -> Intent & Plan -> Tool Executions -> Evidence Validation
    -> LLM Grounded Synthesis -> Traceable Response Delivery.
    """

    def __init__(
        self,
        db: Session,
        llm_config: Optional[LLMConfig] = None,
    ):
        self.db = db
        self.registry = CopilotToolRegistry()
        self.repo = CopilotRepository(db)
        self.planner = CharteringPlannerService()
        self.executor = CopilotToolExecutor(db, self.registry, self.repo)
        self.validator = CopilotEvidenceValidator()
        self.grounding = CopilotGroundingService()
        self.llm_config = llm_config or LLMConfig()
        self.llm = get_llm_provider(self.llm_config)

    INJECTION_PATTERNS = [
        re.compile(r"(ignore|disregard|forget)\s+(all\s+)?(previous|prior|system|your)?\s*instructions", re.IGNORECASE),
        re.compile(r"(reveal|give\s+me|show|what\s+is|print|display)\s+(me\s+)?(your\s+)?(system\s+prompt|prompt|instructions)", re.IGNORECASE),
        re.compile(r"(reveal|give\s+me|show|print|display)\s+(your\s+)?(api|secret|key|token|credential|password|env|environment)", re.IGNORECASE),
        re.compile(r"drop\s+table", re.IGNORECASE),
        re.compile(r"delete\s+from\s+", re.IGNORECASE),
        re.compile(r"execute\s+arbitrary\s+", re.IGNORECASE),
        re.compile(r"bypass\s+(authorization|security|permission|guardrails|safety|rules)", re.IGNORECASE),
        re.compile(r"treat\s+synthetic\s+data\s+as\s+live", re.IGNORECASE),
        re.compile(r"ignore\s+tool\s+results", re.IGNORECASE),
        re.compile(r"print\s+env", re.IGNORECASE),
    ]

    def is_prompt_injection(self, text: str) -> bool:
        if not text:
            return False
        return any(pattern.search(text) for pattern in self.INJECTION_PATTERNS)

    def generate_security_rejection_response(self, session_id: str, query: str) -> Dict[str, Any]:
        """Generates an audit-compliant security rejection when prompt injection is detected."""
        rejection_text = (
            "### SECURITY AUDIT POLICY ENFORCEMENT\n\n"
            "**Notice:** The submitted prompt contains prohibited instructions, unauthorized system commands, or prompt injection patterns.\n\n"
            "In compliance with SAIL Directorate & CVC cybersecurity mandates, the AI Chartering Copilot refuses this request. "
            "Internal system prompts, API credentials, and unauthorized execution routines are strictly protected."
        )
        structured = StructuredCopilotResponse(
            summary="Security Guardrail Triggered: Request blocked due to detected prompt injection or unauthorized system instructions.",
            findings=[
                "Prompt injection pattern detected and intercepted before tool scheduling.",
                "Zero internal tools or database modifications were permitted.",
                "Session integrity preserved under strict governance guardrails.",
            ],
            decision_context={},
            evidence=[],
            risks=[{"type": "Cybersecurity Policy Violation", "severity": "HIGH", "description": "Attempt to bypass model instructions or request confidential credentials."}],
            economics={},
            assumptions=[],
            uncertainties=[],
            data_quality={"overall_status": "BLOCKED", "confidence_score": 0.0, "provenance_verified": True},
            actions=[],
        )
        assistant_msg = self.repo.add_message(
            session_id=session_id,
            role=CopilotRole.ASSISTANT,
            content=rejection_text,
            structured_response=structured.model_dump(),
        )
        return {
            "session_id": session_id,
            "message": {
                "id": assistant_msg.id,
                "role": assistant_msg.role.value if hasattr(assistant_msg.role, "value") else str(assistant_msg.role),
                "content": assistant_msg.content,
                "structured_response": structured.model_dump(),
                "created_at": assistant_msg.created_at.isoformat(),
            },
            "response": rejection_text,
            "plan": None,
            "tool_results": [],
            "structured_response": structured.model_dump(),
            "data_quality": {"status": "BLOCKED", "score": 0.0, "disclosures": ["Request blocked by security guardrails"]},
        }

    def process_chat(
        self,
        request: CopilotChatRequest,
    ) -> Dict[str, Any]:
        """
        Synchronously processes a user chat inquiry through the complete
        analytical and grounding pipeline.
        """
        # 1. Resolve or create session
        session = self._resolve_session(request)

        # Check prompt injection security guardrail
        if self.is_prompt_injection(request.message):
            logger.warning(f"Prompt injection attempt detected in session {session.id}: {request.message[:100]}")
            return self.generate_security_rejection_response(session.id, request.message)

        # 2. Add user message
        user_msg = self.repo.add_message(
            session_id=session.id,
            role=CopilotRole.USER,
            content=request.message,
        )

        # 3. Build context & generate structured plan
        context = self._build_context(session, request)
        plan_steps = self.planner.generate_plan(request.message, context)
        plan = self.repo.create_plan(
            session_id=session.id,
            user_goal=request.message,
            plan_steps=[s.model_dump() for s in plan_steps],
            status=CopilotPlanStatus.EXECUTING,
        )

        # 4. Execute tool calls sequentially
        tool_results: List[ToolResultSchema] = []
        has_failure = False

        for step in plan_steps:
            res = self.executor.execute_tool(
                session_id=session.id,
                tool_name=step.tool_name,
                arguments=step.arguments,
                message_id=user_msg.id,
                plan_id=plan.id,
            )
            validated_res = self.validator.validate_tool_result(res)
            tool_results.append(validated_res)
            if validated_res.status == CopilotToolStatus.FAILED:
                has_failure = True

        # 5. Audit evidence quality
        audit = self.validator.audit_evidence_collection(tool_results)
        final_plan_status = CopilotPlanStatus.PARTIAL if has_failure else CopilotPlanStatus.COMPLETED
        self.repo.update_plan_status(plan.id, final_plan_status)

        # 6. Synthesize grounded assessment with LLM provider
        markdown_text, structured_resp = self.llm.synthesize_assessment(
            user_query=request.message,
            context=context,
            tool_results=tool_results,
            config=self.llm_config,
        )

        # 7. Apply grounding audit & mandatory disclosures
        is_grounded, violations = self.grounding.verify_grounding(markdown_text, structured_resp, tool_results)
        structured_resp = self.grounding.enforce_disclaimers(structured_resp, tool_results)

        # 8. Record assistant response
        assistant_msg = self.repo.add_message(
            session_id=session.id,
            role=CopilotRole.ASSISTANT,
            content=markdown_text,
            structured_response=structured_resp.model_dump(),
            plan_id=plan.id,
        )

        return {
            "session_id": session.id,
            "message": {
                "id": assistant_msg.id,
                "role": assistant_msg.role.value if hasattr(assistant_msg.role, "value") else str(assistant_msg.role),
                "content": assistant_msg.content,
                "structured_response": structured_resp.model_dump(),
                "created_at": assistant_msg.created_at.isoformat(),
            },
            "plan": {
                "id": plan.id,
                "status": plan.status.value if hasattr(plan.status, "value") else str(plan.status),
                "steps": [s.model_dump() for s in plan_steps],
            },
            "tool_results": [r.model_dump() for r in tool_results],
            "structured_response": structured_resp.model_dump(),
            "data_quality": audit,
        }

    def generate_plan_only(self, user_query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Generates the execution plan without executing tools immediately."""
        session = self.repo.get_session_by_id(session_id) if session_id else None
        context = self._build_context(session, None)
        steps = self.planner.generate_plan(user_query, context)
        return {
            "query": user_query,
            "steps": [s.model_dump() for s in steps],
            "total_tools": len(steps),
        }

    def _resolve_session(self, request: CopilotChatRequest) -> CopilotSession:
        if request.session_id:
            session = self.repo.get_session_by_id(request.session_id)
            if session:
                if request.cargo_request_id or request.vessel_id or request.voyage_id:
                    self.repo.update_session_context(
                        session_id=session.id,
                        cargo_request_id=request.cargo_request_id,
                        vessel_id=request.vessel_id,
                        voyage_id=request.voyage_id,
                    )
                return session

        # Derive initial title from query or preset
        title = "Newcastle to Paradip (75k MT Coal)"
        if request.scenario_preset == "VIZAG_CAPESIZE":
            title = "Newcastle to Vizag (168k MT Coal)"
        elif len(request.message) < 40:
            title = request.message

        context_data = {
            "origin_port": "Newcastle (AUNCL)",
            "destination_port": "Paradip (INPRT)",
            "commodity": "Coking Coal",
            "quantity_mt": 75000.0,
            "distance_nm": 5840.0,
        }

        return self.repo.create_session(
            title=title,
            cargo_request_id=request.cargo_request_id,
            vessel_id=request.vessel_id,
            voyage_id=request.voyage_id,
            context_data=context_data,
        )

    def _build_context(self, session: Optional[CopilotSession], request: Optional[CopilotChatRequest]) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "origin_port": "Port of Newcastle (AUNCL)",
            "origin_port_id": "",
            "destination_port": "Paradip Port (INPRT)",
            "destination_port_id": "",
            "cargo_type": "Coking Coal",
            "quantity_mt": 75000.0,
            "distance_nm": 5840.0,
            "cargo_request_id": None,
            "vessel_id": None,
            "voyage_id": None,
        }

        if session:
            if session.cargo_request_id:
                context["cargo_request_id"] = session.cargo_request_id
            if session.vessel_id:
                context["vessel_id"] = session.vessel_id
            if session.voyage_id:
                context["voyage_id"] = session.voyage_id
            if session.context_json:
                try:
                    loaded = json.loads(session.context_json)
                    context.update(loaded)
                except Exception:
                    pass

        if request:
            if request.cargo_request_id:
                context["cargo_request_id"] = request.cargo_request_id
            if request.vessel_id:
                context["vessel_id"] = request.vessel_id
            if request.voyage_id:
                context["voyage_id"] = request.voyage_id

        # If cargo_request_id is present, populate actual particulars
        if context.get("cargo_request_id"):
            req = CargoRepository(self.db).get_requirement_by_id(context["cargo_request_id"])
            if req:
                context["cargo_type"] = req.cargo_type.value if hasattr(req.cargo_type, "value") else str(req.cargo_type)
                context["quantity_mt"] = req.quantity_mt
                context["origin_port_id"] = req.load_port_id
                context["destination_port_id"] = req.discharge_port_id
                if req.load_port:
                    context["origin_port"] = f"{req.load_port.name} ({req.load_port.unlocode})"
                if req.discharge_port:
                    context["destination_port"] = f"{req.discharge_port.name} ({req.discharge_port.unlocode})"

            # Check if an existing canonical decision context exists
            from app.repositories.decision_repo import DecisionRepository
            dec_repo = DecisionRepository(self.db)
            decision = dec_repo.get_decision_by_cargo_id(context["cargo_request_id"])
            if decision and decision.canonical_context_json:
                try:
                    dec_ctx = json.loads(decision.canonical_context_json)
                    context["decision_id"] = decision.id
                    context["analysis_run_id"] = decision.latest_analysis_run_id
                    context["canonical_decision"] = dec_ctx
                except Exception:
                    pass

        return context
