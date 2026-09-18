# 🎨 FreightIQ — UI/UX Design Brief & Style System
## Document Code: SPEC-UIX-004 | Version: 2.0 | SIH2026 Problem SIH26006
### Focus: Visual Philosophy, Design Tokens, Component Standards & Screen Wireframes

---

## 1. Visual Philosophy: The Maritime Command Center

FreightIQ is styled as a **high-density, mission-critical naval operations dashboard** used by senior fleet controllers, chartering directors, and admiralty risk officers.
* **Aesthetic Identity:** Industrial Cyber-Maritime. Deep oceanic navy canvas accented with vivid signal colors (Electric Cyan, Emerald Green, Amber Gold, and Alert Crimson).
* **Theme Default:** **Dark Mode First** (WCAG AA accessible contrast). Eliminates eye strain during prolonged monitoring sessions and creates a sleek, state-of-the-art aesthetic for hackathon judges.
* **Density & Hierarchy:** High information density without visual clutter. Key metrics use large tabular numerals with subtle metadata tags below.
* **Zero Placeholders:** Every gauge, chart, and queue table renders live or synthetic maritime ground-truth data.

---

## 2. Color Palette & Design Tokens

### 2.1 Core Palette (Exact Hex Codes)

| Token Name | Hex Value | Tailwind Class | Semantic Usage |
|---|---|---|---|
| **Canvas Background** | `#030712` | `bg-gray-950` | Primary application viewport background |
| **Card Surface** | `#0F172A` | `bg-slate-900` / `bg-gray-900` | Surface cards, floating panels, data tables |
| **Elevated Surface** | `#1E293B` | `bg-slate-800` | Dropdowns, hover states, modals |
| **Subtle Border** | `#1F2937` | `border-gray-800` | Structural dividers, card borders |
| **Highlight Border** | `#334155` | `border-slate-700` | Interactive card focus, active selection |
| **Electric Cyan** | `#06B6D4` | `text-cyan-400` | Primary maritime accent, AIS vessel indicators, canal routes |
| **Royal Blue** | `#2563EB` | `bg-blue-600` | Primary action buttons, active navigation items |
| **Emerald Green** | `#10B981` | `text-emerald-400` | Bullish signals, profits, safe drafts, Grade A green shipping |
| **Amber Warning** | `#F59E0B` | `text-amber-400` | High market volatility, bunker spikes, intermediate risk |
| **Crimson Alert** | `#EF4444` | `text-red-500` | Draft violations, demurrage traps, critical port congestion |

### 2.2 Dynamic Market Regime Tokens
```tsx
const REGIME_COLOR_MAP = {
  BEAR_DISTRESS:   "bg-red-500/20 text-red-300 border-red-500/40",
  NEUTRAL:         "bg-blue-500/20 text-blue-300 border-blue-500/40",
  SEASONAL_LIFT:   "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  SUPERCYCLE_BULL: "bg-amber-500/20 text-amber-300 border-amber-500/40",
};
```

### 2.3 IMO CII Carbon Rating Tokens
```tsx
const CII_COLOR_MAP = {
  A: { color: "#22c55e", label: "Superior Efficiency" },
  B: { color: "#86efac", label: "High Efficiency" },
  C: { color: "#eab308", label: "Moderate Baseline" },
  D: { color: "#f97316", label: "Sub-Standard Warning" },
  E: { color: "#ef4444", label: "Critical Tier Penalty" },
};
```

---

## 3. Typography System & Hierarchy

* **Primary Sans:** `Inter`, system-ui, -apple-system, sans-serif. Used for headers, descriptions, navigation labels, and tooltips.
* **Monospace Data Font:** `JetBrains Mono`, `Consolas`, monospace. Used for all numbers, financial figures ($/MT), nautical coordinates (lat/long), timestamps, and vessel IMO identifiers.

