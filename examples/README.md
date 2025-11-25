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

- **`basic_climate.py`** - Get annual precipitation and temperature (30-year averages)
- **`climate_with_elevation.py`** - Mix climate and elevation data in one call
- **`error_handling.py`** - Handle missing data and invalid inputs gracefully

### Advanced Examples

- **`provider_comparison.py`** - Compare results from different data providers

## Running Examples

### From command line:
```bash
python examples/basic_climate.py
python examples/climate_with_elevation.py
```

### From Python:
```python
import examples.basic_climate
examples.basic_climate.main()
```

## Need More Help?

See the full documentation: [NMDC Submission Values Guide](https://contextualizer-ai.github.io/biosample-enricher/submission_values.html)

## Archived Examples

Previous examples showing MongoDB integration, adapters, and low-level service APIs have been moved to `archived/examples/`. See `archived/README.md` for details.
