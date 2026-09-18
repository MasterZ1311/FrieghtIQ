# 🗄️ FreightIQ — Backend Schema & Authentication Flow
## Document Code: SPEC-DAT-005 | Version: 2.0 | SIH2026 Problem SIH26006
### Focus: Relational Database Schema, ER Diagrams, JWT Auth & RBAC Security

---

## 1. Authentication & Security Architecture

### 1.1 Token Architecture & Cryptographic Standards
FreightIQ implements a stateless **JSON Web Token (JWT)** session architecture designed for enterprise single sign-on (SSO) and hackathon security compliance:
* **Access Tokens:** Short-lived (15 minutes), signed with HMAC-SHA256 (`HS256`) or asymmetric `RS256`. Contains `user_id`, `role`, `department`, and `scope` claims.
* **Refresh Tokens:** Long-lived (7 days), stored in an HTTP-only secure cookie or persisted in the `user_sessions` table with cryptographic hashing (`SHA-256`) to enable immediate revocation.
* **Password Hashing:** `Argon2id` or `bcrypt` (12 rounds) with unique cryptographic salt per user.

### 1.2 Role-Based Access Control (RBAC) Matrix

| Endpoint / Action | `ADMIN` | `CHARTERING_LEAD` | `OPERATIONS_OFFICER` | `AUDITOR_VIEWER` |
|---|:---:|:---:|:---:|:---:|
| View Dashboard & Quantile Forecasts | ✅ | ✅ | ✅ | ✅ |
| Run Port Constraints & Tidal Checks | ✅ | ✅ | ✅ | ✅ |
| Generate Voyage P&L & Carbon Accounting | ✅ | ✅ | ✅ | ✅ |
| Query AI Chartering Copilot | ✅ | ✅ | ✅ | ❌ |
| Create / Lock Formal Charter Fixture | ✅ | ✅ | ❌ | ❌ |
| Override Synthetic Rates / Re-Seed Database | ✅ | ❌ | ❌ | ❌ |
| View System Audit Logs | ✅ | ❌ | ❌ | ✅ |

### 1.3 Complete Authentication Sequence Diagram

```mermaid
sequenceDiagram
    participant Client as Next.js Client
    participant AuthAPI as FastAPI /api/auth
    participant DB as Database (SQLite / Postgres)
    participant Protected as Protected Endpoint (/api/*)

    Note over Client,AuthAPI: Phase 1: Authentication & Token Issuance
    Client->>AuthAPI: POST /api/auth/login (email, password)
    AuthAPI->>DB: SELECT * FROM users WHERE email = ?
    DB-->>AuthAPI: User record + password_hash
    AuthAPI->>AuthAPI: Verify password with bcrypt.checkpw()
    alt Credentials Invalid
        AuthAPI-->>Client: 401 Unauthorized ("Invalid credentials")
    else Credentials Valid
        AuthAPI->>DB: INSERT INTO user_sessions (user_id, refresh_token_hash, expires_at)
        AuthAPI-->>Client: 200 OK (access_token, refresh_token, user_profile)
    end

    Note over Client,Protected: Phase 2: Accessing Protected Resources
    Client->>Protected: GET /api/dashboard/summary (Bearer access_token)
    Protected->>Protected: Validate JWT Signature & Expiration
    alt Token Valid
        Protected-->>Client: 200 OK (Data Payload)
    else Token Expired (401)
        Note over Client,AuthAPI: Phase 3: Silent Token Refresh
        Client->>AuthAPI: POST /api/auth/refresh (refresh_token)
        AuthAPI->>DB: Verify refresh token active in user_sessions
        AuthAPI-->>Client: 200 OK (new access_token)
        Client->>Protected: Retry request with new token
    end
```

---

