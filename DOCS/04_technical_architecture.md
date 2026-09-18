# 🗺️ Document 4: Technical Architecture
## SIH26006 — System Design, ML Models & Implementation Blueprint

---

## 1. High-Level Architecture

```
╔══════════════════════════════════════════════════════════════════════╗
║              FreightIQ 2.0 — SAIL Edition Architecture              ║
╠══════════════════════════════════════════════════════════════════════╣
║  LAYER 1: DATA INGESTION (Real-Time + Historical)                   ║
║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────────┐ ║
║  │ AIS Feed │ │ BDI/BCI  │ │  INCOIS  │ │   News NLP RSS Stream  │ ║
║  │ (4h lag) │ │ (daily)  │ │  Tides   │ │   (15-min polling)     │ ║
║  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────────┬────────────┘ ║
║       └────────────┴────────────┴───────────────────┘             ║
║                        ↓ Feature Engineering Pipeline              ║
╠══════════════════════════════════════════════════════════════════════╣
║  LAYER 2: ML CORE (Three Parallel Engines)                         ║
║  ┌──────────────────┐ ┌─────────────────┐ ┌───────────────────────┐ ║
║  │ TFT Rate         │ │ HMM Regime      │ │ BSM Options Pricing   │ ║
║  │ Forecaster       │ │ Classifier      │ │ Engine                │ ║
║  │ 7 / 14 / 30 day  │ │ 4 regime states │ │ Wait vs. Fix signal   │ ║
║  │ BCI / BPI / BSI  │ │ Transition prob │ │ Option value $/MT     │ ║
║  └─────────┬────────┘ └────────┬────────┘ └──────────┬────────────┘ ║
║            └──────────────────┴──────────────────────┘             ║
║                           ↓ Ensemble Signal                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  LAYER 3: DECISION ENGINE                                          ║
║  • Vessel-Port Compatibility Matrix (draft / LOA / DWT / cargo)    ║
║  • Voyage Economics Calculator (TCE, bunker, canal, port dues)     ║
║  • Virtual Arrival Speed Optimizer (AIS queue → optimal knots)     ║
║  • Contract Mix Optimizer (Markowitz Efficient Frontier)           ║
║  • Tidal Gate Scheduler (INCOIS + vessel ETA)                      ║
║  • Carbon-Adjusted Cost Calculator (CII + EU ETS)                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  LAYER 4: API (FastAPI — 15 Modular Routers)                       ║
║  /forecast  /vessels  /ports  /economics  /contracts  /risk        ║
║  /regime    /options  /tides  /congestion /portfolio  /copilot     ║
╠══════════════════════════════════════════════════════════════════════╣
║  LAYER 5: INTERFACE                                                ║
║  ┌──────────────────────────┐ ┌─────────────────────────────────┐  ║
║  │ Interactive Dashboard    │ │ AI Chartering Copilot           │  ║
║  │ (Next.js 14 + Recharts)  │ │ (LLM + Tool Calling Interface)  │  ║
║  │ • Live Port Heatmap      │ │ • Natural language queries      │  ║
║  │ • BDI Forecast Chart     │ │ • Multi-step reasoning          │  ║
║  │ • Regime Gauge           │ │ • PDF report export             │  ║
║  │ • Tidal Calendar         │ │ • Annual program advisor        │  ║
║  │ • Efficient Frontier     │ │                                 │  ║
║  └──────────────────────────┘ └─────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 2. ML Model Details

### 2.1 Temporal Fusion Transformer (TFT) — Rate Forecaster

**Why TFT over LSTM:**
| Feature | LSTM | TFT |
|---------|------|-----|
| Multi-horizon output | Single step only | 7/14/30 days natively |
| Interpretability | Black box | Built-in attention weights (SHAP-equivalent) |
| Exogenous variables | Difficult to integrate | Native support (past + known future) |
| Quantile forecasting | Not native | Native (P10/P50/P90) |
| Training stability | Vanishing gradient risk | Stable via attention |

**Input Features:**
```
Past Observed Variables (time series):
  - BCI ($/day)           - BPI ($/day)
  - BSI ($/day)           - VLSFO bunker price ($/MT)
  - Newcastle coal FOB    - ICI4 Indonesia FOB
  - Port congestion score - Fleet utilization %
  - AIS anchor count      - News sentiment score

