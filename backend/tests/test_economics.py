"""
Automated Tests: Voyage Economics & Maritime Physics
===================================================
Tests sea days, bunker consumption, TCE equations, and breakeven rates.
"""
import pytest
from app.domain.models import Cargo, Vessel, Port
from app.domain.economics_rules import calculate_voyage_economics
from app.services.economics_service import calculate_economics


def test_voyage_economics_calculations():
    """Validates core maritime economics formulas."""
    cargo = Cargo(commodity="Coal", quantity_mt=70000.0, origin="Australia", destination="Gangavaram")
    vessel = Vessel(
        vessel_type="Panamax",
        capacity_mt=75000.0,
        loa=225.0,
        beam=32.2,
        draft=14.0,
        speed=14.5,
        daily_cost=9500.0,
        fuel_consumption_mt_day=34.0,
    )
    port = Port(
        name="Gangavaram",
        country="India",
        region="destination",
        max_loa=330.0,
        max_beam=55.0,
        max_draft=18.0,
        handling_rate=35000.0,
        port_dues_usd=28000.0,
    )

    distance_nm = 5000.0
    freight_rate = 14.00
    bunker_price = 650.0

    res = calculate_voyage_economics(
        cargo=cargo,
        vessel=vessel,
        dest_port=port,
        distance_nm=distance_nm,
        freight_rate_usd_per_mt=freight_rate,
        bunker_price_usd_per_mt=bunker_price,
        port_days_origin=2.0,
    )

    # 1. Sea days = 5000 / (14.5 * 24) = 14.368 days
    assert 14.0 <= res["sea_days"] <= 15.0

    # 2. Port days = 2.0 (origin) + (70000 / 35000 + 1) = 5.0 days
    assert 4.5 <= res["port_days"] <= 5.5

    # 3. Freight revenue = 14.00 * 70000 = $980,000
    assert res["freight_revenue"] == 980000.0

    # 4. Total cost > 0, breakeven > 0
    assert res["total_cost"] > 0
    assert res["breakeven_rate"] > 0
    assert res["cost_per_mt"] == res["breakeven_rate"]

    # 5. TCE equation: (Revenue - Voyage Expenses) / Total Days
    voyage_expenses = res["bunker_cost"] + res["port_dues"] + res["canal_dues"]
    expected_tce = (res["freight_revenue"] - voyage_expenses) / res["total_voyage_days"]
    assert abs(res["tce"] - round(expected_tce, 0)) <= 2.0


def test_bunker_price_sensitivity():
    """Higher bunker prices should increase total cost and decrease gross profit."""
    res_cheap = calculate_economics(
        db=None,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000.0,
        freight_rate_usd_per_mt=15.0,
        bunker_price_usd_per_mt=500.0,
    )
    res_expensive = calculate_economics(
        db=None,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000.0,
        freight_rate_usd_per_mt=15.0,
        bunker_price_usd_per_mt=850.0,
    )

    assert res_expensive["bunker_cost"] > res_cheap["bunker_cost"]
    assert res_expensive["total_cost"] > res_cheap["total_cost"]
    assert res_expensive["gross_profit"] < res_cheap["gross_profit"]
    assert res_expensive["tce"] < res_cheap["tce"]
