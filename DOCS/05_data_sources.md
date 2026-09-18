# 🗄️ Document 5: Data Sources Catalog
## SIH26006 — All Free Data Sources for FreightIQ (Total Cost: ₹0)

---

> **Key Point:** One of the jury metrics is "Number of data sources successfully integrated." This document catalogs every free/public source available for building a credible, real-data-backed platform.

---

## 1. Baltic Freight Indices (BDI, BCI, BPI, BSI, BHSI)

### Source 1: Baltic Exchange (Official)
- **URL:** [balticexchange.com](https://www.balticexchange.com)
- **Free Access:** Weekly market reports (PDF), some historical CSV samples
- **Data Available:** BDI, BCI, BPI, BSI, BHSI daily closing values
- **Format:** CSV / Excel download
- **Update Frequency:** Daily (published at 13:00 London time)
- **Historical Depth:** Free samples going back to 2000 on request
- **How to Use:**
  ```python
  import pandas as pd
  
  # Load Baltic Exchange CSV sample
  bdi_df = pd.read_csv("baltic_exchange_bdi_history.csv", 
                         parse_dates=["Date"],
                         index_col="Date")
  # Columns: Date, BDI, BCI, BPI, BSI, BHSI
  ```

### Source 2: Quandl / NASDAQ Data Link
- **URL:** [data.nasdaq.com/data/CHRIS](https://data.nasdaq.com)
- **Free API:** Yes — 50 calls/day free
- **Relevant Datasets:**
  - `BCHAIN/TOTBC` — Global trade proxy indicators
  - `FRED/DCOILWTICO` — Oil price (correlated with bunker)
  - `ODA/PCOALGR_USD` — Australian coal price (Newcastle benchmark)
  - `ODA/PIORECR_USD` — Iron ore price (China demand proxy)
- **API Call Example:**
  ```python
  import nasdaqdatalink
  nasdaqdatalink.ApiConfig.api_key = "YOUR_FREE_KEY"
  
  coal_price = nasdaqdatalink.get("ODA/PCOALGR_USD", 
                                    start_date="2018-01-01",
                                    end_date="2024-12-31")
  ```

### Source 3: IMF Primary Commodity Prices
- **URL:** [imf.org/en/Research/commodity-prices](https://www.imf.org/en/Research/commodity-prices)
- **Free Access:** Yes — complete download
- **Data Available:** Monthly commodity prices (coal, iron ore, crude oil, natural gas)
- **Format:** Excel with 70+ commodity time series
- **No API key required**

---

## 2. Vessel Tracking (AIS Data)

### Source 4: AISHub
- **URL:** [aishub.net](https://www.aishub.net)
- **Free Tier:** Yes — free for non-commercial / academic use
- **Data Available:**
  - Real-time vessel positions (MMSI, latitude, longitude, speed, course, heading)
  - Vessel status (underway, anchored, moored, aground)
  - 4-hour delay on free tier
- **API Type:** HTTP REST
- **Rate Limit:** 1 request per vessel per hour (free tier)
- **Format:** JSON / XML
- **API Example:**
  ```python
  import requests
  
  # Get all vessels within 10 NM of Paradip port
  params = {
      "username": "YOUR_FREE_USERNAME",
      "format": "1",  # JSON
      "latmin": "19.8",  "latmax": "20.5",  # Bounding box around Paradip
      "lonmin": "86.3",  "lonmax": "87.0"
  }
  response = requests.get("http://data.aishub.net/ws.php", params=params)
  vessels = response.json()
  ```

### Source 5: OpenSeaMap
- **URL:** [openseamap.org](https://openseamap.org) / [t.marinetraffic.com/ais/](https://www.marinetraffic.com/en/ais/)
- **Free Tier:** MarineTraffic free tier — 50 calls/month
- **Data Available:** Port call events, vessel movements, port congestion estimates
- **Note:** Free tier sufficient for demo; real-time updates every 24h

### Source 6: VesselFinder
- **URL:** [vesselfinder.com](https://www.vesselfinder.com)
- **Free Tier:** Web scraping for port vessel lists (for demo purposes)
- **Useful For:** Manually verifying AIS data, port-specific vessel counts

### Port Bounding Boxes for AIS Queries
```python
PORT_BOUNDING_BOXES = {
    "paradip":     {"latmin": 20.10, "latmax": 20.45, "lonmin": 86.55, "lonmax": 86.75},
    "visakhapatnam":{"latmin": 17.60, "latmax": 17.80, "lonmin": 83.25, "lonmax": 83.40},
    "gangavaram":  {"latmin": 17.58, "latmax": 17.75, "lonmin": 83.20, "lonmax": 83.35},
    "dhamra":      {"latmin": 20.88, "latmax": 21.05, "lonmin": 86.85, "lonmax": 87.05},
    "haldia":      {"latmin": 22.00, "latmax": 22.10, "lonmin": 88.05, "lonmax": 88.20},
    "gopalpur":    {"latmin": 19.22, "latmax": 19.35, "lonmin": 84.87, "lonmax": 85.02},
    "sagar":       {"latmin": 21.62, "latmax": 21.72, "lonmin": 88.04, "lonmax": 88.18}
}

# Origin Ports
ORIGIN_BOUNDING_BOXES = {
    "newcastle":   {"latmin": -33.0, "latmax": -32.6, "lonmin": 151.7, "lonmax": 152.0},
    "port_hedland":{"latmin": -20.5, "latmax": -20.2, "lonmin": 118.5, "lonmax": 118.7},
    "hampton_roads":{"latmin": 36.8, "latmax": 37.2, "lonmin": -76.5, "lonmax": -76.0},
    "kalimantan":  {"latmin": -3.8,  "latmax": -2.0,  "lonmin": 115.5, "lonmax": 117.0}
}
```

---

## 3. Tidal Data (India-Specific)

### Source 7: INCOIS (Indian National Centre for Ocean Information Services)
- **URL:** [incois.gov.in](https://www.incois.gov.in)
- **Free Access:** Yes — Government of India open data
- **Data Available:**
  - Tidal predictions for all major Indian ports (Haldia, Paradip, Vizag, Gopalpur, Dhamra, Sagar)
  - Hourly tide height forecasts up to 30 days ahead
  - Historical tidal observations
  - Ocean current data (relevant for vessel routing efficiency)
- **API Endpoint:**
  ```
  GET https://incois.gov.in/portal/tides/tidedata.jsp
    ?port=HALDIA
    &startdate=2026-09-18
    &enddate=2026-10-18
    &format=json
  ```
- **Response Format:**
  ```json
  {
    "port": "HALDIA",
    "data": [
      {"datetime": "2026-09-18T06:45:00", "height_m": 4.82, "type": "HIGH"},
      {"datetime": "2026-09-18T12:30:00", "height_m": 0.43, "type": "LOW"},
      {"datetime": "2026-09-18T19:15:00", "height_m": 5.01, "type": "HIGH"}
    ]
  }
  ```

### Source 8: NOAA Tides (For Origin Ports — US)
- **URL:** [tidesandcurrents.noaa.gov](https://tidesandcurrents.noaa.gov/api-helper/url-helper.html)
- **Free API:** Yes — no key required
- **Stations Available:** Hampton Roads, Baltimore, all US East Coast ports
- **API Example:**
  ```python
  url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
  params = {
      "station": "8638610",  # Hampton Roads
      "product": "predictions",
      "datum": "MLLW",
      "time_zone": "lst_ldt",
      "interval": "h",       # Hourly
      "units": "metric",
      "application": "freightiq",
      "format": "json",
      "begin_date": "20260918",
      "end_date": "20261018"
  }
  ```

---

## 4. Weather & Cyclone Data

### Source 9: IMD (India Meteorological Department)
- **URL:** [mausam.imd.gov.in](https://mausam.imd.gov.in) / [imdaws.com](https://www.imdaws.com)
- **Free Access:** Yes — Government of India open data
- **Data Available:**
  - Bay of Bengal cyclone warnings (affects East Coast India ports)
  - Wind and wave height forecasts (affects vessel safety speed)
  - Port-level weather observations
  - Seasonal forecast bulletins
- **Use in FreightIQ:**
  - **Cyclone alert** → Auto-trigger port closure warning + voyage delay estimate
  - **High wave forecast** (>3m) → Speed reduction recommendation
  - **Monsoon schedule** → Seasonal demand pattern feature

### Source 10: ECMWF ERA5 / Open-Meteo
- **URL:** [open-meteo.com](https://open-meteo.com) — No API key needed
- **Data Available:** Wind speed, wave height, visibility at any ocean coordinates
- **API Example:**
  ```python
  url = "https://marine-api.open-meteo.com/v1/marine"
  params = {
      "latitude": "19.5",   # Mid-Bay of Bengal
      "longitude": "85.5",
      "hourly": "wave_height,wind_speed_10m,ocean_current_velocity",
      "forecast_days": "7"
  }
  ```

---

## 5. Bunker Fuel Prices

### Source 11: Ship & Bunker
- **URL:** [shipandbunker.com](https://shipandbunker.com)
- **Free Tier:** Yes — historical data and daily prices visible on website
- **Data Available:**
  - VLSFO prices at all major bunkering ports (Singapore, Fujairah, Rotterdam, Houston)
  - MGO, HSFO prices
  - Bunker price index trends
- **Scraping / Manual Download:**
  ```python
  import requests
  from bs4 import BeautifulSoup
  
  # Scrape Singapore VLSFO price (biggest bunkering hub, price benchmark)
  response = requests.get("https://shipandbunker.com/prices/apac/sea/sg-sin-singapore")
  soup = BeautifulSoup(response.text, "html.parser")
  price_table = soup.find("table", class_="price-history")
  ```

### Source 12: EIA (US Energy Information Administration)
- **URL:** [eia.gov/petroleum/gasdiesel/](https://www.eia.gov/petroleum/gasdiesel/)
- **Free API:** Yes — key required (free registration)
- **Data Available:** Crude oil, distillate fuel oil prices (proxy for marine fuel)
- **Correlation:** Brent crude price is 85%+ correlated with VLSFO prices

---

## 6. Port-Specific Data (Indian East Coast)

### Source 13: Paradip Port Authority (PPA)
- **URL:** [paradipport.gov.in](https://paradipport.gov.in)
- **Free Data:** Port statistics, vessel call data, cargo handling volumes
- **Monthly Reports:** Published as PDF — parseable for historical throughput

### Source 14: Visakhapatnam Port Trust (VPT)
- **URL:** [vishakapatnamport.gov.in](https://www.vishakapatnamport.gov.in)
- **Free Data:** Traffic statistics, berthing information

### Source 15: Gangavaram Port (now Adani)
- **URL:** [gangavamport.com](https://www.gangavamport.com)
- **Free Data:** Vessel information, capacity data, handling rates

### Source 16: Ministry of Ports (MoPSW) Open Data
- **URL:** [data.gov.in → search "ports"](https://data.gov.in)
- **Free Data:** All major port statistics, cargo volumes, vessel call data
- **Format:** CSV download, updated quarterly

---

## 7. News & Sentiment Data

### Source 17: Reuters RSS Feeds
- **Free Access:** Yes — public RSS feeds
- **Relevant Feeds:**
  ```
  https://feeds.reuters.com/reuters/businessNews
  https://feeds.reuters.com/reuters/companyNews
  ```
- **Keywords to Filter:** "shipping", "freight", "Baltic", "coal", "India port", "Suez", "Red Sea"

### Source 18: TradeWinds
- **URL:** [tradewindsnews.com](https://www.tradewindsnews.com)
- **Free Access:** 5 articles/month free; RSS feed partial access
- **Content:** Dry bulk market news, charter deals, port news

### Source 19: Google News API / NewsAPI
- **URL:** [newsapi.org](https://newsapi.org) — 100 requests/day free
- **Queries:**
  ```python
  params = {
      "q": "shipping freight Baltic India coal",
      "sortBy": "publishedAt",
      "language": "en",
      "apiKey": "YOUR_FREE_KEY"
  }
  ```

---

## 8. Economic Indicators

### Source 20: World Bank Open Data
- **URL:** [data.worldbank.org](https://data.worldbank.org)
- **Free API:** Yes — no key required
- **Data Available:** GDP growth, industrial production, steel output by country
- **API Example:**
  ```python
  # China GDP growth (primary driver of Capesize demand)
  url = "https://api.worldbank.org/v2/country/CHN/indicator/NY.GDP.MKTP.KD.ZG"
  params = {"format": "json", "date": "2015:2026", "per_page": "50"}
  ```

### Source 21: FRED (Federal Reserve Economic Data)
- **URL:** [fred.stlouisfed.org](https://fred.stlouisfed.org)
- **Free API:** Yes — free key registration
- **Relevant Series:**
  - `DCOILWTICO` — WTI Crude (bunker proxy)
  - `INDPRO` — US Industrial Production (coal export demand)
  - `CSUSHPISA` — Steel-related construction indicator

---

## 9. Vessel Specifications Database

### Source 22: Clarksons (Limited Free Data)
- **URL:** [sea-web.com](https://www.sea-web.com)
- **Free Access:** Basic vessel lookup
- **Alternative:** IHS Markit vessel database (limited free tier)

### Source 23: Equasis (EU Open Data)
- **URL:** [equasis.org](https://www.equasis.org) — Free after registration
- **Data Available:** Vessel registry, flag state, gross tonnage, DWT
- **Use:** Validate vessel CII rating and technical specs

---

## 10. Data Integration Summary

| Data Type | Source | API/Download | Update Freq | Priority |
|-----------|--------|-------------|-------------|----------|
| BDI / BCI / BPI | Baltic Exchange + Quandl | CSV + API | Daily | 🔴 Critical |
| VLSFO Bunker | Ship & Bunker (scrape) | Web scrape | Daily | 🔴 Critical |
| AIS Vessel Positions | AISHub | REST API | 4 hours | 🔴 Critical |
| Tidal Windows | INCOIS (India) | REST API | Daily | 🟠 High |
| Coal FOB Price | Quandl / IMF | API | Monthly | 🟠 High |
| Iron Ore Price | World Bank / Quandl | API | Monthly | 🟠 High |
| Weather/Cyclone | IMD + Open-Meteo | REST API | 6 hours | 🟠 High |
| Port Traffic Stats | MoPSW Open Data | CSV Download | Quarterly | 🟡 Medium |
| News Sentiment | Reuters RSS + NewsAPI | RSS + API | 15 minutes | 🟡 Medium |
| Crude Oil Price | FRED | API | Daily | 🟡 Medium |
| US Tides (Hampton Roads) | NOAA | REST API | Daily | 🟢 Low |
| Vessel Specs | Equasis | Web Portal | As needed | 🟢 Low |

**Total external data cost for full platform: ₹0 / $0**

---

## 11. Data Pipeline Implementation

```python
# backend/data/ingestion_pipeline.py

import asyncio
import schedule
from datetime import datetime

class FreightIQDataPipeline:
    
    async def run_all_ingestion_tasks(self):
        """Orchestrate all data collection tasks"""
        
        tasks = [
            self.ingest_ais_data(),          # Every 4 hours
            self.ingest_bunker_prices(),     # Daily at 08:00 IST
            self.ingest_bdi_data(),          # Daily at 15:30 IST (after Baltic close)
            self.ingest_tidal_predictions(), # Daily at 00:00 IST
            self.ingest_weather_alerts(),    # Every 6 hours
            self.ingest_news_sentiment(),    # Every 15 minutes
            self.ingest_commodity_prices()   # Weekly (Monday morning)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {task.__name__: result for task, result in zip(tasks, results)}
    
    async def ingest_ais_data(self):
        """Fetch AIS positions for all 14 relevant ports"""
        for port, bbox in ALL_PORT_BOUNDING_BOXES.items():
            vessels = await self.aishub_client.get_vessels(bbox)
            congestion_score = self.calculate_congestion_score(vessels, port)
            await self.db.upsert_congestion(port, congestion_score, vessels)
    
    async def ingest_tidal_predictions(self):
        """Fetch INCOIS predictions for all tide-gated Indian ports"""
        for port in ["haldia", "gopalpur", "sagar"]:
            tidal_data = await self.incois_client.get_predictions(port, days=30)
            windows = self.extract_entry_windows(tidal_data, port)
            await self.db.upsert_tidal_windows(port, windows)
    
    def calculate_congestion_score(self, vessels: list, port: str) -> int:
        """Compute 0–100 congestion score from AIS vessel list"""
        anchor_count = sum(1 for v in vessels if v["status"] in ["1", "5"])  # Anchored/moored
        drifting_count = sum(1 for v in vessels if v["sog"] < 0.5)  # Near-stopped
        
        max_anchor = PORT_ANCHOR_CAPACITY[port]
        score = min(100, int(
            0.60 * (anchor_count / max_anchor) * 100 +
            0.25 * (drifting_count / (anchor_count + 1)) * 100 +
            0.15 * random.gauss(0, 5)  # Noise term
        ))
        return score
```

---

*Document 5 of 6 | SIH26006 Research Suite | FreightIQ Platform*