| Scale | Tailwind Class | Size / Weight | Usage |
|---|---|---|---|
| **Display Header** | `text-2xl font-black` | 24px / 900 | Page titles, primary KPI numbers |
| **Section Title** | `text-xs font-bold uppercase tracking-wider` | 12px / 700 | Card titles, table header columns |
| **Card Body** | `text-xs text-gray-300` | 12px / 400 | Analytical descriptions, explanatory notes |
| **Caption / Meta** | `text-[10px] text-gray-500 uppercase` | 10px / 600 | Secondary subtitles, timestamps, unit labels |

---

## 4. Reusable Component Standards

### 4.1 `StatCard` Component
* Fixed border radius (`rounded-xl`), background `#0F172A`, border `#1F2937`.
* Upper row: uppercase label + icon container.
* Middle row: large tabular number in white + optional unit tag.
* Lower row: colored pill badge or subtitle comparison.

### 4.2 `CiiRing` SVG Visualizer
* An inline SVG circular progress ring ($100 \times 100$ viewBox).
* Background track circle (`stroke="#1f2937"`).
* Foreground animated arc with `strokeDashoffset` dynamically calculated based on letter grade (A = 100%, B = 80%, C = 60%, D = 40%, E = 20%).
* Drop-shadow glow matching the tier color.
* Centered letter grade in `font-black text-2xl` with a subtle "CII" badge below.

### 4.3 Quantile Chart Visualization Standard (Recharts)
* **P90 Optimistic Line:** Green dotted line (`stroke="#22c55e"`, `strokeDasharray="3 3"`).
* **P50 Expected Median:** Solid/dashed amber line (`stroke="#f59e0b"`, `strokeWidth=2.5`).
* **P10 Pessimistic Line:** Red dotted line (`stroke="#ef4444"`, `strokeDasharray="3 3"`).
* **Confidence Shaded Area:** Linear gradient fill (`fill="#3b82f6"`, `opacity=0.15`) between P10 and P90 bounds.

### 4.4 Responsive Navigation Sidebar (`Sidebar.tsx`)
* Desktop ($\ge 1024\text{px}$): Fixed 256px wide left sidebar, `bg-gray-950`, border right `border-gray-800`.
* Mobile ($< 1024\text{px}$): Hidden off-screen (`-translate-x-full`); toggled via floating hamburger button with backdrop dark overlay (`bg-black/60`).
* Active link: `bg-blue-600/15 text-blue-400 border-r-2 border-blue-500`.

---

## 5. Screen Layout Wireframes

### 5.1 Executive Dashboard (`/`)
```
+---------------------------------------------------------------------------------------------------+
| [FreightIQ Logo]  Status: ONLINE  |  Regime: [SEASONAL_LIFT (74% Conf)]  WAIT 12d ($120k)  [Menu] |
+---------------------------------------------------------------------------------------------------+
| CORRIDOR SHORTCUTS:                                                                               |
| [AUS -> Thoothukudi: $11.47]  [AUS -> Chennai: $12.10]  [IDN -> Chennai: $7.80]  [AUS -> Paradip] |
+---------------------------------------------------------------------------------------------------+
| PORT CONGESTION RADAR:                                                                            |
| [Thoothukudi: 48/100 (Green Hub)] [Chennai: 54/100] [Paradip: 82/100 (Severe)] [Haldia: 65/100]  |
+-----------------------------------------------------------------+---------------------------------+
| QUANTILE FREIGHT RATE FORECAST (P10 / P50 / P90)                | TIDAL NAVIGATION CALENDAR       |
|                                                                 | Port: Thoothukudi VOCPA         |
|  $30 |                 /-- P90 Optimistic                       | High Tide: 14:20 (+1.4m Safe)   |
|  $20 |     ...====----'                                         | Low Tide:  20:45 (-0.3m Risk)   |
|  $10 | ___/                                                     | Next Safe Window: 4h 15m        |
|      +------------------------------------------                +---------------------------------+
|        Jan   Feb   Mar   Apr   May   Jun   Jul                  | AI CHARTER RECOMMENDATION       |
|                                                                 | "Delay fixture by 12 days to    |
|  [Legend: - Historical  -- P50 Median  .. P10/P90 Quantiles]    | capture $120,155 option value." |
+-----------------------------------------------------------------+---------------------------------+
```

