"""
FreightIQ Seed Data & Synthetic Datasets Generator
=================================================
All data below is strictly SYNTHETIC / DEMO data generated for hackathon demonstration.
It reflects maritime physics, port engineering parameters, and economic relationships,
but does NOT represent actual market data, proprietary shipping quotes, or official port logs.

Explicit Classification: [DEMO] Synthetic Data
"""
from datetime import date, timedelta
import random
import math

random.seed(42)

# ─── 1. PORT DATA (Origins & East Coast India Destinations) ───────────────────

PORTS = [
    # ── ORIGIN PORTS ──────────────────────────────────────────────────────────
    {
        "name": "Newcastle",
        "country": "Australia",
        "region": "origin",
        "max_dwt": 200000,
        "max_draft_m": 15.0,
        "max_loa_m": 330.0,
        "max_beam_m": 55.0,
        "berths": 14,
        "tide_restricted": False,
        "congestion_level": "medium",
        "avg_turnaround_days": 4.5,
        "handling_rate_mt_day": 35000,
        "port_dues_usd_per_call": 12000,
        "suitable_commodities": ["Coal", "Grain"],
        "latitude": -32.927,
        "longitude": 151.777,
        "notes": "Major Australian coal export terminal. High-speed belt conveyor loader capacity ~35k MT/day.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Port Hedland",
        "country": "Australia",
        "region": "origin",
        "max_dwt": 280000,
        "max_draft_m": 19.0,
        "max_loa_m": 340.0,
        "max_beam_m": 65.0,
        "berths": 10,
        "tide_restricted": True,
        "congestion_level": "low",
        "avg_turnaround_days": 3.0,
        "handling_rate_mt_day": 45000,
        "port_dues_usd_per_call": 15000,
        "suitable_commodities": ["Iron Ore"],
        "latitude": -20.316,
        "longitude": 118.573,
        "notes": "World's premier bulk mineral export gateway. Very deep water, tidal exit windows.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Baltimore",
        "country": "United States",
        "region": "origin",
        "max_dwt": 120000,
        "max_draft_m": 13.7,
        "max_loa_m": 290.0,
        "max_beam_m": 50.0,
        "berths": 8,
        "tide_restricted": False,
        "congestion_level": "medium",
        "avg_turnaround_days": 5.0,
        "handling_rate_mt_day": 20000,
        "port_dues_usd_per_call": 18000,
        "suitable_commodities": ["Coal", "Grain"],
        "latitude": 39.283,
        "longitude": -76.613,
        "notes": "US Mid-Atlantic coal/grain hub. Draft restricted to Panamax/Baby-Cape size.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Hampton Roads",
        "country": "United States",
        "region": "origin",
        "max_dwt": 150000,
        "max_draft_m": 14.5,
        "max_loa_m": 305.0,
        "max_beam_m": 52.0,
        "berths": 12,
        "tide_restricted": False,
        "congestion_level": "low",
        "avg_turnaround_days": 4.0,
        "handling_rate_mt_day": 30000,
        "port_dues_usd_per_call": 20000,
        "suitable_commodities": ["Coal", "Grain", "Fertilizer"],
        "latitude": 36.831,
        "longitude": -76.298,
        "notes": "Norfolk/Newport News metallurgical & thermal coal export hub.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Nacala",
        "country": "Mozambique",
        "region": "origin",
        "max_dwt": 180000,
        "max_draft_m": 14.0,
        "max_loa_m": 300.0,
        "max_beam_m": 50.0,
        "berths": 4,
        "tide_restricted": False,
        "congestion_level": "high",
        "avg_turnaround_days": 7.0,
        "handling_rate_mt_day": 15000,
        "port_dues_usd_per_call": 8000,
        "suitable_commodities": ["Coal"],
        "latitude": -14.541,
        "longitude": 40.700,
        "notes": "Moatize basin coal corridor terminus. Moderate handling rate, rail bottlenecks.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Murmansk",
        "country": "Russia",
        "region": "origin",
        "max_dwt": 100000,
        "max_draft_m": 12.5,
        "max_loa_m": 270.0,
        "max_beam_m": 45.0,
        "berths": 6,
        "tide_restricted": False,
        "congestion_level": "medium",
        "avg_turnaround_days": 5.5,
        "handling_rate_mt_day": 18000,
        "port_dues_usd_per_call": 9000,
        "suitable_commodities": ["Coal", "Fertilizer"],
        "latitude": 68.973,
        "longitude": 33.091,
        "notes": "Ice-free Russian Arctic port. Suitable for Handysize/Supramax/Panamax.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Kalimantan",
        "country": "Indonesia",
        "region": "origin",
        "max_dwt": 80000,
        "max_draft_m": 12.0,
        "max_loa_m": 250.0,
        "max_beam_m": 43.0,
        "berths": 8,
        "tide_restricted": True,
        "congestion_level": "medium",
        "avg_turnaround_days": 4.0,
        "handling_rate_mt_day": 20000,
        "port_dues_usd_per_call": 6000,
        "suitable_commodities": ["Coal", "Bauxite"],
        "latitude": -1.681,
        "longitude": 116.419,
        "notes": "East/South Kalimantan river anchorage loading. Draft limited to 12.0m. Capesize infeasible.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    # ── DESTINATION PORTS (East Coast India) ──────────────────────────────────
    {
        "name": "Paradip",
        "country": "India",
        "region": "destination",
        "max_dwt": 180000,
        "max_draft_m": 14.5,
        "max_loa_m": 300.0,
        "max_beam_m": 50.0,
        "berths": 15,
        "tide_restricted": False,
        "congestion_level": "high",
        "avg_turnaround_days": 6.0,
        "handling_rate_mt_day": 25000,
        "port_dues_usd_per_call": 22000,
        "suitable_commodities": ["Coal", "Iron Ore", "Fertilizer"],
        "latitude": 20.268,
        "longitude": 86.674,
        "notes": "Major central East Coast deep port. Draft 14.5m allows Panamax. Capesize (18m draft) cannot berth fully laden. High anchorage congestion.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Visakhapatnam",
        "country": "India",
        "region": "destination",
        "max_dwt": 200000,
        "max_draft_m": 15.0,
        "max_loa_m": 320.0,
        "max_beam_m": 52.0,
        "berths": 24,
        "tide_restricted": False,
        "congestion_level": "medium",
        "avg_turnaround_days": 5.0,
        "handling_rate_mt_day": 30000,
        "port_dues_usd_per_call": 25000,
        "suitable_commodities": ["Coal", "Iron Ore", "Grain", "Fertilizer"],
        "latitude": 17.686,
        "longitude": 83.222,
        "notes": "Major PSU natural harbour. Outer harbour takes Baby-Capesize (partially laden) and Panamax. Inner harbour draft 11.5m.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Gangavaram",
        "country": "India",
        "region": "destination",
        "max_dwt": 200000,
        "max_draft_m": 18.0,
        "max_loa_m": 330.0,
        "max_beam_m": 55.0,
        "berths": 8,
        "tide_restricted": False,
        "congestion_level": "low",
        "avg_turnaround_days": 3.5,
        "handling_rate_mt_day": 35000,
        "port_dues_usd_per_call": 28000,
        "suitable_commodities": ["Coal", "Iron Ore"],
        "latitude": 17.625,
        "longitude": 83.200,
        "notes": "Ultra-deepwater modern private terminal. 18.0m draft fully accommodates fully laden Capesize up to 200k DWT. Fast discharge.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Gopalpur",
        "country": "India",
        "region": "destination",
        "max_dwt": 60000,
        "max_draft_m": 11.0,
        "max_loa_m": 220.0,
        "max_beam_m": 38.0,
        "berths": 3,
        "tide_restricted": True,
        "congestion_level": "low",
        "avg_turnaround_days": 5.5,
        "handling_rate_mt_day": 12000,
        "port_dues_usd_per_call": 12000,
        "suitable_commodities": ["Coal", "Iron Ore"],
        "latitude": 19.257,
        "longitude": 84.886,
        "notes": "Shallow draft port in Odisha. Panamax and Capesize strictly infeasible. Handysize and small Supramax only. Tidal window required.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Dhamra",
        "country": "India",
        "region": "destination",
        "max_dwt": 180000,
        "max_draft_m": 17.0,
        "max_loa_m": 310.0,
        "max_beam_m": 52.0,
        "berths": 6,
        "tide_restricted": False,
        "congestion_level": "low",
        "avg_turnaround_days": 3.5,
        "handling_rate_mt_day": 30000,
        "port_dues_usd_per_call": 20000,
        "suitable_commodities": ["Coal", "Iron Ore", "Fertilizer"],
        "latitude": 20.784,
        "longitude": 86.904,
        "notes": "Modern deepwater bulk port. 17.0m draft accommodates Panamax and Capesize. Low turnaround and rapid mechanized unloading.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Sagar-Sandheads",
        "country": "India",
        "region": "destination",
        "max_dwt": 120000,
        "max_draft_m": 13.0,
        "max_loa_m": 280.0,
        "max_beam_m": 45.0,
        "berths": 5,
        "tide_restricted": True,
        "congestion_level": "medium",
        "avg_turnaround_days": 6.5,
        "handling_rate_mt_day": 18000,
        "port_dues_usd_per_call": 18000,
        "suitable_commodities": ["Coal", "Grain", "Fertilizer"],
        "latitude": 21.667,
        "longitude": 88.083,
        "notes": "Deep outer anchorage / transhipment lightening point for the Hooghly river system. Suitable up to Panamax; tide-restricted.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
    {
        "name": "Haldia",
        "country": "India",
        "region": "destination",
        "max_dwt": 80000,
        "max_draft_m": 9.5,
        "max_loa_m": 230.0,
        "max_beam_m": 38.0,
        "berths": 12,
        "tide_restricted": True,
        "congestion_level": "high",
        "avg_turnaround_days": 7.0,
        "handling_rate_mt_day": 12000,
        "port_dues_usd_per_call": 15000,
        "suitable_commodities": ["Coal", "Grain", "Fertilizer"],
        "latitude": 22.026,
        "longitude": 88.068,
        "notes": "River port on Hooghly estuary. Critical 9.5m draft restriction. Capesize and Panamax fully laden strictly infeasible. Handysize optimal.",
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Port Profile",
    },
]

# ─── 2. VESSEL CLASS DEFINITIONS ─────────────────────────────────────────────

VESSELS = [
    {
        "vessel_class": "Handysize",
        "name": "Handysize Bulker (Demo)",
        "dwt_min": 25000,
        "dwt_max": 40000,
        "loa_m": 190.0,
        "beam_m": 32.0,
        "draft_m": 10.5,
        "daily_opex_usd": 7000,
        "daily_hire_usd": 11000,
        "speed_kn": 13.5,
        "fuel_consumption_mt_day": 22.0,
        "suitable_commodities": ["Coal", "Grain", "Fertilizer", "Bauxite", "Iron Ore"],
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Vessel Spec",
    },
    {
        "vessel_class": "Supramax",
        "name": "Supramax Bulker (Demo)",
        "dwt_min": 50000,
        "dwt_max": 65000,
        "loa_m": 200.0,
        "beam_m": 36.0,
        "draft_m": 12.8,
        "daily_opex_usd": 8500,
        "daily_hire_usd": 15000,
        "speed_kn": 14.0,
        "fuel_consumption_mt_day": 28.0,
        "suitable_commodities": ["Coal", "Grain", "Fertilizer", "Bauxite", "Iron Ore"],
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Vessel Spec",
    },
    {
        "vessel_class": "Panamax",
        "name": "Panamax Bulker (Demo)",
        "dwt_min": 65000,
        "dwt_max": 82000,
        "loa_m": 225.0,
        "beam_m": 32.2,
        "draft_m": 14.0,
        "daily_opex_usd": 9500,
        "daily_hire_usd": 18000,
        "speed_kn": 14.5,
        "fuel_consumption_mt_day": 34.0,
        "suitable_commodities": ["Coal", "Grain", "Fertilizer", "Iron Ore"],
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Vessel Spec",
    },
    {
        "vessel_class": "Capesize",
        "name": "Capesize Bulker (Demo)",
        "dwt_min": 150000,
        "dwt_max": 200000,
        "loa_m": 295.0,
        "beam_m": 50.0,
        "draft_m": 18.0,
        "daily_opex_usd": 13000,
        "daily_hire_usd": 28000,
        "speed_kn": 14.5,
        "fuel_consumption_mt_day": 58.0,
        "suitable_commodities": ["Coal", "Iron Ore"],
        "is_demo": True,
        "data_label": "[DEMO] Synthetic Vessel Spec",
    },
]

# ─── 3. ROUTE DISTANCE TABLE (Nautical Miles) ────────────────────────────────

ROUTE_DISTANCES = {
    # Australia
    ("Australia", "Paradip"): 5100,
    ("Australia", "Visakhapatnam"): 5200,
    ("Australia", "Gangavaram"): 5200,
    ("Australia", "Gopalpur"): 5150,
    ("Australia", "Dhamra"): 5250,
    ("Australia", "Sagar-Sandheads"): 5350,
    ("Australia", "Haldia"): 5400,
    # United States (via Suez Canal)
    ("United States", "Paradip"): 12800,
    ("United States", "Visakhapatnam"): 12900,
    ("United States", "Gangavaram"): 12900,
    ("United States", "Gopalpur"): 12850,
    ("United States", "Dhamra"): 12950,
    ("United States", "Sagar-Sandheads"): 13050,
    ("United States", "Haldia"): 13100,
    # Mozambique
    ("Mozambique", "Paradip"): 4800,
    ("Mozambique", "Visakhapatnam"): 4900,
    ("Mozambique", "Gangavaram"): 4900,
    ("Mozambique", "Gopalpur"): 4850,
    ("Mozambique", "Dhamra"): 4950,
    ("Mozambique", "Sagar-Sandheads"): 5050,
    ("Mozambique", "Haldia"): 5100,
    # Russia (via Suez Canal)
    ("Russia", "Paradip"): 9200,
    ("Russia", "Visakhapatnam"): 9300,
    ("Russia", "Gangavaram"): 9300,
    ("Russia", "Gopalpur"): 9250,
    ("Russia", "Dhamra"): 9350,
    ("Russia", "Sagar-Sandheads"): 9450,
    ("Russia", "Haldia"): 9500,
    # Indonesia
    ("Indonesia", "Paradip"): 2900,
    ("Indonesia", "Visakhapatnam"): 3000,
    ("Indonesia", "Gangavaram"): 3000,
    ("Indonesia", "Gopalpur"): 2950,
    ("Indonesia", "Dhamra"): 3050,
    ("Indonesia", "Sagar-Sandheads"): 3150,
    ("Indonesia", "Haldia"): 3200,
}

# ─── 4. BASE FREIGHT RATES (USD/MT Benchmark Starting Points) ────────────────

BASE_FREIGHT_RATES = {
    # Australia
    ("Australia", "Handysize"): 18.0,
    ("Australia", "Supramax"): 13.5,
    ("Australia", "Panamax"): 10.5,
    ("Australia", "Capesize"): 7.0,
    # United States
    ("United States", "Handysize"): 38.0,
    ("United States", "Supramax"): 30.0,
    ("United States", "Panamax"): 24.0,
    ("United States", "Capesize"): 18.0,
    # Mozambique
    ("Mozambique", "Handysize"): 25.0,
    ("Mozambique", "Supramax"): 19.0,
    ("Mozambique", "Panamax"): 15.5,
    ("Mozambique", "Capesize"): 11.0,
    # Russia
    ("Russia", "Handysize"): 28.0,
    ("Russia", "Supramax"): 22.0,
    ("Russia", "Panamax"): 17.0,
    ("Russia", "Capesize"): 12.5,
    # Indonesia
    ("Indonesia", "Handysize"): 8.5,
    ("Indonesia", "Supramax"): 6.5,
    ("Indonesia", "Panamax"): 5.0,
    ("Indonesia", "Capesize"): None,  # Physically restricted at Indonesian loading ports
}

# Port congestion baseline indices
PORT_BASE_CONGESTION = {
    "Paradip": 0.70,
    "Haldia": 0.75,
    "Sagar-Sandheads": 0.55,
    "Visakhapatnam": 0.50,
    "Gopalpur": 0.35,
    "Dhamra": 0.38,
    "Gangavaram": 0.30,
}


# ─── 5. FREIGHT RATE & HISTORICAL TIME-SERIES GENERATORS ──────────────────────

def generate_freight_history(
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str,
    start_date: date = date(2022, 1, 1),
    weeks: int = 130,
) -> list[dict]:
    """
    Generate ~2.5 years (130 weeks) of synthetic freight rate observations.
    Incorporates seasonality, bunker shocks, congestion premiums, and demand pull.
    """
    base = BASE_FREIGHT_RATES.get((origin, vessel_class))
    if base is None:
        return []

    # Adjust base slightly by destination distance relative to 5000 NM reference
    dist = ROUTE_DISTANCES.get((origin, destination), 5000)
    distance_factor = dist / 5000.0
    # Economies of scale dampens distance impact for larger vessels
    scale_elasticity = {"Handysize": 0.35, "Supramax": 0.28, "Panamax": 0.22, "Capesize": 0.18}.get(vessel_class, 0.25)
    adjusted_base = base * (1.0 + scale_elasticity * (distance_factor - 1.0))

    dest_congestion_base = PORT_BASE_CONGESTION.get(destination, 0.50)

    records = []
    rate = adjusted_base
    bunker = 650.0
    congestion = dest_congestion_base
    demand = 0.55

    for w in range(weeks):
        current_date = start_date + timedelta(weeks=w)
        month = current_date.month

        # Seasonal factor: Q4 (Oct-Dec) & Q1 peak, Q3 (monsoon) low
        seasonal = 1.0 + 0.15 * math.sin(2 * math.pi * (month - 2) / 12)

        # Correlated bunker price random walk
        bunker_shock = random.gauss(0, 0.015)
        bunker = bunker * (1 + bunker_shock)
        bunker = max(400.0, min(950.0, bunker))

        # Congestion random walk anchored around destination port baseline
        congestion = max(0.15, min(0.95, congestion + 0.2 * (dest_congestion_base - congestion) + random.gauss(0, 0.025)))

        # Demand index (Indian power/steel demand)
        demand = max(0.25, min(0.92, demand + random.gauss(0, 0.02)))

        # Vessel availability (inversely correlated with demand)
        avail = max(0.15, min(0.85, 1.0 - demand + random.gauss(0, 0.03)))

        # Structural economic equilibrium
        bunker_elasticity = 0.15 * (bunker / 650.0 - 1.0)
        congestion_premium = 0.08 * (congestion - 0.5)
        demand_pull = 0.12 * (demand - 0.55)
        equilibrium = adjusted_base * seasonal * (1.0 + bunker_elasticity + congestion_premium + demand_pull)

        # Mean-reverting random walk towards equilibrium
        shock = random.gauss(0, 0.018)
        rate = rate + 0.18 * (equilibrium - rate) + adjusted_base * shock
        rate = max(adjusted_base * 0.5, min(adjusted_base * 2.2, rate))

        # BPI proxy (weighted by vessel class)
        bpi_multiplier = {"Handysize": 0.7, "Supramax": 0.85, "Panamax": 1.0, "Capesize": 1.4}
        bpi = (1500 + 800 * demand + random.gauss(0, 80)) * bpi_multiplier.get(vessel_class, 1.0)

        # Approximate TCE ($/day)
        cargo_dwt = {"Handysize": 32000, "Supramax": 57000, "Panamax": 73000, "Capesize": 175000}.get(vessel_class, 70000)
        fuel_mt = {"Handysize": 22.0, "Supramax": 28.0, "Panamax": 34.0, "Capesize": 58.0}.get(vessel_class, 30.0)
        speed = 14.0
        sea_days = dist / (speed * 24)
        port_days = 5.0
        tot_days = sea_days + port_days
        freight_rev = rate * cargo_dwt
        voyage_cost = (fuel_mt * sea_days + fuel_mt * 0.15 * port_days) * bunker + 40000
        tce = (freight_rev - voyage_cost) / tot_days if tot_days > 0 else 15000

        records.append(
            {
                "date": current_date,
                "origin": origin,
                "destination": destination,
                "vessel_class": vessel_class,
                "commodity": commodity,
                "rate_usd_per_mt": round(rate, 2),
                "tce_usd_per_day": round(max(2000, tce), 0),
                "bpi_index": round(bpi, 1),
                "bunker_price": round(bunker, 1),
                "congestion_index": round(congestion, 3),
                "vessel_availability": round(avail, 3),
                "demand_index": round(demand, 3),
                "is_demo": True,
                "data_label": "[DEMO] Synthetic Freight Rate",
            }
        )

    return records


def generate_all_history() -> list[dict]:
    """Generate freight history for all 5 origins, all 7 East Coast destinations, and viable vessel classes."""
    origins = ["Australia", "United States", "Mozambique", "Russia", "Indonesia"]
    destinations = ["Paradip", "Visakhapatnam", "Gangavaram", "Gopalpur", "Dhamra", "Sagar-Sandheads", "Haldia"]
    vessel_classes = ["Handysize", "Supramax", "Panamax", "Capesize"]
    commodities = {
        "Australia": "Coal",
        "United States": "Coal",
        "Mozambique": "Coal",
        "Russia": "Coal",
        "Indonesia": "Coal",
    }

    all_records = []
    for origin in origins:
        for dest in destinations:
            for vc in vessel_classes:
                # Indonesia + Capesize is physically blocked at loading origin
                if origin == "Indonesia" and vc == "Capesize":
                    continue
                records = generate_freight_history(
                    origin=origin,
                    destination=dest,
                    vessel_class=vc,
                    commodity=commodities[origin],
                )
                all_records.extend(records)
    return all_records


def generate_routes() -> list[dict]:
    """Generate route profiles for all 5 origins to all 7 East Coast destinations."""
    origins = ["Australia", "United States", "Mozambique", "Russia", "Indonesia"]
    destinations = ["Paradip", "Visakhapatnam", "Gangavaram", "Gopalpur", "Dhamra", "Sagar-Sandheads", "Haldia"]
    records = []
    for o in origins:
        for d in destinations:
            dist = ROUTE_DISTANCES.get((o, d), 5000)
            vc_map = {
                "Australia": ["Handysize", "Supramax", "Panamax", "Capesize"],
                "United States": ["Handysize", "Supramax", "Panamax", "Capesize"],
                "Mozambique": ["Handysize", "Supramax", "Panamax", "Capesize"],
                "Russia": ["Handysize", "Supramax", "Panamax"],
                "Indonesia": ["Handysize", "Supramax", "Panamax"],
            }
            records.append({
                "origin": o,
                "destination": d,
                "distance_nm": dist,
                "typical_vessel_classes": vc_map.get(o, ["Supramax", "Panamax"]),
                "typical_commodities": ["Coal"],
                "canal_transit": "Suez" if o in ["United States", "Russia"] else None,
                "is_demo": True,
                "data_label": "[DEMO] Synthetic Route Table",
            })
    return records


# ─── 6. MARKET INDICATORS GENERATOR ──────────────────────────────────────────

def generate_market_indicators(start_date: date = date(2022, 1, 1), weeks: int = 130) -> list[dict]:
    """
    Generate weekly Baltic indices (BDI, BCI, BPI, BSI, BHSI), bunker benchmarks,
    and fleet utilization proxies.
    """
    records = []
    bdi = 1800.0
    vlsfo = 640.0
    ifo380 = 490.0
    mgo = 880.0

    for w in range(weeks):
        current_date = start_date + timedelta(weeks=w)
        month = current_date.month

        # Macro cycle + seasonal demand factor
        cycle = 1.0 + 0.12 * math.sin(2 * math.pi * (month - 3) / 12)
        bdi = max(800.0, min(3500.0, (bdi + random.gauss(0, 45)) * 0.98 + 1800.0 * cycle * 0.02))

        # Baltic sub-indices correlated with BDI
        bci = round(bdi * random.uniform(1.3, 1.6), 1)
        bpi = round(bdi * random.uniform(0.9, 1.15), 1)
        bsi = round(bdi * random.uniform(0.75, 0.95), 1)
        bhsi = round(bdi * random.uniform(0.45, 0.65), 1)

        # Bunker price series
        vlsfo = max(450.0, min(950.0, vlsfo * (1 + random.gauss(0, 0.015))))
        ifo380 = round(vlsfo * 0.77, 1)
        mgo = round(vlsfo * 1.35, 1)

        fleet_util = round(max(78.0, min(94.0, 84.0 + (bdi - 1800) / 200 + random.gauss(0, 0.5))), 1)
        orderbook = round(max(6.5, min(11.0, 8.2 + random.gauss(0, 0.1))), 2)

        records.append({
            "date": current_date,
            "bdi_index": round(bdi, 1),
            "bci_index": bci,
            "bpi_index": bpi,
            "bsi_index": bsi,
            "bhsi_index": bhsi,
            "bunker_vlsfo_usd": round(vlsfo, 1),
            "bunker_ifo380_usd": ifo380,
            "bunker_mgo_usd": mgo,
            "fleet_utilization_pct": fleet_util,
            "orderbook_to_fleet_pct": orderbook,
            "is_demo": True,
            "data_label": "[DEMO] Synthetic Baltic & Bunker Indicator",
        })
    return records


# ─── 7. PORT CONGESTION HISTORY GENERATOR ─────────────────────────────────────

def generate_port_congestion_history(start_date: date = date(2022, 1, 1), weeks: int = 130) -> list[dict]:
    """
    Generate weekly port congestion, queue length, and turnaround observations
    for all 7 East Coast Indian ports.
    """
    ports_config = {
        "Paradip": {"base_wait": 5.5, "base_vessels": 24, "base_cong": 0.72, "status": "high"},
        "Haldia": {"base_wait": 7.0, "base_vessels": 18, "base_cong": 0.78, "status": "high"},
        "Sagar-Sandheads": {"base_wait": 4.0, "base_vessels": 12, "base_cong": 0.55, "status": "medium"},
        "Visakhapatnam": {"base_wait": 3.0, "base_vessels": 15, "base_cong": 0.48, "status": "medium"},
        "Gopalpur": {"base_wait": 2.5, "base_vessels": 6, "base_cong": 0.35, "status": "low"},
        "Dhamra": {"base_wait": 1.5, "base_vessels": 8, "base_cong": 0.28, "status": "low"},
        "Gangavaram": {"base_wait": 1.5, "base_vessels": 7, "base_cong": 0.26, "status": "low"},
    }

    records = []
    for port_name, cfg in ports_config.items():
        wait = cfg["base_wait"]
        vessels = cfg["base_vessels"]
        cong = cfg["base_cong"]

        for w in range(weeks):
            current_date = start_date + timedelta(weeks=w)
            month = current_date.month

            # Monsoon (Jun-Sep) & Cyclone (Oct-Nov) weather impacts on Bay of Bengal
            weather_delay = 0.0
            if month in [6, 7, 8, 9]:
                weather_delay = round(random.uniform(0.2, 0.5), 2)
            elif month in [10, 11]:
                weather_delay = round(random.uniform(0.1, 0.4), 2)

            wait_shock = random.gauss(0, 0.4) + weather_delay * 2.0
            wait = max(0.5, min(14.0, (wait + wait_shock) * 0.85 + cfg["base_wait"] * 0.15))

            vessels_shock = int(random.gauss(0, 2)) + int(weather_delay * 6)
            vessels = max(1, min(45, vessels + vessels_shock))

            berth_occ = round(max(40.0, min(98.0, 75.0 + (wait - 3.0) * 4.0 + random.gauss(0, 2))), 1)
            cong_idx = round(max(0.10, min(0.98, cong * (wait / max(cfg["base_wait"], 1.0)))), 3)

            status = "severe" if cong_idx > 0.85 else "high" if cong_idx > 0.65 else "medium" if cong_idx > 0.40 else "low"

            records.append({
                "date": current_date,
                "port_name": port_name,
                "vessels_waiting_count": vessels,
                "avg_waiting_days": round(wait, 1),
                "berth_occupancy_pct": berth_occ,
                "congestion_index": cong_idx,
                "weather_delay_factor": weather_delay,
                "status": status,
                "is_demo": True,
                "data_label": "[DEMO] Synthetic Port Congestion Metric",
            })
    return records


# ─── 8. COMMODITY INDICATORS GENERATOR ───────────────────────────────────────

def generate_commodity_indicators(start_date: date = date(2022, 1, 1), weeks: int = 130) -> list[dict]:
    """
    Generate weekly benchmark commodity FOB/CFR pricing and Indian industrial demand indices.
    """
    commodities_config = [
        {"origin": "Australia", "commodity": "Coal", "base_price": 140.0},
        {"origin": "United States", "commodity": "Coal", "base_price": 220.0},
        {"origin": "Mozambique", "commodity": "Coal", "base_price": 125.0},
        {"origin": "Russia", "commodity": "Coal", "base_price": 100.0},
        {"origin": "Indonesia", "commodity": "Coal", "base_price": 65.0},
    ]

    records = []
    for cfg in commodities_config:
        price = cfg["base_price"]
        for w in range(weeks):
            current_date = start_date + timedelta(weeks=w)
            month = current_date.month

            # Seasonal demand peak in pre-winter Q4 (Oct-Dec) and post-monsoon restocking
            seasonal_demand = 0.55 + 0.15 * math.sin(2 * math.pi * (month - 2) / 12)
            demand_idx = round(max(0.20, min(0.95, seasonal_demand + random.gauss(0, 0.02))), 3)

            price = max(cfg["base_price"] * 0.6, min(cfg["base_price"] * 1.8, price * (1 + random.gauss(0, 0.012))))
            steel_idx = round(max(0.30, min(0.95, 0.60 + 0.1 * math.sin(2 * math.pi * month / 12) + random.gauss(0, 0.02))), 3)
            power_idx = round(max(0.35, min(0.98, 0.65 + 0.15 * math.sin(2 * math.pi * (month - 4) / 12) + random.gauss(0, 0.02))), 3)

            records.append({
                "date": current_date,
                "commodity": cfg["commodity"],
                "origin": cfg["origin"],
                "price_index_usd_per_mt": round(price, 2),
                "india_import_demand_index": demand_idx,
                "steel_production_index": steel_idx,
                "power_generation_demand_index": power_idx,
                "is_demo": True,
                "data_label": "[DEMO] Synthetic Commodity Market Indicator",
            })
    return records


# ─── 9. HISTORICAL OBSERVATIONS UNIFIED GENERATOR ────────────────────────────

def generate_historical_observations(freight_records: list[dict]) -> list[dict]:
    """
    Format unified historical observations linking route, vessel, rates, and indicators.
    """
    obs = []
    for r in freight_records:
        dist = ROUTE_DISTANCES.get((r["origin"], r["destination"]), 5000)
        obs.append({
            "date": r["date"],
            "origin": r["origin"],
            "destination": r["destination"],
            "vessel_class": r["vessel_class"],
            "commodity": r["commodity"],
            "distance_nm": dist,
            "freight_rate_usd_per_mt": r["rate_usd_per_mt"],
            "tce_usd_per_day": r["tce_usd_per_day"],
            "bunker_price_usd_per_mt": r["bunker_price"],
            "congestion_index": r["congestion_index"],
            "vessel_availability_index": r["vessel_availability"],
            "demand_index": r["demand_index"],
            "bpi_index": r["bpi_index"],
            "is_demo": True,
            "data_label": "[DEMO] Synthetic Historical Observation",
        })
    return obs
