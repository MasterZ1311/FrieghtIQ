# SIH26006 — Deep Research & Unique Ideation
### Development of an Intelligent Freight Forecasting Model for Optimized Vessel Chartering and Bulk Cargo Procurement (East Coast India)
**Organization:** SAIL · Ministry of Steel | **Prize:** ₹1,50,000 | **Deadline:** 20 September 2026

---

## 🔍 Problem Deep-Dive: What's Really Going On

### The Core Pain (In SAIL's Own Words)
> *"Facilitate moving from multiple single spot contracts being entered into currently to short-term / medium-term multiple voyage contracts."*

SAIL's stated **Objective** is not just forecasting — it is a **procurement strategy transformation**. Today SAIL enters *n* individual spot contracts each time it needs to move bulk cargo. The goal is to move to **COA (Contract of Affreightment)** and **Time Charter** structures that lock in rates across multiple voyages.

This means the system must generate enough **confidence in rate direction** that procurement managers are willing to commit to multi-voyage contracts rather than hedging with expensive spot deals.

### The Hidden Sub-Problems Nobody Talks About

| Layer | Visible Problem | Hidden Depth |
|-------|----------------|--------------|
| **Forecasting** | Predict BDI / freight rates | Must predict *regime changes* — BDI collapsed 94% in 2008, rebounded 700% in 2021. Black swan events break every model |
| **Vessel Selection** | Match vessel to port draft | Must account for *laden vs. ballast draft*, tidal windows at Haldia (changes every 6h), and seasonal silting at Paradip |
| **Contract Timing** | When to fix a charter | Must factor in LIBOR/SOFR floating cost, FFA (Forward Freight Agreement) hedging, and counterparty credit risk |
| **Idle Time** | Minimize anchorage waiting | Involves active "virtual arrival" negotiation — a speed protocol between owner and charterer that requires contractual consent |
| **Port Congestion** | Queue estimation | Congestion at one port cascades: a vessel diverted from Paradip to Vizag cascades Vizag's queue, changing everyone's ETAs |

---

## 📊 Real-World Context: The Numbers That Matter

### SAIL's Import Scale
- SAIL imports **~20–25 million tonnes** of coking coal annually (primary feedstock for BF-BOF steelmaking)
- Predominantly from **Australia (BHP, Glencore)** and **USA (Arch Resources)**
- A 1 USD/MT saving in freight = **~$20–25 million saved annually**
- A single Capesize charter at wrong timing can cost **$200,000–$500,000 extra** vs. optimal entry

### Freight Rate Volatility — The Real Enemy
- **BCI (Baltic Capesize Index):** Has ranged from $2,000/day to $86,000/day (2008–2021). That's 43x volatility.
- **VLSFO Bunker Fuel:** Swings of ±$400/tonne in a year are common (post-IMO 2020)
- **Paradip Congestion:** Documented waiting times of 7–15 days in peak months (Oct–Jan) — at $15,000–25,000/day demurrage, that's $100k–$375k per vessel

### Why Spot-Only Chartering Is Expensive
- Brokers add **1.25% commission** per fixture — over 50+ fixtures/year, this compounds
- No leverage to negotiate **reduced laytime** or **fast dispatch** clauses in spot markets
- Continuous broker engagement costs (daily market calls, telex costs, Reuters/Baltic subscriptions)

---

## 🧠 Unique Ideas & Innovation Angles

### Idea 1: Freight Regime Detection + Forward Contract Trigger Engine ⭐⭐⭐⭐⭐

**What Most Solutions Miss:** They predict *rate level* but not *market regime*. The BDI has 4 distinct behavioral regimes:
- **Supercycle Bull** (sustained $30k+/day Capesize): Lock in TC immediately
- **Seasonal Lift** (Oct–Jan monsoon relief, Chinese New Year steel buildup): Short COA window
- **Contango/Backwardation** (FFA structure reveals market expectations): Spot vs. Forward arbitrage
- **Bear Distress** ($4k–8k/day): Spot only — owners desperate, rates below OPEX

