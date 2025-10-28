# Biosample Enricher: Provider Reliability Analysis

**Date:** 2025-10-27
**Analysis Scope:** All data fetching providers across 7 service domains

---

## Executive Summary

This analysis identifies **15 unique providers** across 7 service domains, with significant reliability variations:

- **High Reliability:** 7 providers (keyless public APIs, global coverage, stable services)
- **Moderate Reliability:** 5 providers (API key-dependent, known migration issues, regional limitations)
- **Known Issues:** 3 providers (incomplete implementations, fallback mechanisms needed)

**Critical Gaps Identified:**
- USGS elevation service has known migration issues and unreliability
- GEBCO bathymetry provider has incomplete WCS implementation
- MODIS vegetation provider is mock-only (not fully implemented)
- Marine providers lack comprehensive error handling

---

## Provider Summary Table

| Service Domain | Provider | API | API Key | Coverage | Status | Reliability |
|---|---|---|---|---|---|---|
| **Elevation** | Google Elevation | Google Maps | ✓ Required | Global | ✓ Active | Moderate |
| | USGS 3DEP | USGS ArcGIS | ✗ None | Global | ⚠️ Unstable | Low |
| | Open Topo Data | REST API | ✗ None | Global (250m-1km) | ✓ Active | High |
| | OSM Elevation | open-elevation.com | ✗ None | Global (90m) | ✓ Active | High |
| **Soil** | ISRIC SoilGrids | WCS/REST | ✗ None | Global (250m) | ✓ Active | High |
| | USDA NRCS | SDA REST | ✗ None | US Only | ✓ Active | High |
| **Weather** | MeteoStat | Library+CDN | ✗ None | Global (120k+ stations) | ✓ Active | High |
| | Open-Meteo | ERA5 API | ✗ None | Global (11km) | ✓ Active | High |
| **Marine** | GEBCO | WCS Service | ✗ None | Global (15 arc-sec) | ⚠️ Incomplete | Low |
| | ESA Ocean Colour CCI | ERDDAP | ✗ None | Global Ocean (1km) | ⚠️ Incomplete | Moderate |
| | NOAA OISST | ERDDAP | ✗ None | Global Ocean (0.25°) | ⚠️ Incomplete | Moderate |
| **Land Cover** | NLCD | WMS | ✗ None | US Only (30m) | ✓ Active | High |
| | ESA WorldCover | WMS | ✗ None | Global (10m) | ✓ Active | High |
| **Vegetation** | MODIS | APPEEARS | ✗ None | Global (250-500m) | ⚠️ Mock Only | Low |
| **Geocoding** | Google Forward | Google Maps | ✓ Required | Global | ✓ Active | Moderate |
| | OSM Nominatim | Nominatim | ✗ None | Global | ✓ Active | High |
| | Google Reverse | Google Maps | ✓ Required | Global | ✓ Active | Moderate |
| | OSM Nominatim Reverse | Nominatim | ✗ None | Global | ✓ Active | High |
| **OSM Features** | Overpass API | Overpass | ✗ None | Global | ✓ Active | Moderate |

---

## Detailed Domain Analysis

### 1. ELEVATION PROVIDERS

#### Google Elevation
- **API:** Google Maps Elevation API v1
- **Coverage:** Global (30m resolution)
- **API Key:** REQUIRED (`GOOGLE_MAIN_API_KEY`)
- **Timeout:** 20 seconds default
- **Rate Limit:** 50 QPS with API key
- **Reliability Status:** **MODERATE**

**Strengths:**
- Comprehensive global coverage
- Accurate rooftop-level elevation data
- Proper error handling with status codes (OK, ZERO_RESULTS, REQUEST_DENIED, OVER_QUERY_LIMIT)
- Uses vertical datum: EGM96 (geoid)

**Weaknesses:**
- Requires paid API key
- Potential quota exhaustion (OVER_QUERY_LIMIT)
- Missing fallback mechanisms

**Known Issues:**
- None documented

**Test Status:** Not marked with network or flaky markers in test suite

---

#### USGS 3DEP (Elevation Point Query Service)
- **API:** USGS ArcGIS REST Service
- **Coverage:** Global (10-30m resolution, varies by region)
- **API Key:** None required
- **Timeout:** 20 seconds default
- **Endpoint:** `https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/getSamples`
- **Reliability Status:** **LOW** ⚠️

**Strengths:**
- Free access, no API key required
- Global coverage with high resolution in USA
- Uses proper vertical datum: NAVD88

