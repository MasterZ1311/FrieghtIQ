"""
Regime Service — FreightIQ 2.0
Bridges the HMM ML module to the database and HTTP layer.
"""

import logging
from sqlalchemy.orm import Session

from app.ml.regime import get_detector
from app.models.market_intelligence import MarketRegime
from app.models import MarketIndicator

logger = logging.getLogger(__name__)


def _get_bci_series_from_db(db: Session, limit: int = 30) -> list[float]:
    """Pull the most recent BCI values from market_indicators table."""
    rows = (
        db.query(MarketIndicator)
        .order_by(MarketIndicator.date.desc())
        .limit(limit)
        .all()
    )
    # Reverse so oldest-first (chronological order for HMM)
    series = [float(r.bci_index) for r in reversed(rows)]
    if not series:
        # Safe synthetic default if DB has no data yet
        series = [15000.0] * 30
    return series


def get_current_regime(db: Session, bci_series: list[float] | None = None) -> dict:
    """
    Detect the current market regime.

    Args:
        db         : Active SQLAlchemy session.
        bci_series : Optional override BCI series. If None, reads from DB.

    Returns:
        Regime detection dict (see ml/regime.py → FreightRegimeDetector.detect)
    """
    if bci_series is None or len(bci_series) < 2:
        bci_series = _get_bci_series_from_db(db)

    detector = get_detector()
    result = detector.detect(bci_series)

    # Persist snapshot to DB
    try:
        record = MarketRegime(
            regime_name=result["regime"],
            confidence=result["confidence"],
            bci_avg_30d=result.get("bci_recent_avg"),
            transition_probabilities=result["transition_prob"],
            primary_driver=result["primary_driver"],
            regime_duration_estimate_days=result["regime_duration_estimate_days"],
            contract_recommendation=result["contract_recommendation"],
            urgency=result["urgency"],
        )
        db.add(record)
        db.commit()
    except Exception as exc:
        logger.warning("Could not persist regime record: %s", exc)
        db.rollback()

    return result


def get_regime_history(db: Session, limit: int = 30) -> list[dict]:
    """Return the N most recent regime snapshots from the database."""
    rows = (
        db.query(MarketRegime)
        .order_by(MarketRegime.detected_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "detected_at": r.detected_at.isoformat() if r.detected_at else None,
            "regime": r.regime_name,
            "confidence": r.confidence,
            "contract_recommendation": r.contract_recommendation,
            "urgency": r.urgency,
            "primary_driver": r.primary_driver,
            "transition_prob": r.transition_probabilities,
            "bci_avg_30d": r.bci_avg_30d,
        }
        for r in rows
    ]
