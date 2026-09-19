import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotPlanRequest,
    CopilotSessionSchema,
    CopilotSessionDetailSchema,
    CopilotMessageSchema,
    CopilotToolCallSchema,
)
from app.services.copilot import (
    CopilotService,
    CopilotToolRegistry,
    CharteringPlannerService,
)
from app.repositories.copilot_repo import CopilotRepository
from app.models.enums import CopilotRole, CopilotPlanStatus, CopilotToolStatus

logger = logging.getLogger("freight_iq.api.copilot")

copilot_router = APIRouter(prefix="/copilot", tags=["AI Chartering Copilot"])


@copilot_router.post("/chat")
def chat_copilot(
    request: CopilotChatRequest,
    db: Session = Depends(get_db),
):
    """
    Primary conversational decision-support endpoint.
    Orchestrates Intent -> Planning -> Tool Executions -> Grounded Synthesis.
    Supports real-time execution event streaming (SSE) when request.stream=True.
    """
    service = CopilotService(db)

    if not request.stream:
        try:
            return service.process_chat(request)
        except Exception as e:
            logger.error(f"Copilot chat error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Copilot analysis failed: {str(e)}")

    # SSE Event Streaming Mode
    def sse_event_stream():
        try:
            session = service._resolve_session(request)
            yield f"event: step\ndata: {json.dumps({'type': 'init', 'label': 'Initializing session & context...', 'session_id': session.id})}\n\n"

            # Record user query
            user_msg = service.repo.add_message(
                session_id=session.id,
                role=CopilotRole.USER,
                content=request.message,
            )

            # Security Guardrail Check
            if service.is_prompt_injection(request.message):
                rejection = service.generate_security_rejection_response(session.id, request.message)
                yield f"event: step\ndata: {json.dumps({'type': 'security_blocked', 'label': 'Request blocked by security guardrails.'})}\n\n"
                yield f"event: token\ndata: {json.dumps({'delta': rejection['response']})}\n\n"
                yield f"event: final\ndata: {json.dumps({'message_id': rejection['message_id'], 'structured': rejection['structured_response']})}\n\n"
                return

            # Build context & plan
            yield f"event: step\ndata: {json.dumps({'type': 'planning', 'label': 'Compiling analytical plan...'})}\n\n"
            context = service._build_context(session, request)
            plan_steps = service.planner.generate_plan(request.message, context)
            plan = service.repo.create_plan(
                session_id=session.id,
                user_goal=request.message,
                plan_steps=[s.model_dump() for s in plan_steps],
                status=CopilotPlanStatus.EXECUTING,
            )

            yield f"event: step\ndata: {json.dumps({'type': 'plan_ready', 'label': f'Plan compiled with {len(plan_steps)} tools', 'steps': [s.model_dump() for s in plan_steps]})}\n\n"

            # Sequential Tool Execution with real-time SSE progress
            tool_results = []
            has_failure = False

            for idx, step in enumerate(plan_steps):
                yield f"event: step\ndata: {json.dumps({'type': 'tool_start', 'step_index': idx + 1, 'total_steps': len(plan_steps), 'tool': step.tool_name, 'label': f'Executing {step.tool_name}...'})}\n\n"
                
                res = service.executor.execute_tool(
                    session_id=session.id,
                    tool_name=step.tool_name,
                    arguments=step.arguments,
                    message_id=user_msg.id,
                    plan_id=plan.id,
                )
                validated_res = service.validator.validate_tool_result(res)
                tool_results.append(validated_res)

                if validated_res.status == CopilotToolStatus.FAILED:
                    has_failure = True

                yield f"event: step\ndata: {json.dumps({'type': 'tool_complete', 'tool': step.tool_name, 'status': validated_res.status.value, 'time_ms': round(validated_res.execution_time_ms, 1), 'data_status': validated_res.data_status.value})}\n\n"

            # Evidence Validation & Audit
            yield f"event: step\ndata: {json.dumps({'type': 'validating', 'label': 'Auditing data provenance and grounding facts...'})}\n\n"
            audit = service.validator.audit_evidence_collection(tool_results)
            final_plan_status = CopilotPlanStatus.PARTIAL if has_failure else CopilotPlanStatus.COMPLETED
            service.repo.update_plan_status(plan.id, final_plan_status)

            # Grounded LLM Synthesis
            yield f"event: step\ndata: {json.dumps({'type': 'synthesis', 'label': 'Synthesizing evidence-grounded chartering assessment...'})}\n\n"
            markdown_text, structured_resp = service.llm.synthesize_assessment(
                user_query=request.message,
                context=context,
                tool_results=tool_results,
                config=service.llm_config,
            )

            # Grounding enforcement & disclaimers
            is_grounded, violations = service.grounding.verify_grounding(markdown_text, structured_resp, tool_results)
            structured_resp = service.grounding.enforce_disclaimers(structured_resp, tool_results)

            assistant_msg = service.repo.add_message(
                session_id=session.id,
                role=CopilotRole.ASSISTANT,
                content=markdown_text,
                structured_response=structured_resp.model_dump(),
                plan_id=plan.id,
            )

            final_payload = {
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
                "data_quality": audit,
            }

            yield f"event: message\ndata: {json.dumps(final_payload)}\n\n"
            yield f"event: done\ndata: {json.dumps({'session_id': session.id})}\n\n"

        except Exception as e:
            logger.error(f"SSE streaming exception: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")


