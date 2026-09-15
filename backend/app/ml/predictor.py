"""
FreightIQ ML Predictor & Explainability Service
===============================================
High-level prediction service delivering:
- Point estimate: `predicted_rate`
- Baseline rate: `current_rate`
- Time horizon: `horizon` (days)
- Uncertainty interval: `lower_bound`, `upper_bound`
- Model confidence: `confidence` (percentage)
- Explainable drivers: `drivers` with directional impact and domain rationale
- Full backwards-compatibility with FreightIQ API & UI schemas
- Explicit DEMO / SYNTHETIC disclaimers
"""
from __future__ import annotations
import logging
import math
import random
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


import numpy as np

from app.ml.dataset_generator import get_distance
from app.ml.model import get_model
from app.ml.preprocessing import (
    FEATURE_NAMES,
    build_single_feature_vector,
)

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "[DEMO] This forecast is generated from a synthetic/demo econometric simulation. "
    "Not verified financial or physical shipping market advice."
)

FACTOR_METADATA: Dict[str, Dict[str, str]] = {
    "bunker_price_norm": {
        "factor": "Bunker/Fuel Price",
        "high_direction": "bearish",
        "low_direction": "bullish",
        "high_desc": "High VLSFO/bunker costs increase voyage expenses, compressing net owner margins.",
        "low_desc": "Lower fuel costs reduce total voyage disbursements, providing rate relief.",
    },
    "congestion_index": {
        "factor": "Port Congestion",
        "high_direction": "bullish",
        "low_direction": "neutral",
        "high_desc": "Elevated port turnaround delays tie up tonnage at anchor, tightening vessel supply and lifting rates.",
        "low_desc": "Fluid port operations maintain rapid vessel turnaround and normal vessel availability.",
    },
    "vessel_availability": {
        "factor": "Vessel Availability",
        "high_direction": "bearish",
        "low_direction": "bullish",
        "high_desc": "Surplus vessel supply relative to cargo fixtures places downward pressure on spot quotes.",
        "low_desc": "Tight tonnage lists across key loading basins give shipowners strong charter bargaining power.",
    },
    "demand_index": {
        "factor": "Cargo Demand",
        "high_direction": "bullish",
        "low_direction": "bearish",
        "high_desc": "Strong Indian industrial import appetite drives active chartering inquiries.",
        "low_desc": "Subdued steel and thermal restocking softens demand for dry bulk fixtures.",
    },
    "q4_demand_flag": {
        "factor": "Q4 Pre-Winter Restocking",
        "high_direction": "bullish",
        "low_direction": "neutral",
        "high_desc": "Q4 seasonal inventory buildup ahead of winter pushes regional spot demand up.",
        "low_desc": "Off-peak seasonal period with baseline cargo inquiries.",
    },
    "monsoon_flag": {
        "factor": "Monsoon Season",
        "high_direction": "bearish",
        "low_direction": "neutral",
        "high_desc": "Indian Ocean southwest monsoon slows port handling operations and limits lighterage.",
        "low_desc": "Fair weather window across the Bay of Bengal and Arabian Sea.",
    },
    "distance_norm": {
        "factor": "Voyage Route Distance",
        "high_direction": "bullish",
        "low_direction": "bearish",
        "high_desc": "Longer haul voyage routes require greater fuel and time charter commitments.",
        "low_desc": "Short coastal/regional trade lane with lower total voyage disbursements.",
    },
    "lag_rate_1w": {
        "factor": "Recent Rate Momentum",
        "high_direction": "bullish",
        "low_direction": "bearish",
        "high_desc": "Upward momentum from previous fixtures provides strong support to current offer levels.",
        "low_desc": "Downward correction in recent spot fixtures softens near-term forward pricing.",
    },
    "rolling_mean_4w": {
        "factor": "4-Week Moving Average",
        "high_direction": "bullish",
        "low_direction": "bearish",
        "high_desc": "Sustained monthly upward moving average indicates underlying structural firming.",
        "low_desc": "Sustained monthly decline indicates soft underlying charter demand.",
    },
    "commodity_index_norm": {
        "factor": "Commodity Benchmark Price",
        "high_direction": "bullish",
        "low_direction": "bearish",
        "high_desc": "Firm underlying commodity benchmarks support cargo margins and freight willingness.",
        "low_desc": "Weaker commodity price proxies soften charterers' willingness to pay high freight.",
    },
}


