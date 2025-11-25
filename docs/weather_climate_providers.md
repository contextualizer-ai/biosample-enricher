# Weather and Climate Provider Documentation

## Overview

The biosample-enricher weather service supports multiple weather and climate data providers for both **day-specific weather** (collection date conditions) and **climate normals** (long-term averages). Each provider has different strengths in terms of cost, coverage, temporal range, and data quality.

## Climate Normals Providers

Climate normals provide baseline environmental conditions over standard multi-year periods (typically 30 years), representing typical climate rather than day-to-day weather variability. Used for submission-schema slots: `annual_precpt`, `annual_temp`.

### Dynamic Period Calculation

The `get_climate_normals()` method uses a **dynamic period calculation** based on the current year:

```python
service.get_climate_normals(lat, lon, years_back=30)  # Default
```

- **Default behavior**: Requests 30 years back from current year
  - If current year is 2025: requests 1995-2025
  - If current year is 2030: requests 2000-2030
- **Customizable**: Can specify different period (e.g., `years_back=20` for 20 years)
- **Provider flexibility**: Each provider returns whatever period they actually have available
- **Transparency**: Response includes both requested and returned periods for each provider

**Important**: The requested period is a *goal*, not a guarantee. Providers will return the data they have:
- Meteostat always returns 1991-2020 (WMO standard, pre-computed)
- NASA POWER always returns 2001-2020 (satellite era, pre-computed)
- The metadata shows both what you requested and what each provider actually returned

### Provider Comparison Table

| Provider | Period | Resolution | Coverage | API Key | Cost | Stability | Best Use Case |
|----------|--------|------------|----------|---------|------|-----------|---------------|
| **Meteostat** | 1991-2020 (30yr) | Station-based | Global, 120k+ stations | ✗ None | Free | High | Station-rich regions, WMO standard |
| **NASA POWER** | 2001-2020 (20yr) | 0.5° × 0.625° grid | Global | ✗ None | Free | High | Remote areas, satellite validation |
| **Open-Meteo*** | 1991-2020 (computed) | 11km grid | Global | ✗ None | Free | High | Not implemented (requires 30yr download) |

\* Open-Meteo could provide climate normals by downloading and aggregating 30 years of daily data, but this is not currently implemented due to cost (360+ API calls per location).

---

## Detailed Provider Analysis

### 1. Meteostat (Recommended Primary)

**Endpoint**: Meteostat Python library + CDN
**Data Source**: WMO weather stations
**Climatology Period**: 1991-2020 (30-year WMO standard)

#### Strengths
- ✅ **Standard WMO period**: 30-year 1991-2020 normals (matches NOAA, Environment Canada standards)
- ✅ **Station-based ground truth**: Direct measurements, not modeled
- ✅ **No API key required**: Completely free
- ✅ **Extensive station network**: 120,000+ stations globally
- ✅ **High reliability**: Stable service, well-maintained library
- ✅ **Distance tracking**: Knows how far the nearest station is
- ✅ **Pre-computed normals**: Fast retrieval, no aggregation needed

#### Weaknesses
- ❌ **Station availability varies**: Sparse in remote regions (deserts, mountains, oceans)
- ❌ **Distance uncertainty**: Uses nearest station (may be 50-100km away in remote areas)
- ❌ **Data gaps**: Some stations lack complete monthly normals
- ❌ **Requires 10/12 months**: Won't return partial year data

#### Coverage Areas
- **Dense coverage**: Europe, North America, Australia, populated Asia
- **Moderate coverage**: South America, Africa, Middle East
- **Sparse coverage**: Deserts, high mountains, polar regions, open oceans

#### Data Quality
- **Temperature accuracy**: ±0.5°C (at station), degrades with distance
- **Precipitation accuracy**: ±10% (at station), higher uncertainty with distance
- **Quality penalty**: Applies distance-based quality reduction

#### Best Use Cases
- Biosamples collected near populated areas
- When WMO-standard 30-year normals required
- Scientific research requiring station-based observations
- When you know there's a weather station nearby