**Innovation:** Build a **Hidden Markov Model (HMM) regime classifier** running in parallel to the rate forecaster. When the model detects a regime transition probability >70%, automatically trigger a **contract recommendation bulletin** with:
- Estimated duration of current regime
- Optimal contract length (1 voyage / 3-voyage COA / 6-month TC)
- Confidence interval and "regret cost" if wrong

**Why Unique:** No published academic paper applies HMM regime detection specifically to Indian port chartering decisions. This combines time-series ML with decision theory.

---

### Idea 2: AIS-Derived Port Congestion Intelligence ⭐⭐⭐⭐⭐

**The Problem with Existing Port Congestion Data:** Port Trust data is delayed 24–72 hours, self-reported, and politically sanitized. Real congestion is measured in AIS data.

**Innovation:** Build a real-time AIS data ingestion pipeline to:
1. Count vessels **at anchor / drifting** within 10 nautical miles of each East Coast Indian port
2. Track **vessel speed reduction** approaching port (classic congestion signal)
3. Measure **Port Dwell Time** = Time from port entry AIS signal to port departure
4. Build a **congestion heatmap** across 7 Indian ports + 7 origin ports updated every 4 hours

**Output:** A "Congestion Score" (0-100) for every port that feeds into:
- Optimal vessel sailing speed calculation (virtual arrival timing)
- Diversion decision engine (if Paradip CS=85, reroute to Vizag at CS=40)
- Demurrage exposure calculator ($k at risk per vessel in queue)

**Free Data Sources:**
- AISHub (aishub.net) — free for non-commercial
- OpenSeaMap AIS (openseamap.org) — open AIS data
- Satellite AIS free tier: ExactEarth Academic

---

### Idea 3: Synthetic Options Pricing for "Wait vs. Fix Now" Decisions ⭐⭐⭐⭐

**The Financial Insight:** A charter contract is structurally identical to a **call option** on freight rates. When you "wait to fix," you hold the option. When you "fix now," you exercise it.

**Innovation:** Apply **Black-Scholes-Merton options pricing** to freight:
- **S** = Current spot rate ($/MT or $/day)
- **K** = Strike = Target rate you want to lock in
- **σ** = Historical BDI volatility (annualized)
- **T** = Time until cargo is needed (days)
- **r** = Risk-free rate (RBI repo rate)

Calculate the **"Waiting Premium"** = Price of holding the option open vs. fixing today.

- If waiting premium > expected savings → **FIX NOW**
- If waiting premium < expected savings → **WAIT**

**Dashboard Widget:** A live "Option Value" ticker next to every route showing:
*"Waiting 7 more days for this route is worth ₹12.4 lakhs in expected savings — but has a 34% chance of costing ₹8.2 lakhs more."*

This is quantitative finance applied to industrial procurement. No other hackathon team will build this.

---

### Idea 4: Multi-Agent LLM Chartering Copilot ⭐⭐⭐⭐

**Concept:** Instead of a static dashboard, build a conversational AI agent that mimics how an expert shipping broker thinks:

```
User: "I need to move 70,000 MT of coking coal from Hampton Roads to 
       Paradip in the next 45 days. What's my best play?"

Agent: "Analyzing... 
       Route: Hampton Roads → Paradip: 12,900 NM via Suez 
       Draft: Paradip limit 14.5m → Panamax (14.0m draft) optimal
       Rates: Current Panamax $28/MT | 30-day forecast: $24.5/MT (-12.5%)
       Regime: BEARISH with 73% confidence
       Congestion: Paradip CS=78, ~6 day queue
       
       RECOMMENDATION: Fix in 12 days. 
         Expected saving vs. fixing today: $210,000
         Virtual arrival offset: depart 3 days late, absorb 2.1 queue days at sea
         Bunker saving from speed reduction: $89,000
       
       Want me to model a 3-voyage COA vs. 2 spot fixtures comparison?"
```

