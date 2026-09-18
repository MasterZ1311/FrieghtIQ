"""
HMM Market Regime Classifier — FreightIQ 2.0
=============================================
4-state Hidden Markov Model applied to BCI/BDI freight rate series.

States:
  0 → BEAR_DISTRESS   : BCI < ~$8k/day  — 100% spot, no urgency
  1 → NEUTRAL         : BCI $8k–$15k/day — mixed spot + short COA
  2 → SEASONAL_LIFT   : BCI $15k–$30k/day — short COA (3-voyage)
  3 → SUPERCYCLE_BULL : BCI > $30k/day  — lock in Time Charter immediately
"""

import pickle
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

try:
    from hmmlearn import hmm as _hmm
    _HMM_AVAILABLE = True
except ImportError:
    _HMM_AVAILABLE = False
    logger.warning("hmmlearn not installed — using statistical fallback regime detector")


# Sorted lowest→highest so state indices match regime ordering
REGIME_NAMES = {
    0: "BEAR_DISTRESS",
    1: "NEUTRAL",
    2: "SEASONAL_LIFT",
    3: "SUPERCYCLE_BULL",
}

REGIME_ACTIONS = {
    "BEAR_DISTRESS":   {"contract": "SPOT_ONLY",       "urgency": "NO_RUSH"},
    "NEUTRAL":         {"contract": "MIXED_SPOT_COA",  "urgency": "EVALUATE_WEEKLY"},
    "SEASONAL_LIFT":   {"contract": "SHORT_COA_3V",    "urgency": "WITHIN_2_WEEKS"},
    "SUPERCYCLE_BULL": {"contract": "TIME_CHARTER_6M", "urgency": "IMMEDIATE"},
}

# Approximate BCI midpoints for each regime (used in fallback + ordering)
REGIME_BCI_THRESHOLDS = [0, 8000, 15000, 30000, 999999]