#### Example Usage
```python
from biosample_enricher.weather.service import WeatherService

service = WeatherService()

# Default: requests 30 years back from current year
normals = service.get_climate_normals(
    lat=40.7128,
    lon=-74.0060,
    providers=["meteostat"]  # Explicit selection
)

# Custom period: request 20 years back
normals = service.get_climate_normals(
    lat=40.7128,
    lon=-74.0060,
    years_back=20,  # e.g., 2005-2025 if current year is 2025
    providers=["meteostat"]
)

# Check what was actually returned
print(f"Requested: {normals.requested_start_year}-{normals.requested_end_year}")
print(f"Returned: {normals.providers['meteostat'].normals_period}")
print(f"Annual precipitation: {normals.get_consensus_precipitation()} mm/year")
```

---

### 2. NASA POWER (Recommended Secondary/Fallback)

**Endpoint**: `https://power.larc.nasa.gov/api/temporal/climatology/point`
**Data Source**: MERRA-2 satellite reanalysis (NASA/GMAO)
**Climatology Period**: 2001-2020 (20-year period)

#### Strengths
- ✅ **True global coverage**: Satellite-based, works anywhere on Earth
- ✅ **No API key required**: Free NASA public service
- ✅ **No distance uncertainty**: Gridded data, provides value for exact location
- ✅ **Works in remote areas**: Deserts, mountains, oceans all covered
- ✅ **High stability**: NASA/GMAO operational service
- ✅ **Consistent methodology**: Same satellite sensors globally
- ✅ **Fast response**: Pre-computed climatologies

#### Weaknesses
- ❌ **Shorter period**: 20-year (2001-2020) vs standard 30-year
- ❌ **Coarser resolution**: 0.5° × 0.625° (~50-60km at mid-latitudes)
- ❌ **Satellite bias**: May differ from ground truth in complex terrain
- ❌ **Not WMO standard**: Different period than standard climate normals
- ❌ **Model-based**: Reanalysis product, not direct measurements

#### Coverage Areas
- **Global**: 90°S to 90°N, 180°W to 180°E
- **Ocean coverage**: Excellent (unlike station-based data)
- **Remote regions**: Excellent (Antarctica, Sahara, Amazon, etc.)
- **Urban areas**: May differ from local station observations

#### Data Quality
- **Temperature accuracy**: ±1-2°C globally (varies by region)
- **Precipitation accuracy**: ±20-30% (satellite estimation uncertainty)
- **Resolution**: 0.5° latitude × 0.625° longitude

#### Best Use Cases
- Remote biosamples (far from weather stations)
- Ocean/marine samples
- Validation/comparison against station data
- When Meteostat has no nearby stations
- Global-scale studies requiring consistent methodology

#### Example Usage
```python
from biosample_enricher.weather.service import WeatherService

service = WeatherService()
normals = service.get_climate_normals(
    lat=-14.2350,  # Amazon rainforest (sparse stations)
    lon=-51.9253,
    providers=["nasa_power"]  # Force satellite data
)

# Always global coverage
print(f"Data source: {normals.providers['nasa_power'].provider}")  # nasa_power
print(f"Requested: {normals.requested_start_year}-{normals.requested_end_year}")
print(f"Returned: {normals.providers['nasa_power'].normals_period}")  # (2001, 2020)
```

---

### 3. Open-Meteo (Not Implemented for Climate Normals)

**Endpoint**: `https://archive-api.open-meteo.com/v1/archive`
**Data Source**: ERA5/ERA5-Land reanalysis
**Potential Period**: 1991-2020 (would need to compute from daily data)

#### Why Not Implemented

Open-Meteo provides **historical daily weather** back to 1940, but does **NOT** provide pre-computed climate normals. To get 1991-2020 normals, we would need to:

1. Download 30 years × 365 days ≈ **11,000 daily records per location**
2. Aggregate to monthly means
3. Compute 30-year averages

**Cost analysis:**
- Best case: 30 API calls (one per year, with monthly data)
- Realistic: 360 API calls (one per month)
- Worst case: 11,000 API calls (one per day)
- Inefficient compared to pre-computed normals