def _get_current_market_proxies(destination: str, ref_date: date) -> Dict[str, float]:
    """
    Simulate live market proxies for current inference.
    In real production, these connect to external AIS/Bunker feeds; here we use
    deterministic date-based estimators to guarantee 100% offline self-containment.
    """
    month = ref_date.month
    day_seed = ref_date.toordinal()
    rng = random.Random(day_seed + hash(destination) % 10000)

    congestion_defaults = {
        "Paradip": 0.68,
        "Haldia": 0.74,
        "Visakhapatnam": 0.48,
        "Gangavaram": 0.34,
        "Gopalpur": 0.28,
        "Dhamra": 0.38,
        "Sagar-Sandheads": 0.52,
    }
    congestion = congestion_defaults.get(destination, 0.50) + rng.gauss(0, 0.03)
    congestion = max(0.10, min(0.95, congestion))

    seasonal_demand = 0.55 + 0.10 * math.sin(2 * math.pi * (month - 3) / 12.0)
    demand = max(0.20, min(0.95, seasonal_demand + rng.gauss(0, 0.025)))

    availability = max(0.15, min(0.85, 1.0 - demand * 0.85 + rng.gauss(0, 0.03)))
    bunker = max(450.0, min(850.0, 630.0 + rng.gauss(0, 25.0)))
    commodity_index = max(70.0, min(160.0, 105.0 + rng.gauss(0, 8.0)))

    return {
        "congestion_index": round(congestion, 3),
        "demand_index": round(demand, 3),
        "vessel_availability": round(availability, 3),
        "bunker_price": round(bunker, 1),
        "commodity_index": round(commodity_index, 2),
    }