@copilot_router.get("/sessions", response_model=List[CopilotSessionSchema])
def list_sessions(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve list of active and recent Copilot inquiry sessions."""
    repo = CopilotRepository(db)
    sessions = repo.get_all_sessions(limit=limit)
    out = []
    for s in sessions:
        context_dict = None
        if s.context_json:
            try:
                context_dict = json.loads(s.context_json)
            except Exception:
                pass
        out.append(CopilotSessionSchema(
            id=s.id,
            title=s.title,
            cargo_request_id=s.cargo_request_id,
            vessel_id=s.vessel_id,
            voyage_id=s.voyage_id,
            context_data=context_dict,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages) if s.messages else 0,
        ))
    return out


@copilot_router.get("/sessions/{id}")
def get_session(
    id: str,
    db: Session = Depends(get_db),
):
    """Retrieve session details with current context."""
    repo = CopilotRepository(db)
    s = repo.get_session_by_id(id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    context_dict = None
    if s.context_json:
        try:
            context_dict = json.loads(s.context_json)
        except Exception:
            pass

    return {
        "id": s.id,
        "title": s.title,
        "cargo_request_id": s.cargo_request_id,
        "vessel_id": s.vessel_id,
        "voyage_id": s.voyage_id,
        "context_data": context_dict,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "cargo_requirement": {
            "title": s.cargo_request.title,
            "quantity_mt": s.cargo_request.quantity_mt,
            "cargo_type": s.cargo_request.cargo_type.value if hasattr(s.cargo_request.cargo_type, "value") else str(s.cargo_request.cargo_type),
        } if s.cargo_request else None,
        "vessel": {
            "name": s.vessel.vessel_name,
            "vessel_class": s.vessel.vessel_class.value if hasattr(s.vessel.vessel_class, "value") else str(s.vessel.vessel_class),
        } if s.vessel else None,
    }


@copilot_router.get("/sessions/{id}/messages")
def get_session_messages(
    id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full chronological conversation message history for a session."""
    repo = CopilotRepository(db)
    messages = repo.get_messages_for_session(id)
    out = []
    for m in messages:
        structured = None
        if m.structured_response:
            try:
                structured = json.loads(m.structured_response)
            except Exception:
                pass
        out.append({
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role.value if hasattr(m.role, "value") else str(m.role),
            "content": m.content,
            "structured_response": structured,
            "plan_id": m.plan_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })
    return out


@copilot_router.get("/sessions/{id}/tools")
def get_session_tools(
    id: str,
    db: Session = Depends(get_db),
):
    """Retrieve all analytical tools executed during a copilot session."""
    repo = CopilotRepository(db)
    tools = repo.get_tool_calls_for_session(id)
    out = []
    for t in tools:
        args = {}
        if t.arguments:
            try:
                args = json.loads(t.arguments)
            except Exception:
                pass
        result_data = None
        source = "FREIGHT_IQ"
        data_status = "SYNTHETIC"
        if t.result:
            source = t.result.source
            data_status = t.result.data_status.value if hasattr(t.result.data_status, "value") else str(t.result.data_status)
            if t.result.result_json:
                try:
                    result_data = json.loads(t.result.result_json)
                except Exception:
                    pass

        out.append({
            "id": t.id,
            "tool_name": t.tool_name,
            "arguments": args,
            "status": t.status.value if hasattr(t.status, "value") else str(t.status),
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "execution_time_ms": t.execution_time_ms,
            "error": t.error,
            "source": source,
            "data_status": data_status,
            "result": result_data,
        })
    return out


@copilot_router.get("/sessions/{id}/trace")
def get_session_trace(
    id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve comprehensive audit trace including plans, sequential tool calls,
    outputs, execution durations, and data provenance.
    """
    repo = CopilotRepository(db)
    session = repo.get_session_by_id(id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    tools = repo.get_tool_calls_for_session(id)
    latest_plan = repo.get_latest_plan_for_session(id)

    plan_data = None
    if latest_plan:
        steps = []
        if latest_plan.plan_json:
            try:
                steps = json.loads(latest_plan.plan_json)
            except Exception:
                pass
        plan_data = {
            "id": latest_plan.id,
            "user_goal": latest_plan.user_goal,
            "status": latest_plan.status.value if hasattr(latest_plan.status, "value") else str(latest_plan.status),
            "steps": steps,
            "created_at": latest_plan.created_at.isoformat() if latest_plan.created_at else None,
            "completed_at": latest_plan.completed_at.isoformat() if latest_plan.completed_at else None,
        }

    total_execution_ms = sum((t.execution_time_ms or 0.0) for t in tools)

    return {
        "session_id": session.id,
        "title": session.title,
        "total_tools_executed": len(tools),
        "total_execution_time_ms": round(total_execution_ms, 2),
        "latest_plan": plan_data,
        "tools_trace": [
            {
                "tool_name": t.tool_name,
                "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                "execution_time_ms": t.execution_time_ms,
                "source": t.result.source if t.result else "FREIGHT_IQ",
                "data_status": (t.result.data_status.value if hasattr(t.result.data_status, "value") else str(t.result.data_status)) if t.result else "UNKNOWN",
                "error": t.error,
            }
            for t in tools
        ],
    }


@copilot_router.post("/plan")
def preview_plan(
    request: CopilotPlanRequest,
    db: Session = Depends(get_db),
):
    """
    Preview the deterministic tool plan for a user query without immediate execution.
    """
    service = CopilotService(db)
    return service.generate_plan_only(request.query, request.session_id)