Known Future Variables:
  - Seasonal dummies (month, quarter)
  - Chinese New Year calendar (planned)
  - Indian import program calendar (if provided by SAIL)
  - Vessel delivery schedule (from Clarksons data)

Static Covariates (per-series metadata):
  - Route ID (35 routes)
  - Vessel class (4 types)
  - Origin-destination pair
```

**Output:**
```python
{
  "route": "Australia_Newcastle_Paradip_Panamax",
  "forecast": {
    "7d":  {"p10": 24.1, "p50": 27.3, "p90": 31.2},  # $/MT
    "14d": {"p10": 22.8, "p50": 26.5, "p90": 32.4},
    "30d": {"p10": 20.1, "p50": 25.8, "p90": 35.1}
  },
  "key_drivers": {
    "BCI_trend": 0.45,         # SHAP-style importance weights
    "congestion_delta": 0.22,
    "news_sentiment": 0.18,
    "coal_fob_price": 0.15
  },
  "direction_signal": "BEARISH",
  "confidence": 0.73
}
```

### 2.2 HMM Regime Classifier

```python
# 4-state Gaussian HMM
states = ["SUPERCYCLE_BULL", "SEASONAL_LIFT", "NEUTRAL", "BEAR_DISTRESS"]

# Feature matrix per time step
features = [
    bdi_return_7d,      # 7-day return
    bdi_return_30d,     # 30-day return  
    bdi_volatility_30d, # Rolling 30-day realized volatility
    fleet_utilization,  # % of fleet employed
    coal_fob_normalized,# Newcastle coal relative to 5yr avg
    port_congestion_avg,# Average global port congestion
    sentiment_score_7d  # 7-day rolling sentiment
]

# Contract recommendation per regime
regime_to_action = {
    "SUPERCYCLE_BULL": {
        "contract": "TIME_CHARTER_6M",
        "urgency": "IMMEDIATE",
        "confidence_threshold": 0.60
    },
    "SEASONAL_LIFT": {
        "contract": "SHORT_COA_3V",
        "urgency": "WITHIN_2_WEEKS", 
        "confidence_threshold": 0.65
    },
    "NEUTRAL": {
        "contract": "MIXED_SPOT_COA",
        "urgency": "EVALUATE_WEEKLY",
        "confidence_threshold": 0.70
    },
    "BEAR_DISTRESS": {
        "contract": "SPOT_ONLY",
        "urgency": "NO_RUSH",
        "confidence_threshold": 0.75
    }
}
```

### 2.3 Ensemble Decision

```python
def generate_market_signal(tft_forecast, hmm_regime, options_value):
    """Combine all three models into a single actionable signal"""
    
    regime = hmm_regime["current_regime"]
    regime_confidence = hmm_regime["regime_confidence"]
    rate_direction = tft_forecast["direction_signal"]
    rate_confidence = tft_forecast["confidence"]
    
    # Options value signal
    if options_value["option_value"] > options_value["fix_now_value"] * 0.15:
        options_signal = "WAIT"
    else:
        options_signal = "FIX_NOW"
    
    # Weighted ensemble
    signals = {
        "tft": ("BUY_NOW" if rate_direction == "BULLISH" else "WAIT", rate_confidence),
        "hmm": (regime_to_action[regime]["contract"], regime_confidence),
        "options": (options_signal, 0.80)  # BSM is deterministic, high confidence
    }
    
    # Plurality vote with confidence weighting
    final_signal = weighted_vote(signals)
    
    return {
        "signal": final_signal,
        "reasoning": generate_explanation(signals),
        "expected_saving": calculate_expected_saving(final_signal, tft_forecast),
        "risk_of_being_wrong": calculate_downside(final_signal, options_value)
    }
