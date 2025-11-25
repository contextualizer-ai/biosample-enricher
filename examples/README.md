# NMDC Submission Values Examples

Simple, copy-paste ready examples showing how to use `get_submission_values()` to populate NMDC submission-schema slots.

## Quick Start

All examples use the same simple pattern:

```python
from biosample_enricher.submission_values import get_submission_values

result = get_submission_values(
    lat=your_latitude,
    lon=your_longitude,
    slots=["slot_name_1", "slot_name_2"]
)

# Use the values
values = result["values"]
```

## Available Examples

### Basic Examples

| File | Description |
|------|-------------|
| `basic_climate.py` | Get annual precipitation and temperature (30-year averages) |
| `climate_with_elevation.py` | Mix climate and elevation data in one call |
| `error_handling.py` | Handle missing data and invalid inputs gracefully |

### Advanced Examples

| File | Description |
|------|-------------|
| `weather_with_datetime.py` | Get point-in-time weather data (requires datetime) |
| `consensus_strategies.py` | Compare different multi-provider consensus strategies |
| `provider_comparison.py` | Inspect individual provider results for data quality |

## Running Examples

### From command line:

```bash
# Basic examples
uv run python examples/basic_climate.py
uv run python examples/climate_with_elevation.py
uv run python examples/error_handling.py

# Advanced examples
uv run python examples/weather_with_datetime.py
uv run python examples/consensus_strategies.py
uv run python examples/provider_comparison.py
```

### Using the CLI instead:

```bash
# Equivalent to basic_climate.py
uv run biosample-enricher get --lat 37.7749 --lon -122.4194 --slots annual_precpt,annual_temp

# Equivalent to weather_with_datetime.py
uv run biosample-enricher get --lat 34.0522 --lon -118.2437 --slots temp --datetime 2023-07-15

# Using median consensus strategy
uv run biosample-enricher get --lat 46.8523 --lon -121.7603 --slots elev --strategy median
```

## Slots Quick Reference

| Category | Slots | Datetime Required? |
|----------|-------|-------------------|
| Climate | `annual_precpt`, `annual_temp` | No |
| Elevation | `elev` | No |
| Weather | `temp`, `air_temp`, `humidity`, `wind_speed`, `wind_direction`, `solar_irradiance` | **Yes** |
| Marine | `depth` | No |
| Soil | `ph`, `soil_type` | No |

## Need More Help?

- **Full documentation**: [NMDC Submission Values Guide](https://microbiomedata.github.io/biosample-enricher/submission_values.html)
- **CLI reference**: [CLI Documentation](https://microbiomedata.github.io/biosample-enricher/cli.html)
- **Issues?** [Report on GitHub](https://github.com/microbiomedata/biosample-enricher/issues)
