# Biosample Enricher

Infer AI-friendly environmental and geographic metadata about biosamples from multiple sources.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type--checked-mypy-blue.svg)](https://mypy-lang.org/)

## Overview

Biosample Enricher provides 8 specialized services for enriching biosample metadata with environmental and geographic information from authoritative data sources. Each service focuses on a specific domain (elevation, weather, soil, marine, land cover, geocoding, geographic features) and returns structured, type-safe data ready for analysis or AI applications.

## Features

- **8 Specialized Services**: Elevation, soil, weather, marine, land cover, forward/reverse geocoding, geographic features
- **Service-Based Architecture**: Independent services with focused responsibilities
- **Type Safety**: Full type hints with Pydantic validation and mypy checking
- **Smart Caching**: HTTP caching with coordinate canonicalization for efficiency
- **Multiple Providers**: Automatic fallback between data providers (USGS, Google, OSM, etc.)
- **Click-Based CLIs**: User-friendly command-line tools for each service
- **Flexible Installation**: Core services only, or add optional mongodb/metrics/schema extras

## Installation

### Prerequisites

- Python 3.11 or higher
- [UV package manager](https://github.com/astral-sh/uv) (recommended)

### Core Installation (Recommended)

Install with all 8 enrichment services but without evaluation/demo tools:

```bash
# From source (recommended for development)
git clone https://github.com/contextualizer-ai/biosample-enricher.git
cd biosample-enricher
uv sync
```

### Optional Extras

Add optional features as needed:

```bash
# MongoDB support (for fetching from NMDC/GOLD databases)
uv sync --extra mongodb

# Metrics and visualization tools
uv sync --extra metrics

# Schema analysis tools
uv sync --extra schema

# Everything
uv sync --extra all
```

## Quick Start

### Python API

The package exports 8 services from the top level:

```python
from biosample_enricher import (
    ElevationService,
    ElevationRequest,
    SoilService,
    WeatherService,
    MarineService,
    LandService,
    ReverseGeocodingService,
    ForwardGeocodingService,
    OSMFeaturesService,
)
from datetime import date

# Get elevation for a location
elevation_service = ElevationService()
request = ElevationRequest(latitude=40.7128, longitude=-74.0060)
observations = elevation_service.get_elevation(request)

for obs in observations:
    if obs.value_numeric is not None:
        print(f"{obs.provider.name}: {obs.value_numeric}m")
    # Output: usgs_3dep: 13.15m, google_elevation: 13.26m

# Get weather data for a location and date
weather_service = WeatherService()
weather_result = weather_service.get_daily_weather(
    lat=37.7749,
    lon=-122.4194,
    target_date=date(2024, 1, 15)
)
print(f"Temperature: {weather_result.temperature.value}°C")
print(f"Precipitation: {weather_result.precipitation.value}mm")

# Get soil properties
soil_service = SoilService()
soil_result = soil_service.enrich_location(
    latitude=40.7128,
    longitude=-74.0060,
    depth_cm="0-5cm"
)
print(f"Provider: {soil_result.provider}")
print(f"Quality score: {soil_result.quality_score}")

# Get marine data (SST, bathymetry, chlorophyll)
marine_service = MarineService()
marine_result = marine_service.get_comprehensive_marine_data(
    latitude=36.6,
    longitude=-121.9,
    target_date=date(2024, 1, 15)
)
if marine_result.sst:
    print(f"Sea surface temp: {marine_result.sst.value}°C")
if marine_result.bathymetry:
    print(f"Water depth: {marine_result.bathymetry.value}m")

# Reverse geocoding (coordinates -> place names)
geocoding_service = ReverseGeocodingService()
result = geocoding_service.reverse_geocode(lat=40.7128, lon=-74.0060)
if result:
    print(f"Location: {result.get_formatted_address()}")

# Get nearby geographic features
osm_service = OSMFeaturesService()
features = osm_service.get_features_for_location(
    latitude=37.7749,
    longitude=-122.4194,
    radius_m=1000
)
if features and features.named_features:
    for feature in features.named_features[:5]:
        print(f"{feature.name} ({feature.category}): {feature.distance_km:.2f}km")
```

### CLI Usage

Each service has its own CLI command:

```bash
# Elevation lookup
uv run elevation-lookup lookup --lat 40.7128 --lon -74.0060

# Soil data
uv run soil-enricher lookup --lat 40.7128 --lon -74.0060 --depth 10

# Weather data
uv run weather-enricher lookup --lat 37.7749 --lon -122.4194 --date 2024-01-15

# Marine data
uv run marine-enricher lookup --lat 36.6 --lon -121.9 --date 2024-01-15

# Land cover
uv run land-enricher lookup --lat 40.7128 --lon -74.0060

# Batch processing from CSV
uv run elevation-lookup batch --input samples.csv --lat-col latitude --lon-col longitude

# Version info
uv run biosample-version
```

## Services

### 1. Elevation Service

Get elevation data from multiple providers (USGS, Google, Open Topo Data).

**Providers**: USGS (US only, free), Google (global, requires API key), Open Topo Data (global, free)

**Python**:
```python
from biosample_enricher import ElevationService, ElevationRequest

service = ElevationService()
request = ElevationRequest(latitude=40.7128, longitude=-74.0060)
observations = service.get_elevation(request)
```

**CLI**:
```bash
uv run elevation-lookup lookup --lat 40.7128 --lon -74.0060
```

### 2. Soil Service

Get soil properties (texture, pH, organic carbon, etc.).

**Providers**: SoilGrids (global coverage), USDA NRCS (US only)

**Python**:
```python
from biosample_enricher import SoilService

service = SoilService()
soil_result = service.enrich_location(
    latitude=40.7128,
    longitude=-74.0060,
    depth_cm="0-5cm"
)
```

**CLI**:
```bash
uv run soil-enricher lookup --lat 40.7128 --lon -74.0060 --depth 10
```

### 3. Weather Service

Get historical weather data (temperature, precipitation, humidity, etc.).

**Providers**: Open-Meteo (free, global), Meteostat (free, global)

**Python**:
```python
from biosample_enricher import WeatherService
from datetime import date

service = WeatherService()
weather_result = service.get_daily_weather(
    lat=37.7749,
    lon=-122.4194,
    target_date=date(2024, 1, 15)
)
```

**CLI**:
```bash
uv run weather-enricher lookup --lat 37.7749 --lon -122.4194 --date 2024-01-15
```

### 4. Marine Service

Get marine data (sea surface temperature, bathymetry, chlorophyll).

**Providers**: NOAA OISST (SST), GEBCO (bathymetry), ESA CCI (chlorophyll)

**Python**:
```python
from biosample_enricher import MarineService
from datetime import date

service = MarineService()
marine_result = service.get_comprehensive_marine_data(
    latitude=36.6,
    longitude=-121.9,
    target_date=date(2024, 1, 15)
)
```

**CLI**:
```bash
uv run marine-enricher lookup --lat 36.6 --lon -121.9 --date 2024-01-15
```

### 5. Land Service

Get land cover classification.

**Providers**: ESA WorldCover, MODIS, NLCD (US only)

**Python**:
```python
from biosample_enricher import LandService

service = LandService()
land_result = service.enrich_location(
    latitude=40.7128,
    longitude=-74.0060
)
```

**CLI**:
```bash
uv run land-enricher lookup --lat 40.7128 --lon -74.0060
```

### 6. Reverse Geocoding Service

Convert coordinates to human-readable addresses.

**Providers**: OSM Nominatim (free), Google Geocoding (requires API key)

**Python**:
```python
from biosample_enricher import ReverseGeocodingService

service = ReverseGeocodingService()
result = service.reverse_geocode(lat=40.7128, lon=-74.0060)
if result:
    print(result.get_formatted_address())
```

### 7. Forward Geocoding Service

Convert addresses/place names to coordinates.

**Providers**: OSM Nominatim (free), Google Geocoding (requires API key)

**Python**:
```python
from biosample_enricher import ForwardGeocodingService

service = ForwardGeocodingService()
result = service.geocode("New York City")
if result and result.locations:
    for location in result.locations[:3]:
        print(f"{location.formatted_address}: {location.latitude}, {location.longitude}")
```

### 8. OSM Features Service

Get nearby geographic features (parks, water bodies, landmarks).

**Providers**: OpenStreetMap Overpass API (free), Google Places (requires API key)

**Python**:
```python
from biosample_enricher import OSMFeaturesService

service = OSMFeaturesService()
features = service.get_features_for_location(
    latitude=37.7749,
    longitude=-122.4194,
    radius_m=1000
)
if features and features.named_features:
    for feature in features.named_features[:5]:
        print(f"{feature.name} ({feature.category})")
```

## API Keys

Only required for Google services (optional - OSM alternatives available for everything):

```bash
# Single API key for all Google services
export GOOGLE_MAIN_API_KEY="your-key-here"
```

All other services are free and require no authentication.

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/contextualizer-ai/biosample-enricher.git
cd biosample-enricher

# Complete development setup
make dev-setup
```

### Testing

```bash
# Run fast tests (excludes network/slow tests)
make test-fast

# Run all tests with coverage
make test-cov

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests
```

### Code Quality

```bash
# Format, lint, type-check, test
make dev-check

# Full CI validation
make check-ci

# Individual checks
make format       # Format with ruff
make lint         # Lint with ruff
make type-check   # Type check with mypy
make dep-check    # Check dependencies with deptry
```

## Project Structure

```
biosample-enricher/
├── biosample_enricher/
│   ├── __init__.py           # Public API exports
│   ├── elevation/            # Elevation service
│   ├── soil/                 # Soil service
│   ├── weather/              # Weather service
│   ├── marine/               # Marine service
│   ├── land/                 # Land cover service
│   ├── reverse_geocoding/    # Reverse geocoding
│   ├── forward_geocoding/    # Forward geocoding
│   ├── osm_features/         # Geographic features
│   ├── models.py             # Core data models
│   ├── http_cache.py         # HTTP caching
│   └── cli*.py               # CLI commands
├── tests/                    # Test suite
├── pyproject.toml           # Project configuration
└── Makefile                 # Development automation
```

## Dependencies

### Core Dependencies
- **Always installed**: pandas, rasterio, meteostat (required for weather aggregation and global soil coverage)
- CLI and data validation: click, pydantic, requests, rich, pyyaml

### Optional Dependencies
- **mongodb**: `pymongo` for fetching from NMDC/GOLD databases (evaluation/demo only)
- **metrics**: `matplotlib`, `seaborn` for visualization
- **schema**: `genson` for schema analysis

Install with: `uv sync --extra mongodb` or `uv sync --extra all`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run checks (`make dev-check`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [UV](https://github.com/astral-sh/uv) for fast package management
- CLI powered by [Click](https://click.palletsprojects.com/)
- Data validation with [Pydantic](https://pydantic.dev/)
- Console output with [Rich](https://github.com/Textualize/rich)
- Caching with [requests-cache](https://github.com/requests-cache/requests-cache)

## Support

- **Issues**: [GitHub Issues](https://github.com/contextualizer-ai/biosample-enricher/issues)
- **Email**: info@contextualizer.ai
