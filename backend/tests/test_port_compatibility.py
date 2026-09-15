"""
Automated Tests: Port Compatibility Rules
=========================================
Tests physical draught, LOA, beam, DWT, tidal, and congestion limits.
"""
import pytest
from app.domain.models import Port, Vessel, Cargo
from app.domain.port_rules import evaluate_port_compatibility
from app.services.port_service import check_compatibility


def test_capesize_fails_at_shallow_haldia():
    """Capesize vessel (18m draft) must fail at shallow river port Haldia (8.5m draft)."""
    haldia = Port(
        name="Haldia",
        country="India",
        region="destination",
        max_loa=230.0,
        max_beam=32.5,
        max_draft=8.5,
        handling_rate=18000.0,
        max_dwt=55000.0,
    )
    capesize = Vessel(
        vessel_type="Capesize",
        capacity_mt=180000.0,
        loa=295.0,
        beam=45.0,
        draft=18.0,
        speed=14.5,
        daily_cost=13000.0,
    )
    cargo = Cargo(
        commodity="Coal",
        quantity_mt=150000.0,
        origin="Australia",
        destination="Haldia",
    )

    result = evaluate_port_compatibility(haldia, capesize, cargo)
    assert result["compatible"] is False
    # Verify Draft constraint failed
    draft_constraint = next(c for c in result["constraints"] if c["constraint"] == "Draft")
    assert draft_constraint["status"] == "FAIL"
    # Verify LOA constraint failed
    loa_constraint = next(c for c in result["constraints"] if c["constraint"] == "Length (LOA)")
    assert loa_constraint["status"] == "FAIL"


def test_capesize_succeeds_at_deepwater_gangavaram():
    """Capesize vessel (18m draft) must be compatible at deepwater Gangavaram (18.0m draft)."""
    gangavaram = Port(
        name="Gangavaram",
        country="India",
        region="destination",
        max_loa=330.0,
        max_beam=55.0,
        max_draft=18.0,
        handling_rate=35000.0,
        max_dwt=200000.0,
    )
    capesize = Vessel(
        vessel_type="Capesize",
        capacity_mt=180000.0,
        loa=295.0,
        beam=45.0,
        draft=17.5,
        speed=14.5,
        daily_cost=13000.0,
    )
    cargo = Cargo(
        commodity="Coal",
        quantity_mt=160000.0,
        origin="Australia",
        destination="Gangavaram",
    )

    result = evaluate_port_compatibility(gangavaram, capesize, cargo)
    assert result["compatible"] is True
    assert all(c["status"] != "FAIL" for c in result["constraints"])


def test_tidal_and_commodity_warnings():
    """Tidal ports and non-standard commodities should trigger informative WARNING status."""
    port = Port(
        name="Gopalpur",
        country="India",
        region="destination",
        max_loa=220.0,
        max_beam=38.0,
        max_draft=11.5,
        handling_rate=12000.0,
        max_dwt=60000.0,
        tide_restricted=True,
        suitable_commodities=["Coal", "Iron Ore"],
    )
    supramax = Vessel(
        vessel_type="Supramax",
        capacity_mt=55000.0,
        loa=190.0,
        beam=32.2,
        draft=10.5,
        speed=14.0,
        daily_cost=8500.0,
    )
    cargo = Cargo(
        commodity="Fertilizer",  # Not in suitable commodities
        quantity_mt=50000.0,
        origin="Mozambique",
        destination="Gopalpur",
    )

    result = evaluate_port_compatibility(port, supramax, cargo)
    assert result["compatible"] is True  # Warnings do not fail compatibility
    tide_c = next(c for c in result["constraints"] if c["constraint"] == "Tide Restriction")
    assert tide_c["status"] == "WARNING"
    comm_c = next(c for c in result["constraints"] if c["constraint"] == "Commodity Handling")
    assert comm_c["status"] == "WARNING"


def test_service_level_check_compatibility_deterministic_fallback():
    """Service check_compatibility should work even with None DB using demo fallback."""
    result = check_compatibility(
        db=None,
        port_name="Paradip",
        vessel_class="Panamax",
        cargo_mt=70000.0,
        commodity="Coal",
    )
    assert "compatible" in result
    assert "constraints" in result
    assert result["port"] == "Paradip"
    assert result["vessel_class"] == "Panamax"
    assert result["handling_rate"] > 0