## 2. Complete Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    USERS ||--o{ USER_SESSIONS : maintains
    USERS ||--o{ AUDIT_LOGS : generates
    USERS ||--o{ CHARTER_FIXTURES : authorizes
    USERS ||--o{ COPILOT_CONVERSATIONS : owns

    PORTS ||--o{ ROUTES : origins
    PORTS ||--o{ ROUTES : destinations
    PORTS ||--o{ TIDAL_PREDICTIONS : records
    PORTS ||--o{ AIS_VESSEL_POSITIONS : docks

    VESSELS ||--o{ CHARTER_FIXTURES : assigned_to
    ROUTES ||--o{ FREIGHT_RATES : tracks
    ROUTES ||--o{ CHARTER_FIXTURES : operates_on

    COPILOT_CONVERSATIONS ||--o{ COPILOT_MESSAGES : contains

    USERS {
        int id PK
        string email UK
        string password_hash
        string full_name
        string role
        string department
        boolean is_active
        datetime created_at
    }

    USER_SESSIONS {
        int id PK
        int user_id FK
        string refresh_token_hash
        datetime expires_at
        datetime created_at
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action
        string target_entity
        string ip_address
        datetime timestamp
    }

    FREIGHT_RATES {
        int id PK
        int route_id FK
        date date
        string origin
        string destination
        string vessel_class
        string commodity
        float rate_usd_per_mt
        float tce_usd_per_day
        float bpi_index
        float bunker_price
        float congestion_index
        boolean is_demo
    }

    PORTS {
        int id PK
        string code UK
        string name
        string country
        float max_draft_m
        float max_loa_m
        float max_dwt
        int berth_count
        float mechanized_norm_tpd
        boolean green_hydrogen_hub
        float latitude
        float longitude
    }

    VESSELS {
        int id PK
        string name
        string vessel_class
        float dwt
        float draft_laden_m
        float draft_ballast_m
        float loa_m
        float beam_m
        float service_speed_knots
        float eco_speed_knots
        float fuel_burn_laden_tpd
        float fuel_burn_eco_tpd
    }

    ROUTES {
        int id PK
        string origin_port_code FK
        string destination_port_code FK
        float nautical_miles
        boolean passes_suez
        boolean passes_panama
        float typical_transit_days
    }

    CHARTER_FIXTURES {
        int id PK
        int route_id FK
        int vessel_id FK
        int user_id FK
        string fixture_number UK
        string charterer
        float agreed_rate_usd_mt
        float cargo_mt
        date laycan_start
        date laycan_end
        float demurrage_rate_usd_day
        string status
    }

    AIS_VESSEL_POSITIONS {
        int id PK
        int port_id FK
        string vessel_name
        string imo_number
        string vessel_class
        float latitude
        float longitude
        float speed_knots
        string destination
        datetime eta
        string berth_assigned
        string status
    }

    TIDAL_PREDICTIONS {
        int id PK
        int port_id FK
        datetime timestamp
        float height_meters
        string tide_type
        boolean safe_for_deep_draft
    }

    MARKET_REGIMES {
        int id PK
        date date
        string regime_name
        float confidence
        string primary_driver
        string contract_recommendation
    }

    COPILOT_CONVERSATIONS {
        string session_id PK
        int user_id FK
        datetime created_at
        datetime updated_at
    }

    COPILOT_MESSAGES {
        int id PK
        string session_id FK
        string sender
        text content
        json tools_called
        json citations
        datetime created_at
    }
```

---

## 3. Database Table Definitions & Schema Specifications

### Table 1: `users`
Stores user authentication records and role permissions.
* `id` (INTEGER, Primary Key, Auto-increment)
* `email` (VARCHAR(128), Unique, Indexed, NOT NULL)
* `password_hash` (VARCHAR(255), NOT NULL)
* `full_name` (VARCHAR(128), NOT NULL)
* `role` (VARCHAR(32), Default: `'CHARTERING_LEAD'`) — `ADMIN`, `CHARTERING_LEAD`, `OPERATIONS_OFFICER`, `AUDITOR_VIEWER`
* `department` (VARCHAR(64), Default: `'SAIL Shipping Cell'`)
* `is_active` (BOOLEAN, Default: `true`)
* `created_at` (DATETIME, Default: `CURRENT_TIMESTAMP`)

---

### Table 2: `freight_rates`
Historical and synthetic weekly spot freight observations (24,700 rows).
* `id` (INTEGER, Primary Key, Auto-increment)
* `date` (DATE, Indexed, NOT NULL)
* `origin` (VARCHAR(64), Indexed, NOT NULL) — e.g., `'Australia'`, `'Indonesia'`, `'United States'`
* `destination` (VARCHAR(64), Indexed, NOT NULL) — e.g., `'Thoothukudi'`, `'Chennai'`, `'Paradip'`
* `vessel_class` (VARCHAR(32), Indexed, NOT NULL) — `'Panamax'`, `'Supramax'`, `'Capesize'`
* `commodity` (VARCHAR(64), NOT NULL) — `'Coal'`, `'Iron Ore'`, `'Pig Iron'`
* `rate_usd_per_mt` (FLOAT, NOT NULL) — Base freight rate
* `tce_usd_per_day` (FLOAT, NOT NULL) — Daily Time Charter Equivalent
* `bpi_index` (FLOAT) — Associated Baltic Panamax Index value
* `bunker_price` (FLOAT, NOT NULL) — VLSFO price USD/MT
* `congestion_index` (FLOAT, Default: `0.0`) — Port congestion index 0.0–1.0
* `is_demo` (BOOLEAN, Default: `true`) — Audit label for synthetic/demo isolation

---

### Table 3: `ports`
Port physical restrictions, berths, and specialized facilities.
* `id` (INTEGER, Primary Key, Auto-increment)
* `code` (VARCHAR(16), Unique, Indexed, NOT NULL) — e.g., `'IN_TUT'` (VOCPA), `'IN_MAA'` (Chennai)
* `name` (VARCHAR(64), NOT NULL)
* `max_draft_m` (FLOAT, NOT NULL) — 14.2m for Thoothukudi, 15.5m for Chennai, 8.5m for Haldia
* `max_loa_m` (FLOAT, NOT NULL)
* `max_dwt` (FLOAT, NOT NULL) — 95,000 for VOCPA, 150,000 for Chennai, 180,000 for Kamarajar
* `berth_count` (INTEGER, NOT NULL)
* `mechanized_norm_tpd` (FLOAT, Default: `15000.0`) — Discharge norm in MT/day
* `green_hydrogen_hub` (BOOLEAN, Default: `false`) — `true` for Thoothukudi and Paradip
* `latitude` (FLOAT, NOT NULL)
* `longitude` (FLOAT, NOT NULL)

---

### Table 4: `vessels`
Standard dry-bulk vessel class specifications and consumption curves.
* `id` (INTEGER, Primary Key, Auto-increment)
* `name` (VARCHAR(64), NOT NULL) — e.g., `'MV Vishva Vijay'`, `'MV Supra Monarch'`
* `vessel_class` (VARCHAR(32), NOT NULL) — `'Handysize'`, `'Supramax'`, `'Panamax'`, `'Capesize'`
* `dwt` (FLOAT, NOT NULL)
* `draft_laden_m` (FLOAT, NOT NULL)
* `loa_m` (FLOAT, NOT NULL)
* `beam_m` (FLOAT, NOT NULL)
* `service_speed_knots` (FLOAT, Default: `14.0`)
* `eco_speed_knots` (FLOAT, Default: `11.5`)
* `fuel_burn_laden_tpd` (FLOAT, NOT NULL) — Tons/day VLSFO at service speed
* `fuel_burn_eco_tpd` (FLOAT, NOT NULL) — Tons/day VLSFO at eco speed

---

### Table 5: `ais_vessel_positions`
Live AIS telemetry queue data extracted from maritime gazettes.
* `id` (INTEGER, Primary Key, Auto-increment)
* `port_id` (INTEGER, Foreign Key to `ports.id`, NOT NULL)
* `vessel_name` (VARCHAR(64), NOT NULL)
* `imo_number` (VARCHAR(16), NOT NULL)
* `vessel_class` (VARCHAR(32), NOT NULL)
* `latitude` (FLOAT, NOT NULL)
* `longitude` (FLOAT, NOT NULL)
* `speed_knots` (FLOAT, NOT NULL)
* `destination` (VARCHAR(64), NOT NULL)
* `eta` (DATETIME)
* `berth_assigned` (VARCHAR(32)) — e.g., `'NCB-I'`, `'JD-2'`, `'CB1'`
* `status` (VARCHAR(32)) — `'DISCHARGING'`, `'IN_QUEUE'`, `'AT_ANCHOR'`

---

### Table 6: `market_regimes`
HMM regime historical classification and 30-day transition tracking.
* `id` (INTEGER, Primary Key, Auto-increment)
* `date` (DATE, NOT NULL)
* `regime_name` (VARCHAR(32), NOT NULL) — `'BEAR_DISTRESS'`, `'NEUTRAL'`, `'SEASONAL_LIFT'`, `'SUPERCYCLE_BULL'`
* `confidence` (FLOAT, NOT NULL) — 0.0 to 1.0
* `primary_driver` (VARCHAR(128), NOT NULL)
* `contract_recommendation` (VARCHAR(128), NOT NULL)

---

## 4. Indexing & Query Optimization Strategy

To ensure zero latency on complex dashboard loads:
1. **Composite Index on `freight_rates`:**
   ```sql
   CREATE INDEX idx_rates_composite ON freight_rates(origin, destination, vessel_class, date DESC);
   ```
2. **Date Index on `market_regimes`:**
   ```sql
   CREATE INDEX idx_regime_date ON market_regimes(date DESC);
   ```
3. **Port Foreign Key on `ais_vessel_positions`:**
   ```sql
   CREATE INDEX idx_ais_port ON ais_vessel_positions(port_id, status);
   ```