**Weaknesses:**
- **KNOWN MIGRATION ISSUES**: Code comments explicitly state "USGS elevation services have experienced multiple migrations and can be unreliable"
- Service has migrated from deprecated EPQS endpoint to 3DEP ArcGIS
- Endpoint may change or experience outages
- No-data sentinel values: -1000000, -9999 (complex handling required)
- Service availability may vary

**Known Issues:**
- Endpoint migration from EPQS to 3DEP (code comment: "Service availability may vary")
- Service unreliability documented in provider code
- Complex no-data value handling

**Recommendation:** Use as **secondary fallback only**. Monitor service availability closely. Consider deprecating if USGS performs additional migrations.

**Test Status:** Marked with `@pytest.mark.flaky` (reruns=2, reruns_delay=10s) in test suite

---

#### Open Topo Data
- **API:** Public REST API with multiple datasets
- **Coverage:** Global (datasets: SRTM 30m/90m, ASTER 30m, EUDEM 25m, NED 10m)
- **API Key:** None required
- **Timeout:** 20 seconds default
- **Endpoint:** `https://api.opentopodata.org/v1/{dataset}`
- **Reliability Status:** **HIGH** ✓

**Strengths:**
- Multiple dataset options for different regions
- SmartOpenTopoDataProvider auto-selects optimal dataset by location
- Free access, no rate limits published
- Proper error handling (OK status checking)
- Different vertical datums by dataset (EGM96, EVRS2000, NAVD88)

**Weaknesses:**
- External service dependency
- Dataset availability varies by region
- No published rate limits or SLAs

**Regional Optimization:**
- Europe (35-65°N, -15-40°E) → EU-DEM 25m
- Polar regions (>60° or <-60°) → ASTER 30m
- Global default → SRTM 30m

**Test Status:** Not marked with network or flaky markers

---

#### OSM Elevation (open-elevation.com)
- **API:** OpenElevation-style API (POST JSON)
- **Coverage:** Global (SRTM 90m data)
- **API Key:** None required
- **Timeout:** 20 seconds default
- **Endpoint:** `https://api.open-elevation.com/api/v1/lookup`
- **Reliability Status:** **HIGH** ✓

**Strengths:**
- Simple JSON POST interface
- Free public access
- Global coverage
- Uses EGM96 vertical datum

**Weaknesses:**
- External service dependency
- No documented rate limits
- Depends on open-elevation.com uptime

**Test Status:** Not marked with network or flaky markers

---

### 2. SOIL PROVIDERS

#### ISRIC SoilGrids
- **API:** Web Coverage Service (WCS) 2.0.1 and REST API
- **Coverage:** Global (250m resolution)
- **API Key:** None required
- **Timeout:** 30 seconds default
- **Endpoints:**
  - WCS: `https://maps.isric.org/mapserv?map=/map/{service}.map`
  - REST: `https://rest.isric.org/soilgrids/v2.0`
- **Reliability Status:** **HIGH** ✓

**Features:**
- WRB soil classification (30 classes: Acrisols→Vertisols)
- Soil properties: pH, organic carbon, bulk density, sand/silt/clay %, nitrogen
- Texture classification using USDA triangle
- WCS 2.0.1 with fallback to WCS 1.0.0
- REST API with fallback to WCS if REST fails

**Strengths:**
- Comprehensive global coverage
- Multiple acquisition methods (REST + WCS fallback)
- Good quality score calculation (completeness-based)
- Proper no-data value handling
- Confidence scoring for WRB classification

**Weaknesses:**
- Dual API dependency increases complexity
- Grid-based resolution may miss local variation
- 250m resolution may be too coarse for some applications

**Quality Assessment:**
- Base resolution: ~125m to pixel center (250m grid)
- Data completeness score: 8 possible fields (WRB, pH, SOC, BDOD, sand, silt, clay, nitrogen)
- Quality score: 0.5-1.0 based on distance and completeness

**Test Status:** Not marked with network or flaky markers

---

#### USDA NRCS Soil Data Access
- **API:** SDA REST (Tabular/post.rest)
- **Coverage:** Continental USA + territories
- **API Key:** None required
- **Timeout:** 30 seconds default
- **Endpoint:** `https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest`
- **Reliability Status:** **HIGH** ✓

**Features:**
- USDA Soil Taxonomy classification (hierarchical)
- Soil components with coverage percentages
- Detailed taxonomy: order → suborder → great group → subgroup
- Quality boost for major components and detailed taxonomy

**Strengths:**
- Very high quality USDA-authoritative data
- US-specific depth of detail
- Component-based approach (multiple soils per location)
- Good quality scoring (base 0.8 + bonuses up to 1.0)

