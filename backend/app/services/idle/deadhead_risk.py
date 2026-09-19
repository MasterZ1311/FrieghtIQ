"""
Deadhead Risk Service
Evaluates the exposure of unhedged ballast transit (deadheading) without securing laden employment.

DEADHEAD RISK EVALUATION RULES:
1. UNKNOWN:
   - Repositioning distance is uncalculated / None.
   - Target port compatibility is UNKNOWN.
   - Laycan timing compatibility is UNKNOWN.
   - Data completeness is False.

2. HIGH:
   - Target port compatibility is FAIL (vessel physically rejected, guaranteed stranded ballast leg).
   - Laycan timing is MISSED_LAYCAN (canceling date passed, fixture canceled).
   - No secured cargo requirement and ballast distance > 2,500 NM (high-exposure speculative steaming).

3. MEDIUM:
   - Repositioning distance between 1,500 NM and 3,000 NM with confirmed cargo.
   - Laycan timing is TIGHT (buffer < 1.5 days).
   - Port compatibility is CONDITIONAL (requires tidal window / lighterage).

4. LOW:
   - Ballast distance <= 1,500 NM.
   - Port compatibility is PASS.
   - Laycan timing is ON_TIME.
   - Target cargo fixture is confirmed.
"""
from typing import Optional, Tuple
from app.models.enums import DeadheadRiskLevel


class DeadheadRiskService:
    @staticmethod
    def evaluate_risk(
        distance_nm: Optional[float],
        port_compatibility: str,
        timing_compatibility: str,
        has_secured_cargo: bool,
        is_data_complete: bool
    ) -> Tuple[DeadheadRiskLevel, str]:
        """
        Returns:
            (DeadheadRiskLevel, explanatory_rule_narrative)
        """
        # Rule 1: Unknown data check
        if not is_data_complete or distance_nm is None:
            return (
                DeadheadRiskLevel.UNKNOWN,
                "Deadhead risk cannot be assessed due to incomplete route distance or vessel parameters."
            )

        if port_compatibility == "UNKNOWN" or timing_compatibility == "UNKNOWN":
            return (
                DeadheadRiskLevel.UNKNOWN,
                "Port berth clearance or laycan window is unverified; deadhead risk remains UNKNOWN."
            )

        # Rule 2: High exposure triggers
        if port_compatibility == "FAIL":
            return (
                DeadheadRiskLevel.HIGH,
                "HIGH RISK: Target port physical constraints reject vessel; high probability of empty stranded deadhead."
            )

        if timing_compatibility == "MISSED_LAYCAN":
            return (
                DeadheadRiskLevel.HIGH,
                "HIGH RISK: Estimated arrival misses cargo canceling date; fixture subject to immediate cancellation."
            )

        if not has_secured_cargo and distance_nm > 2500.0:
            return (
                DeadheadRiskLevel.HIGH,
                f"HIGH RISK: Long speculative ballast leg ({distance_nm:,.0f} NM) exceeding 2,500 NM without confirmed cargo fixture."
            )

        # Rule 3: Medium exposure triggers
        if (
            (1500.0 <= distance_nm <= 3000.0) or
            timing_compatibility == "TIGHT" or
            port_compatibility == "CONDITIONAL"
        ):
            reasons = []
            if distance_nm > 1500.0:
                reasons.append(f"moderate ballast distance ({distance_nm:,.0f} NM)")
            if timing_compatibility == "TIGHT":
                reasons.append("tight laycan buffer (< 1.5 days)")
            if port_compatibility == "CONDITIONAL":
                reasons.append("conditional tidal/lighterage berth clearance")

            return (
                DeadheadRiskLevel.MEDIUM,
                f"MEDIUM RISK: Repositioning exposure driven by {', '.join(reasons)}."
            )

        # Rule 4: Low exposure
        if distance_nm <= 1500.0 and port_compatibility == "PASS" and timing_compatibility == "ON_TIME":
            return (
                DeadheadRiskLevel.LOW,
                f"LOW RISK: Short ballast repositioning ({distance_nm:,.0f} NM) with verified port clearance and comfortable laycan arrival."
            )

        return (
            DeadheadRiskLevel.MEDIUM,
            f"MEDIUM RISK: Repositioning leg distance {distance_nm:,.0f} NM with verified cargo opportunity."
        )
