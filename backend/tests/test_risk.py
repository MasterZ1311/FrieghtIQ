"""
Automated Tests: Multi-Factor Deterministic Risk Engine
======================================================
Tests multi-dimension risk scoring, transit exposure, weather seasonality, and levels.
"""
from datetime import date
import pytest
from app.domain.models import Cargo, Vessel, Port
from app.domain.risk_rules import score_risk_dimensions
from app.services.risk_service import score_risk


def test_russia_origin_higher_transit_risk_than_australia():
    """Russia origin routes must yield higher transit & canal exposure than Australian routes."""
    vessel = Vessel(
        vessel_type="Panamax",
        capacity_mt=75000.0,
        loa=225.0,
        beam=32.2,
        draft=14.0,
        speed=14.5,
        daily_cost=9500.0,
    )
    port = Port(
        name="Paradip",
        country="India",
        region="destination",
        max_loa=300.0,
        max_beam=48.0,
        max_draft=14.5,
        handling_rate=30000.0,
    )

    cargo_russia = Cargo(commodity="Coal", quantity_mt=70000.0, origin="Russia", destination="Paradip")
    cargo_aus = Cargo(commodity="Coal", quantity_mt=70000.0, origin="Australia", destination="Paradip")

    risk_russia = score_risk_dimensions(cargo_russia, vessel, port)
    risk_aus = score_risk_dimensions(cargo_aus, vessel, port)

    sched_russia = next(f for f in risk_russia.risk_factors if f.name == "Schedule Risk")
    sched_aus = next(f for f in risk_aus.risk_factors if f.name == "Schedule Risk")

    assert sched_russia.score > sched_aus.score
    assert risk_russia.overall_risk_score > risk_aus.overall_risk_score


def test_monsoon_months_yield_higher_weather_risk():
    """Laycan in monsoon months (July) should score higher schedule/weather risk than dry winter (February)."""
    vessel = Vessel(
        vessel_type="Panamax",
        capacity_mt=75000.0,
        loa=225.0,
        beam=32.2,
        draft=14.0,
        speed=14.5,
        daily_cost=9500.0,
    )
    port = Port(
        name="Paradip",
        country="India",
        region="destination",
        max_loa=300.0,
        max_beam=48.0,
        max_draft=14.5,
        handling_rate=30000.0,
    )
    cargo = Cargo(commodity="Coal", quantity_mt=70000.0, origin="Australia", destination="Paradip")

    monsoon_risk = score_risk_dimensions(cargo, vessel, port, laycan_date=date(2026, 7, 15))
    dry_risk = score_risk_dimensions(cargo, vessel, port, laycan_date=date(2026, 2, 15))

    sched_monsoon = next(f for f in monsoon_risk.risk_factors if f.name == "Schedule Risk")
    sched_dry = next(f for f in dry_risk.risk_factors if f.name == "Schedule Risk")

    assert sched_monsoon.score > sched_dry.score
    assert "monsoon" in sched_monsoon.description.lower()


def test_service_level_risk_analysis():
    """Service score_risk returns 6 factors, component scores, top risks, and actionable recommendations."""
    res = score_risk(
        db=None,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        commodity="Coal",
        cargo_mt=70000.0,
        contract_type="Spot",
    )
    assert "overall_risk_score" in res
    assert "overall_risk_level" in res
    assert 0.0 <= res["overall_risk_score"] <= 100.0
    assert len(res["risk_factors"]) == 6
    assert "component_scores" in res
    assert len(res["component_scores"]) == 6
    assert len(res["top_risks"]) <= 3
    assert len(res["recommended_actions"]) > 0