def predict_freight_rate(
    origin: str,
    destination: str,
    vessel_class: str,
    commodity: str = "Coal",
    horizon_days: int = 30,
    laycan_start: Optional[date] = None,
    recent_rates: Optional[List[Dict[str, Any]]] = None,
    bunker_price: Optional[float] = None,
    congestion_index: Optional[float] = None,
    vessel_availability: Optional[float] = None,
    demand_index: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Main forecasting entry point.
    Returns standard FreightIQ response dictionary containing both requested ML keys
    and backward-compatible API keys.
    """
    today = date.today()
    ref_date = laycan_start or (today + timedelta(days=horizon_days))

    # Retrieve live/estimated proxies
    proxies = _get_current_market_proxies(destination, ref_date)
    if bunker_price is not None:
        proxies["bunker_price"] = bunker_price
    if congestion_index is not None:
        proxies["congestion_index"] = congestion_index
    if vessel_availability is not None:
        proxies["vessel_availability"] = vessel_availability
    if demand_index is not None:
        proxies["demand_index"] = demand_index

    # Determine baseline rate from recent history or static base
    from app.ml.dataset_generator import BASE_FREIGHT_RATES
    dist = get_distance(origin, destination)
    dist_factor = (dist / 5000.0) ** 0.35
    base_default = (BASE_FREIGHT_RATES.get((origin, vessel_class), 12.0)) * dist_factor

    current_rate = base_default
    lag_1w = 0.0
    lag_2w = 0.0
    lag_4w = 0.0
    lag_12w = 0.0
    rolling_4w = 0.0
    rolling_12w = 0.0
    rolling_std = 0.0

    if recent_rates and len(recent_rates) > 0:
        rates_series = [float(r["rate_usd_per_mt"]) for r in recent_rates if "rate_usd_per_mt" in r]
        if rates_series:
            current_rate = rates_series[-1]
            ref_base = max(0.5, float(np.mean(rates_series)))
            lag_1w = (rates_series[-1] / ref_base) - 1.0
            if len(rates_series) >= 2:
                lag_2w = (rates_series[-2] / ref_base) - 1.0
            if len(rates_series) >= 4:
                lag_4w = (rates_series[-4] / ref_base) - 1.0
                r4 = rates_series[-4:]
                rolling_4w = (float(np.mean(r4)) / ref_base) - 1.0
                rolling_std = float(np.std(r4)) / ref_base
            if len(rates_series) >= 12:
                lag_12w = (rates_series[-12] / ref_base) - 1.0
                r12 = rates_series[-12:]
                rolling_12w = (float(np.mean(r12)) / ref_base) - 1.0

    feat_vec = build_single_feature_vector(
        origin=origin,
        destination=destination,
        vessel_class=vessel_class,
        commodity=commodity,
        ref_date=ref_date,
        bunker_price=proxies["bunker_price"],
        congestion_index=proxies["congestion_index"],
        vessel_availability=proxies["vessel_availability"],
        demand_index=proxies["demand_index"],
        commodity_index=proxies.get("commodity_index", 100.0),
        lag_rate_1w=lag_1w,
        lag_rate_2w=lag_2w,
        lag_rate_4w=lag_4w,
        lag_rate_12w=lag_12w,
        rolling_mean_4w=rolling_4w,
        rolling_mean_12w=rolling_12w,
        rolling_std_4w=rolling_std,
    )

    model = get_model()
    pred_res = model.predict(feat_vec, horizon_days=horizon_days)
    predicted_rate = float(pred_res["point"])
    lower_bound = float(pred_res["lower"])
    upper_bound = float(pred_res["upper"])
    confidence = float(pred_res["confidence_pct"])

    # Determine trend
    delta = (predicted_rate - current_rate) / max(current_rate, 1.0)
    if delta > 0.025:
        trend = "rising"
    elif delta < -0.025:
        trend = "falling"
    else:
        trend = "stable"

    # Compute feature importance and drivers explanation
    importances = model.feature_importances()
    top_importances = sorted(importances.items(), key=lambda x: -x[1])

    drivers: List[Dict[str, Any]] = []
    influencing_factors: List[Dict[str, Any]] = []

    for feat_name, imp in top_importances[:5]:
        meta = FACTOR_METADATA.get(feat_name)
        if not meta:
            continue

        feat_idx = FEATURE_NAMES.index(feat_name)
        feat_val = float(feat_vec[feat_idx])

        # Direction logic based on feature deviation
        if feat_name in ("sin_annual", "cos_annual", "q4_demand_flag", "q1_demand_flag", "monsoon_flag"):
            if feat_val > 0.3:
                direction = meta["high_direction"]
                desc = meta["high_desc"]
            else:
                direction = "neutral"
                desc = meta["low_desc"]
        elif feat_name in ("lag_rate_1w", "lag_rate_4w", "rolling_mean_4w"):
            if feat_val > 0.02:
                direction = "bullish"
                desc = meta["high_desc"]
            elif feat_val < -0.02:
                direction = "bearish"
                desc = meta["low_desc"]
            else:
                direction = "neutral"
                desc = "Recent freight rates have traded inside a flat consolidation band."
        else:
            if feat_val > 0.58:
                direction = meta["high_direction"]
                desc = meta["high_desc"]
            elif feat_val < 0.42:
                direction = meta["low_direction"]
                desc = meta["low_desc"]
            else:
                direction = "neutral"
                desc = f"Neutral baseline conditions observed for {meta['factor']}."

        magnitude = "high" if imp >= 0.15 else ("medium" if imp >= 0.05 else "low")
        impact_pct = round(imp * 100.0, 1)

        driver_item = {
            "factor": meta["factor"],
            "impact_pct": impact_pct,
            "direction": direction,
            "magnitude": magnitude,
            "description": desc,
        }
        drivers.append(driver_item)

        # InfluencingFactor schema for frontend
        influencing_factors.append({
            "factor": meta["factor"],
            "direction": direction,
            "magnitude": magnitude,
            "description": desc,
        })

    # TCE Economics Estimation
    vessel_speeds = {"Handysize": 13.5, "Supramax": 14.0, "Panamax": 14.5, "Capesize": 14.5}
    vessel_fuels = {"Handysize": 22.0, "Supramax": 28.0, "Panamax": 34.0, "Capesize": 58.0}
    vessel_cargo = {"Handysize": 32000, "Supramax": 57000, "Panamax": 73000, "Capesize": 175000}

    speed = vessel_speeds.get(vessel_class, 14.0)
    fuel = vessel_fuels.get(vessel_class, 32.0)
    cargo = vessel_cargo.get(vessel_class, 70000)

    sea_days = dist / (speed * 24.0)
    port_days = 5.0
    total_days = max(1.0, sea_days + port_days)
    revenue = predicted_rate * cargo
    bunker_expense = (fuel * sea_days + (fuel * 0.15) * port_days) * proxies["bunker_price"]
    port_dues = 40000.0
    tce = (revenue - bunker_expense - port_dues) / total_days

    # Unified payload containing exact user required keys + backwards-compatible keys
    return {
        # --- Explicitly requested keys ---
        "current_rate": round(current_rate, 2),
        "predicted_rate": round(predicted_rate, 2),
        "horizon": horizon_days,
        "lower_bound": round(lower_bound, 2),
        "upper_bound": round(upper_bound, 2),
        "confidence": confidence,
        "drivers": drivers,
        # --- Backwards compatibility keys for existing endpoints & UI ---
        "origin": origin,
        "destination": destination,
        "vessel_class": vessel_class,
        "commodity": commodity,
        "current_rate_usd_per_mt": round(current_rate, 2),
        "predicted_rate_usd_per_mt": round(predicted_rate, 2),
        "horizon_days": horizon_days,
        "confidence_pct": confidence,
        "tce_estimate_usd_per_day": round(max(0.0, tce), 0),
        "trend": trend,
        "influencing_factors": influencing_factors,
        "disclaimer": DISCLAIMER_TEXT,
        "is_demo": True,
        "generated_at": datetime.now(timezone.utc),
    }