```

---

## 3. API Architecture (FastAPI)

### Router Map (15 endpoints)

```
/api/
├── forecast/
│   ├── POST /predict          → TFT rate forecast (7/14/30d, P10/P50/P90)
│   └── GET  /regime           → HMM regime + transition probabilities
│
├── options/
│   └── POST /wait-or-fix      → BSM options value for wait vs. fix decision
│
├── vessels/
│   └── POST /recommend        → Vessel class + feasibility score
│
├── ports/
│   ├── POST /check            → Draft/LOA/DWT physical compatibility check
│   ├── GET  /congestion       → Live congestion score (AIS-derived)
│   └── GET  /tidal-windows    → INCOIS tidal predictions for tide-gated ports
│
├── economics/
│   ├── POST /calculate        → Voyage P&L (TCE, bunker, canal, dues)
│   └── POST /carbon-adjusted  → Carbon-adjusted total cost (CII + EU ETS)
│
├── contracts/
│   ├── POST /compare          → Spot vs. COA vs. TC economic comparison
│   └── POST /portfolio        → Annual procurement Markowitz optimization
│
├── market-entry/
│   └── POST /signal           → BUY_NOW / WAIT / CAUTIOUS_BUY signal
│
├── risk/
│   └── POST /score            → Multi-factor risk score (geopolitical, congestion, bunker)
│
├── scenarios/
│   ├── POST /simulate         → What-if scenario comparison
│   └── POST /idle-analysis    → Demurrage + virtual arrival optimization
│
└── copilot/
    └── POST /chat             → LLM chartering copilot (multi-turn)
