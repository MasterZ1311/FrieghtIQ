"""
Repositioning Economics Service
Performs trade-off comparison between holding idle, repositioning, and alternative employment.

STRICT DATA INTEGRITY:
- If commercial freight revenue is unrecorded: does NOT invent revenue.
- Returns ECONOMIC_COMPARISON_INCOMPLETE status.
- Highlights confidence and data gaps transparently.
"""
from typing import Optional, Dict, Any, List


class RepositioningEconomicsService:
    @staticmethod
    def compare_strategies(
        vessel_name: str,
        idle_days: Optional[float],
        daily_vessel_cost: Optional[float],
        repositioning_options: List[Dict[str, Any]],
        commercial_revenue_usd: Optional[float] = None,
        data_confidence: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Compares WAIT / IDLE vs REPOSITION TO ALTERNATIVE CARGO.
        """
        # 1. Evaluate WAIT / IDLE Strategy
        wait_idle_cost = None
        if idle_days is not None and daily_vessel_cost is not None:
            wait_idle_cost = round(idle_days * daily_vessel_cost, 2)

        wait_strategy = {
            "strategy_name": "WAIT / IDLE AT PORT",
            "idle_days": idle_days,
            "repositioning_days": 0.0,
            "distance_nm": 0.0,
            "distance_method": "STATIONARY",
            "bunker_cost": 0.0,
            "daily_cost": daily_vessel_cost,
            "estimated_total_cost": wait_idle_cost,
            "cost_status": "CALCULATED" if wait_idle_cost is not None else "UNAVAILABLE",
            "summary": (
                f"Wait at current location. Holding cost ${wait_idle_cost:,.2f} over {idle_days:.1f} days."
                if wait_idle_cost is not None
                else "Wait at current location. Daily vessel cost unrecorded; exact economic loss unavailable."
            )
        }

        # 2. Evaluate Repositioning Candidates
        repo_strategies = []
        for opt in repositioning_options:
            target_port = opt.get("target_port_name", "Target Port")
            cargo_name = opt.get("cargo_name", "Cargo Opportunity")
            sailing_days = opt.get("sailing_days")
            distance_nm = opt.get("distance_nm")
            bunker_cost = opt.get("estimated_bunker_cost")
            total_cost = opt.get("estimated_total_cost")

            repo_strategies.append({
                "strategy_name": f"REPOSITION TO {target_port.upper()} ({cargo_name})",
                "idle_days": 0.0,
                "repositioning_days": sailing_days,
                "distance_nm": distance_nm,
                "distance_method": opt.get("distance_method", "UNKNOWN"),
                "bunker_cost": bunker_cost,
                "daily_cost": daily_vessel_cost,
                "estimated_total_cost": total_cost,
                "cost_status": "CALCULATED" if total_cost is not None else "INCOMPLETE",
                "summary": (
                    f"Ballast steaming {distance_nm:,.0f} NM ({sailing_days:.1f} days). Est cost: ${total_cost:,.2f}."
                    if total_cost is not None
                    else f"Ballast steaming {distance_nm or 0:,.0f} NM. Complete bunker/charter economics unrecorded."
                )
            })

        # 3. Commercial Revenue Assessment
        comparison_status = "COMPLETE" if (
            wait_idle_cost is not None and
            all(r["cost_status"] == "CALCULATED" for r in repo_strategies)
        ) else "ECONOMIC_COMPARISON_INCOMPLETE"

        revenue_status = (
            f"Commercial freight revenue of ${commercial_revenue_usd:,.2f} verified."
            if commercial_revenue_usd is not None
            else "Commercial freight revenue not recorded in requirement. Revenue and net TCE cannot be fabricated."
        )

        return {
            "vessel_name": vessel_name,
            "comparison_status": comparison_status,
            "data_confidence": data_confidence,
            "revenue_status": revenue_status,
            "wait_strategy": wait_strategy,
            "repositioning_strategies": repo_strategies,
            "recommendation_note": (
                "Direct economic comparison complete."
                if comparison_status == "COMPLETE"
                else "Economic comparison incomplete: Daily vessel cost, bunker consumption, or freight revenue requires verification before final financial ranking."
            )
        }
