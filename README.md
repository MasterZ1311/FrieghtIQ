# FreightIQ

**Intelligent Freight Forecasting & Vessel Chartering Decision-Support Platform**

> ⚠ **DEMO MODE**: All market indicators, freight rates, port queues, vessel specifications, and forecast series are **clearly labelled SYNTHETIC / DEMO values** generated for hackathon demonstration. They reflect real-world maritime physics, engineering constraints, and economic equilibria, but do NOT represent proprietary market data or physical chartering quotes.

---

## Overview

FreightIQ empowers dry bulk charterers, steel producers, and power utilities importing raw materials to the East Coast of India to optimize chartering decisions:

1. **Forward Freight Forecasting**: Multi-horizon freight rate predictions with explainability drivers and confidence bounds.
2. **Vessel Feasibility & Selection**: Validates physical compatibility (draft, LOA, beam, DWT) and recommends optimal tonnage.
3. **Port Constraint Intelligence**: Checks draft limits, tide gates, and turnaround speeds across all East Coast Indian ports.
4. **Voyage Economics**: Full maritime voyage cost breakdown including bunker fuel burn, port dues, canal tolls, and Time Charter Equivalent (TCE).
5. **Idle Scenario & Demurrage Management**: Anchorage queue exposure calculations, virtual arrival slow-steaming bunker savings, and port diversion alternatives.
6. **Procurement & Contract Strategy**: Quantitative trade-off between Spot, Short-Term COA, and Medium-Term Time Charter contracts.
7. **Multi-Factor Risk Scoring**: Evaluates geopolitical, bunker volatility, congestion, and operational risks (0–100 scale).

---

## System Architecture

```
freightiq/
├── backend/                  # Python FastAPI + SQLAlchemy + scikit-learn
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint + lifespan initialization
│   │   ├── config.py         # App settings & CORS configuration
│   │   ├── database.py       # SQLAlchemy engine & SQLite session
│   │   ├── models/           # SQLAlchemy ORM models (8 synthetic datasets)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routers/          # 9 modular API routers
│   │   ├── services/         # Maritime business logic engines
│   │   ├── ml/               # ML ensemble (GBM, RF, Ridge) + preprocessing
│   │   └── seed/             # Synthetic data generators & seeder
│   ├── fixtures/
│   │   ├── payloads/         # 9 sample API request payloads (JSON)
│   │   └── scenarios/        # Scenarios A, B, C, D definitions (JSON)
│   ├── seed.py               # Standalone database seeder CLI
│   ├── reset_db.py           # Clean database teardown & re-seed tool
│   ├── run_scenarios.py      # Automated scenario validation runner
│   ├── verify_all.py         # Full integration test suite (10/10 endpoints)
│   ├── smoke_test.py         # HTTP smoke test
│   ├── .env.example          # Environment variable template
│   └── requirements.txt
│
└── frontend/                 # Next.js 14 + TypeScript + Tailwind + Recharts
    └── src/
        ├── app/              # Next.js App Router pages
        ├── components/       # UI widgets and charts
        ├── lib/              # API client & utilities
        └── types/            # TypeScript interfaces
```

---

## Quick Start & Developer Setup

### 1. Environment Configuration

```bash
cd backend

# Create virtual environment (Python 3.10+)
python -m venv venv
venv\Scripts\activate          # Windows PowerShell / CMD
# source venv/bin/activate     # Linux / macOS

# Install backend dependencies
pip install -r requirements.txt

# Copy environment variables
copy .env.example .env         # Windows
# cp .env.example .env         # Linux / macOS
```

### 2. Database Initialization & Seeding

FreightIQ includes automated CLI tools for database lifecycle management:

```bash
# Full Database Reset & Clean Re-Seed (recreates schema, seeds 8 datasets, trains ML model)
python reset_db.py

# Standalone Seeder (seed without dropping existing tables, or use --force)
python seed.py --force
```

### 3. Run Validation Suites

```bash
# Execute and validate the 4 compelling demo scenarios
python run_scenarios.py

# Run complete 10-module integration test suite
python verify_all.py
```

### 4. Start the Development Server

```bash
# Start backend on http://localhost:8000
uvicorn app.main:app --reload --port 8000
```

- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Synthetic Datasets Catalog

