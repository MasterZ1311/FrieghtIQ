# 📊 Document 2: Market Research
## SIH26006 — Freight Market, SAIL Context & Industry Trends

---

## 1. SAIL's Actual Scale of Operations

### Import Volume
- SAIL imports approximately **20–25 million tonnes** of coking coal annually
- This is the primary feedstock for Blast Furnace–Basic Oxygen Furnace (BF-BOF) steelmaking
- Primary suppliers: **BHP & Glencore (Australia)**, **Arch Resources & Alpha Natural (USA)**
- Secondary origins: Mozambique (Nacala corridor), Indonesia (thermal blending coal)

### Financial Implications
| Metric | Value |
|--------|-------|
| 1 USD/MT freight saving | ~$20–25 million saved annually |
| Single Capesize charter at wrong timing | $200,000–$500,000 extra cost vs. optimal |
| Annual broker commission at 1.25% on 50 fixtures | Significant recurring overhead |
| Reuters/Baltic subscription + daily broker calls | ~$50,000–$100,000/year in market intelligence costs |

### SAIL's 2024–2025 Strategic Context
- SAIL uses a **systematic empanelment system** for Indian ship-owners and domestic brokers
- Specialized port agents stationed at Paradip and Dhamra for import coordination
- Under pressure from **Ministry of Steel** to demonstrate cost efficiency in raw material procurement
- Adopting **Sagar Setu** and **E-Samudra** digital platforms for port documentation — indicates appetite for digitization

---

## 2. Baltic Dry Index (BDI) — Volatility Analysis

### Historical Range (2008–2026)
| Period | BDI Range | Key Driver |
|--------|-----------|-----------|
| 2008 Pre-crash | ~11,000 | Chinese infrastructure boom |
| 2008 Crash | ~663 (94% drop) | Global financial crisis |
| 2010–2014 Recovery | 1,000–4,000 | Moderate Chinese demand |
| 2015–2016 Distress | ~290 (record low) | Oversupply of vessels |
| 2021 Supercycle | ~5,650 | Post-COVID demand surge, port congestion |
| 2022–2023 | 700–3,000 | Geopolitical disruptions, normalization |
| 2024 | 1,200–2,800 | Stable demand, Red Sea rerouting |

### Baltic Capesize Index (BCI) — Most Relevant for SAIL
- BCI has ranged from **$2,000/day to $86,000/day** — a 43x range
- Daily rate swings of 10–15% in volatile periods are common
- **A 1-week delay in fixing a Capesize during a bull market = $70,000–$100,000 extra cost**

### Sub-Index Breakdown (All Relevant to SAIL Routes)
| Index | Vessel Class | SAIL Relevance |
|-------|-------------|----------------|
| BCI | Capesize (180k DWT) | Australia/Africa → Gangavaram/Dhamra |
| BPI | Panamax (74k DWT) | Australia/USA → Paradip/Vizag (primary workhorse) |
| BSI | Supramax (55k DWT) | Indonesia → all ports |
| BHSI | Handysize (28k DWT) | Short-haul, Haldia/Gopalpur |

---

## 3. Bunker Fuel Costs (Second-Largest Voyage Cost)

### Fuel Types Post-IMO 2020
| Fuel | Description | 2024 Price Range |
|------|-------------|-----------------|
| VLSFO | Very Low Sulphur Fuel Oil (0.5% S) — now standard | $550–$750/MT |
| HSFO | High Sulphur (3.5% S) + scrubber | $380–$550/MT |
| MGO | Marine Gas Oil — slow steaming/port | $750–$950/MT |

### Voyage Fuel Consumption (Typical)
| Vessel | Speed | Daily Consumption | Per-Voyage (Australia→India ~5,000 NM) |
|--------|-------|------------------|-----------------------------------------|
| Capesize | 13 knots | 55 MT/day | ~1,100 MT VLSFO (~$660,000–$825,000) |
| Panamax | 13 knots | 32 MT/day | ~640 MT (~$384,000–$480,000) |
| Supramax | 12 knots | 25 MT/day | ~500 MT (~$300,000–$375,000) |