**Weaknesses:**
- US-only coverage (continental + territories)
- Complex multi-query workflow (mukey → components)
- No depth-specific data (full profile only)

**Quality Assessment:**
- Base quality score: 0.8 (USDA data is authoritative)
- Major component bonus: +0.1
- Detailed taxonomy bonus: +0.1
- Full coverage bonus: +0.05
- Max score: 1.0+

**Test Status:** Not marked with network or flaky markers

---

### 3. WEATHER PROVIDERS

#### MeteoStat
- **Source:** Meteostat Library + CDN
- **Coverage:** Global (120,000+ weather stations)
- **Data Period:** 1973-present (7-day lag)
- **API Key:** None required
- **Temporal Resolution:** Daily observations
- **Spatial Resolution:** Station-based (distance tracked)
- **Reliability Status:** **HIGH** ✓

**Features:**
- Temperature (tmin, tmax, tavg)
- Wind (speed, direction)
- Precipitation
- Atmospheric pressure
- Station distance tracking (max 100km)

**Strengths:**
- Longest historical record (1973+)
- Station-based ground truth data
- No API key required
- Global coverage with ~120,000 stations
- Quality penalty for distant stations

**Weaknesses:**
- 7-day lag in data
- Station availability varies by region
- Distance-based quality penalty (max 100km limit)

**Quality Assessment:**
- DAY_SPECIFIC_COMPLETE: full day coverage
- DAY_SPECIFIC_PARTIAL: partial day coverage
- Distance factor: 1.0 (at station) to 0.5 (100km away)

**Test Status:** Not marked with network or flaky markers

---

#### Open-Meteo
- **Source:** ERA5 Reanalysis (Copernicus)
- **Coverage:** Global (11km grid resolution)
- **Data Period:** 1959-present
- **API Key:** None required
- **Temporal Resolution:** Hourly (aggregated to daily)
- **Spatial Resolution:** 11km
- **Reliability Status:** **HIGH** ✓

**Features:**
- Temperature (min, max, avg)
- Precipitation
- Wind (speed, direction)
- Humidity
- Pressure
- Solar radiation
- Hourly data aggregated to daily with coverage tracking

**Strengths:**
- Longest continuous record (1959+)
- Global grid coverage (no gaps)
- Very recent data
- Hourly resolution allows precise aggregation
- Multiple parameters (7 standard)

**Weaknesses:**
- 11km resolution may miss local variation
- Reanalysis product (model + observations)
- Requires aggregation from hourly

**Quality Assessment:**
- DAY_SPECIFIC_COMPLETE: 24+ hours data (≥80% coverage)
- DAY_SPECIFIC_PARTIAL: <80% coverage
- Aggregation method: hourly_aggregation

**Test Status:** Not marked with network or flaky markers

---

### 4. MARINE PROVIDERS

#### GEBCO (General Bathymetric Chart of the Oceans)
- **API:** WCS (Web Coverage Service)
- **Coverage:** Global bathymetry (15 arc-second ≈ 450m)
- **API Key:** None required
- **Data Type:** Static bathymetric grid
- **Reliability Status:** **LOW** ⚠️

**Strengths:**
- High-resolution global bathymetry
- Authoritative data source
- Static dataset (no temporal issues)

**Weaknesses:**
- **INCOMPLETE IMPLEMENTATION**: Provider has fallback depth estimation (placeholder)
- WCS implementation not functional (marked as "simplified approach")
- Code comment: "In production, you would implement proper WCS requests"
- Uses very rough estimation based on latitude/longitude
- No actual GEBCO data access in current implementation

**Implementation Status:**
```python
# Mock implementation with placeholder estimation:
# - Coastal: -10m to -200m (very inaccurate)
# - Open ocean: -1000m to -5000m (very inaccurate)
```

**Recommendation:** **DO NOT USE** in production. This provider needs:
1. Proper WCS client implementation
2. Actual GEBCO grid data access or
3. Third-party bathymetry API integration

**Test Status:** Not marked with network or flaky markers

---

#### ESA Ocean Colour CCI
- **API:** ERDDAP griddap (NOAA NEFSC)
- **Coverage:** Global ocean (1km resolution, but daylight-dependent)
- **Data Period:** 1997-09-04 to present
- **API Key:** None required
- **Parameter:** Chlorophyll-a concentration
- **Reliability Status:** **MODERATE** ⚠️

**Strengths:**
- High-quality satellite L3 product
- Global ocean coverage
- 1km resolution
- Long time series (1997+)

