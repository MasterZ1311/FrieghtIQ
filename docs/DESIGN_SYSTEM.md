# FREIGHT IQ — Design System & Architectural Standards
**Version**: 1.0.0 (Phase 01 Production Foundation)  
**Target Organization**: Ministry of Steel / Steel Authority of India Limited (SAIL)  
**Problem Statement**: SIH 2026 (SIH26006)

---

## 1. Visual Concept & Design Philosophy

FREIGHT IQ is designed as a **Maritime Intelligence Command Center**. Inspired by mission-critical analytical workstations (Bloomberg Terminal, Palantir Foundry, Datadog), it prioritizes:
- **Information Density**: High data throughput without visual clutter.
- **Data Honesty & Transparency**: Every number and chart explicitly conveys its provenance, status, and confidence level. Unverified fields are strictly displayed as `UNKNOWN` or `DATA PENDING`.
- **Operational Trust**: Dark obsidian/navy themes reduce eye strain during prolonged chartering and procurement operations.
- **Predictable Rhythm**: Standardized 4px spacing increments, subtle single-pixel borders, and muted semantic coloring.

---

## 2. Color Palette & Semantic Design Tokens

All colors are centralized in `src/app/globals.css` and mapped to Tailwind CSS utilities.

| Token | CSS Variable | Hex Value | Semantic Usage |
| :--- | :--- | :--- | :--- |
| **Background** | `--background` | `#07111F` | Deep Naval Obsidian; primary application backdrop |
| **Surface** | `--surface` | `#0B1626` | Standard container, table, and sidebar background |
| **Surface Elevated** | `--surface-elevated` | `#112238` | Interactive cards, modal dialogs, and popovers |
| **Surface Hover** | `--surface-hover` | `#162A45` | Hover state for interactive list rows and buttons |
| **Border** | `--border` | `#1E3A5F` | Primary component perimeter border |
| **Border Subtle** | `--border-subtle` | `#13253B` | Inner table row dividers and card section lines |
| **Primary** | `--primary` | `#2563EB` | Maritime Blue; primary calls-to-action |
| **Primary Hover** | `--primary-hover` | `#1D4ED8` | Hover state for primary action buttons |
| **Accent** | `--accent` | `#0284C7` | Cyan maritime radar signal and secondary metrics |
| **Success** | `--success` | `#10B981` | Low risk, operational readiness, active status |
| **Warning** | `--warning` | `#F59E0B` | Moderate risk, data pending, analyzing |
| **Danger** | `--danger` | `#EF4444` | High risk, draft violation, critical constraint failure |
| **Info / Telemetry** | `--info` | `#06B6D4` | Data feeds, reference tags, provenance notes |
| **Text Primary** | `--text-primary` | `#F8FAFC` | Primary headings, values, and strong labels |
| **Text Secondary** | `--text-secondary`| `#94A3B8` | Body text, descriptions, and breadcrumbs |
| **Text Muted** | `--text-muted` | `#64748B` | Metadata, unit indicators, and timestamps |

---

## 3. Typography Hierarchy

The system standardizes on **Inter** for clean UI sans-serif readability and **JetBrains Mono** for numerical values and technical maritime coordinates.

| Hierarchy Level | Font Family | Size / Weight | Usage Context |
| :--- | :--- | :--- | :--- |
| **Display / Metric** | Mono / Tabular | 28px–32px / Bold | KPI metric cards, delivered TCE ($/MT) |
| **H1 (Page Header)** | Sans-Serif | 20px–24px / Bold | Primary module titles in uppercase |
| **H2 / Section** | Sans-Serif | 14px–16px / Bold | Form sections, card headers |
| **H3 / Card Title** | Sans-Serif | 13px–14px / SemiBold | Sub-panels, risk item titles |
| **Body** | Sans-Serif | 12px–13px / Regular | Descriptions, table values, instructions |
| **Caption / Mono** | Mono | 10px–11px / Medium | Coordinates, timestamps, UN/LOCODE, IMO numbers |

### Tabular Numerals
Financial and cargo values must always include `.tabular-nums` or `font-mono` to prevent jitter during updates:
```html
<span className="font-mono tabular-nums">$14.20/MT</span>
```

---

## 4. Spacing, Borders & Radii System

### Spacing Scale
Components strictly observe a 4px geometric progression:
- `4px` (`gap-1`, `p-1`): Tag paddings, icon margins
- `8px` (`gap-2`, `p-2`): Small input padding, button gaps
- `12px` (`gap-3`, `p-3`): Dense card interiors, filter rows
- `16px` (`gap-4`, `p-4`): Standard table cell padding, form column gaps
- `20px–24px` (`p-5`, `p-6`): Standard card wrappers, dashboard widgets
- `32px` (`mb-8`, `p-8`): Empty state hero containers

### Border & Radii
- Cards and panels utilize `rounded-xl` (12px) with `border border-border`.
- Modals and drawers utilize `rounded-xl` with backdrop blur (`backdrop-blur-sm`).
- Buttons and form controls utilize `rounded-lg` (8px).
- Heavy dropshadows and exaggerated glassmorphism are avoided to preserve crisp operational contrast.

---

## 5. Status & Data Provenance System

Every component rendering data must declare its status using standard badges:

### 1. Data Provenance Status (`DataStatusBadge`)
- `LIVE`: Verified real-time telemetry stream.
- `RECENT`: Verified within accepted SLA window.
- `STALE`: Out of date transponder or benchmark update.
- `DEMO` / `DEMO DATA`: Simulated record for testing / Phase 01 architecture.
- `SYNTHETIC`: Procedurally generated time series.
- `DATA PENDING`: Awaiting official authority or API integration.
- `UNAVAILABLE`: Feed offline or unconfigured.

### 2. Operational Status (`StatusBadge`)
- `ACTIVE`, `AVAILABLE`, `AT SEA`, `AT PORT`, `AT ANCHORAGE`, `UNKNOWN`

### 3. Risk Levels (`RiskBadge`)
- `LOW RISK`: Emerald badge.
- `MEDIUM RISK`: Amber badge.
- `HIGH RISK`: Rose badge.
- `UNKNOWN`: Muted slate badge.

---

## 6. Component Library Conventions

All shared components are encapsulated under `src/components/`:
- `layout/`: `AppShell`, `Sidebar`, `Header`, `PageHeader`, `Breadcrumbs`
- `badges/`: `StatusBadge`, `RiskBadge`, `DataStatusBadge`, `ConfidenceBadge`, `SourceBadge`
- `data-display/`: `MetricCard`, `DataTable`, `FilterBar`, `ChartContainer`
- `feedback/`: `EmptyState`, `LoadingSkeleton`, `ErrorState`
- `navigation/`: `CommandPalette` (`Ctrl+K`), `GlobalSearchModal`, `NotificationPanel`, `UserMenu`
- `brand/`: `FreightIqLogo`

### Rules:
1. **Never inline mock data inside view templates**: Always import from `@/data/demo/*`.
2. **Never swallow unverified parameters**: If a vessel draft or port LOA is unconfirmed, output `UNKNOWN`.
3. **Empty States**: Modules scheduled for future phases must render `<EmptyState />` detailing the planned architecture rather than placeholder dummy numbers.

---

## 7. Global Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + K` / `Cmd + K` | Open Command Palette (instant route jumping) |
| `Ctrl + /` | Open Global Entity Search Modal |
| `ESC` | Dismiss any open modal, drawer, or search overlay |
| `↑` / `↓` + `Enter` | Navigate and select items in command palette |
