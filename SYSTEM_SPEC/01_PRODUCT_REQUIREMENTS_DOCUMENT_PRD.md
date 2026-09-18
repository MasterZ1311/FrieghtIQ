# 📄 FreightIQ — Product Requirements Document (PRD)
## Document Code: SPEC-PRD-001 | Version: 2.0 | SIH2026 Problem SIH26006
### Focus: Bulk Freight Forecasting & Chartering Decision Support (Thoothukudi & Chennai Centric)

---

## 1. Executive Summary & Product Vision

### 1.1 App Overview
**FreightIQ** is an AI-powered maritime freight intelligence, chartering decision-support, and voyage economics platform designed specifically for **Steel Authority of India Limited (SAIL)** and Indian maritime logistics operators. It synthesizes real-time and historical dry-bulk freight market dynamics, maritime physics, AIS vessel telemetry, INCOIS tidal gates, and macroeconomic commodity signals to answer four pivotal questions for bulk cargo chartering:
1. **WHEN to charter?** (Timing optimization via Black-Scholes Real Options and 4-State HMM Market Regimes).
2. **WHICH vessel to charter?** (Physics-based vessel matching considering draft, LOA, beam, and cargo density).
3. **WHICH port corridor to route through?** (Comparative economics across East/South coast ports: Thoothukudi VOCPA, Chennai, Kamarajar, Visakhapatnam, Paradip, and Haldia).
4. **HOW MUCH to pay & under WHAT contract structure?** (Quantile rate forecasting [P10/P50/P90], Spot vs. COA vs. Time Charter optimization, and IMO CII/EU ETS carbon penalty adjustments).

### 1.2 The Core Problem Statement
* Indian state-owned enterprises such as SAIL import over 15 to 20 Million Metric Tons (MMT) of coking coal and raw materials annually from Australia, Indonesia, the US, and Mozambique.
* **Extreme Volatility:** Dry bulk freight rates (Baltic Capesize/Panamax indices) exhibit annualized volatilities exceeding 45–60%. Fixing a single Capesize cargo 10 days too early or too late can result in an unhedged cash delta of **$300,000 to $1,200,000**.
* **Demurrage Traps:** Port congestion and draft mismatches at Indian ports generate over **$10M–$40M** in avoidable demurrage penalties annually (averaging $18,000–$32,000/day per idle vessel).
* **Decarbonization Mandates:** The International Maritime Organization's (IMO) Carbon Intensity Indicator (CII) and the European Union Emissions Trading System (EU ETS) penalize inefficient tonnage, creating hidden freight surcharges.

---

## 2. Target User Personas & Roles

| Persona | Title | Core Objective | Key Pain Point Solved |
|---|---|---|---|
| **Persona 1: The Chartering Manager** | Chief General Manager (Shipping & Raw Materials, SAIL) | Minimize CIF procurement costs for coking coal; optimize spot vs. long-term contract exposure. | Eliminates guesswork in booking timing; provides mathematical justification (Black-Scholes option value) to fix or defer. |
| **Persona 2: Port Logistics Operations Lead** | General Manager (Port Operations, VOCPA / Chennai / Paradip) | Prevent vessel waiting queues, match parcels to safe berth draft, schedule tidal arrivals. | Eliminates demurrage via Virtual Arrival speed negotiation and tidal gate clearance. |
| **Persona 3: Financial Risk Officer** | Executive Director (Finance & Commercial Audit) | Audit procurement decisions, ensure anti-corruption compliance, stress-test freight budgets against market disruptions. | Transparent synthetic and historical audit logs; scenario simulation for Red Sea/Suez disruptions. |
| **Persona 4: Chartering Officer (Vibe Coder / Junior Analyst)** | Deputy Manager (Commercial Logistics) | Rapidly generate voyage P&L, TCE estimates, and executive briefing reports. | Natural language AI Copilot with tool-calling; guided 4-step chartering workflow wizard. |

---

## 3. Core Functional Feature Modules

### Module 1: 4-State Hidden Markov Model (HMM) Market Regime Classifier
* **User Story:** As a Chartering Manager, I need to know the underlying hidden state of the freight market so I don't book long-term contracts during market peaks or spot fixtures during supercycle bulls.
* **Features:**
  - Classifies market into 4 distinct macro regimes:
    1. `BEAR_DISTRESS` (Falling rates, high tonnage surplus, recommend Spot booking).
    2. `NEUTRAL` (Mean-reverting rates, balanced fleet, recommend short-term COA).
    3. `SEASONAL_LIFT` (Rising rates driven by monsoon/cyclone/seasonal restocking, recommend fixing ahead).
    4. `SUPERCYCLE_BULL` (Demand shock / fleet supply crunch, recommend forward index hedging or long-term charters).
  - Displays transition probability matrix ($4 \times 4$) indicating probability of shifting to another regime over the next 30 days.
  - Interactive 30-day Baltic Capesize Index (BCI) historical chart with color-coded regime bands.