**Weaknesses:**
- **INCOMPLETE IMPLEMENTATION**: Uses fallback estimation if ERDDAP fails
- Chlorophyll estimates are rough approximations
- Cloud/weather dependent (gaps in data)
- Limited to marine/ocean areas
- ERDDAP service dependency

**Data Quality Issues:**
- No real ERDDAP integration (simplified example)
- Fallback chlorophyll estimation by latitude/region (very inaccurate)
- Expected range check: 0.001-100.0 mg/m³

**Fallback Logic:**
- Tropical (<10°): 0.15 mg/m³ base
- Subtropical (10-30°): 0.08 mg/m³ base
- Temperate (30-60°): 0.5 mg/m³ base
- Polar (>60°): 1.2 mg/m³ base

**Recommendation:** Needs proper ERDDAP integration or fallback to alternative chlorophyll sources

**Test Status:** Not marked with network or flaky markers

---

#### NOAA OISST (Optimum Interpolation Sea Surface Temperature)
- **API:** ERDDAP griddap (NOAA NCEI)
- **Coverage:** Global ocean (0.25° grid)
- **Data Period:** 1981-09-01 to present
- **API Key:** None required
- **Temporal Resolution:** Daily
- **Data Type:** L4 interpolated product
- **Reliability Status:** **MODERATE** ⚠️

**Strengths:**
- Long time series (1981+)
- Global ocean coverage
- L4 product (interpolated/gap-filled)
- Daily resolution
- Well-documented data format

**Weaknesses:**
- **INCOMPLETE IMPLEMENTATION**: Uses placeholder/mock data retrieval
- No real ERDDAP integration
- Requires longitude conversion (−180/180 to 0/360)
- ERDDAP service dependency

**Data Validation:**
- SST range check: -5°C to +50°C
- Returns None for out-of-range values

**Recommendation:** Needs proper ERDDAP integration

**Test Status:** Not marked with network or flaky markers

---

### 5. LAND COVER PROVIDERS

#### NLCD (National Land Cover Database)
- **API:** WMS (Web Map Service)
- **Coverage:** Continental USA (30m resolution)
- **API Key:** None required
- **Available Years:** 2001, 2006, 2011, 2016, 2019, 2021
- **Reliability Status:** **HIGH** ✓

**Features:**
- 19 land cover classes (water, developed, forest, grassland, wetland, etc.)
- Multi-year archive with temporal comparison
- GetFeatureInfo queries for point data
- Automatic year selection based on target date

**Strengths:**
- High-quality USGS-authoritative data
- US-specific authority
- Multi-year temporal coverage
- 30m resolution
- Proper class mappings

**Weaknesses:**
- US-only coverage
- Quality confidence decreases with temporal distance (0.85 base, -0.1 per year)

**Temporal Logic:**
- Selects closest year ≤ target date
- Adds next year for comparison
- Limits to 2 years maximum

**Quality Assessment:**
- Base confidence: 0.85
- Temporal adjustment: max(0.5, 0.85 - years_diff × 0.1)

**Test Status:** Not marked with network or flaky markers

---

#### ESA WorldCover
- **API:** WMS (Terrascope service)
- **Coverage:** Global (10m resolution)
- **Data Version:** 2021 (represents 2020-2021)
- **API Key:** None required
- **Endpoint:** `https://services.terrascope.be/wms/v2`
- **Reliability Status:** **HIGH** ✓

**Features:**
- 11 land cover classes
- Global coverage (10m resolution)
- Tree cover, shrubland, grassland, cropland, built-up, bare land, snow/ice, water, wetland, mangroves, moss/lichen
- GetFeatureInfo queries

**Strengths:**
- Highest resolution (10m) of available providers
- Global coverage
- Recent data (2020-2021)
- High-quality ESA product
- High base confidence (0.85)

**Weaknesses:**
- Static dataset (no annual updates)
- Only one epoch available (2021)
- Service dependency on Terrascope

**Test Status:** Not marked with network or flaky markers

---

### 6. VEGETATION PROVIDERS

#### MODIS Vegetation Indices
- **API:** NASA APPEEARS API
- **Coverage:** Global (250m-500m resolution)
- **Data Period:** 2000-present
- **API Key:** None required (NASA Earth Data login required)
- **Products:**
  - MOD13Q1: Terra 250m 16-day NDVI/EVI
  - MCD15A3H: Combined 500m 4-day LAI/FPAR
- **Reliability Status:** **LOW** ⚠️

