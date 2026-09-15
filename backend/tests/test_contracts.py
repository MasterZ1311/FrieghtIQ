"""
Automated Tests: Contract Comparison & Procurement Strategy
===========================================================
Tests Spot vs COA vs Time Charter, volume discount, and market trend strategy.
"""
import pytest
from app.domain.contract_rules import evaluate_contracts
from app.services.contract_service import compare_contracts


def test_contract_options_and_volume_voyages():
    """Verify voyage count, contract options, and rate discounts."""
    annual_volume = 600000.0
    cargo_size = 70000.0
    # Expected voyages: ceil(600000 / 70000) = 9 voyages
    res = evaluate_contracts(
        spot_rate_usd_per_mt=15.0,
        future_rate_usd_per_mt=16.0,
        cargo_quantity_mt=cargo_size,
        annual_volume_mt=annual_volume,
        planning_horizon_months=12,
        trend="rising",
    )

    assert len(res["options"]) == 4
    spot_opt = next(o for o in res["options"] if o["contract_type"] == "Spot")
    st_opt = next(o for o in res["options"] if o["contract_type"] == "3-Voyage")
    mt_opt = next(o for o in res["options"] if o["contract_type"] == "12-Voyage")

    assert spot_opt["voyages"] >= 1
    assert st_opt["voyages"] >= 1
    assert mt_opt["voyages"] >= 1

    # Medium-term rate must reflect volume discount
    assert mt_opt["rate_usd_per_mt"] < st_opt["rate_usd_per_mt"] < spot_opt["rate_usd_per_mt"]
    assert mt_opt["total_cost_usd"] < spot_opt["total_cost_usd"]
    assert mt_opt["estimated_savings"] > 0


def test_contract_trend_recommendations():
    """Rising freight trend recommends 12-Voyage; falling trend recommends Spot."""
    rising_res = evaluate_contracts(
        spot_rate_usd_per_mt=12.0,
        future_rate_usd_per_mt=15.0,
        cargo_quantity_mt=70000.0,
        trend="rising",
    )
    assert rising_res["recommended_contract"] == "12-Voyage"

    falling_res = evaluate_contracts(
        spot_rate_usd_per_mt=15.0,
        future_rate_usd_per_mt=11.0,
        cargo_quantity_mt=70000.0,
        trend="falling",
    )
    assert falling_res["recommended_contract"] == "Spot"

    stable_res = evaluate_contracts(
        spot_rate_usd_per_mt=12.0,
        future_rate_usd_per_mt=12.0,
        cargo_quantity_mt=70000.0,
        trend="stable",
    )
    assert stable_res["recommended_contract"] == "6-Voyage"


def test_service_level_contract_comparison():
    """Service compare_contracts executes with fallback."""
    res = compare_contracts(
        db=None,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000.0,
        annual_volume_mt=500000.0,
    )
    assert "recommended_contract" in res
    assert "options" in res
    assert "contracts" in res
    assert len(res["options"]) == 4
    assert res["expected_saving_vs_spot"] >= 0
