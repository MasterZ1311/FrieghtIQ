# FREIGHT IQ — Design System & UI/UX Architectural Standards

<div align="center">

**Version**: 2.0.0 (Production shadcn/ui Preset `b1Yobvfjk` & Dual-Theme System)  
**Target Organization**: Ministry of Steel / Steel Authority of India Limited (SAIL)  
**Problem Statement**: Smart India Hackathon 2026 (SIH26006)  
**Status**: ACTIVE PRODUCTION STANDARD  

</div>

---

## 1. Visual Concept & Design Philosophy

FREIGHT IQ is designed as an **Enterprise Maritime Decision Intelligence Command Center**. Inspired by mission-critical analytical workstations (Bloomberg Terminal, Palantir Foundry, Datadog), the interface balances intense information density with modern visual clarity:

- **High-Density Information Architecture**: Optimized for chartering officers, logistics directors, and demurrage analysts who require multi-variable trade telemetry at a glance without pagination friction.
- **Data Honesty & Absolute Provenance**: Every metric, calculation, and forecast declares its provenance, confidence score, and status. Missing or unverified particulars strictly evaluate to `UNKNOWN` or `DATA PENDING` rather than fabricated default values.
- **Dual-Theme High Contrast**:
  - **Naval Obsidian Dark Mode**: Pure black canvas (`#000000`) with charcoal cards (`#0c0d12`) and electric maritime blue accents (`#3b82f6`) eliminating eye strain during multi-hour chartering operations.
  - **Clean Maritime Light Mode**: Pure white canvas (`#ffffff`) with light ash surfaces (`#f8fafc`) and royal maritime blue accents (`#2563eb`) providing high readability in well-lit boardroom environments.
- **Predictable 4px Rhythm**: Consistent spacing progression, single-pixel subtle borders, and accessible focus rings.

---

## 2. shadcn/ui Configuration & Foundation

The UI foundation is built upon **shadcn/ui** using the custom design preset **`b1Yobvfjk`**:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/app/globals.css",
    "baseColor": "zinc",
    "cssVariables": true,
    "prefix": ""
  },
  "iconLibrary": "lucide",
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

---

## 3. Dual-Theme Color Palette & Semantic Design Tokens

All colors are centralized in `src/app/globals.css` as CSS Custom Properties and integrated into Tailwind CSS v4 utilities.

### 3.1 Naval Obsidian Dark Mode (`.dark`, `[data-theme="dark"]`)

| Token | CSS Variable | Hex Value | Semantic Usage Context |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | `--background` | `#000000` | Pure Black application backdrop |
| **Card Surface** | `--surface` / `--card` | `#0c0d12` | Charcoal card container, tables, panels |
| **Surface Elevated** | `--surface-elevated` | `#13151c` | Modal dialogs, popovers, hover cards |
| **Surface Hover** | `--surface-hover` | `#1a1e28` | Hover state for interactive list rows & buttons |
| **Border Primary** | `--border` | `#1e222d` | Container perimeter border (single pixel) |
| **Border Subtle** | `--border-subtle` | `#141720` | Inner table dividers and section lines |
| **Primary Action** | `--primary` | `#3b82f6` | Electric Maritime Blue for primary CTAs |
| **Primary Hover** | `--primary-hover` | `#60a5fa` | Hover state for primary action buttons |
| **Accent / Radar** | `--accent` | `#38bdf8` | Cyan maritime radar indicators & active tabs |
| **Success** | `--success` | `#10b981` | Low risk, berth clearance PASS, active status |
| **Warning** | `--warning` | `#f59e0b` | Moderate risk, CONDITIONAL tidal window, queue delay |
| **Danger** | `--danger` | `#ef4444` | High risk, draft violation FAIL, cyclonic weather |
| **Info / Telemetry**| `--info` | `#06b6d4` | Live data stream tags, UN/LOCODE identifiers |
| **Text Primary** | `--text-primary` | `#ffffff` | Headings, primary KPI values, strong labels |
| **Text Secondary** | `--text-secondary`| `#cbd5e1` | Body descriptions, table cell labels, breadcrumbs |
| **Text Muted** | `--text-muted` | `#8090a7` | Timestamps, unit labels, metadata badges |