```

---

## 4. Database Schema (Extended from Existing)

### New Tables Added to Existing 8

```sql
-- Tidal Window Predictions (from INCOIS)
CREATE TABLE tidal_windows (
    id INTEGER PRIMARY KEY,
    port_code VARCHAR(10),
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    max_draft_at_window DECIMAL(4,2),
    tide_height DECIMAL(4,2),
    source VARCHAR(20) DEFAULT 'INCOIS',
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- AIS Congestion Snapshots
CREATE TABLE port_congestion_ais (
    id INTEGER PRIMARY KEY,
    port_code VARCHAR(10),
    snapshot_time TIMESTAMP,
    anchor_count INTEGER,
    drifting_count INTEGER,
    berthed_count INTEGER,
    avg_approach_speed DECIMAL(5,2),
    congestion_score INTEGER CHECK (congestion_score BETWEEN 0 AND 100),
    vessel_list JSONB  -- Array of {mmsi, vessel_type, cargo_type}
);

-- Market Regime History
CREATE TABLE market_regimes (
    id INTEGER PRIMARY KEY,
    regime_name VARCHAR(30),
    start_date DATE,
    end_date DATE,
    confidence DECIMAL(4,3),
    bci_avg DECIMAL(10,2),
    primary_driver VARCHAR(100)
);

-- News Sentiment Feed
CREATE TABLE news_sentiment (
    id INTEGER PRIMARY KEY,
    headline TEXT,
    source VARCHAR(50),
    published_at TIMESTAMP,
    category VARCHAR(30),
    sentiment_score DECIMAL(4,3),  -- -1.0 to +1.0
    relevance_score DECIMAL(4,3),  -- 0.0 to 1.0
    relevant_routes JSONB,
    rate_impact_prediction VARCHAR(20),
    lag_days_estimate INTEGER
);

-- Carbon Profiles (Vessel × Voyage)
CREATE TABLE carbon_calculations (
    id INTEGER PRIMARY KEY,
    voyage_id INTEGER,
    vessel_class VARCHAR(20),
    co2_emitted_mt DECIMAL(10,2),
    cii_rating CHAR(1),
    eu_ets_cost_usd DECIMAL(10,2),
    total_carbon_cost_usd DECIMAL(10,2),
    calculated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. ML Training Pipeline

```python
# backend/ml/training_pipeline.py

class FreightIQTrainingPipeline:
    
    def __init__(self):
        self.tft_trainer = TFTTrainer(
            max_epochs=50,
            learning_rate=0.001,
            hidden_size=64,
            attention_head_size=4,
            dropout=0.1,
            output_size=7  # P10,P20,P30,P50,P70,P80,P90
        )
        self.hmm_trainer = HMMTrainer(n_states=4, n_iter=1000)
    
    def train_all(self, historical_data: pd.DataFrame):
        """Full training pipeline called by reset_db.py"""
        
        # Step 1: Feature engineering
        features = self.engineer_features(historical_data)
        
        # Step 2: Train TFT on all 35 routes × 4 vessel classes = 140 time series
        tft_model = self.tft_trainer.fit(features)
        
        # Step 3: Train HMM regime classifier on BDI + exogenous
        hmm_model = self.hmm_trainer.fit(features[["bdi", "fleet_util", "coal_fob"]])
        
        # Step 4: Calibrate BSM volatility surface from historical rates
        vol_surface = self.calibrate_volatility_surface(historical_data)
        
        # Step 5: Save all models
        self.save_models(tft_model, hmm_model, vol_surface)
        
        return {
            "tft_backtest_rmse": tft_model.evaluate()["rmse"],
            "hmm_regime_accuracy": hmm_model.evaluate()["accuracy"],
            "vol_surface_calibration_r2": vol_surface.r2_score
        }
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature engineering for all models
        """
        df["bdi_return_7d"] = df["bdi"].pct_change(7)
        df["bdi_return_30d"] = df["bdi"].pct_change(30)
        df["bdi_volatility_30d"] = df["bdi"].rolling(30).std()
        df["coal_fob_normalized"] = df["coal_fob"] / df["coal_fob"].rolling(252).mean()
        df["bunker_premium"] = df["vlsfo_price"] - df["hsfo_price"]
        df["congestion_global"] = df[["paradip_cs", "vizag_cs", "gangavaram_cs"]].mean(axis=1)
        
        # Seasonality features
        df["month"] = pd.to_datetime(df["date"]).dt.month
        df["quarter"] = pd.to_datetime(df["date"]).dt.quarter
        df["is_coal_season"] = (df["month"].isin([10, 11, 12, 1])).astype(int)
        df["is_chinese_new_year"] = (df["month"].isin([1, 2])).astype(int)
        
        return df
```

---

## 6. LLM Copilot — Tool-Calling Architecture

```python
# backend/services/copilot.py

from langchain.agents import AgentExecutor
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

# Define all tools the LLM can call
@tool
def get_freight_forecast(route: str, vessel_class: str, horizon_days: int) -> dict:
    """Get TFT freight rate forecast for a specific route and vessel class"""
    return forecast_service.predict(route, vessel_class, horizon_days)

@tool  
def check_port_constraints(port: str, vessel_draft: float, 
                            cargo_mt: float, vessel_loa: float) -> dict:
    """Validate vessel physical compatibility with port"""
    return port_service.check(port, vessel_draft, cargo_mt, vessel_loa)

@tool
def calculate_voyage_economics(origin: str, destination: str, 
                                 cargo_mt: float, vessel_class: str) -> dict:
    """Calculate full voyage P&L including TCE, bunker, canal tolls"""
    return economics_service.calculate(origin, destination, cargo_mt, vessel_class)

@tool
def get_market_regime() -> dict:
    """Get current market regime from HMM classifier"""
    return regime_service.current_regime()

@tool
def get_wait_or_fix_signal(route: str, target_rate: float, 
                             days_until_needed: int) -> dict:
    """BSM options pricing: should SAIL wait or fix charter now?"""
    return options_service.calculate(route, target_rate, days_until_needed)

@tool
def get_port_congestion(port_name: str) -> dict:
    """Get live AIS-derived congestion score for an East Coast India port"""
    return congestion_service.get_score(port_name)

@tool
def get_tidal_windows(port: str, days_ahead: int = 30) -> dict:
    """Get INCOIS tidal entry windows for tide-gated ports"""
    return tidal_service.get_windows(port, days_ahead)

@tool
def optimize_annual_portfolio(annual_mt: float, 
                               routes: list,
                               risk_tolerance: str = "moderate") -> dict:
    """Markowitz optimization: optimal Spot/COA/TC mix for annual program"""
    return portfolio_service.optimize(annual_mt, routes, risk_tolerance)

# Initialize the copilot agent
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.1)
tools = [get_freight_forecast, check_port_constraints, calculate_voyage_economics,
         get_market_regime, get_wait_or_fix_signal, get_port_congestion,
         get_tidal_windows, optimize_annual_portfolio]

agent = AgentExecutor(
    agent=create_openai_tools_agent(llm, tools, CHARTERING_PROMPT),
    tools=tools,
    memory=ConversationBufferWindowMemory(k=10),  # Remember last 10 turns
    verbose=True
)
```

---

## 7. Frontend Component Map (Next.js 14)

```
frontend/src/
├── app/
│   ├── page.tsx                    → Dashboard home
│   ├── copilot/page.tsx            → AI Chartering Copilot chat UI
│   ├── portfolio/page.tsx          → Annual procurement optimizer
│   └── scenarios/page.tsx          → What-if scenario builder
│
├── components/
│   ├── charts/
│   │   ├── FreightForecastChart.tsx    → TFT P10/P50/P90 area chart
│   │   ├── RegimeGauge.tsx             → HMM regime visualization
│   │   ├── PortCongestionHeatmap.tsx   → AIS congestion across ports
│   │   ├── TidalCalendar.tsx           → 30-day tidal window calendar
│   │   ├── EfficientFrontier.tsx       → D3.js scatter (risk vs. cost)
│   │   └── VoyageEconomicsWaterfall.tsx → Cost breakdown waterfall chart
│   │
│   ├── maps/
│   │   ├── EastCoastPortMap.tsx        → Leaflet.js port map + AIS overlay
│   │   └── PortDepthVisualizer.tsx     → SVG cross-section digital twin
│   │
│   ├── widgets/
│   │   ├── OptionValueTicker.tsx       → Live BSM "wait vs fix" widget
│   │   ├── MarketPulseScore.tsx        → NLP news sentiment gauge
│   │   ├── ContractRecommendation.tsx  → BUY_NOW / WAIT card
│   │   └── CarbonFootprintCard.tsx     → CO2 + CII + EU ETS display
│   │
│   └── copilot/
│       ├── CopilotChat.tsx             → Streaming LLM chat interface
│       └── ToolCallVisualizer.tsx      → Shows which tools were called
```

---

## 8. Deployment Architecture

```
Production Stack:
  Backend:  FastAPI (Uvicorn) → Docker → Cloud Run (GCP) or Railway
  Frontend: Next.js → Vercel (auto-deploy from GitHub)
  DB:       PostgreSQL → Supabase (free tier, 500MB)
  Cache:    Redis → Upstash Redis (free tier, real-time data)
  ML:       Models serialized → .pkl files → loaded at startup
  LLM:      Google AI API (Gemini 1.5 Pro) / Anthropic Claude API

Demo / Hackathon Stack:
  Backend:  localhost:8000 (uvicorn)
  Frontend: localhost:3000 (next dev)
  DB:       SQLite (existing) → upgrade to PostgreSQL in 2h
  Cache:    In-memory dict (sufficient for demo)
  ML:       Pre-trained models loaded from backend/ml/saved/
```

---

*Document 4 of 6 | SIH26006 Research Suite | FreightIQ Platform*