**Technical Stack:**
- Gemini 1.5 Pro / Claude 3.5 as reasoning backbone
- Tool calls: get_freight_forecast(), check_port_constraints(), calculate_voyage_economics()
- Memory: Previous queries stored to track SAIL's annual procurement calendar
- Output: Structured JSON recommendation + natural language explanation

**Why This Wins Judges:** The conversational interface lowers barrier to entry for non-technical logistics managers — the actual end users of this system.

---

### Idea 5: Carbon-Adjusted Freight Cost (CAFC) Calculator ⭐⭐⭐⭐

**The Regulatory Angle Nobody Covers:** IMO 2023 Carbon Intensity Indicator (CII) regulations mean vessels with poor CII ratings (D/E) face:
- Trading restrictions from 2025
- Charter rate discounts of $500–2,000/day vs. A/B rated vessels
- EU ETS cost pass-through (€60–80/tonne CO2 for EU-adjacent voyages)

**Innovation:** Add a **Carbon Risk Layer** to every voyage calculation:
1. Calculate CO2 emissions per voyage: `CO2 = fuel_consumption × emission_factor`
2. Apply CII rating lookup per vessel class
3. Calculate EU ETS exposure (for Suez-routed voyages with EU port calls)
4. Compute **True Total Cost** = Freight + Bunker + Port Dues + Carbon Cost

**Output:** A "Carbon-Adjusted Break-Even" showing which vessel class is truly cheapest after carbon costs — Capesize often looks cheapest but has highest absolute emissions.

This future-proofs the platform and demonstrates regulatory awareness that impresses Ministry-level judges.

---

### Idea 6: Tidal Gate Scheduler for Haldia & Gopalpur ⭐⭐⭐

**The Ultra-Niche Problem:** Haldia (draft limit 9.5m) and Gopalpur (11.0m, tide-gated) are river/coastal ports where entry is **only possible during a ±2 hour tidal window** that repeats ~twice daily.

**Innovation:** Integrate **INCOIS (Indian National Centre for Ocean Information Services)** tidal prediction API — which is **free and publicly available** — to:
1. Predict the next 30 days of safe entry windows for every tide-gated port
2. Auto-calculate: If vessel arrives T hours early/late, it misses the tide window and waits N hours
3. Factor tidal gate delay into voyage TCE calculation
4. Alert: "Vessel arriving Dec 18 at 14:00 IST will miss Haldia tidal window by 3 hours — consider adjusting speed from 12 to 13.5 knots to catch the 11:45 IST window"

**Data source:** INCOIS Portal (incois.gov.in) — real tidal prediction data, 100% free government API.

This is a uniquely India-specific feature that no generic maritime platform has. Judges from SAIL will immediately recognize its operational value.

---

### Idea 7: Procurement Calendar Optimization (Annual Voyage Planning) ⭐⭐⭐⭐

**The Bigger Picture:** SAIL's procurement isn't one-off — it's a **rolling annual program** of 40–60 shipments. The optimization problem is:

*"Given 500,000 MT annual import program from Australia to Paradip, what is the optimal mix of Spot, 3-voyage COA, and 6-month TC contracts across the year to minimize total freight cost at a given risk tolerance?"*

**Innovation:** Frame this as a **Stochastic Portfolio Optimization** problem:
- **Decision variables:** % allocated to Spot vs. COA vs. TC for each quarter
- **Objective:** Minimize E[Total Freight Cost] subject to Variance(Cost) ≤ Risk Budget
- **Constraint:** Physical delivery requirement (minimum 40k MT/month to prevent mill stockout)
- **Method:** Monte Carlo simulation of 10,000 rate scenarios × portfolio weightings → Efficient Frontier

