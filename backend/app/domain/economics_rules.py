"""
Voyage Economics & Maritime Physics Domain Rules
================================================
Pure domain calculations for voyage performance, bunker consumption,
operating expenses, port & canal dues, TCE, and breakeven rates.
"""
from typing import Dict, Any, Optional
from app.domain.models import Cargo, Vessel, Port


CANAL_TRANSIT_FEES = {
    "suez": 250000.0,
    "panama": 180000.0,
}

ORIGIN_CANAL_REQUIREMENT = {
    "united states": "suez",
    "russia": "suez",
}


def calculate_voyage_economics(
    cargo: Cargo,
    vessel: Vessel,
    dest_port: Port,
    distance_nm: float,
    freight_rate_usd_per_mt: float,
    bunker_price_usd_per_mt: float = 650.0,
    port_days_origin: float = 2.0,
    port_days_dest: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Executes maritime voyage economics equations.
    """
    speed = vessel.speed if vessel.speed > 0 else 14.0
    daily_fuel = vessel.fuel_consumption_mt_day if vessel.fuel_consumption_mt_day > 0 else 30.0
    daily_opex = vessel.daily_cost if vessel.daily_cost > 0 else 9000.0

    # 1. Timeline
    sea_days = distance_nm / (speed * 24.0) if distance_nm > 0 else 1.0
    if port_days_dest is None:
        # Calculate from port handling rate
        hr = dest_port.handling_rate if dest_port.handling_rate > 0 else 25000.0
        port_days_dest = (cargo.quantity_mt / hr) + 1.0  # discharge time + mooring/unmooring

    total_port_days = port_days_origin + port_days_dest
    total_voyage_days = sea_days + total_port_days

    # 2. Bunker Fuel Consumption (Main Engine at sea + Aux Gens in port)
    sea_bunker_mt = daily_fuel * sea_days
    port_bunker_mt = (daily_fuel * 0.15) * total_port_days
    total_bunker_mt = sea_bunker_mt + port_bunker_mt
    bunker_cost_usd = total_bunker_mt * bunker_price_usd_per_mt

    # 3. Port Dues & Tariffs
    port_dues_dest = dest_port.port_dues_usd if dest_port.port_dues_usd > 0 else 25000.0
    port_dues_origin = 15000.0  # Estimated load port disbursement
    port_dues_total_usd = port_dues_origin + port_dues_dest

    # 4. Canal Dues
    canal_key = ORIGIN_CANAL_REQUIREMENT.get(cargo.origin.strip().lower())
    canal_dues_usd = CANAL_TRANSIT_FEES.get(canal_key, 0.0) if canal_key else 0.0

    # 5. Operating Costs & Revenues
    opex_total_usd = daily_opex * total_voyage_days
    voyage_expenses_usd = bunker_cost_usd + port_dues_total_usd + canal_dues_usd
    total_cost_usd = voyage_expenses_usd + opex_total_usd

    freight_revenue_usd = freight_rate_usd_per_mt * cargo.quantity_mt
    gross_profit_usd = freight_revenue_usd - total_cost_usd

    # 6. Time Charter Equivalent (TCE) & Breakeven
    # Standard maritime formula: TCE = (Freight Revenue - Voyage Expenses) / Total Voyage Days
    rounded_voyage_days = round(total_voyage_days, 1)
    tce_usd_per_day = (freight_revenue_usd - voyage_expenses_usd) / rounded_voyage_days if rounded_voyage_days > 0 else 0.0
    cost_per_mt = total_cost_usd / cargo.quantity_mt if cargo.quantity_mt > 0 else 0.0
    breakeven_rate_usd_per_mt = cost_per_mt
    margin_pct = (gross_profit_usd / freight_revenue_usd * 100.0) if freight_revenue_usd > 0 else 0.0

    return {
        "origin": cargo.origin,
        "destination": cargo.destination,
        "vessel_class": vessel.vessel_type,
        "vessel_type": vessel.vessel_type,
        "cargo_mt": cargo.quantity_mt,
        "quantity_mt": cargo.quantity_mt,
        "distance_nm": round(distance_nm, 1),
        "sea_days": round(sea_days, 1),
        "port_days": round(total_port_days, 1),
        "total_voyage_days": round(total_voyage_days, 1),
        "freight_revenue_usd": round(freight_revenue_usd, 0),
        "freight_revenue": round(freight_revenue_usd, 0),
        "freight_rate_usd_per_mt": round(freight_rate_usd_per_mt, 2),
        "freight_rate": round(freight_rate_usd_per_mt, 2),
        "bunker_cost_usd": round(bunker_cost_usd, 0),
        "bunker_cost": round(bunker_cost_usd, 0),
        "port_dues_usd": round(port_dues_total_usd, 0),
        "port_dues": round(port_dues_total_usd, 0),
        "canal_dues_usd": round(canal_dues_usd, 0),
        "canal_dues": round(canal_dues_usd, 0),
        "opex_usd": round(opex_total_usd, 0),
        "opex": round(opex_total_usd, 0),
        "total_cost_usd": round(total_cost_usd, 0),
        "total_cost": round(total_cost_usd, 0),
        "cost_per_mt": round(cost_per_mt, 2),
        "gross_profit_usd": round(gross_profit_usd, 0),
        "gross_profit": round(gross_profit_usd, 0),
        "tce_usd_per_day": round(max(0.0, tce_usd_per_day), 0),
        "tce": round(max(0.0, tce_usd_per_day), 0),
        "breakeven_rate_usd_per_mt": round(breakeven_rate_usd_per_mt, 2),
        "breakeven_rate": round(breakeven_rate_usd_per_mt, 2),
        "margin_pct": round(margin_pct, 1),
        "disclaimer": "[DEMO] Voyage economics calculated using synthetic operational parameters.",
    }
