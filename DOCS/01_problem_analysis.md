# 📋 Document 1: Problem Analysis
## SIH26006 — Intelligent Freight Forecasting for SAIL

---

## 1. Problem Statement (Official)

**Title:** Development of an Intelligent Freight Forecasting Model for Optimized Vessel Chartering and Bulk Cargo Procurement from overseas to East Coast of India

**Organization:** Steel Authority of India Limited (SAIL)
**Ministry:** Ministry of Steel
**Category:** Software | Transportation & Logistics
**Prize:** ₹1,50,000 (₹75k joint)
**Deadline:** 20 September 2026
**Technical Complexity:** 8/10 | **Hackathon Viability:** 9/10 | **Dataset Accessibility:** 7/10

---

## 2. Layman Summary

> SAIL currently **guesses** when to rent ships for importing bulk cargo, leading to higher costs and delays. This problem asks us to build a smart system that predicts future shipping prices and recommends the best time and type of ship to rent, considering port limitations, to save money and improve efficiency.

---

## 3. The Real Core Objective (Often Missed)

SAIL's stated **Objective field** in the problem statement reads:

> *"Development of model to facilitate moving from multiple single spot contracts being entered into currently to short-term / medium-term multiple voyage contracts."*

This is **NOT just a forecasting problem.** It is a **procurement strategy transformation problem.**

| Today (Current State) | Target State |
|----------------------|-------------|
| Enter `n` individual spot contracts per shipment | Sign COA (Contract of Affreightment) for 3–12 voyages at once |
| React to daily market prices | Proactively lock in rates when the model signals a bull-to-bear transition |
| Broker-dependent decision making | Data-driven, AI-assisted chartering recommendations |
| Per-voyage TCE (Time Charter Equivalent) optimization | Annual program optimization across contract types |

**Implication:** The system must generate enough **confidence in rate direction** that a procurement manager feels comfortable committing to multi-voyage contracts rather than hedging with expensive spot deals.

---

## 4. Official Problem Description (Verbatim Key Points)

### Background
> "The current approach to vessel chartering for bulk cargo procurement to India's East Coast ports often involves **daily market exploration**, leading to **reactive decision-making** and likely missed opportunities for cost savings and efficiency."

> "The highly volatile nature of global freight markets, coupled with varying supply and demand dynamics from key origins like Australia, the US, Mozambique, Russia and Indonesia, makes it challenging to identify optimal entry points for short-term or mid-term charter contracts."

> "Without a robust future forecasting mechanism, determining the most suitable vessel type (Handysize, Supramax, Panamax, Capesize) for specific cargo parcels and routes, while accounting for **port infrastructure limitations at both origin and destination, results in suboptimal utilization and increased idle time.**"

### Expected Solution Components (a–d)
**a. Optimal Market Entry Timing**
Identify ideal windows to secure short-term or mid-term vessel charter contracts for specific cargo requirements, minimizing freight costs.

**b. Vessel Type Optimization**
Recommend the most suitable vessel type (Handysize, Supramax, Panamax, Capesize) for a given cargo volume and origin-destination pair, considering all known port infrastructure limitations at both loading and discharge ports on India's East Coast. This includes factoring in draft restrictions, LOA, and cargo handling capabilities to prevent idle time and ensure efficient turnaround.

**c. Idle Scenario Management**
Propose strategies for minimizing vessel idle time by forecasting periods of low demand and suggesting alternative employment opportunities or optimized positioning to reduce deadheading.

**d. Risk Mitigation**
Provide early warnings for potential market volatility, port congestion, or other disruptions that could impact chartering decisions.

---

## 5. Hidden Sub-Problems (What the PS Doesn't Tell You)

| Layer | Visible Problem (Surface) | Hidden Depth (What Judges Want to See) |
|-------|--------------------------|---------------------------------------|
| **Forecasting** | Predict BDI / freight rates | Must predict *regime changes* — BDI collapsed 94% in 2008, rebounded 700% in 2021. Black swan events break every standard ML model |
| **Vessel Selection** | Match vessel to port draft | Must account for *laden vs. ballast draft* differences, tidal windows at Haldia (changes every 6h), and seasonal silting at Paradip |
| **Contract Timing** | When to fix a charter | Must factor in SOFR floating cost, FFA (Forward Freight Agreement) hedging curves, and counterparty credit risk |
| **Idle Time** | Minimize anchorage waiting | Involves "virtual arrival" negotiation — a speed protocol between owner and charterer requiring contractual consent in charterparty |
| **Port Congestion** | Queue wait estimation | Congestion at one port cascades: a vessel diverted from Paradip to Vizag adds to Vizag's queue, changing ETAs for all other vessels |
| **Data Integration** | Multiple data sources | Port data is often self-reported and delayed 24–72h; real congestion is invisible without AIS tracking |
| **Contract Mix** | Spot vs. COA comparison | SAIL needs annual procurement optimization — what % should be Spot, COA, and TC to minimize total annual freight cost at a given risk level? |

---

## 6. Origin Ports & Constraints