**Visualization:** A **"Freight Efficient Frontier"** chart — exactly like Markowitz Portfolio Theory but for shipping contracts. No academic paper applies Modern Portfolio Theory to dry bulk procurement for Indian PSUs.

---

### Idea 8: Geopolitical Risk Pulse via NLP News Sentiment ⭐⭐⭐

**The Soft Data Problem:** Russian coal embargoes, Suez/Red Sea disruptions, Australian export restrictions — these move freight rates 30% in 48 hours, but they're in the news 2–3 days before they move the BDI.

**Innovation:** Build a **real-time news sentiment pipeline**:
1. RSS/API feeds: Reuters Shipping, TradeWinds, Lloyd's List, India Ports, S&P Global Platts
2. NLP model (fine-tuned BERT/DistilBERT or GPT API) classifies each article:
   - Category: Geopolitical / Weather / Demand / Supply / Port-specific
   - Sentiment Score: -1.0 (very bearish) to +1.0 (very bullish) for rates
   - Relevance: Is this article relevant to SAIL's specific trade lanes?
3. Aggregate into a daily **"Market Pulse Score"** that feeds into the ML model as an exogenous variable

**Technical:** Sentiment lag study shows BDI responds to news 48–72 hours after publication — exploitable alpha.

---

### Idea 9: Vessel-Port Compatibility Digital Twin ⭐⭐⭐

