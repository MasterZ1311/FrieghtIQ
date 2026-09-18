"""
Copilot Router — FreightIQ 2.0
==============================
Exposes interactive AI chartering assistant endpoint for decision makers.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.copilot_service import chat

router = APIRouter(prefix="/api/copilot", tags=["AI Copilot"])


class CopilotRequest(BaseModel):
    message: str = Field(..., min_length=2, description="User prompt or chartering scenario query")
    session_id: str = Field(default="default", description="Conversation session ID")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional active frontend voyage context")


class CopilotResponse(BaseModel):
    reply: str
    session_id: str
    tools_called: list[str] = []
    recommendations: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=CopilotResponse, summary="Chat with FreightIQ AI Chartering Advisor")
def copilot_chat(req: CopilotRequest):
    """
    Submits a procurement scenario to the AI Copilot.
    The agent dynamically checks physical port constraints, rate forecast distributions,
    HMM market regime, Black-Scholes real options timing, and AIS congestion.
    """
    return chat(message=req.message, session_id=req.session_id)
