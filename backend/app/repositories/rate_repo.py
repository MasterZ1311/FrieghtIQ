"""
Rate Repository
===============
Data access for historical and recent freight rates, indices, and baseline prices.
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models import FreightRate as FreightRateModel
from app.seed.seed_data import BASE_FREIGHT_RATES

logger = logging.getLogger(__name__)


class RateRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_recent_rates(
        self,
        origin: str,
        destination: str,
        vessel_class: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recent historical rate entries for ML feature engineering.
        """
        if self.db:
            try:
                rows = (
                    self.db.query(FreightRateModel)
                    .filter(
                        FreightRateModel.origin.ilike(origin.strip()),
                        FreightRateModel.vessel_class.ilike(vessel_class.strip()),
                    )
                    .order_by(FreightRateModel.date.desc())
                    .limit(limit)
                    .all()
                )
                if rows:
                    return [
                        {
                            "date": r.date,
                            "rate_usd_per_mt": r.rate_usd_per_mt,
                            "bunker_price": r.bunker_price,
                            "congestion_index": r.congestion_index,
                            "demand_index": r.demand_index,
                        }
                        for r in reversed(rows)
                    ]
            except Exception as e:
                logger.warning(f"Failed to query recent rates from DB: {e}")

        # Deterministic fallback rates
        base = BASE_FREIGHT_RATES.get((origin, vessel_class), 12.0) or 12.0
        return [
            {
                "date": None,
                "rate_usd_per_mt": base,
                "bunker_price": 650.0,
                "congestion_index": 0.5,
                "demand_index": 0.55,
            }
        ]

    def get_baseline_rate(self, origin: str, vessel_class: str) -> float:
        """Returns benchmark baseline spot freight rate in USD/MT."""
        # Check direct match
        rate = BASE_FREIGHT_RATES.get((origin, vessel_class))
        if rate is not None:
            return float(rate)
        # Check case-insensitive
        for (o, vc), r in BASE_FREIGHT_RATES.items():
            if o.lower() == origin.lower() and vc.lower() == vessel_class.lower():
                return float(r) if r is not None else 12.0
        return 12.50
