# Biosample Enricher

Get NMDC submission-schema values from geographic coordinates.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type--checked-mypy-blue.svg)](https://mypy-lang.org/)

## Overview

Biosample Enricher retrieves environmental metadata from authoritative data sources and returns it in the format needed for NMDC submissions. Give it GPS coordinates, get back submission-ready values with units and provenance.

## Features

- **Simple API**: One function - `get_environmental_metadata(lat, lon, slots)`
- **Multiple Data Sources**: Climate normals, elevation, weather, soil, marine data
- **Multi-Provider Consensus**: Queries multiple providers and returns consensus values
- **Type Safety**: Full type hints with Pydantic validation and mypy checking
- **Smart Caching**: HTTP caching with coordinate canonicalization for efficiency
- **CLI Tool**: Get values without writing code

## Installation

### Prerequisites

- Python 3.11 or higher
- [UV package manager](https://github.com/astral-sh/uv) (recommended)

### Add to Your Project

```bash
# Basic installation
uv add biosample-enricher

# Or with pip
pip install biosample-enricher

# Optional dependencies
uv add biosample-enricher --extra metrics   # Metrics and visualization
uv add biosample-enricher --extra mongodb   # MongoDB support for NMDC/GOLD
uv add biosample-enricher --extra all       # All optional features
```

### From Source (Development)

```bash
git clone https://github.com/contextualizer-ai/biosample-enricher.git
cd biosample-enricher
uv sync
```

## Quick Start

### Python API

```python
from biosample_enricher.environmental_metadata import get_environmental_metadata

# Get environmental metadata for a location
result = get_environmental_metadata(
    lat=37.7749,   # San Francisco
    lon=-122.4194,
    slots=["annual_precpt", "annual_temp", "elev"]
)

# Use the values in your NMDC submission
print(result["values"])
# {'annual_precpt': 519.3, 'annual_temp': 14.1, 'elev': 10.2}

# Check which data sources were used
print(result["metadata"]["climate_normals"]["providers_used"])
# ['meteostat', 'nasa_power']
```

### CLI Usage

```bash
# Get climate and elevation data
uv run biosample-enricher get \
    --lat 37.7749 \
    --lon -122.4194 \
    --slots annual_precpt,annual_temp,elev

# Get all supported slots
uv run biosample-enricher get --lat 37.7749 --lon -122.4194 --slots all

# Show available slots and providers
uv run biosample-enricher info

# List slot names (for scripting)
uv run biosample-enricher slots
```

## Supported Slots

| Category | Slots | Datetime Required? |
|----------|-------|-------------------|
| Climate | `annual_precpt`, `annual_temp` | No |
| Elevation | `elev` | No |
| Weather | `temp`, `air_temp`, `humidity`, `wind_speed`, `wind_direction`, `solar_irradiance` | Yes |
| Marine | `depth` | No |
| Soil | `ph`, `soil_type` | No |

**Production-ready slots**: `annual_precpt`, `annual_temp`, `elev`

See the [full documentation](https://contextualizer-ai.github.io/biosample-enricher/) for complete details.

## API Keys

Only required for Google services (optional - alternatives available):

```bash
export GOOGLE_MAIN_API_KEY="your-key-here"
```

All other services are free and require no authentication.

## Documentation

- [**get_environmental_metadata() Reference**](https://contextualizer-ai.github.io/biosample-enricher/environmental_metadata.html) - Main API documentation
- [Full Documentation](https://contextualizer-ai.github.io/biosample-enricher/)
- [CLI Reference](https://contextualizer-ai.github.io/biosample-enricher/cli.html)

## Development

```bash
# Clone and setup
git clone https://github.com/contextualizer-ai/biosample-enricher.git
cd biosample-enricher
make dev-setup

# Run tests
make test-fast

# Full CI validation
make check-ci
```

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/contextualizer-ai/biosample-enricher/issues)
- **Email**: info@contextualizer.ai
