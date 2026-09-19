from typing import Dict, Any, List
from app.models.enums import DecisionReadinessStatus
from app.services.decision.quality_gate import DataQualityGate


class DecisionReadinessService:
    """
    Evaluates evidence sufficiency to answer:
    'Can FREIGHT IQ provide a sufficiently supported analytical assessment using currently available evidence?'

    Produces a transparent score, blockers list, conditional warnings, and executive rationale.
    """

    @classmethod
    def evaluate_readiness(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        gate_res = DataQualityGate.evaluate_decision_quality(context)
        status: DecisionReadinessStatus = gate_res["overall_status"]
        blockers: List[str] = gate_res["blockers"]
        warnings: List[str] = gate_res["warnings"]
        score: float = round(gate_res["confidence_score"] * 100.0, 1)

        if status == DecisionReadinessStatus.BLOCKED:
            rationale = (
                f"DECISION BLOCKED: {len(blockers)} critical prerequisite(s) failed verification: "
                + "; ".join(blockers)
                + ". Resolution required before chartering commitment."
            )
        elif status == DecisionReadinessStatus.CONDITIONAL:
            rationale = (
                f"CONDITIONAL READINESS ({score:.0f}% evidence confidence): Core operational and technical "
                f"feasibility is confirmed. Notice: {warnings[0] if warnings else 'Subject to assumptions'}."
            )
        elif status == DecisionReadinessStatus.PARTIAL:
            rationale = (
                f"PARTIAL READINESS ({score:.0f}% evidence confidence): Some analytical engines could not complete. "
                "Assessment is advisory; manual broker confirmation recommended."
            )
        else:
            rationale = (
                f"DECISION READY (100% evidence confidence): All technical, navigational, and commercial "
                "parameters have been verified through active models and public port tariffs."
            )

        return {
            "status": status,
            "score": score,
            "blockers": blockers,
            "warnings": warnings,
            "rationale": rationale,
            "checkpoints": gate_res["checkpoints"],
            "limitations_explanation": gate_res["limitations_explanation"],
        }
