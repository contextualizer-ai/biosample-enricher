# Provider Documentation

This document provides comprehensive information about all data providers available in the biosample-enricher package.

## Table of Contents

1. [Provider Overview](#provider-overview)
2. [Comparison by Domain](#comparison-by-domain)
   - [Elevation](#comparison-by-domain)
   - [Geocoding](#comparison-by-domain)
   - [Land](#comparison-by-domain)
   - [Marine](#comparison-by-domain)
   - [Soil](#comparison-by-domain)
   - [Weather](#comparison-by-domain)
3. [Detailed Provider Profiles](#detailed-provider-profiles)
   - [Google Elevation API](#google-elevation-api)
   - [Open Topo Data](#open-topo-data)
   - [OSM Elevation (open-elevation.com)](#osm-elevation-open-elevation.com)
   - [USGS 3DEP Elevation](#usgs-3dep-elevation)
   - [Google Geocoding (Forward)](#google-geocoding-forward)
   - [Google Reverse Geocoding](#google-reverse-geocoding)
   - [OSM Nominatim (Forward)](#osm-nominatim-forward)
   - [OSM Nominatim (Reverse)](#osm-nominatim-reverse)
   - [ESA WorldCover](#esa-worldcover)
   - [MODIS Vegetation Indices](#modis-vegetation-indices)
   - [USGS NLCD](#usgs-nlcd)
   - [ESA Ocean Colour CCI](#esa-ocean-colour-cci)
   - [GEBCO Bathymetry](#gebco-bathymetry)
   - [NOAA OISST](#noaa-oisst)
   - [ISRIC SoilGrids](#isric-soilgrids)
   - [USDA NRCS Web Soil Survey](#usda-nrcs-web-soil-survey)
   - [Meteostat](#meteostat)
   - [NASA POWER](#nasa-power)
   - [Open-Meteo](#open-meteo)

---

## Provider Overview

| Provider | Domain | Coverage | API Key | Cost | Stability |
|----------|--------|----------|---------|------|-----------|
| Google Elevation API | Elevation | Global | Required | paid | HIGH |
| Open Topo Data | Elevation | Global | No | free | HIGH |
| OSM Elevation (open-elevation.com) | Elevation | Global | No | free | HIGH |
| USGS 3DEP Elevation | Elevation | Global (best in USA) | No | free | LOW |
| Google Geocoding (Forward) | Geocoding | Global | Required | paid | HIGH |
| Google Reverse Geocoding | Geocoding | Global | Required | paid | HIGH |
| OSM Nominatim (Forward) | Geocoding | Global | No | free | HIGH |
| OSM Nominatim (Reverse) | Geocoding | Global | No | free | HIGH |
| ESA WorldCover | Land | Global | No | free | HIGH |
| MODIS Vegetation Indices | Land | Global | Required | free | LOW |
| USGS NLCD | Land | USA only | No | free | HIGH |
| ESA Ocean Colour CCI | Marine | Global oceans | No | free | MODERATE |
| GEBCO Bathymetry | Marine | Global oceans | No | free | MODERATE |
| NOAA OISST | Marine | Global oceans | No | free | MODERATE |
| ISRIC SoilGrids | Soil | Global | No | free | HIGH |
| USDA NRCS Web Soil Survey | Soil | USA only | No | free | HIGH |
| Meteostat | Weather | Global (120,000+ stations) | No | free | HIGH |
| NASA POWER | Weather | Global | No | free | HIGH |
| Open-Meteo | Weather | Global | No | free | HIGH |


## Comparison by Domain

### Elevation

| Provider | Resolution | Coverage | Data Quality | Best For |
|----------|------------|----------|--------------|----------|
| Google Elevation API | 30m (varies by region) | Global | ground_truth | Production systems with API budget |
| Open Topo Data | 250m-1km (dataset dependent) | Global | satellite | Development and testing |
| OSM Elevation (open-elevation.com) | 90m (SRTM-based) | Global | satellite | Free alternative with decent resolution |
| USGS 3DEP Elevation | 10-30m (varies by region) | Global (best in USA) | ground_truth | US locations when available |

### Geocoding

| Provider | Coverage | API Key | Cost | Best For |
|----------|----------|---------|------|----------|
| Google Geocoding (Forward) | Global | Required | paid | Production with budget |
| Google Reverse Geocoding | Global | Required | paid | Production with budget |
| OSM Nominatim (Forward) | Global | No | free | Free geocoding |
| OSM Nominatim (Reverse) | Global | No | free | Free reverse geocoding |

### Land

| Provider | Coverage | Resolution | Data Type | Best For |
|----------|----------|------------|-----------|----------|
| ESA WorldCover | Global | 10m | Sentinel-1 & Sentinel-2 | Global land cover classification |
| MODIS Vegetation Indices | Global | 250-500m | MODIS satellite | Future implementation |
| USGS NLCD | USA only | 30m | Landsat satellite classification | USA land cover classification |

### Marine

| Provider | Coverage | Resolution | Data Type | Best For |
|----------|----------|------------|-----------|----------|
| ESA Ocean Colour CCI | Global oceans | 1km | Satellite ocean color | Marine biogeochemistry when available |
| GEBCO Bathymetry | Global oceans | 15 arc-seconds (~450m) | Compiled bathymetric surveys | Ocean depth estimates when working |
| NOAA OISST | Global oceans | 0.25 degrees (~25km) | Optimally Interpolated SST | Sea surface temperature when available |

### Soil

| Provider | Coverage | Resolution | Depths | Best For |
|----------|----------|------------|--------|----------|
| ISRIC SoilGrids | Global | 250m | Multiple | Global soil property estimates |
| USDA NRCS Web Soil Survey | USA only | Polygon-based (variable) | Multiple | USA locations requiring high accuracy |

### Weather

| Provider | Resolution | Coverage | Data Quality | Best For |
|----------|------------|----------|--------------|----------|
| Meteostat | Station-based (point measurements) | Global (120,000+ stations) | ground_truth | Urban/suburban locations with dense station coverage |
| NASA POWER | 0.5° x 0.625° (~50-60km grid) | Global | satellite_reanalysis | Remote locations far from weather stations |
| Open-Meteo | 11km (ERA5-Land) | Global | satellite_reanalysis | Day-specific weather (collection date) |


# Detailed Provider Profiles

Below are comprehensive profiles for each provider, including technical specifications, reliability information, and use case recommendations.

---

## Google Elevation API

**Google Earth elevation database**

### Quick Facts

- **API Type**: REST
- **Endpoint**: https://maps.googleapis.com/maps/api/elevation/json
- **Authentication**: api_key_required
- **API Key**: `GOOGLE_MAIN_API_KEY`
- **Coverage**: Global
- **Resolution**: 30m (varies by region)

### Reliability

- **Stability**: HIGH
- **Data Quality**: ground_truth
- **Uptime**: Excellent (major provider)

### Cost

- **Pricing Model**: paid
- **Free Tier**: No free tier
- **Quotas**: Based on billing account

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Comprehensive global coverage | ✗ Requires paid API key (no free tier) |
| ✓ Accurate rooftop-level elevation data | ✗ Cost accumulates with high-volume use |
| ✓ Robust error handling with detailed status codes | ✗ Quota exhaustion possible (OVER_QUERY_LIMIT) |
| ✓ Well-documented API | ✗ No fallback mechanisms if quota exceeded |
| ✓ High reliability and uptime |  |

### Use Cases

**Best For:**
- Production systems with API budget
- High-accuracy requirements
- Urban/suburban locations

**Not Suitable For:**
- High-volume batch processing without budget
- Development/testing without API key

**Complements:**
- Open Topo Data (free fallback)
- USGS 3DEP (US-specific validation)

### NMDC Integration

- **Schema Slots**: elev
- **Role**: primary_if_key_available
- **Excellent For**: urban, suburban, developed_areas

**API Documentation**: https://maps.googleapis.com/maps/api/elevation/json

---

## Open Topo Data

**ASTER GDEM, SRTM, ETOPO1**

### Quick Facts

- **API Type**: REST
- **Endpoint**: https://api.opentopodata.org/v1/aster30m
- **Authentication**: none
- **Coverage**: Global
- **Resolution**: 250m-1km (dataset dependent)

### Reliability

- **Stability**: HIGH
- **Data Quality**: satellite
- **Uptime**: Good (community-maintained)

### Cost

- **Pricing Model**: free
- **Free Tier**: 1000 requests/day
- **Quotas**: 100/min, 1000/day

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Free access, no API key | ✗ Rate limited (100/min, 1000/day) |
| ✓ Global coverage | ✗ Coarser resolution than Google (250m-1km) |
| ✓ Multiple dataset options (ASTER, SRTM, ETOPO1) | ✗ Community-maintained (not enterprise SLA) |
| ✓ Stable service |  |
| ✓ Good documentation |  |

### Use Cases

**Best For:**
- Development and testing
- Batch processing within rate limits
- Budget-constrained projects

**Not Suitable For:**
- Very high-volume applications (>1000/day)
- Sub-100m precision requirements

**Complements:**
- Google Elevation (for higher accuracy)

### NMDC Integration

- **Schema Slots**: elev
- **Role**: primary_free_option
- **Excellent For**: global
- **Poor For**: requires_sub_100m_accuracy

**API Documentation**: https://api.opentopodata.org/v1/aster30m

---

## OSM Elevation (open-elevation.com)

**SRTM, ASTER GDEM**

### Quick Facts

- **API Type**: REST
- **Endpoint**: https://api.open-elevation.com/api/v1/lookup
- **Authentication**: none
- **Coverage**: Global
- **Resolution**: 90m (SRTM-based)

### Reliability

- **Stability**: HIGH
- **Data Quality**: satellite
- **Uptime**: Good

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited (fair use)
- **Quotas**: None documented

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Free, no API key | ✗ Less mature than other services |
| ✓ Global coverage | ✗ Limited documentation |
| ✓ 90m resolution (better than Open Topo Data) | ✗ Unknown reliability guarantees |
| ✓ No documented rate limits |  |

### Use Cases

**Best For:**
- Free alternative with decent resolution
- Development/testing

**Not Suitable For:**
- Production systems requiring SLA

**Complements:**
- Other free elevation providers

### NMDC Integration

- **Schema Slots**: elev
- **Role**: fallback_free_option
- **Excellent For**: global

**API Documentation**: https://api.open-elevation.com/api/v1/lookup

---

## USGS 3DEP Elevation

**3D Elevation Program**

### Quick Facts

- **API Type**: ArcGIS_REST
- **Endpoint**: https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/getSamples
- **Authentication**: none
- **Coverage**: Global (best in USA)
- **Resolution**: 10-30m (varies by region)

### Reliability

- **Stability**: LOW
- **Data Quality**: ground_truth
- **Uptime**: Unreliable - multiple migrations
- **Known Issues**:
  - Service has migrated multiple times (EPQS → 3DEP)
  - Endpoint URLs change without notice
  - No-data sentinel values (-1000000, -9999) complicate parsing
  - Intermittent availability

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited
- **Quotas**: None documented

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Free access, no API key required | ✗ ⚠️ KNOWN MIGRATION ISSUES - service frequently changes |
| ✓ High resolution data in USA (10m) | ✗ Unreliable availability |
| ✓ Proper vertical datum (NAVD88) | ✗ Complex no-data handling required |
| ✓ Government-maintained dataset | ✗ Endpoint may change without warning |
|  | ✗ Limited documentation on current API |

### Use Cases

**Best For:**
- US locations when available
- Development/testing (free)

**Not Suitable For:**
- Production systems requiring high reliability
- International locations (lower priority/quality)
- Time-critical applications

**Complements:**
- Should be used WITH fallback providers

### NMDC Integration

- **Schema Slots**: elev
- **Role**: fallback_with_caution
- **Excellent For**: usa_conus
- **Poor For**: international, oceans

**API Documentation**: https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/getSamples

---

## Google Geocoding (Forward)

**Google Maps database**

### Quick Facts

- **API Type**: REST
- **Endpoint**: https://maps.googleapis.com/maps/api/geocode/json
- **Authentication**: api_key_required
- **API Key**: `GOOGLE_MAIN_API_KEY`
- **Coverage**: Global
- **Resolution**: Address-level precision

### Reliability

- **Stability**: HIGH
- **Data Quality**: high
- **Uptime**: Excellent

### Cost

- **Pricing Model**: paid
- **Free Tier**: No
- **Quotas**: Based on billing

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ High accuracy | ✗ Requires paid API key |
| ✓ Global coverage | ✗ Cost per request |
| ✓ Excellent address parsing |  |
| ✓ Robust error handling |  |

### Use Cases

**Best For:**
- Production with budget
- High accuracy needs

**Not Suitable For:**
- High-volume without budget

**Complements:**
- OSM Nominatim (free fallback)

### NMDC Integration

- **Schema Slots**: lat_lon
- **Role**: primary_if_key_available
- **Excellent For**: global

**API Documentation**: https://maps.googleapis.com/maps/api/geocode/json

---

## Google Reverse Geocoding

**Google Maps database**

### Quick Facts

- **API Type**: REST
- **Endpoint**: https://maps.googleapis.com/maps/api/geocode/json
- **Authentication**: api_key_required
- **API Key**: `GOOGLE_MAIN_API_KEY`
- **Coverage**: Global
- **Resolution**: Address-level precision

### Reliability

- **Stability**: HIGH
- **Data Quality**: high
- **Uptime**: Excellent

### Cost

- **Pricing Model**: paid
- **Free Tier**: No
- **Quotas**: Based on billing

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ High accuracy | ✗ Requires paid API key |
| ✓ Detailed address components |  |
| ✓ Global coverage |  |

### Use Cases

**Best For:**
- Production with budget

**Not Suitable For:**
- High-volume without budget

**Complements:**
- OSM Nominatim

### NMDC Integration

- **Schema Slots**: geo_loc_name
- **Role**: primary_if_key_available
- **Excellent For**: global

**API Documentation**: https://maps.googleapis.com/maps/api/geocode/json

---

## OSM Nominatim (Forward)

**OpenStreetMap database**

### Quick Facts

- **API Type**: REST
- **Endpoint**: https://nominatim.openstreetmap.org/search
- **Authentication**: none
- **Coverage**: Global
- **Resolution**: Address-level precision

### Reliability

- **Stability**: HIGH
- **Data Quality**: community_maintained
- **Uptime**: Good
- **Known Issues**:
  - Rate limited to 1 request/second
  - Requires User-Agent header

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited (fair use)
- **Quotas**: 1 request/second

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Free access | ✗ Rate limited (1/second) |
| ✓ Global coverage | ✗ Variable accuracy |
| ✓ Community-maintained data | ✗ Requires User-Agent |

### Use Cases

**Best For:**
- Free geocoding
- Development/testing

**Not Suitable For:**
- High-volume batch (>1/second)

**Complements:**
- Google Geocoding

### NMDC Integration

- **Schema Slots**: lat_lon
- **Role**: primary_free_option
- **Excellent For**: global

**API Documentation**: https://nominatim.openstreetmap.org/search

---

## OSM Nominatim (Reverse)

**OpenStreetMap database**

### Quick Facts

- **API Type**: REST
- **Endpoint**: https://nominatim.openstreetmap.org/reverse
- **Authentication**: none
- **Coverage**: Global
- **Resolution**: Address-level precision

### Reliability

- **Stability**: HIGH
- **Data Quality**: community_maintained
- **Uptime**: Good
- **Known Issues**:
  - Rate limited to 1 request/second

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited (fair use)
- **Quotas**: 1 request/second

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Free access | ✗ Rate limited |
| ✓ Global coverage | ✗ Variable accuracy |

### Use Cases

**Best For:**
- Free reverse geocoding

**Not Suitable For:**
- High-volume batch

**Complements:**
- Google Reverse Geocoding

### NMDC Integration

- **Schema Slots**: geo_loc_name
- **Role**: primary_free_option
- **Excellent For**: global

**API Documentation**: https://nominatim.openstreetmap.org/reverse

---

## ESA WorldCover

**Sentinel-1 & Sentinel-2**

### Quick Facts

- **API Type**: WMS
- **Endpoint**: https://services.terrascope.be/wms/v2
- **Authentication**: none
- **Coverage**: Global
- **Resolution**: 10m
- **Temporal**: 2020, 2021

### Reliability

- **Stability**: HIGH
- **Data Quality**: satellite_classified
- **Uptime**: Good (ESA service)

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited
- **Quotas**: None documented

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Global coverage | ✗ Limited temporal coverage (only 2020, 2021) |
| ✓ High resolution (10m - best available) | ✗ Simplified classification scheme |
| ✓ Recent data (2020, 2021) |  |
| ✓ Free access |  |
| ✓ Sentinel satellite quality |  |

### Use Cases

**Best For:**
- Global land cover classification
- International locations
- Recent land cover needed

**Not Suitable For:**
- Historical land cover (pre-2020)
- Detailed US classification (use NLCD)

**Complements:**
- NLCD (for USA detail)

### NMDC Integration

- **Schema Slots**: cur_land_use
- **Role**: primary_global
- **Excellent For**: global, international

**API Documentation**: https://services.terrascope.be/wms/v2

---

## MODIS Vegetation Indices

**MODIS satellite**

### Quick Facts

- **API Type**: APPEEARS
- **Endpoint**: https://appeears.earthdatacloud.nasa.gov/api/
- **Authentication**: earthdata_login
- **Coverage**: Global
- **Resolution**: 250-500m
- **Temporal**: 2000-present

### Reliability

- **Stability**: LOW
- **Data Quality**: satellite
- **Uptime**: Unknown
- **Known Issues**:
  - ⚠️ MOCK IMPLEMENTATION ONLY
  - Not fully implemented
  - Requires NASA Earthdata authentication

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited (with NASA account)
- **Quotas**: Unknown

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Global NDVI/EVI data | ✗ ⚠️ NOT IMPLEMENTED - mock only |
| ✓ Long temporal coverage | ✗ Requires authentication setup |
| ✓ Free with NASA account | ✗ Complex API |

### Use Cases

**Best For:**
- Future implementation

**Not Suitable For:**
- Current use (not implemented)

**Complements:**
- N/A

### NMDC Integration

- **Schema Slots**: ndvi, evi
- **Role**: not_implemented

**API Documentation**: https://appeears.earthdatacloud.nasa.gov/api/

---

## USGS NLCD

**Landsat satellite classification**

### Quick Facts

- **API Type**: WMS
- **Endpoint**: https://www.mrlc.gov/geoserver/mrlc_display/NLCD_*/wms
- **Authentication**: none
- **Coverage**: USA only
- **Resolution**: 30m
- **Temporal**: Multiple years (2001, 2004, 2006, 2008, 2011, 2013, 2016, 2019)

### Reliability

- **Stability**: HIGH
- **Data Quality**: satellite_classified
- **Uptime**: Good (USGS service)

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ High resolution (30m) | ✗ USA only coverage |
| ✓ USA-specific classification scheme | ✗ Limited to available years |
| ✓ Multiple time periods |  |
| ✓ Free access |  |

### Use Cases

**Best For:**
- USA land cover classification
- Temporal land use change studies

**Not Suitable For:**
- International locations

**Complements:**
- ESA WorldCover (global)

### NMDC Integration

- **Schema Slots**: cur_land_use
- **Role**: primary_for_usa
- **Excellent For**: usa
- **Poor For**: international

**API Documentation**: https://www.mrlc.gov/geoserver/mrlc_display/NLCD_*/wms

---

## ESA Ocean Colour CCI

**Satellite ocean color**

### Quick Facts

- **API Type**: ERDDAP
- **Endpoint**: https://www.oceancolour.org/erddap/
- **Authentication**: none
- **Coverage**: Global oceans
- **Resolution**: 1km
- **Temporal**: 1997-present

### Reliability

- **Stability**: MODERATE
- **Data Quality**: satellite
- **Uptime**: Fair
- **Known Issues**:
  - ⚠️ Implementation incomplete
  - Complex ERDDAP API

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited
- **Quotas**: None documented

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Global ocean color data | ✗ ⚠️ Incomplete implementation |
| ✓ Long temporal coverage | ✗ Complex ERDDAP queries |
| ✓ Free access | ✗ Limited documentation |

### Use Cases

**Best For:**
- Marine biogeochemistry when available

**Not Suitable For:**
- Production use (incomplete)

**Complements:**
- Other marine providers

### NMDC Integration

- **Schema Slots**: chlorophyll
- **Role**: experimental
- **Excellent For**: oceans

**API Documentation**: https://www.oceancolour.org/erddap/

---

## GEBCO Bathymetry

**Compiled bathymetric surveys**

### Quick Facts

- **API Type**: WCS
- **Endpoint**: https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/
- **Authentication**: none
- **Coverage**: Global oceans
- **Resolution**: 15 arc-seconds (~450m)

### Reliability

- **Stability**: MODERATE
- **Data Quality**: survey_compilation
- **Uptime**: Fair
- **Known Issues**:
  - ⚠️ WCS implementation incomplete
  - Service reliability issues

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Global ocean coverage | ✗ ⚠️ Incomplete WCS implementation |
| ✓ High resolution (15 arc-seconds) | ✗ Service stability concerns |
| ✓ Free access | ✗ Limited error handling |

### Use Cases

**Best For:**
- Ocean depth estimates when working

**Not Suitable For:**
- Production systems requiring reliability

**Complements:**
- Other bathymetry providers needed

### NMDC Integration

- **Schema Slots**: depth
- **Role**: experimental
- **Excellent For**: oceans

**API Documentation**: https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/

---

## NOAA OISST

**Optimally Interpolated SST**

### Quick Facts

- **API Type**: ERDDAP
- **Endpoint**: https://coastwatch.pfeg.noaa.gov/erddap/
- **Authentication**: none
- **Coverage**: Global oceans
- **Resolution**: 0.25 degrees (~25km)
- **Temporal**: 1981-present

### Reliability

- **Stability**: MODERATE
- **Data Quality**: satellite_interpolated
- **Uptime**: Fair
- **Known Issues**:
  - ⚠️ Implementation incomplete

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited
- **Quotas**: None documented

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Global sea surface temperature | ✗ ⚠️ Incomplete implementation |
| ✓ Long temporal coverage | ✗ Coarse resolution (0.25°) |
| ✓ Free access |  |

### Use Cases

**Best For:**
- Sea surface temperature when available

**Not Suitable For:**
- Production use (incomplete)

**Complements:**
- Other SST providers

### NMDC Integration

- **Schema Slots**: temp, sst
- **Role**: experimental
- **Excellent For**: oceans

**API Documentation**: https://coastwatch.pfeg.noaa.gov/erddap/

---

## ISRIC SoilGrids

**Machine learning predictions from soil profiles**

### Quick Facts

- **API Type**: WCS_REST
- **Endpoint**: https://rest.isric.org/soilgrids/v2.0
- **Authentication**: none
- **Coverage**: Global
- **Resolution**: 250m

### Reliability

- **Stability**: HIGH
- **Data Quality**: modeled
- **Uptime**: Good (ISRIC institutional service)

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited
- **Quotas**: None documented

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ Global coverage at 250m resolution | ✗ Modeled data (not direct measurements) |
| ✓ Multiple soil properties (pH, texture, carbon, etc.) | ✗ Accuracy varies by region |
| ✓ Depth-specific layers | ✗ May not reflect recent land use changes |
| ✓ No API key required |  |
| ✓ Well-documented API |  |
| ✓ Regular updates |  |

### Use Cases

**Best For:**
- Global soil property estimates
- Locations without local soil surveys
- Comparative studies across regions

**Not Suitable For:**
- High-precision agriculture requiring ground truth
- Recent land disturbance areas

**Complements:**
- USDA NRCS (for US validation)

### NMDC Integration

- **Schema Slots**: ph, soil_text, org_matter, oc
- **Role**: primary_global
- **Excellent For**: global
- **Poor For**: recently_disturbed

**API Documentation**: https://rest.isric.org/soilgrids/v2.0

---

## USDA NRCS Web Soil Survey

**Ground surveys and lab measurements**

### Quick Facts

- **API Type**: SDA_REST
- **Endpoint**: https://sdmdataaccess.nrcs.usda.gov/Tabular/SDMTabularService/post.rest
- **Authentication**: none
- **Coverage**: USA only
- **Resolution**: Polygon-based (variable)

### Reliability

- **Stability**: HIGH
- **Data Quality**: ground_truth
- **Uptime**: Good (USDA service)

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited
- **Quotas**: None documented

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ High-quality ground truth data | ✗ USA only coverage |
| ✓ Lab-measured soil properties | ✗ Variable spatial resolution |
| ✓ Detailed soil classification | ✗ Complex API (SQL-based queries) |
| ✓ Free access |  |

### Use Cases

**Best For:**
- USA locations requiring high accuracy
- Agricultural research
- Ground truth validation

**Not Suitable For:**
- International locations

**Complements:**
- SoilGrids (global coverage)

### NMDC Integration

- **Schema Slots**: ph, soil_text, org_matter
- **Role**: primary_for_usa
- **Excellent For**: usa
- **Poor For**: international

**API Documentation**: https://sdmdataaccess.nrcs.usda.gov/Tabular/SDMTabularService/post.rest

---

## Meteostat

**WMO weather stations**

### Quick Facts

- **API Type**: Python_Library_CDN
- **Endpoint**: https://bulk.meteostat.net/v2/
- **Authentication**: none
- **Coverage**: Global (120,000+ stations)
- **Resolution**: Station-based (point measurements)
- **Temporal**: 1973-present (daily), 1991-2020 (normals)
- **Freshness**: 7-day lag

### Reliability

- **Stability**: HIGH
- **Data Quality**: ground_truth
- **Uptime**: Excellent (stable library)
- **Known Issues**:
  - Climate normals only available for WMO standard periods (1961-1990, 1971-2000, 1981-2010, 1991-2020)
  - Station coverage sparse in remote regions
  - Requires 10/12 months minimum for normals

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ 30-year WMO standard period (1991-2020) | ✗ Sparse coverage in remote regions (deserts, mountains, oceans) |
| ✓ Station-based ground truth measurements | ✗ Distance uncertainty (may use station 50-100km away) |
| ✓ No API key required | ✗ Only provides specific WMO standard periods |
| ✓ Extensive station network (120,000+) | ✗ Station availability varies by region |
| ✓ Distance tracking for quality assessment | ✗ Data gaps in some stations |
| ✓ Pre-computed normals for fast retrieval |  |
| ✓ High reliability |  |

### Use Cases

**Best For:**
- Urban/suburban locations with dense station coverage
- When WMO-standard 30-year normals required
- Scientific research requiring ground-based observations

**Not Suitable For:**
- Remote desert/mountain/ocean locations
- Custom time periods (not WMO standard)

**Complements:**
- NASA POWER (for remote area coverage)

### NMDC Integration

- **Schema Slots**: annual_precpt, annual_temp, temp, air_temp
- **Role**: primary_for_stations
- **Excellent For**: urban, suburban, europe, north_america, australia
- **Poor For**: deserts, mountains, oceans, remote_regions

**API Documentation**: https://bulk.meteostat.net/v2/

---

## NASA POWER

**MERRA-2 satellite reanalysis**

### Quick Facts

- **API Type**: REST
- **Endpoint**: https://power.larc.nasa.gov/api/temporal/climatology/point
- **Authentication**: none
- **Coverage**: Global
- **Resolution**: 0.5° x 0.625° (~50-60km grid)
- **Temporal**: 2001-2020 (climatologies)
- **Freshness**: Static climatologies

### Reliability

- **Stability**: HIGH
- **Data Quality**: satellite_reanalysis
- **Uptime**: Excellent (NASA operational service)
- **Known Issues**:
  - Only provides 2001-2020 period (not WMO standard 1991-2020)
  - Coarser spatial resolution than station data

### Cost

- **Pricing Model**: free
- **Free Tier**: Unlimited
- **Quotas**: None documented

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ True global coverage (satellite-based) | ✗ Shorter period (20 years: 2001-2020 vs standard 30 years) |
| ✓ No API key required | ✗ Coarser resolution (0.5° × 0.625° vs station point data) |
| ✓ Works anywhere on Earth (deserts, mountains, oceans) | ✗ Satellite bias in complex terrain |
| ✓ Consistent methodology globally | ✗ Not WMO standard period |
| ✓ High stability (NASA/GMAO service) | ✗ Model-based (not direct measurements) |
| ✓ Fast response (pre-computed) |  |

### Use Cases

**Best For:**
- Remote locations far from weather stations
- Ocean/marine samples
- Global-scale studies requiring consistent methodology
- Validation/comparison against station data

**Not Suitable For:**
- Urban areas with local station (prefer Meteostat)
- Studies requiring WMO standard 1991-2020 period

**Complements:**
- Meteostat (for station-rich areas)

### NMDC Integration

- **Schema Slots**: annual_precpt, annual_temp
- **Role**: fallback_for_remote_areas
- **Excellent For**: oceans, deserts, mountains, antarctica, remote_regions

**API Documentation**: https://power.larc.nasa.gov/api/temporal/climatology/point

---

## Open-Meteo

**ERA5/ERA5-Land reanalysis**

### Quick Facts

- **API Type**: REST
- **Endpoint**: https://archive-api.open-meteo.com/v1/era5
- **Authentication**: none
- **Coverage**: Global
- **Resolution**: 11km (ERA5-Land)
- **Temporal**: 1959-present (daily)
- **Freshness**: 5-day lag

### Reliability

- **Stability**: HIGH
- **Data Quality**: satellite_reanalysis
- **Uptime**: Good
- **Known Issues**:
  - Does not provide pre-computed climate normals
  - Would require 30-360 API calls to compute normals

### Cost

- **Pricing Model**: free
- **Free Tier**: 10,000 requests/day
- **Quotas**: 10,000/day

### Strengths & Weaknesses

| Strengths | Weaknesses |
|-----------|------------|
| ✓ ERA5 reanalysis (high quality) | ✗ Not used for climate normals (too many API calls) |
| ✓ 11km resolution (better than NASA POWER) | ✗ Rate limited (10,000/day) |
| ✓ No API key required | ✗ Hourly aggregation required for daily values |
| ✓ Long temporal coverage (1959-present) |  |
| ✓ Good for daily weather |  |

### Use Cases

**Best For:**
- Day-specific weather (collection date)
- Historical daily data

**Not Suitable For:**
- Climate normals (use Meteostat/NASA POWER)

**Complements:**
- Meteostat (for daily weather)

### NMDC Integration

- **Schema Slots**: temp, air_temp, humidity, wind_speed, wind_direction
- **Role**: fallback_daily_weather
- **Excellent For**: global

**API Documentation**: https://archive-api.open-meteo.com/v1/era5

---


---

*This documentation was automatically generated from `config/provider_metadata.yaml` by `scripts/generate_provider_docs.py`*