class FreightRegimeDetector:
    """
    Wraps a 4-state Gaussian HMM trained on BCI-like features.
    Falls back to a rule-based classifier if hmmlearn is absent.
    """

    MODEL_PATH = Path(__file__).parent / "hmm_regime_model.pkl"

    def __init__(self):
        self.model = None
        self._load_or_train()

    # ── Feature Engineering ────────────────────────────────────────────────

    def _build_features(self, series: list[float]) -> np.ndarray:
        """
        Build a 2D feature matrix from a BCI/BDI time series.
        Columns: [level_norm, return_7d, volatility_30d]
        """
        arr = np.array(series, dtype=float)
        n = len(arr)

        # Level (normalised 0→1 within window)
        arr_min, arr_max = arr.min(), arr.max()
        level_norm = (arr - arr_min) / (arr_max - arr_min + 1e-9)

        # 7-day return
        ret_7 = np.zeros(n)
        if n > 7:
            ret_7[7:] = (arr[7:] - arr[:-7]) / (arr[:-7] + 1e-9)

        # 30-day rolling std (normalised)
        vol_30 = np.zeros(n)
        for i in range(n):
            window = arr[max(0, i - 29): i + 1]
            vol_30[i] = np.std(window) / (arr_max + 1e-9)

        return np.column_stack([level_norm, ret_7, vol_30])

    # ── Model Persistence ─────────────────────────────────────────────────

    def _load_or_train(self):
        if self.MODEL_PATH.exists():
            try:
                with open(self.MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                logger.info("HMM regime model loaded from %s", self.MODEL_PATH)
                return
            except Exception as exc:
                logger.warning("Could not load HMM model (%s) — retraining", exc)

        if _HMM_AVAILABLE:
            self._train_default()
        else:
            self.model = None  # Will use rule-based fallback

    def _train_default(self):
        """Train on synthetic four-regime BCI data."""
        np.random.seed(42)
        segments = [
            np.random.normal(5_000, 800, 300),   # Bear
            np.random.normal(11_000, 1_500, 300), # Neutral
            np.random.normal(22_000, 3_000, 300), # Seasonal
            np.random.normal(45_000, 7_000, 100), # Bull
        ]
        synthetic = np.concatenate(segments)
        X = self._build_features(synthetic.tolist())

        model = _hmm.GaussianHMM(
            n_components=4,
            covariance_type="diag",
            n_iter=200,
            random_state=42,
        )
        model.fit(X)

        # Re-order states so index 0=lowest mean, 3=highest mean
        means = model.means_[:, 0]          # level_norm is column 0
        order = np.argsort(means)
        model.means_ = model.means_[order]
        model.covars_ = model.covars_[order]
        model.transmat_ = model.transmat_[np.ix_(order, order)]
        model.startprob_ = model.startprob_[order]

        self.model = model
        self.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        logger.info("HMM regime model trained and saved to %s", self.MODEL_PATH)

    # ── Fallback Rule-Based Classifier ───────────────────────────────────

    def _rule_based_regime(self, series: list[float]) -> tuple[int, float]:
        """Simple percentile-based classifier when hmmlearn is unavailable."""
        recent_bci = np.mean(series[-7:]) if len(series) >= 7 else series[-1]
        for state_idx in range(3, -1, -1):
            if recent_bci >= REGIME_BCI_THRESHOLDS[state_idx]:
                # Confidence based on how far into the regime band we are
                lo = REGIME_BCI_THRESHOLDS[state_idx]
                hi = REGIME_BCI_THRESHOLDS[state_idx + 1]
                conf = min(0.95, 0.55 + 0.40 * (recent_bci - lo) / (hi - lo + 1e-9))
                return state_idx, round(conf, 3)
        return 0, 0.70

    # ── Primary Detection API ─────────────────────────────────────────────

    def detect(self, bci_series: list[float]) -> dict:
        """
        Detect the current freight market regime.

        Args:
            bci_series: List of recent BCI ($/day) values, most recent last.
                        Minimum 7 values; 30+ recommended.

        Returns:
            dict with keys: regime, confidence, transition_prob,
                            contract_recommendation, urgency,
                            regime_duration_estimate_days, primary_driver
        """
        if len(bci_series) < 2:
            bci_series = [15000] * 30  # Safe default

        if self.model is not None:
            X = self._build_features(bci_series)
            try:
                states = self.model.predict(X)
                current_state = int(states[-1])
                trans = self.model.transmat_[current_state]
                confidence = float(np.max(trans))
                transition_prob = {
                    REGIME_NAMES[i]: round(float(p), 3)
                    for i, p in enumerate(trans)
                }
            except Exception as exc:
                logger.warning("HMM predict failed (%s) — using rule-based", exc)
                current_state, confidence = self._rule_based_regime(bci_series)
                transition_prob = self._default_transitions(current_state, confidence)
        else:
            current_state, confidence = self._rule_based_regime(bci_series)
            transition_prob = self._default_transitions(current_state, confidence)

        regime_name = REGIME_NAMES[current_state]
        action = REGIME_ACTIONS[regime_name]

        # Duration estimate: geometric distribution mean = 1 / (1 - stay_prob)
        stay_prob = transition_prob.get(regime_name, confidence)
        duration_est = max(7, int(1.0 / (1.0 - stay_prob + 1e-9)))

        return {
            "regime": regime_name,
            "confidence": round(confidence, 3),
            "transition_prob": transition_prob,
            "contract_recommendation": action["contract"],
            "urgency": action["urgency"],
            "regime_duration_estimate_days": min(duration_est, 180),
            "primary_driver": self._infer_driver(bci_series),
            "bci_recent_avg": round(float(np.mean(bci_series[-7:])), 0),
        }

    def _default_transitions(self, state: int, confidence: float) -> dict:
        """Build a plausible transition probability dict for the fallback."""
        probs = {REGIME_NAMES[i]: 0.05 for i in range(4)}
        probs[REGIME_NAMES[state]] = round(confidence, 3)
        # Distribute remainder to adjacent states
        remainder = 1.0 - confidence
        adjacent = [(state - 1) % 4, (state + 1) % 4]
        for adj in adjacent:
            probs[REGIME_NAMES[adj]] = round(remainder / 2, 3)
        return probs

    def _infer_driver(self, series: list[float]) -> str:
        """Human-readable summary of what is driving the current regime."""
        arr = np.array(series[-30:], dtype=float)
        recent_7 = float(np.mean(arr[-7:]))
        prior_30 = float(np.mean(arr))
        delta_pct = (recent_7 - prior_30) / (prior_30 + 1e-9) * 100

        if delta_pct > 15:
            return f"BCI surging +{delta_pct:.1f}% vs 30-day avg — demand spike or supply tightening"
        if delta_pct > 5:
            return f"BCI rising +{delta_pct:.1f}% vs 30-day avg — moderate demand lift"
        if delta_pct < -15:
            return f"BCI falling {delta_pct:.1f}% vs 30-day avg — demand weakness or vessel oversupply"
        if delta_pct < -5:
            return f"BCI easing {delta_pct:.1f}% vs 30-day avg — softening freight demand"
        return f"BCI stable (±{abs(delta_pct):.1f}% vs 30-day avg) — balanced supply and demand"


# Module-level singleton (lazy-initialised on first import)
_detector: FreightRegimeDetector | None = None


def get_detector() -> FreightRegimeDetector:
    global _detector
    if _detector is None:
        _detector = FreightRegimeDetector()
    return _detector