### 3.2 Clean Maritime Light Mode (`:root`, `.light`, `[data-theme="light"]`)

| Token | CSS Variable | Hex Value | Semantic Usage Context |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | `--background` | `#ffffff` | Pure White application backdrop |
| **Card Surface** | `--surface` / `--card` | `#f8fafc` | Light Ash card container and table rows |
| **Surface Elevated** | `--surface-elevated` | `#ffffff` | Crisp white elevated cards and modal dialogs |
| **Surface Hover** | `--surface-hover` | `#f1f5f9` | Hover state for interactive rows |
| **Border Primary** | `--border` | `#e2e8f0` | Light gray component perimeter border |
| **Border Subtle** | `--border-subtle` | `#f1f5f9` | Inner subtle dividing lines |
| **Primary Action** | `--primary` | `#2563eb` | Royal Maritime Blue for primary CTAs |
| **Primary Hover** | `--primary-hover` | `#1d4ed8` | Darker blue hover state |
| **Accent / Radar** | `--accent` | `#0284c7` | Deep cyan radar signal and secondary metrics |
| **Success** | `--success` | `#059669` | High-contrast emerald green for positive status |
| **Warning** | `--warning` | `#d97706` | Amber alert for conditional/moderate risks |
| **Danger** | `--danger` | `#dc2626` | Deep crimson for critical warnings & failures |
| **Info / Telemetry**| `--info` | `#0284c7` | Telemetry tags and reference chips |
| **Text Primary** | `--text-primary` | `#0f172a` | Deep slate headings and bold values |
| **Text Secondary** | `--text-secondary`| `#334155` | Slate body text and descriptions |
| **Text Muted** | `--text-muted` | `#64748b` | Muted metadata and subtext |

---

## 4. Typography Hierarchy & Rules

The system standardizes on **Roboto** for universal UI sans-serif legibility and **JetBrains Mono** for all numerical, geospatial, and financial figures.

| Hierarchy Level | Font Family | Size / Weight | Usage Context |
| :--- | :--- | :--- | :--- |
| **Display / Metric** | `font-mono` / Tabular | 28px–32px / Bold | KPI metric cards, delivered TCE ($/MT) |
| **H1 (Page Header)** | `font-sans` (Roboto) | 20px–24px / Bold | Primary module titles in uppercase |
| **H2 / Section** | `font-sans` (Roboto) | 14px–16px / Bold | Form sections, card headers |
| **H3 / Card Title** | `font-sans` (Roboto) | 13px–14px / SemiBold | Sub-panels, risk item titles |
| **Body / Labels** | `font-sans` (Roboto) | 12px–13px / Regular | Descriptions, table values, instructions |
| **Caption / Code** | `font-mono` | 10px–11px / Medium | Coordinates, timestamps, UN/LOCODE, IMO numbers |

### Tabular Numerals Requirement
All financial rates, cargo volumes, nautical coordinates, and timestamps **must** include `.tabular-nums` or `font-mono` to prevent layout shift and visual jitter during real-time data updates:
```tsx
<span className="font-mono tabular-nums font-bold text-lg text-primary">
  $14.50 / MT
</span>
```

---

## 5. Spacing Scale, Radii & Border Conventions

### 5.1 Spacing Scale (4px Geometric Grid)
- `4px` (`gap-1`, `p-1`): Tag paddings, icon margins
- `8px` (`gap-2`, `p-2`): Input padding, button inner spacing
- `12px` (`gap-3`, `p-3`): Dense card interiors, filter rows
- `16px` (`gap-4`, `p-4`): Standard table cell padding, form column gaps
- `20px–24px` (`p-5`, `p-6`): Standard card wrappers, dashboard widgets
- `32px` (`p-8`, `mb-8`): Empty state hero containers