**Key Insight:** Slow steaming from 13 to 11 knots reduces fuel burn by ~30% — this is the "virtual arrival" savings SAIL can capture.

---

## 4. Port Congestion — Actual Cost Analysis

### Paradip Port (SAIL's Most Used East Coast Port)
- Historical queue: 5–15 days in Oct–Jan peak season
- Max demurrage clause in charterparties: **$15,000–$25,000/day** for Panamax
- Documented PPA (Paradip Port Authority) measures: Exemption of demurrage on BOXN railway rakes to reduce port dwell time (2024 policy)
- **Oct–Jan is peak congestion** (monsoon ends, coal import season, higher power demand)

### Demurrage Exposure Calculator
```
Scenario: Panamax queued at Paradip for 6 days (Oct congestion)
  Demurrage rate: $20,000/day
  Extra congestion days: 6
  Demurrage bill: $120,000 per vessel

  If virtual arrival absorbs 3 days at sea:
    Bunker saving (speed 11 vs 13 knots): ~$60,000
    Demurrage avoided: 3 days × $20,000 = $60,000
    TOTAL SAVING: $120,000 per voyage
```

### Port-by-Port Congestion Profile
| Port | Peak Season | Avg Wait | High Wait | Berth Handling |
|------|-------------|----------|-----------|---------------|
| Paradip | Oct–Jan | 5.5 days | 15 days | 8k–12k MT/day |
| Haldia | Year-round | 7.0 days | 12 days | 5k–8k MT/day (river port) |
| Vizag | Moderate | 3.0 days | 8 days | 12k–15k MT/day |
| Gangavaram | Low | 1.5 days | 4 days | 35k MT/day (modern) |
| Dhamra | Low | 1.5 days | 3 days | 25k MT/day (new Adani) |

---

## 5. Freight Rate Forecasting — State of the Art (2024–2026)

### ML Models Used for BDI Forecasting
| Model | Strength | Weakness | Accuracy (MAPE) |
|-------|----------|----------|----------------|
| ARIMA/SARIMA | Simple, interpretable | Assumes linearity, no exogenous vars | 15–25% MAPE |
| LSTM / GRU | Captures non-linearity | "Black box," needs large data | 10–18% MAPE |
| **Temporal Fusion Transformer (TFT)** | Multi-horizon, interpretable attention | Computationally heavy | **7–12% MAPE** |
| CNN-BiLSTM-AM | Feature extraction + temporal + attention | Complex to tune | 9–15% MAPE |
| XGBoost / LightGBM + SHAP | Fast, explainable | Not sequential | 12–20% MAPE |
| **Ensemble (TFT + XGBoost)** | Best of both | Development time | **~7% MAPE** |

**Research Finding (2024):** TFT is the state-of-the-art for multi-horizon BDI forecasting. SHAP values from gradient boosting models identify which features drive rates.

### Key Exogenous Variables That Drive BDI
1. **Iron ore price** (China imports → Capesize demand)
2. **Thermal coal benchmark** (Newcastle, Indonesia ICI4)
3. **Coking coal spot price** (Australian FOB benchmark)
4. **Fleet utilization %** (supply side signal)
5. **S&P 500 / DXY index** (macro risk sentiment)
6. **Port congestion global** (AIS-derived effective capacity reduction)
7. **Seasonal patterns** (Q4 Chinese pre-inventory, Indian monsoon end)
8. **News sentiment** (geopolitical events lead BDI by 48–72 hours)

---

## 6. AIS (Automatic Identification System) Data — Emerging Intelligence Layer

### Why AIS Data Matters
- Terrestrial AIS covers ports and coastal areas
- Satellite S-AIS (Space-based AIS) covers open ocean — bridges the data gap
- Modern platforms use AI to process AIS data for: trajectory prediction, anomaly detection, port dwell time measurement, congestion scoring

### AIS-Derived Metrics for FreightIQ
| Metric | How Derived | Update Frequency |
|--------|------------|-----------------|
| Port Congestion Score | Count vessels at anchor within 10 NM of port | Every 4 hours |
| Vessel Speed Reduction | Average speed of vessels approaching port | Every 4 hours |
| Port Dwell Time | Delta between port entry and departure AIS signals | Continuous |
| Origin Port Loading Rate | Time between arrival at load port and departure | Continuous |
| Fleet Availability Signal | Count of ballast vessels in Pacific Basin | Daily |

