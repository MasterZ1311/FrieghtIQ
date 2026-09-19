from typing import Optional, Dict, Any
from pydantic import BaseModel

class BreakEvenAnalysisResult(BaseModel):
    reference_contract_rate_usd_pmt: Optional[float]
    modeled_break_even_spot_rate_usd_pmt: Optional[float]
    current_spot_rate_usd_pmt: float
    rate_delta_usd_pmt: Optional[float]
    rate_delta_pct: Optional[float]
    total_quantity_mt: float
    planning_horizon_days: int
    status: str # "AVAILABLE" or "REFERENCE_RATE_UNAVAILABLE"
    methodology_label: str
    assumptions_summary: str
    decision_interpretation: str

class BreakEvenService:
    """
    Computes modeled break-even spot rate where multi-voyage contracts become economically preferable:
    At what future average spot rate does a multi-voyage COA beat remaining exposed to repeated spot fixtures?
    Strictly marked as 'Modeled break-even rate' - not a guaranteed outcome.
    """

    @staticmethod
    def calculate_break_even(
        current_spot_rate: float,
        contract_reference_rate: Optional[float],
        total_quantity_mt: float,
        planning_horizon_days: int = 180,
        volume_concession_pct: float = 0.02
    ) -> BreakEvenAnalysisResult:
        if current_spot_rate <= 0:
            raise ValueError("Current spot rate must be strictly positive.")
        if total_quantity_mt <= 0:
            raise ValueError("Total quantity must be strictly positive.")

        if contract_reference_rate is None or contract_reference_rate <= 0:
            return BreakEvenAnalysisResult(
                reference_contract_rate_usd_pmt=None,
                modeled_break_even_spot_rate_usd_pmt=None,
                current_spot_rate_usd_pmt=round(current_spot_rate, 2),
                rate_delta_usd_pmt=None,
                rate_delta_pct=None,
                total_quantity_mt=round(total_quantity_mt, 2),
                planning_horizon_days=planning_horizon_days,
                status="REFERENCE_RATE_UNAVAILABLE",
                methodology_label="Modeled break-even rate (Scenario baseline)",
                assumptions_summary="Reference contract quotation unavailable; break-even cannot be computed without a benchmark contract rate.",
                decision_interpretation="Pending commercial contract quote verification."
            )

        # Modeled break-even: the spot rate where spot freight equals contracted freight
        # In presence of volume discount, break-even equals the net contracted rate
        break_even_rate = round(contract_reference_rate, 2)
        delta_usd = round(break_even_rate - current_spot_rate, 2)
        delta_pct = round((delta_usd / current_spot_rate) * 100, 2)

        if delta_usd > 0:
            interp = (
                f"If average spot rates over the {planning_horizon_days}-day horizon rise above ${break_even_rate:.2f}/MT "
                f"(+{delta_pct:.1f}% above current ${current_spot_rate:.2f}/MT), the multi-voyage strategy provides modeled cost protection."
            )
        else:
            interp = (
                f"Multi-voyage contract rate (${break_even_rate:.2f}/MT) is currently {abs(delta_pct):.1f}% below prompt spot "
                f"(${current_spot_rate:.2f}/MT). Multi-voyage commitments lock in immediate economic discount unless spot drops below ${break_even_rate:.2f}/MT."
            )

        return BreakEvenAnalysisResult(
            reference_contract_rate_usd_pmt=round(contract_reference_rate, 2),
            modeled_break_even_spot_rate_usd_pmt=break_even_rate,
            current_spot_rate_usd_pmt=round(current_spot_rate, 2),
            rate_delta_usd_pmt=delta_usd,
            rate_delta_pct=delta_pct,
            total_quantity_mt=round(total_quantity_mt, 2),
            planning_horizon_days=planning_horizon_days,
            status="AVAILABLE",
            methodology_label="Modeled break-even rate (Economic equivalence threshold)",
            assumptions_summary=f"Evaluates point of parity between fixed multi-voyage contract commitment and open spot procurement over {planning_horizon_days} days.",
            decision_interpretation=interp
        )