All records are tagged with `is_demo = True` and explicit demo labels.

| # | Dataset / Model | Table Name | Records | Description |
|---|-----------------|------------|---------|-------------|
| 1 | **Freight Rates** | `freight_rates` | 17,290 | Weekly historical rate time-series across 35 routes and 4 vessel classes over 2.5 years. |
| 2 | **Ports** | `ports` | 14 | 7 Indian East Coast destinations + 7 global export origins with max draft, LOA, beam, and handling rates. |
| 3 | **Vessels** | `vessels` | 4 | Handysize, Supramax, Panamax, and Capesize specifications, fuel burns, and daily OPEX. |
| 4 | **Routes** | `routes` | 35 | Distance table in nautical miles (NM), canal transits (Suez), and viable vessel types. |
| 5 | **Market Indicators** | `market_indicators` | 130 | Baltic Dry Index (BDI), BCI, BPI, BSI, BHSI proxies, VLSFO/IFO/MGO bunker prices, fleet utilization. |
| 6 | **Port Congestion** | `port_congestion` | 910 | Weekly anchorage vessel queues, waiting days, berth occupancy, and weather delay factors for all East Coast ports. |
| 7 | **Commodity Indicators** | `commodity_indicators` | 650 | Benchmark FOB coal pricing (Newcastle, Richards Bay, ICI4 Indonesia, US) and Indian power/steel demand indices. |
| 8 | **Historical Observations** | `historical_observations` | 17,290 | Unified multi-factor historical observations linking rates, bunker, congestion, and demand. |

---

## Origins, Destinations & Vessel Matrix

### Export Origins
- **Australia**: Newcastle (Coal, 15.0m draft), Port Hedland (Iron Ore, 19.0m draft)
- **United States**: Hampton Roads (Coal, 14.5m draft), Baltimore (Coal, 13.7m draft)
- **Mozambique**: Nacala (Coal, 14.0m draft)
- **Russia**: Murmansk (Coal/Fertilizer, 12.5m draft)
- **Indonesia**: Kalimantan (Thermal Coal river anchorage, 12.0m draft)

### East Coast Indian Destinations
- **Paradip**: 14.5m draft limit, 180k max DWT, high congestion (~5.5d wait). Capesize fully laden is infeasible.
- **Visakhapatnam**: 15.0m draft, 200k max DWT, medium congestion (~3.0d wait). Outer harbour takes Panamax & Baby-Cape.
- **Gangavaram**: 18.0m deepwater draft, 200k max DWT, low congestion (~1.5d wait), 35k MT/day handling. Fully accommodates Capesize.
- **Gopalpur**: 11.0m draft limit, 60k max DWT, tide-gated. Panamax/Capesize infeasible; Handysize/small Supramax only.
- **Dhamra**: 17.0m deepwater draft, 180k max DWT, modern Adani port, low turnaround (~1.5d wait).
- **Sagar-Sandheads**: 13.0m draft limit, 120k max DWT, outer anchorage transhipment, tide-restricted.
- **Haldia**: 9.5m shallow river draft limit, 80k max DWT, tide-restricted, high congestion (~7.0d wait). Handysize optimal.

### Vessel Classes
- **Handysize**: 25,000–40,000 DWT | 10.5m Draft | Geared | Shallow ports (Gopalpur, Haldia)
- **Supramax**: 50,000–65,000 DWT | 12.8m Draft | Geared | Versatile river & anchorage access (Indonesia)
- **Panamax**: 65,000–82,000 DWT | 14.0m Draft | Gearless | Standard coal workhorse (Paradip, Vizag, Dhamra)
- **Capesize**: 150,000–200,000 DWT | 18.0m Draft | Gearless | Large scale economics, deepwater only (Gangavaram, Dhamra)

---

## Compelling Demo Scenarios

Run all scenarios with `python run_scenarios.py`. JSON parameters are in `backend/fixtures/scenarios/`.