#### If Implemented, Strengths Would Be
- ✅ ERA5 reanalysis (higher quality than MERRA-2)
- ✅ 11km resolution (better than NASA POWER)
- ✅ No API key required
- ✅ Exact 1991-2020 period possible

#### Why Use NASA POWER Instead
- NASA POWER provides **pre-computed** climatologies (single API call)
- Open-Meteo requires **30-360 API calls** to compute same values
- NASA POWER is more efficient for climate normals use case

---

## Provider Selection Logic

The `WeatherService.get_climate_normals()` method uses intelligent provider routing:

### Default Order (when `providers=None`):
```python
["meteostat", "nasa_power"]
```

**Rationale:**
1. **Try Meteostat first**: Preferred for station-rich regions, WMO standard period
2. **Fallback to NASA POWER**: Handles remote areas where Meteostat has no stations

### When to Override Default

#### Force NASA POWER for:
```python
providers=["nasa_power"]
```
- Ocean/marine samples (no weather stations)
- Remote deserts, mountains, polar regions
- Validation studies comparing satellite vs station data
- When you need consistent global methodology

#### Force Meteostat for:
```python
providers=["meteostat"]
```
- Urban/suburban samples (dense station coverage)
- When WMO 30-year standard required
- When station-based measurements are required
- When you can tolerate "no data" for remote areas

#### Reverse Order (NASA POWER primary):
```python
providers=["nasa_power", "meteostat"]
```
- Global-scale studies where consistency matters more than period
- When you prefer satellite data quality

---

## Day-Specific Weather Providers

For **collection date** weather (submission-schema slots: `temp`, `air_temp`, `humidity`, `wind_speed`, `wind_direction`, `solar_irradiance`), the service uses:

### 1. Meteostat (Primary)
- Daily observations from weather stations
- 1973-present (7-day lag)
- High accuracy for station-rich regions

### 2. Open-Meteo (Secondary)
- ERA5 reanalysis gridded data
- 1959-present
- Global coverage, 11km resolution
- Better for remote areas

See `docs/PROVIDER_RELIABILITY_ANALYSIS.md` for detailed analysis.

---

## Validation and Quality Checking

### Using Multiple Providers for Validation

```python
# Get data from all providers (default behavior)
result = service.get_climate_normals(lat=37.7749, lon=-122.4194)

# Access individual provider results
if 'meteostat' in result.successful_providers:
    meteo_result = result.get_provider_result('meteostat')
    meteo_precip = meteo_result.get_annual_precipitation()
    print(f"Meteostat: {meteo_precip:.1f} mm/year ({meteo_result.normals_period})")

if 'nasa_power' in result.successful_providers:
    nasa_result = result.get_provider_result('nasa_power')
    nasa_precip = nasa_result.get_annual_precipitation()
    print(f"NASA POWER: {nasa_precip:.1f} mm/year ({nasa_result.normals_period})")

# Use consensus (average across providers)
consensus_precip = result.get_consensus_precipitation()
print(f"Consensus: {consensus_precip:.1f} mm/year")

# Check for large discrepancies
precip_range = result.get_value_ranges()['annual_precpt_range']
if precip_range:
    min_precip, max_precip = precip_range
    if max_precip - min_precip > 200:
        print(f"⚠️  Large discrepancy: {min_precip:.1f} vs {max_precip:.1f} mm/year")
```

### What Multiple Providers WILL Detect
- ✅ Provider outages (automatic fallback)
- ✅ Geographic coverage gaps
- ✅ Gross data errors (e.g., 50°C in Alaska)
- ✅ Satellite vs station measurement differences

### What Multiple Providers WON'T Detect
- ❌ Systematic biases affecting all providers
- ❌ Coordinate transformation bugs in our code
- ❌ Unit conversion errors in our code
- ❌ Location identification errors (querying wrong lat/lon)

---

## Cost and Rate Limit Summary