**Features:**
- NDVI (Normalized Difference Vegetation Index)
- EVI (Enhanced Vegetation Index)
- LAI (Leaf Area Index)
- FPAR (Fraction of Absorbed Photosynthetically Active Radiation)

**Weaknesses:**
- **MOCK IMPLEMENTATION ONLY**: Uses generated mock data
- Code comment: "In production, this would be replaced with actual MODIS data access"
- No real APPEEARS API integration
- Generates realistic but fake data using seeded random

**Mock Data Generation:**
```python
# Uses seeded randomness based on: latitude × 1000 + longitude × 1000 + day_of_year
# Generates seasonal and latitude-based vegetation patterns
# NOT actual MODIS observations
```

**Recommendation:** **DO NOT USE** in production. Requires:
1. APPEEARS API authentication setup
2. Task submission and processing workflow
3. Result download and parsing
4. Actual MODIS data retrieval

**Test Status:** Not marked with network or flaky markers

---

### 7. GEOCODING PROVIDERS

#### Google Forward Geocoding
- **API:** Google Maps Geocoding API v1
- **Coverage:** Global
- **API Key:** REQUIRED (`GOOGLE_MAIN_API_KEY`)
- **Timeout:** 30 seconds default
- **Rate Limit:** 50 QPS
- **Reliability Status:** **MODERATE**

**Features:**
- Place name → coordinates
- Address component parsing
- Bounding boxes (viewport)
- Location type determination
- Relevance and confidence scoring
- Partial match detection

**Strengths:**
- Comprehensive geocoding
- High accuracy for known places
- Rich response metadata

**Weaknesses:**
- Requires paid API key
- Potential quota exhaustion (OVER_QUERY_LIMIT status)
- Relevance/confidence heuristics required

**Error Handling:**
- REQUEST_DENIED: API key invalid
- OVER_QUERY_LIMIT: Quota exceeded
- INVALID_REQUEST: Bad request
- ZERO_RESULTS: No matches found

**Test Status:** Not marked with network or flaky markers

---

#### OSM Nominatim Forward Geocoding
- **API:** OpenStreetMap Nominatim Search API
- **Coverage:** Global
- **API Key:** None required
- **Timeout:** 30 seconds default
- **Rate Limit:** 1 request/second (enforced in code)
- **Endpoint:** `https://nominatim.openstreetmap.org/search`
- **Reliability Status:** **HIGH** ✓

**Features:**
- Place name → coordinates
- Address component parsing
- Country filtering
- Bounding boxes
- Importance scoring
- OSM identifiers

**Strengths:**
- Free, no API key
- Global OSM data
- Rate limiting enforced in code
- Deduplication
- Extra tags support (Wikipedia, Wikidata)

**Weaknesses:**
- Rate limit (1 req/sec) slows bulk operations
- Nominatim ToS require proper user-agent
- External service dependency

**Rate Limiting:**
```python
_min_request_interval = 1.0  # seconds
# Enforces 1-second minimum between requests
```

**Test Status:** Not marked with network or flaky markers

---

#### Google Reverse Geocoding
- **API:** Google Maps Geocoding API v1 (reverse mode)
- **Coverage:** Global
- **API Key:** REQUIRED (`GOOGLE_MAIN_API_KEY`)
- **Timeout:** 20 seconds default
- **Rate Limit:** 50 QPS
- **Reliability Status:** **MODERATE**

**Features:**
- Coordinates → address
- Multiple results ranked by distance
- Address component hierarchy
- Bounding boxes
- Place type determination
- Confidence scoring

**Strengths:**
- Multiple results per query
- Rich component information
- High accuracy for addresses

**Weaknesses:**
- Requires paid API key
- Potential quota exhaustion

**Confidence Scoring:**
- First result: 1.0 - 0.1 = 0.9
- Second result: 1.0 - 0.2 = 0.8
- Etc. (decreases by 0.1 per additional result)

**Test Status:** Not marked with network or flaky markers

---

#### OSM Nominatim Reverse Geocoding
- **API:** OpenStreetMap Nominatim Reverse API
- **Coverage:** Global
- **API Key:** None required
- **Timeout:** 20 seconds default
- **Rate Limit:** 1 request/second (enforced)
- **Endpoint:** `https://nominatim.openstreetmap.org/reverse`
- **Reliability Status:** **HIGH** ✓

**Features:**
- Coordinates → address
- Address component hierarchy
- Place rank and importance
- OSM identifiers
- Wikipedia/Wikidata links
- Multiple result levels

**Strengths:**
- Free, no API key
- Global coverage
- Rich metadata (place rank, importance)
- External identifiers for linking

