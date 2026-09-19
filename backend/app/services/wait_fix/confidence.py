from typing import Optional
from app.models.enums import DecisionConfidence, FeasibilityStatus, DataStatusType

class DecisionConfidenceService:
    """
    Evaluates multi-factor decision confidence across forecast quality,
    market regime stability, data freshness, deadline proximity, and port feasibility.
    Returns categorical confidence: HIGH, MEDIUM, or LOW without manufactured precision.
    """
    @staticmethod
    def evaluate_confidence(
        forecast_confidence_pct: float,
        regime_probability: float,
        remaining_days: int,
        port_feasibility: Optional[FeasibilityStatus] = None,
        data_status: DataStatusType = DataStatusType.SYNTHETIC,
        modeled_difference_pct: float = 0.0
    ) -> DecisionConfidence:
        # Normalize inputs to 0.0 - 1.0 scale
        fc_score = max(0.0, min(1.0, forecast_confidence_pct / 100.0 if forecast_confidence_pct > 1.0 else forecast_confidence_pct))
        reg_score = max(0.0, min(1.0, regime_probability))

        # Composite base score
        score = (fc_score * 0.45) + (reg_score * 0.45) + 0.10

        # Port feasibility penalty
        if port_feasibility == FeasibilityStatus.CONDITIONAL:
            score -= 0.15
        elif port_feasibility == FeasibilityStatus.UNKNOWN:
            score -= 0.10

        # Deadline proximity penalty
        if remaining_days <= 2:
            score -= 0.15
        elif remaining_days <= 5:
            score -= 0.05

        # Data freshness penalty
        if data_status == DataStatusType.STALE:
            score -= 0.25
        elif data_status == DataStatusType.UNAVAILABLE:
            score -= 0.40

        # Boundary noise penalty (tiny modeled difference)
        if abs(modeled_difference_pct) < 1.0:
            score -= 0.10

        # Categorize
        if score >= 0.72:
            return DecisionConfidence.HIGH
        elif score >= 0.48:
            return DecisionConfidence.MEDIUM
        else:
            return DecisionConfidence.LOW