### Scenario A: Australia → Paradip
- **Parameters**: 75,000 MT coal shipment; 500,000 MT annual program.
- **Port Feasibility**: Capesize draft (18.0m) exceeds Paradip maximum draft (14.5m) → **FAIL / Infeasible**. Panamax draft (14.0m) is **COMPATIBLE**.
- **Optimal Vessel**: **Panamax** recommended (Fit score 99.0/100).
- **Congestion & Demurrage Mitigation**: Paradip queue wait of 5.5 days creates ~$207k congestion exposure. The engine recommends **Virtual Arrival & Slow-Steaming** (11.5 knots), absorbing 2.4 waiting days at sea and saving **$120,155 in bunker fuel**.
- **Contract Strategy**: Evaluates procurement options across annual volume to mitigate spot rate volatility.

### Scenario B: Indonesia → Dhamra
- **Parameters**: 55,000 MT thermal coal shipment; short-haul route (3,050 NM).
- **Loading Origin Constraints**: Kalimantan loading anchorages have a 12.0m draft limit → Capesize is **physically blocked**.
- **Optimal Vessel**: **Geared Supramax** (55,000 MT) is optimal for river anchorage barge loading and Dhamra deepwater discharge.
- **Forecast Signal**: Freight market model detects softening rate momentum (-16.9% forecast decline) → triggers **WAIT** signal (89.8% confidence), postponing fixture by 15 days to save **$63,250**.

### Scenario C: United States → Visakhapatnam
- **Parameters**: 70,000 MT metallurgical coal; 500,000 MT annual program.
- **Maritime Economics**: Long-haul 12,900 NM route via Suez Canal ($250,000 canal toll). Sea voyage is 37.1 days, burning **$836,904 in bunker fuel**.
- **Contract Optimization**: Fixed-term commitment (12-Voyage COA at $31.33/MT vs Spot $35.81/MT) produces **$2,240,000 in measurable annual freight savings**, shielding the charterer from long-haul bunker and market spikes.

### Scenario D: Mozambique → Gangavaram
- **Parameters**: 160,000 MT bulk coal shipment; 800,000 MT annual volume.
- **Deepwater Advantage**: Unlike Paradip, Gangavaram's **18.0m draft** fully accepts a laden Capesize bulker.
- **Economies of Scale**: Capesize freight rate is **$10.16/MT** vs **$15.35/MT** for Panamax. Transporting 160k MT on a single Capesize saves **$5.19/MT (33.8%)**, delivering **$830,400 in direct freight savings per voyage**.

---

## Sample API Payloads

Ready-to-use JSON payloads are located in `backend/fixtures/payloads/`:

| Endpoint | Payload File | Description |
|----------|--------------|-------------|
| `POST /api/forecast/predict` | `forecast_predict.json` | Freight rate forecast with confidence interval and drivers |
| `POST /api/vessels/recommend` | `vessels_recommend.json` | Recommends optimal vessel class and scores alternatives |
| `POST /api/ports/check` | `ports_check.json` | Physical compatibility check (draft, LOA, DWT, tide) |
| `POST /api/economics/calculate` | `economics_calculate.json` | Voyage P&L, bunker burn, canal tolls, and TCE calculator |
| `POST /api/market-entry/signal` | `market_entry_signal.json` | BUY_NOW / WAIT / CAUTIOUS_BUY market entry signal |
| `POST /api/risk/score` | `risk_score.json` | Multi-factor operational and geopolitical risk assessment |
| `POST /api/contracts/compare` | `contracts_compare.json` | Spot vs COA vs Time Charter economic comparison |
| `POST /api/scenarios/simulate` | `scenarios_simulate.json` | What-if scenario comparison across routes and vessels |
| `POST /api/scenarios/idle-analysis` | `idle_analysis.json` | Anchorage waiting costs, demurrage, and slow steaming |

### Quick cURL Example
```bash
curl -X POST http://localhost:8000/api/ports/check \
  -H "Content-Type: application/json" \
  -d @fixtures/payloads/ports_check.json
```

---

## Developer Tooling Reference

| Command | Action |
|---------|--------|
| `python reset_db.py` | Complete teardown, schema creation, fresh seed, ML retrain, count verification. |
| `python seed.py --force` | Re-seeds all 8 synthetic datasets into the database. |
| `python run_scenarios.py` | Executes Scenarios A, B, C, D and prints verification assertions. |
| `python verify_all.py` | Runs the 10-module FastAPI TestClient integration test suite. |
| `python smoke_test.py` | HTTP endpoint smoke test against a running server (`localhost:8000`). |

---

> Built for SIH Hackathon · FreightIQ Platform v1.0