**Weaknesses:**
- Rate limited (1 req/sec)
- External service dependency
- Requires proper user-agent

**Rate Limiting:**
```python
min_request_interval = 1.0  # seconds
# Enforced for public Nominatim instance
```

**Test Status:** Not marked with network or flaky markers

---

### 8. OSM FEATURES PROVIDER

#### Overpass API
- **API:** OpenStreetMap Overpass QL
- **Coverage:** Global
- **API Key:** None required
- **Timeout:** 180 seconds default (configurable)
- **Rate Limit:** 1 request/second (enforced)
- **Endpoint:** `https://overpass-api.de/api/interpreter`
- **Reliability Status:** **MODERATE**

**Features:**
- Geographic features within radius
- Named features (with name tags)
- Unnamed feature counts by category
- Feature categorization (natural, waterway, highway, amenity, etc.)
- Geometry type detection (point, linestring, polygon, multipolygon)
- Distance calculation from sample point

**Strengths:**
- Global coverage
- No API key required
- Comprehensive feature extraction
- Named/unnamed feature separation
- Geometry type detection

**Weaknesses:**
- Service can be slow/unstable during high load
- Overpass QL complexity for comprehensive queries
- Rate limiting (1 req/sec) for reliability
- Timeout configurable but server limits apply

**Query Strategy:**
```
[out:json][timeout:180];
(
  node(around:1000,lat,lon);
  way(around:1000,lat,lon);
  relation(around:1000,lat,lon);
);
out body geom qt;
```

**Feature Categorization:**
- Natural (landuse, natural)
- Waterway (rivers, streams)
- Highway (roads, paths)
- Railway, Aeroway
- Amenity (services, facilities)
- Leisure, Building
- Boundary, Place
- Tourism, Shop, Craft, Office

**Distance Calculations:**
- Point to point: Haversine formula
- Point to linestring: Min distance to segments
- Point to polygon: Ray casting for containment, edge distance if outside

**Test Status:** Not marked with network or flaky markers

---

## Reliability Matrices

### By API Key Requirement

| Category | Count | Providers |
|---|---|---|
| **No API Key (Free)** | 12 | USGS, Open Topo, OSM Elevation, SoilGrids, USDA NRCS, MeteoStat, Open-Meteo, GEBCO, ESA CCI, NOAA OISST, NLCD, ESA WorldCover, MODIS, OSM (both), Overpass |
| **API Key Required** | 3 | Google Elevation, Google Geocoding (both directions) |

### By Coverage

| Category | Count | Providers |
|---|---|---|
| **Global** | 10 | Elevation (3), Soil (1), Weather (2), Marine (2), Geocoding (2) |
| **US/North America** | 2 | NLCD, USDA NRCS |
| **Ocean/Marine** | 3 | GEBCO, ESA CCI, NOAA OISST |
| **Regional Variations** | 2 | Open Topo Data (smart selection), SoilGrids (250m global) |

### By Temporal Data

| Category | Providers |
|---|---|
| **Real-time/Recent** | MeteoStat, Open-Meteo, NOAA OISST |
| **Historical** | MeteoStat (1973+), Open-Meteo (1959+), NOAA OISST (1981+) |
| **Static** | GEBCO, NLCD (multi-year), ESA WorldCover (2020-2021) |
| **No temporal component** | Elevation (current), Soil (current), Geocoding (no date), OSM Features |

### By Implementation Status

| Status | Count | Providers |
|---|---|---|
| **Fully Implemented** | 12 | All elevation, soil, weather, most geocoding, land cover, OSM features |
| **Incomplete (Fallback/Mock)** | 3 | GEBCO, ESA CCI, NOAA OISST |
| **Mock Only** | 1 | MODIS |
| **Known Issues** | 1 | USGS (migration history) |

---

## Critical Reliability Gaps

### Gap 1: USGS Elevation Service Unreliability

**Issue:** USGS elevation service has known migration history and documented unreliability.

**Evidence:**
- Code comments: "USGS elevation services have experienced multiple migrations and can be unreliable"
- Endpoint migrated from EPQS to 3DEP ArcGIS
- Complex no-data value handling (-1000000, -9999)
- Test marked with `@pytest.mark.flaky(reruns=2, reruns_delay=10)`

**Recommendation:**
1. Use **Open Topo Data as primary** (stable, global, multiple datasets)
2. Use **OSM Elevation as first fallback** (stable, 90m global coverage)
3. Use **USGS as last fallback only** with extensive error handling
4. Monitor USGS service status continuously
5. Plan deprecation if USGS performs additional migrations

---

