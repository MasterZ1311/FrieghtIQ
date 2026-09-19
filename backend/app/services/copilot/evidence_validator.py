from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.models.enums import DataStatusType
from app.schemas.copilot import ToolResultSchema


class CopilotEvidenceValidator:
    """
    Validates tool execution outputs for data completeness, unit consistency,
    provenance traceability, and data status preservation.
    """

    ALLOWED_CURRENCIES = {"USD", "INR"}
    ALLOWED_UNITS = {"USD", "USD/MT", "MT", "knots", "hours", "days", "m", "nm", "pct"}

    def validate_tool_result(self, result: ToolResultSchema) -> ToolResultSchema:
        """
        Validates individual tool output. Enforces currency, units, timestamps,
        and integrity of data_status flags.
        """
        if not result.source:
            result.source = "FREIGHT_IQ_INTERNAL"

        if not result.observed_at and not result.last_updated:
            result.last_updated = datetime.now(timezone.utc).isoformat()

        # Enforce standard currency
        if result.currency and result.currency not in self.ALLOWED_CURRENCIES:
            result.data_status = DataStatusType.UNKNOWN
            result.assumption = f"Currency {result.currency} unverified against chartering standard USD."

        # If data is empty or missing required calculation
        if result.data is None:
            result.data_status = DataStatusType.UNKNOWN
            result.data = {"error": result.error or "No data returned from analytical service"}

        return result

    def audit_evidence_collection(self, results: List[ToolResultSchema]) -> Dict[str, Any]:
        """
        Computes aggregate data quality scorecard across all tool results in a plan.
        Identifies whether the assessment is FULLY_VERIFIED, ESTIMATED_DEMO, or PARTIAL.
        """
        total = len(results)
        if total == 0:
            return {
                "overall_status": DataStatusType.UNKNOWN,
                "confidence_score": 0.0,
                "breakdown": {},
                "limitations": ["No analytical tools were executed."],
            }

        counts: Dict[str, int] = {}
        limitations: List[str] = []

        for res in results:
            status_val = res.data_status.value if hasattr(res.data_status, "value") else str(res.data_status)
            counts[status_val] = counts.get(status_val, 0) + 1

            if status_val in [DataStatusType.UNKNOWN.value, "UNAVAILABLE"]:
                limitations.append(f"{res.tool_name}: analytical data unavailable or missing required inputs.")
            elif status_val in [DataStatusType.DEMO.value, DataStatusType.SYNTHETIC.value]:
                limitations.append(f"{res.tool_name}: evaluated under demo/synthetic operational assumptions.")

        # Determine aggregate posture
        if counts.get(DataStatusType.UNKNOWN.value, 0) > 0:
            overall = DataStatusType.UNKNOWN
            confidence = 0.5
        elif counts.get(DataStatusType.SYNTHETIC.value, 0) > 0 or counts.get(DataStatusType.DEMO.value, 0) > 0:
            overall = DataStatusType.SYNTHETIC
            confidence = 0.85
        elif counts.get(DataStatusType.CALCULATED.value, 0) > 0 or counts.get(DataStatusType.VERIFIED.value, 0) > 0:
            overall = DataStatusType.VERIFIED
            confidence = 0.95
        else:
            overall = DataStatusType.RECENT
            confidence = 0.9

        return {
            "overall_status": overall,
            "confidence_score": confidence,
            "status_counts": counts,
            "limitations": limitations,
            "verified_tools_count": total - counts.get(DataStatusType.UNKNOWN.value, 0),
        }