### 5.2 Voyage Economics & Carbon Footprint (`/economics`)
```
+---------------------------------------------------------------------------------------------------+
| VOYAGE PARAMETERS (LEFT COL)     | VOYAGE P&L & IMO CARBON EMISSIONS (RIGHT COL)                  |
| - Origin: Australia              | +------------------------------------------------------------+ |
| - Destination: Thoothukudi       | | Rev: $1,470,000 | Costs: $579,259 | Profit: $890,741 (26%) | |
| - Vessel: Panamax (74,510 MT)    | +------------------------------------------------------------+ |
| - Cargo: Coking Coal             |                                                                |
| - Bunker: $650 / MT VLSFO        | DISBURSEMENT BREAKDOWN:                                        |
| - Port Days: 2 Load / 3 Disch    | [Bunker: $346k | Port Dues: $112k | Canal: $0k | OPEX: $121k]  |
|                                  |                                                                |
| [ CALCULATE VOYAGE P&L ]         | IMO CARBON INTENSITY & EU ETS EXPOSURE CARD:                   |
|                                  | +------------------------------------------------------------+ |
|                                  | | IMO CII TIER:        VOYAGE CO2:        CARBON SURCHARGE:  | |
|                                  | |    ( B )             2,140 MT CO2       $89,400 USD        | |
|                                  | |   Animated Ring      30.57 kg/MT Cargo  (EU ETS €65/t)     | |
|                                  | +------------------------------------------------------------+ |
+----------------------------------+----------------------------------------------------------------+
```

### 5.3 Port Constraints & AIS Intelligence (`/ports`)
```
+---------------------------------------------------------------------------------------------------+
| PORT PROFILE: V.O. Chidambaranar (Thoothukudi / VOCPA)  [🌿 NATIONAL GREEN HYDROGEN HUB BADGE]    |
+---------------------------------------------------------------------------------------------------+
| Max Draft: 14.2m | Max DWT: 95,000 MT | Berths: 14 (NCB-I, NCB-II, CJ-I) | Norm: 15,000 MT/day   |
+---------------------------------------------------------------------------------------------------+
| PHYSICAL DRAFT FEASIBILITY CHECK:                                                                 |
| Vessel: Panamax (MV Vishva Vijay) | Draft: 14.10m | Beam: 32.2m | Cargo: 74,510 MT Coking Coal    |
| [STATUS: FEASIBLE - SAFE MARGIN 0.10m UNDER HIGH WATER HARMONIC WINDOW]                           |
+---------------------------------------------------------------------------------------------------+
| LIVE AIS ANCHORAGE & BERTH QUEUE (FROM EXIM INDIA SHIPPING TIMES):                                |
| Vessel Name        | Type    | DWT     | Cargo (MT)   | Berth   | Discharge Status                |
|--------------------+---------+---------+--------------+---------+---------------------------------|
| MV Vishva Vijay    | Panamax | 74,510  | Coking Coal  | NCB-I   | Discharging (15,000 MT/day)     |
| MV Lyric Harmony   | Panamax | 76,260  | Met Coal     | NCB-II  | In Waiting Queue (3.2 days)     |
| MV Lila Shanghai   | Panamax | 72,036  | Coal Import  | Anchor  | Virtual Arrival Notice Issued   |
+---------------------------------------------------------------------------------------------------+
```

---

## 6. Micro-Interactions & Loading Transitions

1. **Shimmer Skeletons:** Whenever asynchronous API fetches are in progress, UI surfaces immediately render matching skeleton geometry (`SkeletonCard`, `SkeletonChart`, `SkeletonBanner`) rather than jarring spinners.
2. **Chart Tooltip Morphing:** Hovering over any Recharts time-series smoothly transitions the tooltip card with zero flicker, formatting numbers in monospace typography.
3. **Button Focus & Ripple:** Primary action buttons feature subtle cyan/blue shadow glows (`shadow-lg shadow-blue-600/30`) with smooth active scaling (`active:scale-[0.98]`).