* **Acceptance Criteria:**
  - Dynamic API endpoint `GET /api/regime/current` updates every 60 seconds.
  - Confidence percentage must be displayed alongside the primary market driver.

### Module 2: Temporal Fusion Transformer (TFT) / LightGBM Quantile Rate Forecasting
* **User Story:** As a Commercial Planner, I need probabilistic freight rate forecasts rather than a single misleading point forecast so I can assess downside and upside risk.
* **Features:**
  - Generates 7-day, 14-day, 30-day, and 60-day freight forecasts in USD/MT.
  - Returns 3 quantile lines:
    - **P10 (Pessimistic / Lower Bound):** 10th percentile rate outcome.
    - **P50 (Median / Expected):** 50th percentile baseline expectation.
    - **P90 (Optimistic / Upper Bound):** 90th percentile rate risk ceiling.
  - Historical back-casting toggle comparing predicted vs. actual rates over the prior 90 days.
* **Acceptance Criteria:**
  - Support for 50 primary routes, specifically highlighting **Australia ➔ Thoothukudi**, **Australia ➔ Chennai**, **Indonesia ➔ Chennai**, and **Australia ➔ Paradip**.
  - Response time $< 400\text{ ms}$.

### Module 3: Black-Scholes Real Options Market Entry Timing Engine
* **User Story:** As a Chartering Officer, when rates are volatile, I have the option to wait before fixing. I need to know the financial value of waiting vs. locking in today's rate.
* **Features:**
  - Models charter delay as an American Call Option on freight:
    $$\text{Option Value } C = S \cdot N(d_1) - K \cdot e^{-rT} N(d_2)$$
  - Calculates strike rate ($K$), spot freight ($S$), annualized freight volatility ($\sigma$), and time to laycan ($T$).
  - Produces an unambiguous recommendation: `CHARTER_NOW` vs. `WAIT_X_DAYS`.
  - Calculates the net dollar value of holding the option (e.g., "$120,155 option value if delayed 12 days").
* **Acceptance Criteria:**
  - Signal must output confidence score (0–100%) and quantifiable dollar risk.

### Module 4: Port Physical Constraints & Tidal Navigation Engine
* **User Story:** As a Port Operations Officer, I must ensure that chartered vessels do not run aground, exceed berth LOA, or miss high tide windows at shallow river ports.
* **Features:**
  - Deep validation against physical port limits:
    - **Thoothukudi (VOCPA):** Max draft 14.2m, max DWT 95,000, 14 berths (NCB-I, NCB-II), mechanized rate 15,000 MT/day.
    - **Chennai Port:** Max draft 15.5m, max DWT 150,000, Jawahar Dock JD-2 (pig iron) & Bharathi Dock BD-1/2.
    - **Kamarajar (Ennore):** Max draft 16.0m, max DWT 180,000, deepwater coal berths CB1/CB2.
    - **Haldia:** Max draft 8.5m (strict river limit; Capesize strictly blocked).
    - **Gangavaram / Paradip:** Deepwater berths up to 18.0m draft.
  - Dynamic tidal window simulation based on INCOIS harmonic tidal data for ports requiring high-water navigation (Haldia, Kolkata, Mumbai).
* **Acceptance Criteria:**
  - Returns boolean `compatible: true/false` with specific engineering reasons for rejection (e.g., "Draft 17.5m exceeds VOCPA limit 14.2m by 3.3m").

### Module 5: AIS Port Congestion & Virtual Arrival Demurrage Optimizer
* **User Story:** As a Fleet Controller, when discharge ports are backed up with 10 vessels in queue, I want to instruct the vessel to slow steam so we save bunker fuel instead of burning fuel to wait at anchor.
* **Features:**
  - Monitors live AIS congestion scores (0–100) across all Indian major discharge ports.
  - Real-world vessel queue tracking (e.g., `MV Vishva Vijay` at VOCPA, `MV Supra Monarch` at Chennai).
  - Calculates **Virtual Arrival** economics:
    - Normal transit vs. Slow-steaming transit.
    - Bunker fuel savings in MT and USD ($P \propto v^3$).
    - Demurrage reduction vs. waiting at anchorage.
    - Alternative diversion candidate evaluation (e.g., divert from congested Paradip to Gangavaram).
* **Acceptance Criteria:**
  - Generates exact bunker savings in USD and net congestion exposure dollars.

### Module 6: Maritime Voyage Economics & TCE Calculator
* **User Story:** As a Financial Analyst, I need an audited voyage P&L breaking down bunker fuel, port dues, canal tolls, daily OPEX, and Time Charter Equivalent (TCE).
* **Features:**
  - Nautical distance calculator across 50 international and domestic coastal routes.
  - Fuel consumption physics based on vessel deadweight, displacement, and laden/ballast speed.
  - Full financial P&L statement including gross operating profit and margin percentage.
* **Acceptance Criteria:**
  - Calculates TCE equivalence ($/day) and breakeven freight rate ($/MT).

