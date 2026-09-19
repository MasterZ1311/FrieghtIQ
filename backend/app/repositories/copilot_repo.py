from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload

from app.models.copilot import (
    CopilotSession,
    CopilotPlan,
    CopilotMessage,
    CopilotToolCall,
    CopilotToolResult,
)
from app.models.enums import (
    CopilotRole,
    CopilotPlanStatus,
    CopilotToolStatus,
    DataStatusType,
)


class CopilotRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        title: str = "Chartering Inquiry",
        cargo_request_id: Optional[str] = None,
        vessel_id: Optional[str] = None,
        voyage_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> CopilotSession:
        session = CopilotSession(
            id=str(uuid.uuid4()),
            title=title,
            cargo_request_id=cargo_request_id,
            vessel_id=vessel_id,
            voyage_id=voyage_id,
            context_json=json.dumps(context_data) if context_data else None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_id(self, session_id: str) -> Optional[CopilotSession]:
        return (
            self.db.query(CopilotSession)
            .options(
                joinedload(CopilotSession.cargo_request),
                joinedload(CopilotSession.vessel),
                joinedload(CopilotSession.messages),
                joinedload(CopilotSession.plans),
            )
            .filter(CopilotSession.id == session_id)
            .first()
        )

    def get_all_sessions(self, limit: int = 50) -> List[CopilotSession]:
        return (
            self.db.query(CopilotSession)
            .order_by(CopilotSession.updated_at.desc())
            .limit(limit)
            .all()
        )

    def update_session_context(
        self,
        session_id: str,
        context_data: Optional[Dict[str, Any]] = None,
        cargo_request_id: Optional[str] = None,
        vessel_id: Optional[str] = None,
        voyage_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[CopilotSession]:
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        if context_data is not None:
            session.context_json = json.dumps(context_data)
        if cargo_request_id is not None:
            session.cargo_request_id = cargo_request_id
        if vessel_id is not None:
            session.vessel_id = vessel_id
        if voyage_id is not None:
            session.voyage_id = voyage_id
        if title is not None:
            session.title = title

        session.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(session)
        return session

    def add_message(
        self,
        session_id: str,
        role: CopilotRole,
        content: str,
        structured_response: Optional[Dict[str, Any]] = None,
        plan_id: Optional[str] = None,
    ) -> CopilotMessage:
        message = CopilotMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            structured_response=json.dumps(structured_response) if structured_response else None,
            plan_id=plan_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(message)
        
        # update session timestamp
        session = self.db.query(CopilotSession).filter(CopilotSession.id == session_id).first()
        if session:
            session.updated_at = datetime.now(timezone.utc)
            
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages_for_session(self, session_id: str) -> List[CopilotMessage]:
        return (
            self.db.query(CopilotMessage)
            .filter(CopilotMessage.session_id == session_id)
            .order_by(CopilotMessage.created_at.asc())
            .all()
        )

    def create_plan(
        self,
        session_id: str,
        user_goal: str,
        plan_steps: List[Dict[str, Any]],
        status: CopilotPlanStatus = CopilotPlanStatus.PLANNED,
    ) -> CopilotPlan:
        plan = CopilotPlan(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_goal=user_goal,
            plan_json=json.dumps(plan_steps),
            status=status,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def update_plan_status(
        self,
        plan_id: str,
        status: CopilotPlanStatus,
    ) -> Optional[CopilotPlan]:
        plan = self.db.query(CopilotPlan).filter(CopilotPlan.id == plan_id).first()
        if not plan:
            return None
        plan.status = status
        if status in [CopilotPlanStatus.COMPLETED, CopilotPlanStatus.PARTIAL, CopilotPlanStatus.FAILED]:
            plan.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_latest_plan_for_session(self, session_id: str) -> Optional[CopilotPlan]:
        return (
            self.db.query(CopilotPlan)
            .filter(CopilotPlan.session_id == session_id)
            .order_by(CopilotPlan.created_at.desc())
            .first()
        )

    def record_tool_call(
        self,
        session_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        message_id: Optional[str] = None,
        plan_id: Optional[str] = None,
    ) -> CopilotToolCall:
        tool_call = CopilotToolCall(
            id=str(uuid.uuid4()),
            session_id=session_id,
            message_id=message_id,
            plan_id=plan_id,
            tool_name=tool_name,
            arguments=json.dumps(arguments),
            status=CopilotToolStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(tool_call)
        self.db.commit()
        self.db.refresh(tool_call)
        return tool_call

    def update_tool_call(
        self,
        tool_call_id: str,
        status: CopilotToolStatus,
        execution_time_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> Optional[CopilotToolCall]:
        tool_call = self.db.query(CopilotToolCall).filter(CopilotToolCall.id == tool_call_id).first()
        if not tool_call:
            return None
        tool_call.status = status
        tool_call.completed_at = datetime.now(timezone.utc)
        if execution_time_ms is not None:
            tool_call.execution_time_ms = execution_time_ms
        if error:
            tool_call.error = error
        self.db.commit()
        self.db.refresh(tool_call)
        return tool_call

    def record_tool_result(
        self,
        tool_call_id: str,
        result_data: Dict[str, Any],
        source: str = "FREIGHT_IQ",
        data_status: DataStatusType = DataStatusType.SYNTHETIC,
        dataset_version_id: Optional[str] = None,
    ) -> CopilotToolResult:
        result = CopilotToolResult(
            id=str(uuid.uuid4()),
            tool_call_id=tool_call_id,
            result_json=json.dumps(result_data),
            source=source,
            data_status=data_status,
            dataset_version_id=dataset_version_id,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def get_tool_calls_for_session(self, session_id: str) -> List[CopilotToolCall]:
        return (
            self.db.query(CopilotToolCall)
            .options(joinedload(CopilotToolCall.result))
            .filter(CopilotToolCall.session_id == session_id)
            .order_by(CopilotToolCall.created_at.asc())
            .all()
        )
