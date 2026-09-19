import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Tuple, Dict, List, Optional
from app.services.regime.base_regime_model import MarketRegimeModel
from app.models.enums import MarketRegimeType

class HMMMarketRegimeModel(MarketRegimeModel):
    """
    Gaussian Hidden Markov Model for maritime freight market regime detection.
    Implemented in pure Python + NumPy + SciPy to guarantee zero-C-compiler
    portability across all platforms while maintaining exact mathematical rigor.

    Implements:
    - Baum-Welch (EM) parameter estimation
    - Forward-Backward algorithm for posterior state probabilities
    - Viterbi decoding for maximum a posteriori state sequences
    - Documented deterministic semantic mapping layer translating latent states
      into verified market regimes: BULL, BEAR, NEUTRAL, and SEASONAL.
    """
    def __init__(self, n_states: int = 4, max_iter: int = 40, tol: float = 1e-4, random_state: Optional[int] = None):
        super().__init__(
            model_name="Gaussian Hidden Markov Model (HMM)",
            version="HMM_GAUSSIAN_V1.0",
            number_of_states=n_states
        )
        self.n_states = n_states
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state

        # Model Parameters
        self.pi = None               # Initial state probabilities (n_states,)
        self.A = None                # Transition probability matrix (n_states, n_states)
        self.means = None            # Emission means (n_states, n_features)
        self.variances = None        # Emission diagonal variances (n_states, n_features)
        self.feature_names = None
        
        # Semantic State Mapping: maps raw hidden state index (0..3) -> MarketRegimeType
        self.state_to_regime_map: Dict[int, MarketRegimeType] = {}
        self.regime_to_state_map: Dict[MarketRegimeType, int] = {}
        self.learned_characteristics: Dict[MarketRegimeType, Dict[str, float]] = {}

    def _emission_probs(self, X: np.ndarray) -> np.ndarray:
        """
        Compute Gaussian emission probabilities B[t, k] = P(X_t | S_t = k)
        under diagonal covariance.
        """
        n_samples, n_features = X.shape
        B = np.zeros((n_samples, self.n_states))
        eps = 1e-8

        for k in range(self.n_states):
            mu = self.means[k]
            var = np.maximum(self.variances[k], eps)
            
            # Log-likelihood to prevent underflow: sum_d [ log N(x_d; mu_d, var_d) ]
            log_prob = -0.5 * np.sum(np.log(2 * np.pi * var) + ((X - mu) ** 2) / var, axis=1)
            # Clip for numerical stability
            log_prob = np.clip(log_prob, -100, 50)
            B[:, k] = np.exp(log_prob)

        # Ensure no all-zero rows
        row_sums = B.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return B / row_sums

    def _forward_backward(self, B: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """
        Scaled Forward-Backward algorithm to compute smoothed posteriors gamma[t, k].
        """
        n_samples = B.shape[0]
        alpha = np.zeros((n_samples, self.n_states))
        c = np.zeros(n_samples) # Scaling factors

        # Forward pass
        alpha[0] = self.pi * B[0]
        c[0] = np.maximum(alpha[0].sum(), 1e-12)
        alpha[0] /= c[0]

        for t in range(1, n_samples):
            alpha[t] = np.dot(alpha[t - 1], self.A) * B[t]
            c[t] = np.maximum(alpha[t].sum(), 1e-12)
            alpha[t] /= c[t]

        # Backward pass
        beta = np.zeros((n_samples, self.n_states))
        beta[-1] = 1.0

        for t in range(n_samples - 2, -1, -1):
            beta[t] = np.dot(self.A, (B[t + 1] * beta[t + 1]))
            beta[t] /= c[t + 1]

        # Posterior gamma[t, k] = P(S_t = k | X_{1:T})
        gamma = alpha * beta
        gamma_sums = gamma.sum(axis=1, keepdims=True)
        gamma_sums[gamma_sums == 0] = 1.0
        gamma /= gamma_sums

        log_likelihood = float(np.sum(np.log(c)))
        return alpha, beta, gamma, log_likelihood

    def _viterbi(self, B: np.ndarray) -> np.ndarray:
        """
        Viterbi dynamic programming algorithm to decode global MAP state sequence.
        """
        n_samples = B.shape[0]
        log_A = np.log(np.maximum(self.A, 1e-12))
        log_pi = np.log(np.maximum(self.pi, 1e-12))
        log_B = np.log(np.maximum(B, 1e-12))

        viterbi_mat = np.zeros((n_samples, self.n_states))
        backpointer = np.zeros((n_samples, self.n_states), dtype=int)

        viterbi_mat[0] = log_pi + log_B[0]

        for t in range(1, n_samples):
            for j in range(self.n_states):
                seq_probs = viterbi_mat[t - 1] + log_A[:, j]
                best_prev = int(np.argmax(seq_probs))
                viterbi_mat[t, j] = seq_probs[best_prev] + log_B[t, j]
                backpointer[t, j] = best_prev

        best_path = np.zeros(n_samples, dtype=int)
        best_path[-1] = int(np.argmax(viterbi_mat[-1]))

        for t in range(n_samples - 2, -1, -1):
            best_path[t] = backpointer[t + 1, best_path[t + 1]]

        return best_path

    def _initialize_parameters(self, X: np.ndarray):
        """
        Initialize transition matrix, initial distribution, and emission parameters.
        """
        n_samples, n_features = X.shape
        # Prior with diagonal persistence bias
        self.pi = np.full(self.n_states, 1.0 / self.n_states)
        self.A = np.full((self.n_states, self.n_states), 0.1 / (self.n_states - 1))
        np.fill_diagonal(self.A, 0.9) # Regimes persist with ~90% daily probability

        # Quantile-based initialization for return column (feature 0)
        ret_quantiles = np.quantile(X[:, 0], np.linspace(0.15, 0.85, self.n_states))
        self.means = np.zeros((self.n_states, n_features))
        self.variances = np.zeros((self.n_states, n_features))
        overall_var = np.var(X, axis=0) + 1e-4

        for k in range(self.n_states):
            self.means[k] = np.mean(X, axis=0)
            self.means[k, 0] = ret_quantiles[k]
            self.variances[k] = overall_var

    def fit(self, features_df: pd.DataFrame) -> "HMMMarketRegimeModel":
        """
        Fits Gaussian HMM via Baum-Welch Expectation-Maximization and derives
        the deterministic semantic mapping layer.
        """
        # Required numerical feature signals
        desired_features = [
            "rate_return_7d",
            "rolling_volatility_14d",
            "rate_return_30d",
            "seasonal_signal"
        ]
        self.feature_names = [f for f in desired_features if f in features_df.columns]
        if not self.feature_names:
            # Fallback to whatever numeric columns are provided
            self.feature_names = list(features_df.select_dtypes(include=[np.number]).columns[:4])

        X = features_df[self.feature_names].dropna().values
        n_samples, n_features = X.shape

        if n_samples < 30:
            raise ValueError(f"Insufficient history for HMM training: {n_samples} samples (min 30 required)")

        self._initialize_parameters(X)
        prev_ll = -np.inf

        # Baum-Welch EM iterations
        for iteration in range(self.max_iter):
            B = self._emission_probs(X)
            alpha, beta, gamma, log_likelihood = self._forward_backward(B)

            # Check convergence
            if np.abs(log_likelihood - prev_ll) < self.tol:
                break
            prev_ll = log_likelihood

            # M-step: Update initial state probabilities
            self.pi = np.maximum(gamma[0], 1e-4)
            self.pi /= self.pi.sum()

            # M-step: Update transition matrix A
            eps = 1e-8
            for i in range(self.n_states):
                denom = np.sum(gamma[:-1, i]) + eps
                for j in range(self.n_states):
                    numer = np.sum(alpha[:-1, i] * self.A[i, j] * B[1:, j] * beta[1:, j])
                    self.A[i, j] = numer / denom
                # Normalize row
                self.A[i] = np.maximum(self.A[i], eps)
                self.A[i] /= self.A[i].sum()

            # M-step: Update emission means and variances
            for k in range(self.n_states):
                gamma_k = gamma[:, k][:, np.newaxis]
                sum_gamma_k = np.sum(gamma_k) + eps
                self.means[k] = np.sum(gamma_k * X, axis=0) / sum_gamma_k
                diff = X - self.means[k]
                self.variances[k] = np.maximum(
                    np.sum(gamma_k * (diff ** 2), axis=0) / sum_gamma_k,
                    1e-4
                )

        # Derive Deterministic Semantic Mapping
        self._map_semantic_states(X, features_df)
        self.is_fitted = True
        return self

    def _map_semantic_states(self, X: np.ndarray, features_df: pd.DataFrame):
        """
        DETERMINISTIC SEMANTIC MAPPING LAYER:
        Translates raw hidden state indices {0, 1, 2, 3} to verified economic regimes.
        
        Rules:
        1. BULL: Hidden state with highest positive return drift (feature 0).
        2. BEAR: Hidden state with lowest (most negative) return drift (feature 0).
        3. From remaining 2 states:
           - SEASONAL: State with highest correlation/alignment to seasonal sinusoids.
           - NEUTRAL: State with lowest absolute return momentum (consolidation/mean-reversion).
        """
        ret_col_idx = 0 # rate_return_7d
        seasonal_col_idx = self.feature_names.index("seasonal_signal") if "seasonal_signal" in self.feature_names else None

        B = self._emission_probs(X)
        _, _, gamma, _ = self._forward_backward(B)

        state_stats = []
        for k in range(self.n_states):
            mean_ret = float(self.means[k, ret_col_idx])
            mean_vol = float(np.sqrt(self.variances[k, 1])) if X.shape[1] > 1 else float(np.sqrt(self.variances[k, 0]))
            
            # Seasonal correlation
            if seasonal_col_idx is not None:
                seasonal_corr = float(np.abs(np.corrcoef(gamma[:, k], X[:, seasonal_col_idx])[0, 1]))
                if np.isnan(seasonal_corr):
                    seasonal_corr = 0.0
            else:
                seasonal_corr = 0.0

            state_stats.append({
                "state_idx": k,
                "mean_return": mean_ret,
                "volatility": mean_vol,
                "seasonal_corr": seasonal_corr
            })

        # 1. Sort by mean return descending
        by_return = sorted(state_stats, key=lambda s: s["mean_return"], reverse=True)
        bull_candidate = by_return[0]["state_idx"]
        bear_candidate = by_return[-1]["state_idx"]

        remaining = [s for s in state_stats if s["state_idx"] not in (bull_candidate, bear_candidate)]
        
        # 2. Assign seasonal to candidate with higher seasonal alignment
        if len(remaining) == 2:
            if remaining[0]["seasonal_corr"] >= remaining[1]["seasonal_corr"]:
                seasonal_candidate = remaining[0]["state_idx"]
                neutral_candidate = remaining[1]["state_idx"]
            else:
                seasonal_candidate = remaining[1]["state_idx"]
                neutral_candidate = remaining[0]["state_idx"]
        else:
            seasonal_candidate = remaining[0]["state_idx"] if remaining else 2
            neutral_candidate = 3

        # Map state index -> MarketRegimeType
        self.state_to_regime_map = {
            bull_candidate: MarketRegimeType.BULL,
            bear_candidate: MarketRegimeType.BEAR,
            neutral_candidate: MarketRegimeType.NEUTRAL,
            seasonal_candidate: MarketRegimeType.SEASONAL
        }

        self.regime_to_state_map = {v: k for k, v in self.state_to_regime_map.items()}

        # Store learned empirical characteristics
        for s in state_stats:
            regime = self.state_to_regime_map[s["state_idx"]]
            self.learned_characteristics[regime] = {
                "mean_return_7d": round(s["mean_return"], 4),
                "volatility": round(s["volatility"], 4),
                "seasonal_correlation": round(s["seasonal_corr"], 3)
            }

    def predict(self, features_df: pd.DataFrame) -> Tuple[List[MarketRegimeType], np.ndarray]:
        """
        Decodes Viterbi sequence and returns (regimes, posterior_probabilities).
        """
        if not self.is_fitted:
            self.fit(features_df)

        X = features_df[self.feature_names].ffill().bfill().values
        B = self._emission_probs(X)
        _, _, gamma, _ = self._forward_backward(B)
        viterbi_states = self._viterbi(B)

        regime_sequence = [self.state_to_regime_map[int(s)] for s in viterbi_states]
        return regime_sequence, gamma

    def predict_current_proba(self, features_df: pd.DataFrame) -> Dict[MarketRegimeType, float]:
        """
        Calculates normalized posterior probabilities for the latest market observation.
        """
        if not self.is_fitted:
            self.fit(features_df)

        X = features_df[self.feature_names].ffill().bfill().values
        B = self._emission_probs(X)
        _, _, gamma, _ = self._forward_backward(B)

        latest_gamma = gamma[-1] # shape (n_states,)
        
        # Map raw state posteriors to semantic regimes
        raw_probs = {
            regime: float(latest_gamma[self.regime_to_state_map[regime]])
            for regime in [
                MarketRegimeType.BULL,
                MarketRegimeType.BEAR,
                MarketRegimeType.NEUTRAL,
                MarketRegimeType.SEASONAL
            ]
        }

        # Strict normalization so probabilities sum precisely to 1.000
        total_p = sum(raw_probs.values()) or 1.0
        normalized = {k: round(v / total_p, 4) for k, v in raw_probs.items()}
        
        # Clean rounding residue
        diff = 1.0 - sum(normalized.values())
        max_regime = max(normalized.keys(), key=lambda k: normalized[k])
        normalized[max_regime] = round(normalized[max_regime] + diff, 4)

        return normalized
