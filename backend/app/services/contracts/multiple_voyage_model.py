from typing import Optional, Dict, Any
from pydantic import BaseModel

class MultipleVoyageCostResult(BaseModel):
    contract_rate: Optional[float]
    total_contracted_quantity_mt: float
    voyage_count: int
    parcel_size_mt: float
    contract_duration_str: str
    contract_freight_cost: Optional[float]
    rate_status: str # "AVAILABLE" or "REFERENCE_RATE_UNAVAILABLE"
    volume_concession_pct: float
    concession_amount_usd: float
    is_scenario_based: bool
    assumptions_summary: str

class MultipleVoyageCostModel:
    """
    Evaluates multi-voyage Contract of Affreightment (COA) / time-commitments.
    Formula: Contract Freight Cost = Contract Rate * Contracted Quantity
    Strictly flags REFERENCE_RATE_UNAVAILABLE if no market or reference rate is provided.
    """

    @staticmethod
    def calculate_contract_cost(
        contracted_quantity_mt: float,
        voyage_count: int,
        parcel_size_mt: float,
        contract_duration_str: str,
        reference_rate_usd_pmt: Optional[float] = None,
        volume_concession_pct: float = 0.0 # e.g. 0.015 for 1.5% multi-voyage volume discount
    ) -> MultipleVoyageCostResult:
        if contracted_quantity_mt <= 0:
            raise ValueError("Contracted quantity must be strictly positive.")
        if voyage_count <= 0:
            raise ValueError("Voyage count must be at least 1.")

        if reference_rate_usd_pmt is None or reference_rate_usd_pmt <= 0:
            return MultipleVoyageCostResult(
                contract_rate=None,
                total_contracted_quantity_mt=contracted_quantity_mt,
                voyage_count=voyage_count,
                parcel_size_mt=parcel_size_mt,
                contract_duration_str=contract_duration_str,
                contract_freight_cost=None,
                rate_status="REFERENCE_RATE_UNAVAILABLE",
                volume_concession_pct=volume_concession_pct,
                concession_amount_usd=0.0,
                is_scenario_based=True,
                assumptions_summary="No explicit bilateral contract quotation found. Contract rate flagged as REFERENCE_RATE_UNAVAILABLE."
            )

        # Apply documented volume commitment concession
        effective_rate = reference_rate_usd_pmt * (1.0 - volume_concession_pct)
        total_cost = effective_rate * contracted_quantity_mt
        concession_amount = (reference_rate_usd_pmt - effective_rate) * contracted_quantity_mt

        return MultipleVoyageCostResult(
            contract_rate=round(effective_rate, 2),
            total_contracted_quantity_mt=round(contracted_quantity_mt, 2),
            voyage_count=voyage_count,
            parcel_size_mt=round(parcel_size_mt, 2),
            contract_duration_str=contract_duration_str,
            contract_freight_cost=round(total_cost, 2),
            rate_status="AVAILABLE",
            volume_concession_pct=round(volume_concession_pct * 100, 2),
            concession_amount_usd=round(concession_amount, 2),
            is_scenario_based=False,
            assumptions_summary=f"Derived from reference fix rate ${reference_rate_usd_pmt:.2f}/MT with {volume_concession_pct*100:.1f}% multi-voyage volume concession."
        )
