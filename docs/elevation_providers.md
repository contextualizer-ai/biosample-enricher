# Elevation Provider Documentation

## Overview

The biosample-enricher elevation service supports multiple elevation data providers, each with different strengths, weaknesses, and coverage areas. The service uses intelligent routing to select the most appropriate providers based on coordinate classification.

## Supported Providers

### 1. USGS EPQS (US Geological Survey Elevation Point Query Service)

**Endpoint**: `https://epqs.nationalmap.gov/v1/json`

**Strengths**:
- Highest accuracy for US territories (1-meter resolution)
- Authoritative government data source
- No API key required
- Fast response times for US locations
- Vertical datum: NAVD88 (North American Vertical Datum 1988)

**Weaknesses**:
- US territories only (CONUS, Alaska, Hawaii, Puerto Rico, US territories)
- No coverage outside US boundaries
- Limited to land areas (may return null for water bodies)

**Coverage Areas**:
- Continental United States (CONUS)
- Alaska
- Hawaii
- Puerto Rico
- Guam
- US Virgin Islands
- American Samoa
- Northern Mariana Islands

**Rate Limits**: None specified, but reasonable use expected

**Best Use Cases**:
- Biosamples collected within US territories
- High-precision elevation requirements
- Scientific research requiring authoritative data

---

### 2. Google Maps Elevation API

**Endpoint**: `https://maps.googleapis.com/maps/api/elevation/json`

**Strengths**:
- Global coverage
- High accuracy in most regions
- Reliable service with good uptime
- Well-documented API
- Consistent data quality

**Weaknesses**:
- Requires API key (`GOOGLE_MAIN_API_KEY` environment variable)
- Usage costs after free tier (512 requests/day free)
- Rate limits: 50 QPS for standard accounts
- Vertical datum varies by region

**Coverage Areas**:
- Worldwide coverage
- Higher resolution in populated areas
- Lower resolution in remote regions

**Rate Limits**: 50 queries per second (QPS) for standard accounts

**Best Use Cases**:
- International biosamples
- When high reliability is required
- Commercial applications with API budget

---

### 3. Open Topo Data

**Endpoint**: `https://api.opentopodata.org/v1/{dataset}`

**Strengths**:
- No API key required
- Multiple datasets available (SRTM 30m, SRTM 90m, ASTER 30m, EU-DEM 25m)
- Global coverage
- Free and open service
- Good documentation

**Weaknesses**:
- Variable data quality depending on dataset
- Rate limits: 100 requests per second, 1000 requests per day for anonymous use
- Vertical datum: EGM96 (Earth Gravitational Model 1996)
- No guaranteed uptime (community service)

**Coverage Areas**:
- SRTM 30m: Global coverage between 60°N and 56°S
- SRTM 90m: Global coverage between 60°N and 56°S
- ASTER 30m: Global coverage between 83°N and 83°S
- EU-DEM 25m: Europe only

**Rate Limits**: 100 requests/second, 1000 requests/day (anonymous)

**Best Use Cases**:
- High-volume batch processing
- Development and testing
- When API costs are a concern
- Research projects with flexible accuracy requirements

---

### 4. OpenElevation (OSM Elevation)

**Endpoint**: `https://api.open-elevation.com/api/v1/lookup`

**Strengths**:
- No API key required
- Free service
- Simple API interface
- Global coverage

**Weaknesses**:
- Lower resolution (90m SRTM data)
- Less reliable uptime
- Limited accuracy compared to other providers
- Vertical datum: EGM96
- No guaranteed service level

**Coverage Areas**:
- Global coverage using SRTM 90m data
- Lower accuracy in mountainous regions

**Rate Limits**: No official limits, but reasonable use expected

**Best Use Cases**:
- Quick prototyping
- Low-precision requirements
- Fallback option when other services fail

## Provider Selection Logic

The elevation service uses intelligent routing based on coordinate classification:

### For US Territory Coordinates:
1. **Primary**: USGS EPQS (highest accuracy, authoritative)
2. **Secondary**: Google Maps (reliable fallback)
3. **Tertiary**: Open Topo Data (free alternative)
4. **Fallback**: OpenElevation (last resort)

### For International Coordinates:
1. **Primary**: Google Maps (best global coverage and accuracy)
2. **Secondary**: Open Topo Data (free, good coverage)
3. **Tertiary**: OpenElevation (fallback)
4. **Not Used**: USGS EPQS (no coverage outside US)

### For Ocean Coordinates:
1. **Primary**: Google Maps (handles water bodies better)
2. **Secondary**: Open Topo Data (may return coastline elevation)
3. **Deprioritized**: USGS EPQS (limited water body support)
4. **Fallback**: OpenElevation

## Data Quality Considerations

### Vertical Datums
- **NAVD88** (USGS): Mean sea level datum for North America
- **EGM96** (Open Topo Data, OpenElevation): Global geoid model
- **Variable** (Google): Depends on region, often local mean sea level

### Resolution Comparison
- **USGS EPQS**: 1-3 meter resolution (varies by region)
- **Google Maps**: Variable (typically 1-30m depending on location)
- **Open Topo Data SRTM 30m**: 30-meter resolution
- **Open Topo Data SRTM 90m**: 90-meter resolution
- **OpenElevation**: 90-meter resolution

### Accuracy Estimates
- **USGS EPQS**: ±1-3 meters (US territories)
- **Google Maps**: ±1-10 meters (varies by region)
- **Open Topo Data**: ±10-30 meters (depends on dataset)
- **OpenElevation**: ±10-30 meters

## Best Practices

### For Scientific Research:
1. Use USGS EPQS for US biosamples when highest accuracy is required
2. Use Google Maps for international samples with accuracy requirements
3. Always specify vertical datum in results
4. Consider using multiple providers for validation

### For Batch Processing:
1. Use Open Topo Data for large datasets to avoid API costs
2. Implement caching to reduce redundant requests
3. Use appropriate batch sizes to respect rate limits
4. Handle failures gracefully with fallback providers

### For Real-time Applications:
1. Cache frequently accessed coordinates
2. Use provider routing based on coordinate classification
3. Implement timeout handling (30-60 seconds)
4. Consider pre-warming cache for known sample locations

## Environment Configuration

### Required Environment Variables:
- `GOOGLE_MAIN_API_KEY`: Required for Google Maps Elevation API access

### Optional Configuration:
- Cache settings in HTTP cache configuration
- Provider timeout settings
- Rate limiting parameters

## Error Handling

The service implements comprehensive error handling:
- **Network timeouts**: Automatic retry with exponential backoff
- **API errors**: Graceful degradation to next provider
- **Invalid coordinates**: Validation before API calls
- **Rate limit exceeded**: Automatic fallback to alternative providers
- **Service unavailable**: Skip to next provider in routing list

## Monitoring and Debugging

Each elevation observation includes full provenance:
- Provider name and endpoint
- API version
- Raw response payload with SHA256 hash
- Request/response timestamps
- Error messages if applicable
- Cache hit/miss status