### Module 7: Green Shipping, IMO CII & EU ETS Scope 3 Carbon Accounting
* **User Story:** As an ESG Director, I must ensure all chartered voyages comply with IMO decarbonization rules and track Scope 3 shipping emissions.
* **Features:**
  - Estimates voyage $\text{CO}_2$ emissions in MT and $\text{kg CO}_2 / \text{MT cargo}$.
  - Assigns an **IMO Carbon Intensity Indicator (CII)** letter rating (A, B, C, D, E).
  - Displays an animated SVG circular `CiiRing` visualizer with tier color-coding.
  - Computes EU ETS carbon allowance cost exposure ($€65–85/\text{MT CO}_2$).
  - Highlights Thoothukudi (VOCPA) as India's Green Hydrogen and Green Ammonia Bunkering Hub (*India Green Fuel Conclave '26*).
* **Acceptance Criteria:**
  - Provides slow-steaming emissions abatement recommendations and green charter surcharges.

### Module 8: Multi-Factor Risk Engine & Geopolitical Disruption Simulator
* **User Story:** As a Risk Manager, I need to evaluate route risks including maritime chokepoints (Suez, Panama, Bab-el-Mandeb), bunker spikes, and monsoon weather.
* **Features:**
  - Multi-factor weighted composite risk score (0–100 scale: Low, Moderate, High, Severe).
  - Scenario simulation matrix:
    - *Scenario 1:* Red Sea / Suez Canal Blockade (Cape of Good Hope detour: +14 days, +$420k bunker).
    - *Scenario 2:* Fuel Shock (VLSFO spike to $950/MT).
    - *Scenario 3:* East Coast Monsoon Congestion (Paradip cyclone backlog).
    - *Scenario 4:* Coastal Shipping Mode Shift (CJ Darcl liner corridor: rail-to-ship transition).
* **Acceptance Criteria:**
  - Every scenario displays direct evidence citations from official maritime gazettes (*Exim India Shipping Times*, *Global Timex*).

### Module 9: Contract Structure Optimizer (Spot vs. COA vs. Time Charter)
* **User Story:** As a Procurement Officer, I need recommendations on whether to procure on the Spot market, contract under a Contract of Affreightment (COA), or lease on a 3–12 month Time Charter.
* **Features:**
  - Comparative cost analysis for 500,000 MT annual volume across contract types.
  - Breakeven sensitivity against market volatility and forward curve backwardation/contango.

### Module 10: AI Chartering Copilot (Natural Language with Tool-Calling)
* **User Story:** As an executive, I want to ask plain-English questions (e.g., "Can we dock 75k MT coal at VOCPA right now?") and get authoritative, data-backed answers with clickable evidence.
* **Features:**
  - Integrated Gemini / LLM engine augmented with 5 specialized backend tools:
    1. `search_freight_rates`
    2. `check_port_constraints`
    3. `calculate_voyage_pnl`
    4. `recommend_vessels`
    5. `assess_port_congestion`
  - Visual tool-call chips and source citation panel.
  - Preset quick-query chips for Thoothukudi, Chennai, and Haldia scenarios.

---

## 4. Non-Functional Requirements (NFRs)

1. **Performance & Latency:**
   - Client-side page navigation: $< 100\text{ ms}$ (Next.js 16 static optimization).
   - API endpoints: $< 250\text{ ms}$ for mathematical physics engines; $< 1.5\text{ s}$ for LLM Copilot queries.
2. **Availability & Offline Resilience:**
   - Platform must run 100% offline without active internet connectivity during the SIH evaluation.
   - Self-contained SQLite database (`freightiq.db`) with pre-seeded gazette fixtures.
   - Fallback heuristics for HMM regime classifier when optional libraries are unavailable.
3. **Responsive Design & Accessibility:**
   - Seamless presentation on mobile (hamburger drawer sidebar), tablets, and 4K command-center projection displays.
   - Dark mode default with high-contrast accessibility (WCAG AA compliant).
4. **Security & Data Integrity:**
   - Role-Based Access Control (RBAC).
   - Read-only demo safeguards protecting core fixture data from accidental tampering.

---

## 5. Success Metrics & KPIs for Hackathon Evaluation

| Metric | Target | Verification Method |
|---|---|---|
| **Rate Prediction Accuracy (MAE)** | $< \$0.85\text{ / MT}$ | LightGBM out-of-sample back-test against Baltic fixtures. |
| **Demurrage Avoidance Savings** | $\$100,000\text{ to }\$250,000\text{ per voyage}$ | Virtual Arrival slow-steaming calculator output. |
| **Test Suite Coverage** | $100\%$ Pass (12/12 Endpoints) | Automated execution of `backend/verify_all.py`. |
| **Frontend Production Build** | $0\text{ Errors}, 16/16\text{ Static Routes}$ | `npm run build` Turbopack static compilation. |
| **Official Slide Deck Alignment** | Exactly 6 slides (Strict SIH format) | Automated generation via `scripts/generate_presentation.py`. |