| Origin | Country | Primary Cargo | Max Draft | Notes |
|--------|---------|--------------|-----------|-------|
| Newcastle | Australia | Thermal/Coking Coal | 15.0m | Premier coal export terminal |
| Port Hedland | Australia | Iron Ore | 19.0m | World's largest bulk export port |
| Hampton Roads | USA | Metallurgical Coal | 14.5m | Key US coal export hub |
| Baltimore | USA | Coal | 13.7m | Older infrastructure |
| Nacala | Mozambique | Coal | 14.0m | Growing African export corridor |
| Murmansk | Russia | Coal/Fertilizer | 12.5m | Arctic port, seasonal ice risk |
| Kalimantan | Indonesia | Thermal Coal | 12.0m | River anchorage barge loading |

---

## 7. Destination Ports (East Coast India) — The Critical Constraints

| Port | Max Draft | Max DWT | Avg Wait | Key Constraint | Feasible Vessels |
|------|-----------|---------|----------|---------------|-----------------|
| **Paradip** | 14.5m | 180k | ~5.5 days | Capesize (18m) INFEASIBLE | Panamax max |
| **Visakhapatnam** | 15.0m | 200k | ~3.0 days | Medium congestion | Panamax + Baby-Cape |
| **Gangavaram** | 18.0m | 200k | ~1.5 days | Deepwater, 35k MT/day handling | All incl. Capesize |
| **Gopalpur** | 11.0m | 60k | Tide-gated | Panamax/Cape INFEASIBLE | Handysize/small Supramax only |
| **Dhamra** | 17.0m | 180k | ~1.5 days | Modern Adani port | Capesize-capable |
| **Sagar-Sandheads** | 13.0m | 120k | Tide-restricted | Outer anchorage transhipment | Panamax max |
| **Haldia** | 9.5m | 80k | ~7.0 days | River port, tide-restricted | Handysize optimal |

---

## 8. Vessel Classes Available

| Class | DWT Range | Draft | Gear | Best Routes |
|-------|-----------|-------|------|-------------|
| Handysize | 25k–40k DWT | 10.5m | Geared | Shallow ports (Gopalpur, Haldia) |
| Supramax | 50k–65k DWT | 12.8m | Geared | Versatile — Indonesia river anchorages |
| Panamax | 65k–82k DWT | 14.0m | Gearless | Standard coal workhorse |
| Capesize | 150k–200k DWT | 18.0m | Gearless | Deepwater only (Gangavaram, Dhamra) |

---

## 9. User Personas

### Primary User: SAIL Procurement Manager
- **Background:** Senior logistics professional, non-technical
- **Goal:** Secure the best charter at the right time without spending hours on broker calls
- **Pain Point:** Cannot process all relevant market signals manually; makes gut-feel decisions
- **Needs:** Clear "BUY NOW / WAIT" signals, visual dashboards, natural language interface

### Secondary User: SAIL Chartering Team
- **Background:** Maritime domain experts
- **Goal:** Validate and compare contract options quantitatively
- **Pain Point:** Manual TCE calculations, no integrated port constraint checks
- **Needs:** Voyage economics calculator, scenario comparison, risk reports

### Tertiary User: SAIL Finance/Strategy
- **Background:** Corporate strategy, cost optimization focus
- **Goal:** Minimize annual freight spend across all programs
- **Pain Point:** No annual procurement portfolio view
- **Needs:** Contract mix optimizer, annual cost projection, Board-ready reports

---

## 10. Why the Current Manual Approach Fails

```
Daily Broker Calls
      ↓
Market Rate (today only)
      ↓
Manual TCE Calculation (Excel)
      ↓
No Port Congestion Data
      ↓
No Rate Forecast
      ↓
No Contract Comparison
      ↓
Spot Contract (every time)
      ↓
Higher Cost + Higher Volatility
```

**Problems cascade:**
1. No forecast → can't time the market → always pay spot premium
2. No congestion data → don't know Paradip has 6-day queue → vessel waits → demurrage
3. No vessel-port validation → Capesize booked for Paradip → vessel rejected → emergency rebooking costs
4. No contract optimization → 100% spot → miss COA savings of $2–4/MT across annual volume

---

## 11. Jury Evaluation Metrics

| Metric | What Judges Look For |
|--------|---------------------|
| Forecasting Accuracy | MAE / RMSE on freight rate predictions; backtesting on historical BDI data |
| Cost Reduction | Demonstrated savings in $/MT or ₹ per voyage vs. spot baseline |
| Idle Time Reduction | % reduction in demurrage exposure through virtual arrival / congestion avoidance |
| Recommendation Accuracy | Hit rate on BUY/WAIT signals against historical outcomes |
| System Latency | Time from input to recommendation (<5 seconds expected) |
| UX Simplicity | Can a non-technical manager understand the output in <30 seconds? |
| Data Integration | Number of real data sources successfully integrated |
| Model Robustness | Does the model degrade gracefully on extreme market events? |

---

*Document 1 of 6 | SIH26006 Research Suite | FreightIQ Platform*