### 5.2 Border & Radii Hierarchy
- **Buttons, Form Controls & Badges**: `rounded-lg` (8px / `0.5rem`).
- **Cards & Data Panels**: `rounded-xl` (12px) with `border border-border`.
- **Modals & Drawers**: `rounded-xl` (12px) with subtle backdrop blur (`backdrop-blur-sm`).
- **Border Treatment**: Crisp 1px borders (`border border-border`). Heavy drop-shadows and blurred glassmorphism are explicitly avoided to ensure high data readability.

---

## 6. Standard Component Catalog

### 6.1 Core shadcn/ui Primitives (`src/components/ui/`)
All atomic interactive components are standardized on shadcn primitives:
- `Button` (`@/components/ui/button`): Supports `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`.
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter` (`@/components/ui/card`).
- `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell` (`@/components/ui/table`).
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` (`@/components/ui/tabs`).
- `Dialog`, `DialogTrigger`, `DialogContent`, `DialogHeader`, `DialogFooter` (`@/components/ui/dialog`).
- `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem` (`@/components/ui/dropdown-menu`).
- `Badge` (`@/components/ui/badge`): Base variant for status chips.
- `Input`, `Select`, `Separator`, `Avatar`, `Tooltip`.

### 6.2 Specialized FreightIQ Maritime Components

#### A. Badges (`src/components/badges/`)
1. **`StatusBadge`**: Operational state of vessels and requisitions.
   - `ACTIVE`, `AVAILABLE`, `AT SEA`, `AT PORT`, `AT ANCHORAGE`, `UNKNOWN`.
2. **`RiskBadge`**: Evaluated operational risk levels.
   - `LOW` (Emerald), `MEDIUM` (Amber), `HIGH` (Rose), `UNKNOWN` (Slate).
3. **`DataStatusBadge`**: Telemetry freshness and data source provenance.
   - `LIVE`, `RECENT`, `STALE`, `DEMO DATA`, `SYNTHETIC`, `DATA PENDING`, `UNAVAILABLE`.
4. **`ConfidenceBadge`**: Model algorithmic confidence score.
   - Progress gauge showing `score%` with color graduation (Green $\ge 80\%$, Amber $50–79\%$, Red $< 50\%$).

#### B. Data Display & Analytics (`src/components/data-display/`)
- **`MetricCard`**: High-density KPI indicator with title, tabular value, percentage trend badge, and optional sparkline.
- **`DataTable`**: Sortable, filterable tabular display with sticky headers and pagination.
- **`ChartContainer`**: Recharts wrapper responsive to light/dark CSS variables.
- **`FilterBar`**: Segmented filter row with search input, dropdown selectors, and date pickers.

#### C. Navigation & Workstation Controls (`src/components/navigation/`)
- **`CommandPalette` (`Cmd+K` / `Ctrl+K`)**: Instant search and routing jump overlay across all modules.
- **`GlobalSearchModal` (`Ctrl+/`)**: Deep entity search across vessels, ports, requisitions, and decisions.
- **`NotificationPanel`**: Right-side sliding drawer displaying operational alerts, laycan warnings, and weather risks.
- **`UserMenu`**: Profile drawer displaying active operator credentials, SAIL role, and Theme Toggle.

#### D. Theme Provider & Toggle (`src/components/theme/`)
- **`ThemeProvider`**: Central client context managing `light`, `dark`, and `system` theme states via `next-themes`.
- **`ThemeToggle`**: Seamless toggle button alternating between Naval Obsidian and Clean Light themes.

---

## 7. Global Keyboard Shortcuts

| Key Combination | Action | Scope |
| :--- | :--- | :--- |
| `Ctrl + K` / `Cmd + K` | Summon Command Palette | Global |
| `Ctrl + /` | Open Deep Entity Search | Global |
| `ESC` | Dismiss open modals, drawers, or popovers | Global |
| `Tab` / `Shift + Tab` | Focus traversal across interactive inputs | Global |
| `↑` / `↓` + `Enter` | Navigate and execute Command Palette selections | Global |

---

<div align="center">
  <sub>FreightIQ Design System Specification • Ministry of Steel / Steel Authority of India Limited (SAIL) • SIH 2026</sub>
</div>