**Concept:** Build an interactive visual "Digital Twin" of each East Coast Indian port showing:
- **Cross-sectional depth profile** of the channel (showing how a 18m draft Capesize literally cannot enter Paradip's 14.5m channel)
- **Tide overlay:** How the water level changes through the day and what draft becomes available
- **Berth occupancy:** Which berths are available for which vessel classes
- **LOA constraints:** Visual showing a 300m Capesize vs. Paradip's maximum LOA capacity

**Implementation:** SVG/Canvas-based port visualization with real-time tidal overlay — visually stunning for jury presentation and immediately comprehensible to non-technical decision makers.

---

## 🏆 Winning Strategy: The "Unfair Advantages"

### Technical Differentiators
1. **HMM Regime Classifier** — genuinely novel application, not in textbooks
2. **Options Pricing for Chartering** — financial engineering meets logistics
3. **Live AIS Congestion** — real data vs. synthetic, massive credibility boost
4. **INCOIS Tidal Integration** — free, India-specific, operationally critical

### Presentation Differentiators
1. **Scenario A–D Live Demo** — run all 4 scenarios during judge presentation with live results
2. **ROI Calculator front and center** — show SAIL saves ~₹200 crore/year at current scale
3. **Conversational AI Interface** — let judges type natural language queries
4. **India-Specific Data** — SAIL judges respond to Paradip, Vizag, Dhamra by name

### Free Data Sources Catalog (Total Cost: ₹0)

| Data | Source | Update Frequency |
|------|---------|-----------------|
| Historical BDI/BCI/BPI/BSI | Baltic Exchange CSV (free samples) | Daily |
| Bunker prices | Ship & Bunker API (free tier) | Daily |
| AIS vessel positions | AISHub / OpenSeaMap | Every 4h |
| Tidal predictions | INCOIS Portal (free Gov API) | Daily |
| Port congestion | VPA, PPA, VCTPL websites (scraping) | Daily |
| News sentiment | Reuters RSS, TradeWinds | Real-time |
| Coal commodity prices | Quandl, IMF Commodity Portal | Weekly |
| Weather/cyclone risk | IMD Open Data Portal | Every 6h |

---

## 🗺️ System Architecture: The Grand Vision

```
FreightIQ 2.0 — SAIL Edition
═══════════════════════════════════════════════════════════════

DATA LAYER (Real-Time Ingestion)
 AIS Feed (4h)  ──┐
 BDI Feed (daily)─┤
 INCOIS Tides  ───┤──► Feature Engineering Pipeline
 News NLP RSS  ───┘

ML CORE (Three Parallel Engines)
 ┌─────────────────┐  ┌──────────────┐  ┌─────────────────────┐
 │ TFT Rate        │  │ HMM Regime   │  │ Options Pricing     │
 │ Forecaster      │  │ Classifier   │  │ Engine (BSM)        │
 │ 7/14/30d ahead  │  │ 4 regimes    │  │ Wait vs Fix signal  │
 └────────┬────────┘  └──────┬───────┘  └──────────┬──────────┘
          └─────────────────┴────────────────────┘

DECISION ENGINE
 • Vessel-Port Compatibility Matrix (physical constraints)
 • Voyage Economics Calculator (TCE, bunker, canal dues)
 • Virtual Arrival Speed Optimizer
 • Contract Mix Optimizer (Markowitz Efficient Frontier)
 • Carbon Risk Layer (CII ratings + EU ETS costs)

INTERFACE LAYER
 ┌───────────────────────┐  ┌────────────────────────────┐
 │ Interactive Dashboard │  │ AI Chartering Copilot       │
 │ • Port Heat Map       │  │ Natural language interface  │
 │ • Rate Forecast Chart │  │ Tool-calling to all APIs   │
 │ • Tidal Calendar      │  │ PDF report generation      │
 │ • Efficient Frontier  │  └────────────────────────────┘
 └───────────────────────┘
```

---

## 📐 Jury Scoring Strategy

| Jury Metric | Estimated Weight | Our Strategy |
|-------------|-----------------|--------------|
| Forecasting Accuracy (MAE/RMSE) | 25% | TFT + SHAP explainability; show backtests on real BDI |
| Cost Reduction Demonstrated | 20% | Run all 4 scenarios, display ₹ savings per voyage |
| Innovation & Novelty | 20% | HMM regime + Options pricing = unique combo |
| Data Integration Quality | 15% | 8+ real data sources (not just synthetic) |
| UI/UX & Usability | 10% | AI Copilot lowers learning curve for logistics managers |
| System Architecture | 10% | Clear microservices, real-time pipeline visible |

---

## 🚀 36-Hour Build Plan

### Hour 0–4: Data & Foundation
- Seed synthetic DB (existing reset_db.py)
- Integrate Baltic Exchange CSV samples for real BDI history
- Set up AISHub API key + INCOIS tidal endpoint
- Design HMM and Options pricing module interfaces

### Hour 4–12: ML Core
- Train TFT model on BDI + exogenous features (coal price, BCI, BPI, fleet utilization)
- Build HMM regime classifier (4 states: Bull/Bear/Seasonal/Distress)
- Implement BSM options pricing function for "wait vs. fix" signal

### Hour 12–20: Decision Engine + API
- Voyage economics engine (existing, enhanced with carbon layer)
- Contract mix optimizer (Markowitz on freight scenarios)
- Virtual arrival optimizer (speed vs. port queue ETA)
- LLM Copilot integration (Gemini API with tool-calling)

### Hour 20–30: Frontend
- Interactive port map (Leaflet.js with AIS vessel overlay)
- Real-time rate forecast chart (Recharts with confidence bands)
- Tidal calendar widget (calendar heatmap)
- Efficient frontier visualization (D3.js scatter)
- LLM chat interface panel

### Hour 30–36: Demo & Polish
- Run all 4 scenarios live and record results
- Prepare 15-minute judge demo script
- Calculate and visualize ₹ ROI for SAIL at full annual scale
- Record demo video for submission

---

## 💡 The Winning Pitch (Memorize This)

> **"Every competitor will build a dashboard that shows freight rates. We build the only system that tells SAIL not just what rates will do — but whether it's worth waiting (using options theory), when the market regime is changing (using HMM), and which contract mix across the year minimizes cost at SAIL's specific risk tolerance (using Markowitz optimization). This is the difference between a weather app and a weather-derivatives trading desk."**

---

*Research compiled: September 17, 2026 | SIH26006 · FreightIQ Platform*
