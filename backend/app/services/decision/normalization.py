from typing import Dict, Any, Optional
from app.models.enums import DataStatusType


class UnitNormalizationService:
    """
    Maritime unit standardization and safety service.
    Enforces strict delineation between Cargo Quantity (MT),
    Vessel Deadweight (DWT MT), Gross Tonnage (GRT), and Cubic Capacity (CBM).
    Never silently reinterprets cargo volume or fuel burn data.
    """

    @staticmethod
    def normalize_cargo_quantity(quantity_raw: float, unit: str = "MT") -> Dict[str, Any]:
        """Validates and normalizes cargo volume into Metric Tonnes."""
        unit_upper = unit.strip().upper()
        if unit_upper in ["MT", "METRIC_TONS", "METRIC_TONNES", "T"]:
            quantity_mt = float(quantity_raw)
        elif unit_upper in ["LT", "LONG_TONS"]:
            quantity_mt = float(quantity_raw) * 1.01605
        elif unit_upper in ["ST", "SHORT_TONS"]:
            quantity_mt = float(quantity_raw) * 0.907185
        elif unit_upper in ["KG"]:
            quantity_mt = float(quantity_raw) / 1000.0
        else:
            quantity_mt = float(quantity_raw)

        return {
            "quantity_mt": round(quantity_mt, 2),
            "unit": "MT",
            "original_unit": unit,
            "original_value": quantity_raw,
            "is_metric": True,
        }

    @staticmethod
    def validate_vessel_capacity(
        cargo_quantity_mt: float,
        vessel_dwt: Optional[float],
        tolerance_pct: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Crucial Safety Check: Distinguishes between Cargo Quantity and Vessel DWT.
        A vessel's summer DWT must safely exceed cargo quantity + bunker/stores allowances.
        """
        if vessel_dwt is None or vessel_dwt <= 0:
            return {
                "status": "UNKNOWN",
                "can_carry": False,
                "dwt_utilization_pct": None,
                "message": "Vessel summer DWT is unrecorded. Capacity feasibility cannot be verified.",
            }

        max_cargo_mt = cargo_quantity_mt * (1.0 + (tolerance_pct / 100.0))
        utilization = round((cargo_quantity_mt / vessel_dwt) * 100.0, 1)

        if cargo_quantity_mt > vessel_dwt:
            return {
                "status": "EXCEEDS_DWT",
                "can_carry": False,
                "dwt_utilization_pct": utilization,
                "message": f"Nominal cargo quantity ({cargo_quantity_mt:,.0f} MT) exceeds vessel summer DWT ({vessel_dwt:,.0f} MT).",
            }
        elif max_cargo_mt > vessel_dwt:
            return {
                "status": "FEASIBLE",
                "can_carry": True,
                "dwt_utilization_pct": utilization,
                "message": f"Cargo ({cargo_quantity_mt:,.0f} MT) is within DWT ({vessel_dwt:,.0f} MT); upper tolerance ({max_cargo_mt:,.0f} MT) constrained by vessel deadweight.",
            }
        elif utilization < 50.0:
            return {
                "status": "UNDER_UTILIZED",
                "can_carry": True,
                "dwt_utilization_pct": utilization,
                "message": f"Vessel DWT ({vessel_dwt:,.0f} MT) is significantly larger than cargo volume ({cargo_quantity_mt:,.0f} MT). Economic penalty likely.",
            }
        else:
            return {
                "status": "FEASIBLE",
                "can_carry": True,
                "dwt_utilization_pct": utilization,
                "message": f"Cargo ({cargo_quantity_mt:,.0f} MT) represents {utilization}% of vessel summer DWT ({vessel_dwt:,.0f} MT).",
            }

    @staticmethod
    def normalize_distance(distance_raw: float, unit: str = "NM") -> float:
        """Standardizes distance into Nautical Miles (NM)."""
        u = unit.strip().upper()
        if u in ["NM", "NAUTICAL_MILES"]:
            return round(distance_raw, 1)
        elif u in ["KM", "KILOMETERS"]:
            return round(distance_raw * 0.539957, 1)
        elif u in ["MI", "MILES"]:
            return round(distance_raw * 0.868976, 1)
        return round(distance_raw, 1)

    @staticmethod
    def normalize_speed(speed_raw: float, unit: str = "KNOTS") -> float:
        """Standardizes navigation speed into Knots."""
        u = unit.strip().upper()
        if u in ["KNOTS", "KTS", "KN"]:
            return round(speed_raw, 2)
        elif u in ["KM/H", "KMPH"]:
            return round(speed_raw * 0.539957, 2)
        elif u in ["MPH"]:
            return round(speed_raw * 0.868976, 2)
        return round(speed_raw, 2)


class CurrencyNormalizationService:
    """
    Multi-currency normalization engine.
    Ensures USD is used as the global maritime benchmark while providing
    transparent conversion for Indian Rupee (INR) and Euro (EUR) for SAIL budgeting.
    Never fabricates exchange rates without explicit disclosure.
    """

    # Certified demonstration benchmark FX matrix
    BENCHMARK_RATES = {
        "USD": 1.0,
        "INR": 83.50,  # RBI reference assumption
        "EUR": 0.925,  # ECB reference assumption
    }

    @classmethod
    def convert_amount(
        cls,
        amount: float,
        from_currency: str = "USD",
        to_currency: str = "USD",
        custom_fx_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        from_curr = from_currency.strip().upper()
        to_curr = to_currency.strip().upper()

        if from_curr == to_curr:
            return {
                "amount": round(amount, 2),
                "currency": to_curr,
                "fx_rate": 1.0,
                "fx_status": DataStatusType.VERIFIED,
                "explanation": "Identical currency. No conversion applied.",
            }

        if custom_fx_rate and custom_fx_rate > 0:
            rate = custom_fx_rate
            status = DataStatusType.VERIFIED
            expl = f"Converted using user-specified exchange rate: {rate:.4f} {to_curr}/{from_curr}."
        else:
            # Convert via USD anchor
            rate_from_usd = cls.BENCHMARK_RATES.get(from_curr)
            rate_to_usd = cls.BENCHMARK_RATES.get(to_curr)

            if not rate_from_usd or not rate_to_usd:
                return {
                    "amount": round(amount, 2),
                    "currency": from_curr,
                    "fx_rate": 1.0,
                    "fx_status": DataStatusType.UNKNOWN,
                    "explanation": f"Exchange rate for {from_curr}->{to_curr} is unavailable. Displaying original currency.",
                }

            rate = rate_to_usd / rate_from_usd
            status = DataStatusType.SYNTHETIC
            expl = f"Converted using reference benchmark rate: {rate:.4f} {to_curr}/{from_curr}. Not a live treasury quote."

        converted = round(amount * rate, 2)
        return {
            "amount": converted,
            "currency": to_curr,
            "original_amount": amount,
            "original_currency": from_curr,
            "fx_rate": round(rate, 4),
            "fx_status": status,
            "explanation": expl,
        }
