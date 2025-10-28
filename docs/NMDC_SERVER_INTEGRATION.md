# NMDC Server Integration Guide

## Overview

The biosample-enricher package is designed to provide environmental metadata suggestions to the [nmdc-server](https://github.com/microbiomedata/nmdc-server) metadata submission portal. This document explains how biosample-enricher outputs should be transformed to match NMDC submission schema expectations.

## Architecture

```
┌─────────────────────────┐
│  Submission Portal UI   │
│ (MetadataSuggester.vue) │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   nmdc-server API       │
│ /api/metadata_submission│
│      /suggest           │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ SampleMetadataSuggester │
│  (metadata.py:9)        │
│  - Slot suggester map   │
│  - Calls enrichers      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  biosample-enricher     │
│  - Enrichment services  │
│  - Output transformer   │
│  - NMDC schema mapping  │
└─────────────────────────┘
```

## nmdc-server Metadata Suggester

### Key Components

**Backend:**
- `nmdc_server/metadata.py:9` - `SampleMetadataSuggester` class
  - Line 49: `suggesters` dictionary maps slots → suggestion functions
  - Lines 55-59: Loops through suggesters to generate suggestions
- `nmdc_server/api.py:1642` - API endpoint `/api/metadata_submission/suggest`
  - Line 1648: Calls `suggester.get_suggestions()`

**Frontend:**
- `web/src/views/SubmissionPortal/Components/MetadataSuggester.vue`
  - Line 229: "Metadata Suggester" UI component
  - Line 239: Help text explaining functionality
- `web/src/views/SubmissionPortal/Components/HarmonizerSidebar.vue`
  - Line 68: Tab label "Metadata Suggester"
  - Line 138: `<MetadataSuggester>` component usage

**Tests:**
- `tests/test_metadata.py:4-32` - `test_sample_metadata_suggester_elevation()`
  - Example: Tests elevation suggestion logic

## Integration Points

### 1. Input Format (What nmdc-server sends to biosample-enricher)

The nmdc-server will send biosample records from the submission portal that need metadata suggestions. Expected input:

```json
{
  "sample_id": "nmdc:bsm-11-abc123",
  "latitude": 37.875,
  "longitude": -122.258,
  "collection_date": "2024-01-15",
  "env_broad_scale": null,
  "env_local_scale": null,
  "env_medium": null,
  "elev": null,
  "geo_loc_name": null,
  "ecosystem": null,
  "interface_type": "SoilInterface"
}
```

### 2. biosample-enricher Processing

biosample-enricher will:
1. Normalize input using `BiosampleLocation` model
2. Call relevant enrichment services (elevation, weather, soil, etc.)
3. **Transform outputs using NMDC submission schema mapping**
4. Return suggestions in slot-based format

### 3. Output Format (What biosample-enricher returns to nmdc-server)

**Option A: Slot-based suggestions (recommended for nmdc-server)**

```json
{
  "sample_id": "nmdc:bsm-11-abc123",
  "suggestions": {
    "elev": {
      "value": "3214.13",
      "confidence": 0.95,
      "provider": "USGS 3DEP",
      "source": "elevation_service",
      "units": "meters"
    },
    "geo_loc_name": {
      "value": "USA: Colorado, Boulder",
      "confidence": 0.90,
      "provider": "Google Geocoding",
      "source": "forward_geocoding_service"
    },
    "lat_lon": {
      "value": "37.87500000 -122.25800000",
      "confidence": 1.0,
      "provider": "user_input",
      "source": "normalized_input"
    },
    "annual_temp": {
      "value": "8.5",
      "confidence": 0.85,
      "provider": "Open-Meteo",
      "source": "weather_service",
      "units": "Celsius"
    },
    "ph": {
      "value": "6.2",
      "confidence": 0.70,
      "provider": "SoilGrids",
      "source": "soil_service",
      "units": "pH_scale"
    },
    "env_broad_scale": {
      "value": "forest biome [ENVO:01000174]",
      "confidence": 0.80,
      "provider": "geographic_features",
      "source": "predicted_from_location"
    }
  },
  "metadata": {
    "biosample_enricher_version": "0.1.0",
    "transformation_timestamp": "2024-10-27T12:00:00Z",
    "interface_type": "SoilInterface"
  }
}
```

**Option B: Full enrichment output (for advanced users)**

```json
{
  "sample_id": "nmdc:bsm-11-abc123",
  "input": { ... },
  "elevation": {
    "observations": [
      {
        "variable": "elevation",
        "value_numeric": 3214.134277344,
        "unit_ucum": "m",
        "provider": { "name": "usgs_3dep" },
        ...
      }
    ]
  },
  "weather": { ... },
  "soil": { ... },
  "forward_geocoding": { ... },
  "nmdc_submission_fields": {
    "elev": "3214.13",
    "geo_loc_name": "USA: Colorado, Boulder",
    "lat_lon": "37.87500000 -122.25800000",
    ...
  }
}
```

## Field Mapping Reference

See `config/nmdc_submission_schema_mapping.yaml` for complete mapping specification.

### Common Fields (All Interface Types)

| biosample-enricher source | NMDC field | Transform | Units |
|--------------------------|------------|-----------|-------|
| `input.latitude` + `input.longitude` | `lat_lon` | `format_lat_lon` | decimal degrees (8 decimal places) |
| `elevation.observations[0].value_numeric` | `elev` | `round_to_precision(2)` | meters |
| `forward_geocoding.location_name` | `geo_loc_name` | `format_geo_loc_name` | hierarchical string |
| `input.env_broad_scale` | `env_broad_scale` | `ensure_envo_term` | ENVO term with ID |
| `input.env_local_scale` | `env_local_scale` | `ensure_envo_term` | ENVO term with ID |
| `input.env_medium` | `env_medium` | `ensure_envo_term` | ENVO term with ID |

### SoilInterface-Specific Fields

| biosample-enricher source | NMDC field | Transform | Units |
|--------------------------|------------|-----------|-------|
| `soil.ph_h2o` | `ph` | `round_to_precision(2)` | pH scale (0-14) |
| `soil.organic_carbon` | `org_carb` | `round_to_precision(2)` | g/kg |
| `soil.total_nitrogen` | `org_nitro` | `round_to_precision(2)` | g/kg |
| `soil.texture_class` | `soil_type` | direct | USDA class name |
| `weather.temperature_annual_mean_c` | `annual_temp` | `round_to_precision(1)` | Celsius |
| `weather.precipitation_annual_sum_mm` | `annual_precpt` | `round_to_precision(0)` | mm |

### WaterInterface-Specific Fields

| biosample-enricher source | NMDC field | Transform | Units |
|--------------------------|------------|-----------|-------|
| `weather.temperature_c` | `temp` | `round_to_precision(2)` | Celsius |
| `marine.salinity_psu` | `salinity` | `round_to_precision(2)` | PSU |
| `marine.chlorophyll_a_mg_m3` | `chlorophyll` | `round_to_precision(3)` | mg/m³ |
| `marine.dissolved_oxygen_ml_l` | `diss_oxygen` | `round_to_precision(2)` | mL/L |
| `marine.bathymetry_m` | `depth` | `abs_round_to_precision(1)` | meters (positive) |

## Implementation Checklist

### Phase 1: Transformer Implementation
- [ ] Create `NMDCSubmissionTransformer` class
- [ ] Implement field mapping logic from YAML config
- [ ] Add transformation functions (format_lat_lon, round_to_precision, etc.)
- [ ] Handle interface type detection
- [ ] Add provenance metadata

### Phase 2: API Output Format
- [ ] Add `--format nmdc-submission` CLI option
- [ ] Implement slot-based suggestion format
- [ ] Add confidence scoring for each suggestion
- [ ] Include provider attribution
- [ ] Add validation for required fields

### Phase 3: nmdc-server Integration
- [ ] Create example integration code for nmdc-server
- [ ] Document API contract between systems
- [ ] Add integration tests
- [ ] Create sample request/response examples
- [ ] Update nmdc-server suggester to call biosample-enricher

### Phase 4: Testing
- [ ] Unit tests for transformer
- [ ] Integration tests with real biosample data
- [ ] Validate against NMDC submission schema
- [ ] Test all interface types (Soil, Water, Sediment, Air)
- [ ] Performance testing for batch suggestions

## Example Integration Code

### In nmdc-server (metadata.py)

```python
from biosample_enricher import BiosampleEnricher
from biosample_enricher.transformers import NMDCSubmissionTransformer

class SampleMetadataSuggester:
    def __init__(self):
        self.enricher = BiosampleEnricher()
        self.transformer = NMDCSubmissionTransformer()

        self.suggesters = {
            "elev": self._suggest_elevation,
            "geo_loc_name": self._suggest_geo_loc_name,
            "lat_lon": self._suggest_lat_lon,
            "annual_temp": self._suggest_annual_temp,
            "ph": self._suggest_ph,
            # ... more slots
        }

    def _suggest_elevation(self, biosample: dict) -> dict:
        """Suggest elevation from coordinates."""
        enrichment = self.enricher.enrich(
            latitude=biosample["latitude"],
            longitude=biosample["longitude"],
            services=["elevation"]
        )

        suggestions = self.transformer.to_nmdc_submission(
            enrichment,
            interface_type=biosample.get("interface_type")
        )

        return suggestions.get("elev")

    def get_suggestions(self, biosample: dict) -> dict:
        """Get all metadata suggestions for a biosample."""
        suggestions = {}
        for slot, suggester_fn in self.suggesters.items():
            if biosample.get(slot) is None:  # Only suggest if empty
                try:
                    suggestion = suggester_fn(biosample)
                    if suggestion:
                        suggestions[slot] = suggestion
                except Exception as e:
                    logger.error(f"Error suggesting {slot}: {e}")
        return suggestions
```

## Validation

### NMDC Submission Schema Validation

biosample-enricher should validate transformed outputs against the NMDC submission schema:

```python
from linkml_runtime.dumpers import json_dumper
from linkml_runtime.loaders import yaml_loader
from linkml.validators import validate

# Load NMDC submission schema
schema = yaml_loader.load(
    "https://raw.githubusercontent.com/microbiomedata/submission-schema/main/src/nmdc_submission_schema/schema/nmdc_submission_schema.yaml",
    target_class=SchemaDefinition
)

# Validate transformed output
validate(data=transformed_biosample, schema=schema, target_class="SoilInterface")
```

### Required Field Checks

Each interface type has required fields:

**All Interfaces:**
- `lat_lon`
- `geo_loc_name`
- `env_broad_scale`
- `env_local_scale`
- `env_medium`

**SoilInterface:**
- `elev`
- `ecosystem`

**WaterInterface:**
- `depth`

## Error Handling

### Graceful Degradation

- Missing data → `null` in output (don't fail entire suggestion)
- API failures → Log warning, return partial results
- Invalid coordinates → Skip enrichment, return validation error
- Transformation errors → Include error message in metadata

### Confidence Scoring

Suggestions should include confidence scores based on:
- **1.0**: User-provided input data (lat/lon from input)
- **0.9-1.0**: High-quality API data (USGS elevation, Google geocoding)
- **0.7-0.9**: Reliable predictions (SoilGrids, Open-Meteo)
- **0.5-0.7**: Inferred/predicted data (ecosystem from geographic features)
- **<0.5**: Low confidence (consider not suggesting)

## Performance Considerations

### Caching Strategy

biosample-enricher uses `requests-cache` with:
- Coordinate canonicalization (round to 4 decimal places)
- DateTime canonicalization (truncate to dates)
- SQLite backend with TTL

For nmdc-server integration:
- Share cache backend if possible
- Configure appropriate TTL for submission portal use case
- Consider Redis cache for distributed deployment

### Batch Processing

For bulk suggestions, use batch enrichment:

```python
# Efficient batch processing
enricher.enrich_batch(
    biosamples=[...],
    services=["elevation", "weather", "soil"],
    max_concurrent=10
)
```

## Security Considerations

### API Keys

biosample-enricher requires API keys for some services:
- `GOOGLE_MAIN_API_KEY`: Google Maps services (geocoding, places)
- Other services are keyless (USGS, Open-Meteo, SoilGrids)

nmdc-server should:
- Configure API keys via environment variables
- Handle rate limiting gracefully
- Monitor API usage/costs

### Data Privacy

- biosample-enricher does not store user data permanently
- HTTP cache is local/ephemeral
- Coordinate canonicalization provides some privacy protection
- Consider GDPR implications for EU samples

## Monitoring and Logging

### Metrics to Track

- Suggestion success rate per field
- API provider reliability
- Suggestion confidence distribution
- Processing time per biosample
- Cache hit rate

### Logging

biosample-enricher logs to structured JSON:
- Request parameters (lat/lon, date)
- Provider responses (success/failure)
- Transformation steps
- Errors and warnings

## Next Steps

1. **Implement Transformer**: Create `NMDCSubmissionTransformer` class
2. **Add CLI Support**: `biosample-enricher enrich --format nmdc-submission`
3. **Test Integration**: Work with nmdc-server team to test API contract
4. **Document Examples**: Add real-world biosample examples
5. **Performance Testing**: Validate batch processing performance
6. **Deploy**: Coordinate deployment with nmdc-server release

## References

- [NMDC Submission Schema](https://github.com/microbiomedata/submission-schema)
- [nmdc-server Repository](https://github.com/microbiomedata/nmdc-server)
- [MIxS Standards](https://www.gensc.org/mixs/)
- [ENVO Ontology](http://www.obofoundry.org/ontology/envo.html)
- [biosample-enricher Documentation](https://contextualizer-ai.github.io/biosample-enricher/)