---

## 7. IMO Regulations — Carbon Risk (A Hidden Cost)

### Carbon Intensity Indicator (CII) — IMO 2023
- All vessels >5,000 GT rated A–E on carbon intensity annually
- **D-rated vessels:** Must improve within 3 years or face trading restrictions
- **E-rated vessels:** Immediate corrective action plan required
- Charter rate discounts for poorly-rated vessels: **$500–$2,000/day** vs. A-rated peers

### EU Emissions Trading System (EU ETS) — From 2024
- Applies to all voyages into/out of EU ports
- For SAIL's Suez-routed voyages (US East Coast → India), partial EU ETS exposure
- Cost: **€60–€80 per tonne of CO₂** emitted in EU-covered portions
- Typical Capesize Suez voyage EU ETS exposure: **$80,000–$120,000**

### Carbon Cost by Vessel Class (per SAIL voyage)
| Vessel | CO₂ Emitted | CII Rating (typical) | Carbon Surcharge Risk |
|--------|------------|---------------------|----------------------|
| Capesize (Australia→Gangavaram) | ~3,500 MT | B–C | Moderate |
| Panamax (USA→Paradip, via Suez) | ~2,100 MT | A–B | Low |
| Supramax (Indonesia→Dhamra) | ~900 MT | A | Very Low |

---

## 8. Virtual Arrival & Slow Steaming — Quantified Benefits

### The Speed-Fuel Relationship (Cubic Law)
```
Fuel consumption ∝ Speed³
  → Reducing speed from 13 to 11 knots: (11/13)³ = 0.60
  → 40% fuel saving per day, but voyage takes longer
  → Net saving depends on demurrage exposure at destination
```

### Virtual Arrival — When It Makes Sense
- If port congestion queue > 3 days: **Always reduce speed**
- If voyage is long-haul (>5,000 NM): **Significant savings possible**
- If demurrage rate is high (>$20,000/day): **Every queue hour avoided saves money**

**2024 Trend:** Digital Virtual Arrival clauses being standardized in charterparties. Companies building software to calculate optimal departure speed in real-time.

---

## 9. Geopolitical Risk Events (Recent, Relevant to SAIL Routes)

| Event | Impact on SAIL Routes | Rate Spike |
|-------|-----------------------|-----------|
| Red Sea/Houthi Crisis (2024) | US–India via Cape of Good Hope (+10,000 NM) | +15–25% Panamax |
| Russia-Ukraine War (2022) | Russian coal redirected; European coal demand spike | +30% BCI |
| Australian–China Coal Ban (2020–2022) | Australian coal redirected to India/Japan/Korea | +8% India imports |
| China Port Congestion (2021) | Global vessel pool shrunk 15% effective capacity | +40% BDI |
| IMO 2020 Sulfur Cap | Bunker cost restructuring, scrubber premium | +$200/MT VLSFO vs HSFO |

**Research Finding:** BDI shows statistically significant response to news events within **48–72 hours** of publication — an exploitable signal for the NLP sentiment pipeline.

---

## 10. Contract Types — Economics Comparison

| Contract Type | Duration | Rate Exposure | SAIL Use Case |
|--------------|----------|--------------|---------------|
| **Spot** | Single voyage | 100% market exposure | Emergency procurement, distress market |
| **Short COA** | 3–6 voyages | Partial hedge | Predictable quarterly programs |
| **Medium COA** | 12 voyages | Strong hedge | Annual base-load procurement |
| **Time Charter** | 6–24 months | Fixed daily cost | When expecting rate surge |

### Actual Savings from COA vs. Spot (FreightIQ Scenario C Data)
```
Route: Hampton Roads → Visakhapatnam (500k MT/year program)
  Spot rate: $35.81/MT
  12-Voyage COA rate: $31.33/MT
  Saving: $4.48/MT × 500,000 MT = $2,240,000/year
```

---

*Document 2 of 6 | SIH26006 Research Suite | FreightIQ Platform*
