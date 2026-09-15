"""
Automated Tests: Vessel Selection & Recommendation Rules
========================================================
Tests vessel match scoring, load factor, geographic barriers, and ranking.
"""
import pytest
from app.domain.models import Cargo, Vessel, Port
from app.domain.vessel_rules import evaluate_vessel_candidate, rank_vessel_options
from app.services.vessel_service import recommend_vessels


def test_panamax_preferred_for_70k_coal_shipment():
    """Panamax should achieve highest fit score for standard 70k MT coal shipment."""
    cargo = Cargo(commodity="Coal", quantity_mt=70000.0, origin="Australia", destination="Visakhapatnam")
    dest_port = Port(
        name="Visakhapatnam",
        country="India",
        region="destination",
        max_loa=320.0,
        max_beam=52.0,
        max_draft=15.0,
        handling_rate=30000.0,
        max_dwt=200000.0,
    )
    panamax = Vessel(
        vessel_type="Panamax",
        capacity_mt=75000.0,
        dwt_min=65000.0,
        dwt_max=82000.0,
        loa=225.0,
        beam=32.2,
        draft=14.0,
        speed=14.5,
        daily_cost=9500.0,
        fuel_consumption_mt_day=34.0,
    )
    supramax = Vessel(
        vessel_type="Supramax",
        capacity_mt=58000.0,
        dwt_min=50000.0,
        dwt_max=65000.0,
        loa=200.0,
        beam=32.2,
        draft=12.8,
        speed=14.0,
        daily_cost=8500.0,
        fuel_consumption_mt_day=28.0,
    )

    pana_eval = evaluate_vessel_candidate(panamax, cargo, dest_port, 12.0, 4800.0)
    supra_eval = evaluate_vessel_candidate(supramax, cargo, dest_port, 14.0, 4800.0)

    assert pana_eval["fit_score"] > supra_eval["fit_score"]
    assert pana_eval["port_compatible"] is True
    # Supramax should have warning because 70k exceeds 65k DWT max
    assert any("exceeds" in w.lower() for w in supra_eval["warnings"])


def test_capesize_blocked_from_indonesia_origin():
    """Capesize must be rejected or penalized on Indonesian origin coal routes."""
    cargo = Cargo(commodity="Coal", quantity_mt=150000.0, origin="Indonesia", destination="Paradip")
    dest_port = Port(
        name="Paradip",
        country="India",
        region="destination",
        max_loa=300.0,
        max_beam=48.0,
        max_draft=14.5,
        handling_rate=30000.0,
    )
    capesize = Vessel(
        vessel_type="Capesize",
        capacity_mt=180000.0,
        dwt_min=150000.0,
        dwt_max=200000.0,
        loa=295.0,
        beam=45.0,
        draft=18.0,
        speed=14.5,
        daily_cost=13000.0,
    )
    eval_res = evaluate_vessel_candidate(capesize, cargo, dest_port, 6.0, 2000.0)
    assert eval_res["port_compatible"] is False or eval_res["fit_score"] <= 20.0
    assert any("capesize" in w.lower() for w in eval_res["warnings"])


def test_service_level_vessel_recommendation():
    """Service recommend_vessels returns structured decision and alternatives."""
    res = recommend_vessels(
        db=None,
        origin="Australia",
        destination="Paradip",
        commodity="Coal",
        cargo_mt=70000.0,
    )
    assert "decision" in res
    assert "recommended_class" in res
    assert res["recommended_class"] == "Panamax"
    assert len(res["alternatives"]) >= 3
    assert res["score"] > 50.0
    assert len(res["reasons"]) > 0
