"""
Options Router — FreightIQ 2.0
Black-Scholes-Merton Options Pricing applied to freight chartering decisions.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.options_service import calculate_wait_or_fix

router = APIRouter(prefix="/api/options", tags=["options"])


class OptionsRequest(BaseModel):
    current_rate: float = Field(..., gt=0, description="Current spot freight rate in $/MT")
    target_rate: float = Field(..., gt=0, description="Target/budget freight rate in $/MT")
    days_until_needed: int = Field(..., ge=1, le=180, description="Days until vessel required")
    cargo_mt: float = Field(..., gt=0, description="Cargo volume in metric tonnes")
    route: str = Field(default="default", description="Route name/identifier for historical volatility lookup")
    risk_free_rate: float = Field(default=0.065, ge=0.0, le=0.25, description="Annual risk-free interest rate")


@router.post("/wait-or-fix")
def wait_or_fix(req: OptionsRequest):
    """
    Evaluate whether to WAIT or FIX_NOW using Black-Scholes real options theory.
    Returns the option value, recommendation, downside risk exposure, and probability analysis.
    """
    return calculate_wait_or_fix(
        current_rate=req.current_rate,
        target_rate=req.target_rate,
        days_until_needed=req.days_until_needed,
        cargo_mt=req.cargo_mt,
        route=req.route,
        risk_free_rate=req.risk_free_rate,
    )