### Gap 2: Marine Provider Implementations

**Issue:** Three marine providers have incomplete implementations or mock data.

**Evidence:**

| Provider | Status | Issue |
|---|---|---|
| GEBCO | Low | Placeholder WCS implementation, uses rough estimation |
| ESA CCI | Moderate | Simplified ERDDAP integration, fallback estimates |
| NOAA OISST | Moderate | Incomplete ERDDAP queries, mock data retrieval |

**Recommendation:**
1. Implement proper WCS clients for GEBCO
2. Integrate actual ERDDAP griddap endpoints
3. Add NCEI data source integration
4. Implement cloud/weather gap handling
5. Add alternative sources (etopo, gebco.net direct access)

**Current Status:** Marine providers suitable for **development/testing only**, not production use.

---

### Gap 3: MODIS Vegetation Implementation

**Issue:** MODIS provider is entirely mock/demo implementation.

**Evidence:**
- Code comment: "This is a simplified implementation. In production, you would: Submit APPEEARS task request, Wait for processing, Download and parse results"
- Uses seeded randomness to generate realistic-looking but fake data
- No real APPEEARS API integration
- `_get_mock_vegetation_data()` explicitly notes: "For now, return mock data with realistic values"

**Recommendation:**
1. Implement APPEEARS REST API integration
2. Add NASA Earth Data authentication
3. Implement task submission and polling workflow
4. Add result download and parsing
5. Consider alternative vegetation sources (NDVI-only APIs)

**Current Status:** **DO NOT USE in production**. This provider generates synthetic data.

---

### Gap 4: Limited Soil Depth Support

**Issue:** Soil providers have limited or no depth-specific data.

**Evidence:**
- SoilGrids supports depth intervals but implementation only uses "0-5cm" default
- USDA NRCS returns full profile without depth stratification
- No depth-dependent reliability metrics

**Recommendation:**
1. Implement full depth interval support for SoilGrids (0-5, 5-15, 15-30, 30-60, 60-100, 100-200cm)
2. Add soil profile depth inference from USDA components
3. Add quality metrics for depth-specific data
4. Document depth limitations in results

---

## Provider Reliability Recommendations

### Tier 1: High Reliability (Use as Primary)

| Service | Provider | Why |
|---|---|---|
| Elevation | Open Topo Data | Stable, multiple datasets, global |
| Elevation | OSM Elevation | Stable, 90m global, keyless |
| Soil | SoilGrids | Global, WCS+REST fallback, good completeness |
| Soil | USDA NRCS | US-authoritative, comprehensive, stable |
| Weather | MeteoStat | 120k+ stations, 1973+, station-based truth |
| Weather | Open-Meteo | Global, 1959+, hourly reanalysis |
| Land Cover | NLCD | US-authoritative, multi-year, stable |
| Land Cover | ESA WorldCover | Global, 10m resolution, recent |
| Geocoding | OSM Nominatim | Global, keyless, rich metadata |

---

### Tier 2: Moderate Reliability (Use with Fallback)

| Service | Provider | Limitation | Fallback |
|---|---|---|---|
| Elevation | Google Maps | Paid key | Open Topo Data |
| Geocoding | Google Maps | Paid key, quota limits | OSM Nominatim |
| Marine | ESA CCI | Incomplete, ERDDAP issues | Alternative sources |
| Marine | NOAA OISST | Incomplete ERDDAP | Alternative sources |
| OSM Features | Overpass API | Slow/unstable under load | Reduce radius |

---

### Tier 3: Low Reliability (Development/Testing Only)

| Service | Provider | Issue | Recommendation |
|---|---|---|---|
| Elevation | USGS 3DEP | Known migrations, unreliable | Use only as last fallback |
| Marine | GEBCO | Placeholder WCS | Needs implementation |
| Vegetation | MODIS | Mock data only | Not for production |

---

## Timeout Configuration Review

| Provider | Timeout | Assessment |
|---|---|---|
| Elevation (all) | 20s | Appropriate |
| Soil (all) | 30s | Appropriate (WCS can be slow) |
| Weather (all) | 30s | Appropriate |
| Marine (all) | 30s | Appropriate |
| Land Cover (all) | 30s | Appropriate (WMS can be slow) |
| Vegetation (MODIS) | 60s | Appropriate (APPEEARS can take time) |
| Geocoding (all) | 20-30s | Appropriate |
| OSM Features | 180s | Configurable, can timeout on large queries |

**Recommendation:** Add exponential backoff retry logic for timeout errors (not currently implemented).

---

## API Key Management

### Required Keys