| Provider | API Key | Free Tier | Rate Limits | Notes |
|----------|---------|-----------|-------------|-------|
| **Meteostat** | None | Unlimited | None specified | Python library + CDN |
| **NASA POWER** | None | Unlimited | None specified | NASA public service |
| **Open-Meteo** | None | Unlimited daily weather | None for historical | Climatologies not pre-computed |

**All climate normal providers are completely free with no API keys required.**

---

## Geographic Coverage Heatmap

### Meteostat Station Density
- **Excellent**: Europe, USA, Japan, Australia
- **Good**: Canada, populated China/India, South America coasts
- **Fair**: Africa, Middle East, inland Asia
- **Poor**: Sahara, Amazon interior, Siberia, Antarctica, oceans

### NASA POWER Coverage
- **Uniform**: Global coverage everywhere (satellite-based)

### Recommendation Map

| Region Type | Recommended Provider | Reasoning |
|-------------|---------------------|-----------|
| Urban/suburban areas | Meteostat → NASA POWER | Dense stations, station preferred |
| Rural populated | Meteostat → NASA POWER | Moderate stations available |
| Remote terrestrial | NASA POWER → Meteostat | Sparse or no stations |
| Ocean/marine | NASA POWER only | No weather stations in ocean |
| Mountains > 3000m | NASA POWER preferred | Few high-altitude stations |
| Deserts | NASA POWER preferred | Sparse station coverage |
| Polar regions | NASA POWER preferred | Very limited stations |

---

## Best Practices

### For Scientific Research
1. **Document which provider was used** (returned in `ClimateNormalsResult.provider`)
2. **Check station distance** for Meteostat (`station_distance_km`)
3. **Compare both providers** when accuracy critical
4. **Note the time period** (1991-2020 vs 2001-2020)

### For Batch Processing
1. **Use default provider order** (Meteostat → NASA POWER)
2. **Implement caching** (both providers support HTTP caching)
3. **Handle partial failures gracefully** (some locations may have no data)

### For Real-time Applications
1. **Cache frequently accessed locations**
2. **Use provider selection based on location type**
3. **Implement reasonable timeouts** (30 seconds recommended)

---

## Troubleshooting

### "No climate data available from any provider"

**Meteostat fails if:**
- No weather stations within 100km
- Nearest station lacks monthly normals data
- Less than 10 months of data available

**NASA POWER fails if:**
- Network connectivity issues
- API temporarily unavailable (rare)
- Invalid coordinates (lat/lon out of range)

**Solution:** Check coordinates, try explicit `providers=["nasa_power"]`

### Large discrepancy between providers

**Possible causes:**
- **Station distance**: Meteostat using distant station (check `station_distance_km`)
- **Terrain complexity**: Mountains, coastlines (satellite vs station difference)
- **Local climate effects**: Urban heat islands, valley inversions
- **Time period difference**: 1991-2020 vs 2001-2020 (climate change signal)

**Solution:** Favor Meteostat for flat, populated areas; NASA POWER for complex terrain

---

## Environment Configuration

### Required Environment Variables
**None** - all climate normal providers are keyless

### Optional Configuration
- HTTP cache settings (see `biosample_enricher/http_cache.py`)
- Provider timeout settings (default: 30 seconds)
- Logging verbosity

---

## Future Enhancements

### Potential Additions
1. **WorldClim BIO variables**: If REST API becomes available
2. **PRISM (US only)**: High-resolution climate normals for USA
3. **CHELSA**: High-resolution global climatologies
4. **Open-Meteo computed normals**: If demand justifies API call cost

### Under Consideration
- **Provider consensus mode**: Average results from multiple providers
- **Uncertainty quantification**: Provide confidence intervals
- **WikiData validation**: Test against known city climate data

---

## Related Documentation

- `docs/PROVIDER_RELIABILITY_ANALYSIS.md` - Overall provider stability analysis
- `docs/elevation_providers.md` - Similar analysis for elevation providers
- `biosample_enricher/weather/service.py` - Implementation code
- `tests/test_environmental_metadata.py` - Usage examples in tests