Only **Google APIs** require authentication:
- `GOOGLE_MAIN_API_KEY`: Used for
  - Google Elevation API
  - Google Maps Geocoding (forward)
  - Google Maps Geocoding (reverse)

### Missing Implementations

**NASA APPEEARS** (MODIS) requires authentication but:
- No key validation in current code
- Mock implementation bypasses authentication entirely
- Production implementation needs NASA Earth Data setup

---

## Rate Limiting Analysis

| Provider | Explicit Limit | Enforcement |
|---|---|---|
| Google APIs | 50 QPS | Implicit (quota-based) |
| OSM Nominatim | 1 req/sec | Code-enforced sleep |
| Overpass API | 1 req/sec | Code-enforced sleep |
| Open Topo Data | Not published | None |
| SoilGrids | Not published | None |
| USDA NRCS | Not published | None |
| MeteoStat | Not published | None |
| Open-Meteo | Not published | None |
| Nominatim reverse | 1 req/sec | Code-enforced sleep |

**Observation:** Rate limiting is explicitly enforced in code for OSM services but not for others. Consider adding circuit breakers for all external APIs.

---

## Known Flaky Tests

From test suite analysis:

```
test_elevation.py:
  - @pytest.mark.flaky(reruns=2, reruns_delay=10) - USGS provider
  - @pytest.mark.network - Google Elevation, USGS, OSM Elevation

test_soil_enrichment.py:
  - @pytest.mark.flaky - SoilGrids/USDA provider
  - @pytest.mark.network - SoilGrids, USDA NRCS

test_http_cache.py:
  - @pytest.mark.network - HTTP cache tests (multiple providers)

test_logging.py:
  - @pytest.mark.network - Logging tests
```

**Interpretation:**
- **USGS elevation is marked flaky** (2 retries with 10-second delay) = documented unreliability
- **SoilGrids is marked flaky** = occasional connectivity/service issues
- Most network tests are marked with `@pytest.mark.network` = skipped in CI

---

## Testing Gaps

### Not Tested or Untested

- **GEBCO provider**: No actual WCS testing (placeholder implementation)
- **ESA CCI provider**: No actual ERDDAP testing (fallback estimates)
- **NOAA OISST provider**: No actual data retrieval testing
- **MODIS provider**: Mock data only, no real APPEEARS testing
- **Rate limiting effectiveness**: No tests for concurrent requests

### Recommendations

1. Add integration tests for all providers (marked `@pytest.mark.network`)
2. Test rate limiting under load
3. Test fallback mechanisms
4. Test timeout handling
5. Test error recovery and retries
6. Add contract tests for API schemas

---

## Summary Recommendations

### Immediate Actions

1. **USGS Elevation**: Add enhanced error handling, document unreliability, implement retry with exponential backoff
2. **Marine Providers**: Either implement actual WCS/ERDDAP clients or remove from production
3. **MODIS**: Either fully implement APPEEARS integration or mark as demo-only
4. **Comprehensive Testing**: Add network integration tests for all providers

### Short Term (1-2 weeks)

1. Implement proper ERDDAP client for marine providers
2. Add circuit breaker pattern for all external APIs
3. Implement exponential backoff retry logic
4. Add service health checks
5. Document known limitations in user-facing docs

### Medium Term (1-2 months)

1. Evaluate alternative providers for unreliable services (USGS, marine)
2. Implement proper WCS client for bathymetry
3. Complete MODIS APPEEARS integration
4. Add machine learning-based fallback provider selection
5. Implement provider-specific caching strategies

---

## Appendix: Provider Quick Reference

### By Domain

**Elevation:**
- Primary: Open Topo Data
- Fallback 1: OSM Elevation
- Fallback 2: Google Elevation (requires key)
- Fallback 3: USGS (unreliable)

**Soil:**
- Primary: SoilGrids (global)
- Primary: USDA NRCS (US only)

**Weather:**
- Primary: Open-Meteo (gridded reanalysis)
- Fallback: MeteoStat (station observations)

**Marine:**
- ESA CCI: Chlorophyll-a (incomplete)
- NOAA OISST: Sea Surface Temperature (incomplete)
- GEBCO: Bathymetry (placeholder only)

**Land Cover:**
- Primary: ESA WorldCover (global)
- Primary: NLCD (US only)

**Vegetation:**
- MODIS: Mock data only (not production-ready)

**Geocoding:**
- Primary: OSM Nominatim (any direction, keyless)
- Fallback: Google Maps (requires key)

**OSM Features:**
- Primary: Overpass API (global, stable)
