# Integration with NMDC Server Metadata Suggester

This document describes how biosample-enricher (https://github.com/contextualizer-ai/biosample-enricher) can integrate with the metadata suggester in the NMDC Submission Portal (https://github.com/microbiomedata/nmdc-server).

## Background

The NMDC Submission Portal includes a **metadata suggester** feature that automatically proposes values for biosample metadata slots based on available information. Currently, the suggester supports elevation lookups using the `nmdc_geoloc_tools` package, which queries the Google Maps Elevation API.

Biosample Enricher extends this capability by providing access to **multiple data providers** for a wider range of environmental and geographic metadata, including:

- **Climate data**: Annual precipitation (`annual_precpt`), annual temperature (`annual_temp`)
- **Elevation data**: Ground elevation (`elev`) from multiple providers (USGS, Google, Open Topo Data, OSM)
- **Weather data**: Temperature, humidity, wind speed at collection time
- **Soil data**: pH, soil type
- **Marine data**: Water depth (bathymetry)

## Current NMDC Server Suggester

The current metadata suggester in `nmdc_server/metadata.py` provides:

```python
class SampleMetadataSuggester:
    """A class to suggest sample metadata values based on partial sample metadata."""

    @staticmethod
    def suggest_elevation_from_lat_lon(sample: Dict[str, str]) -> Optional[str]:
        """Suggest an elevation for a sample based on its lat_lon."""
        # Uses nmdc_geoloc_tools with Google Maps API
        elev = nmdc_geoloc_tools.elevation((lat, lon), settings.google_map_api_key)
        return f"{elev:.2f}"

    def get_suggestions(self, sample: Dict[str, str], ...) -> Dict[str, str]:
        """Suggest metadata values for a sample."""
        suggesters: dict[str, list[Callable[...]]] = {
            "elev": [self.suggest_elevation_from_lat_lon],
        }
        # ... returns suggestions dict
```

The suggester is invoked from the Submission Portal UI (`web/src/views/SubmissionPortal/Components/MetadataSuggester.vue`) when users enter sample coordinates.

## Proposed Integration

Biosample Enricher can enhance the metadata suggester by:

1. **Replacing single-provider elevation** with multi-provider consensus
2. **Adding new suggestion types** for climate, weather, soil, and marine data
3. **Providing provenance metadata** showing which data sources contributed

### Integration Options

#### Option A: Direct Python Import

Install biosample-enricher as a dependency of nmdc-server:

```python
# In nmdc_server/metadata.py
from biosample_enricher.environmental_metadata import get_environmental_metadata

class SampleMetadataSuggester:

    def suggest_values_from_lat_lon(
        self, sample: Dict[str, str], slots: list[str]
    ) -> Dict[str, str]:
        """Suggest values using biosample-enricher multi-provider system."""
        lat_lon = sample.get("lat_lon")
        if not lat_lon:
            return {}

        lat_lon_split = re.split("[, ]+", lat_lon)
        if len(lat_lon_split) != 2:
            return {}

        try:
            lat, lon = map(float, lat_lon_split)
            result = get_environmental_metadata(lat=lat, lon=lon, slots=slots)
            return {k: str(v) for k, v in result["values"].items()}
        except (ValueError, Exception):
            return {}

    def get_suggestions(self, sample: Dict[str, str], ...) -> Dict[str, str]:
        suggesters = {
            "elev": [lambda s: self.suggest_values_from_lat_lon(s, ["elev"]).get("elev")],
            "annual_precpt": [lambda s: self.suggest_values_from_lat_lon(s, ["annual_precpt"]).get("annual_precpt")],
            "annual_temp": [lambda s: self.suggest_values_from_lat_lon(s, ["annual_temp"]).get("annual_temp")],
        }
        # ... rest of implementation
```

#### Option B: REST API Service

Deploy biosample-enricher as a standalone service and call it from nmdc-server:

```python
import httpx

class SampleMetadataSuggester:
    ENRICHER_URL = "https://enricher.microbiomedata.org/api/v1/submission-values"

    def suggest_values_from_enricher(
        self, sample: Dict[str, str], slots: list[str]
    ) -> Dict[str, str]:
        """Call biosample-enricher API for suggestions."""
        lat_lon = sample.get("lat_lon")
        if not lat_lon:
            return {}

        lat_lon_split = re.split("[, ]+", lat_lon)
        try:
            lat, lon = map(float, lat_lon_split)
            response = httpx.post(
                self.ENRICHER_URL,
                json={"lat": lat, "lon": lon, "slots": slots},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json().get("values", {})
        except Exception:
            return {}
```

## Slots Roadmap

The following table maps NMDC submission-schema slots to biosample-enricher support status:

| Slot | Schema Link | Status | Notes |
|------|-------------|--------|-------|
| `elev` | [elevation](https://microbiomedata.github.io/submission-schema/elev/) | Ready | Multi-provider with USGS, Google, Open Topo Data, OSM |
| `annual_precpt` | [annual_precpt](https://microbiomedata.github.io/submission-schema/annual_precpt/) | Ready | 30-year climate normals from Meteostat + NASA POWER |
| `annual_temp` | [annual_temp](https://microbiomedata.github.io/submission-schema/annual_temp/) | Ready | 30-year climate normals from Meteostat + NASA POWER |
| `temp` | [temp](https://microbiomedata.github.io/submission-schema/temp/) | Partial | Requires collection datetime; uses Open-Meteo + Meteostat |
| `ph` | [ph](https://microbiomedata.github.io/submission-schema/ph/) | Partial | SoilGrids provider has intermittent issues (Issue #184) |
| `depth` | [depth](https://microbiomedata.github.io/submission-schema/depth/) | Partial | Marine bathymetry only; GEBCO reliability issues (Issue #181) |
| `cur_vegetation` | [cur_vegetation](https://microbiomedata.github.io/submission-schema/cur_vegetation/) | Planned | Issue #194: Land cover to vegetation text mapping |
| `flooding` | [flooding](https://microbiomedata.github.io/submission-schema/flooding/) | Planned | Issue #192: Research flood history data sources |
| `slope_aspect` | [slope_aspect](https://microbiomedata.github.io/submission-schema/slope_aspect/) | Planned | Listed in Suggester Tool Super-Issue #1441 |
| `slope_gradient` | [slope_gradient](https://microbiomedata.github.io/submission-schema/slope_gradient/) | Planned | Listed in Suggester Tool Super-Issue #1441 |

See [microbiomedata/issues#1441](https://github.com/microbiomedata/issues/issues/1441) for the complete list of slots proposed for the suggester.

## Relevant Issues and Discussions

### In microbiomedata/issues:

- [#1441: Suggester Tool Super-Issue](https://github.com/microbiomedata/issues/issues/1441) - Master issue tracking slots to add: annual_precpt, annual_temp, cur_vegetation, slope_aspect, slope_gradient, flooding

### In microbiomedata/nmdc-server:

- [#1542: Highlight metadata suggester tab](https://github.com/microbiomedata/nmdc-server/issues/1542) - UI enhancement for when suggestions are available

### In contextualizer-ai/biosample-enricher:

- [#192: Research and implement flooding data support](https://github.com/contextualizer-ai/biosample-enricher/issues/192)
- [#193: Add submission-schema extraction helpers](https://github.com/contextualizer-ai/biosample-enricher/issues/193)
- [#194: Map land cover data to cur_vegetation text values](https://github.com/contextualizer-ai/biosample-enricher/issues/194)
- [#189: Implement NMDC Submission Schema Transformer](https://github.com/contextualizer-ai/biosample-enricher/issues/189)

## Meeting Notes and Slack Discussions

Key discussions about this integration:

### BBOP Slack (2025-10-20):

> "Justin and I would like to meet with you and other interested BBOP-NMDCers about adapting https://github.com/contextualizer-ai/biosample-enricher/ for the NMDC Submission Portal metadata suggester at 12:15 PDT this Wednesday the 22nd." - Mark Miller

### NMDC-Group Slack (2025-10-13):

> "Chris Mungall has been encouraging us to think about which bits of that code can be used to propose values for which nmdc-schema fields, so that it can be plugged into Patrick K's metadata suggester for the submission portal" - Mark Miller

### NMDC-Group Slack (2025-11-21) - Olivia Hess feedback:

> - "If you want this to be used by different projects, try not to get too in the weeds of making a function per slot - that would be NMDC's job. You want to be able to develop a framework that any project can easily access the weather, soil, flooding, etc data that they need easier with your package than reaching out to the API"
> - "For example - you can get daily, monthly, or yearly wind data in xyz units from lat lon inputs"

### Chris & Mark Rolling Notes (Google Doc):

- 2025-11-21: "Biosample enricher emit BERtron like structures"
- 2025-09-26: "Mungall's Biosample-ingester => 'biosample-enricher'" - "Publish biosample enricher output to NMDC NERSC www"
- 2025-08-22: "Alpha version of Pydantic AI assessment... Look forward to handing off to metadata suggester"
- 2025-08-04: "Factor out some crawl first into the NMDC submission metadata suggester"

### Patrick Kalita (BBOP Slack 2025-10-13):

> "If the functionality is available via HTTP requests to a server you manage or via an installable Python package those both seem like decent ways forward. Now, if you did deploy a server with an API layer on top of biosample-enricher are you going to be a free, open proxy to the Google Maps Elevation API? Because that would be awesome."

## Integration Checklist

To integrate biosample-enricher with nmdc-server:

- [ ] Decide on integration approach (direct import vs. API service)
- [ ] Add biosample-enricher as dependency to nmdc-server (if direct import)
- [ ] Extend `SampleMetadataSuggester` class with new suggestion methods
- [ ] Update `MetadataSuggester.vue` to display new slot suggestions
- [ ] Add UI indicators when suggestions are available (#1542)
- [ ] Test with sample biosamples from various environmental contexts
- [ ] Document API key requirements (Google Maps API key shared between systems)
- [ ] Consider caching strategy for repeated coordinate lookups

### API Key Considerations

Biosample-enricher uses the same `GOOGLE_MAIN_API_KEY` environment variable for Google services. For keyless operation, biosample-enricher can fall back to:

- **Elevation**: USGS (US only), Open Topo Data, OSM
- **Climate**: Meteostat, NASA POWER (both keyless)
- **Weather**: Open-Meteo, Meteostat (both keyless)
- **Soil**: SoilGrids (keyless)

## Example Usage in Suggester Context

Here's how a submission portal workflow might use biosample-enricher:

```python
from biosample_enricher.environmental_metadata import get_environmental_metadata
from datetime import datetime

def suggest_metadata_for_sample(sample: dict) -> dict:
    """
    Generate metadata suggestions for a biosample submission.

    Args:
        sample: Dict with at least 'lat_lon' and optionally 'collection_date'

    Returns:
        Dict of {slot_name: suggested_value} for display in suggester UI
    """
    suggestions = {}

    # Parse coordinates
    lat_lon = sample.get("lat_lon", "")
    parts = lat_lon.replace(",", " ").split()
    if len(parts) != 2:
        return suggestions

    try:
        lat, lon = float(parts[0]), float(parts[1])
    except ValueError:
        return suggestions

    # Determine which slots to suggest based on environmental package
    env_package = sample.get("env_package", {}).get("has_raw_value", "soil")

    if env_package == "soil":
        slots = ["elev", "annual_precpt", "annual_temp", "ph", "soil_type"]
    elif env_package == "water":
        slots = ["elev", "annual_precpt", "annual_temp", "depth"]
    elif env_package == "sediment":
        slots = ["elev", "annual_precpt", "annual_temp", "depth"]
    else:
        slots = ["elev", "annual_precpt", "annual_temp"]

    # Parse collection date if available (for weather data)
    datetime_obj = None
    collection_date = sample.get("collection_date", {}).get("has_raw_value")
    if collection_date:
        try:
            datetime_obj = datetime.fromisoformat(collection_date.replace("Z", "+00:00"))
            slots.extend(["temp", "humidity"])
        except ValueError:
            pass

    # Get suggestions
    try:
        result = get_environmental_metadata(
            lat=lat,
            lon=lon,
            slots=slots,
            datetime_obj=datetime_obj
        )

        # Convert to string format expected by submission portal
        for slot, value in result["values"].items():
            if value is not None:
                suggestions[slot] = str(value)

    except Exception as e:
        # Log error but don't fail - suggestions are optional
        logger.warning(f"Failed to get suggestions: {e}")

    return suggestions
```

## Related Projects

- [contextualizer-ai/env-embeddings](https://github.com/contextualizer-ai/env-embeddings) - Predicts MIxS environmental context triad (env_broad_scale, env_local_scale, env_medium) using satellite image embeddings from Google Earth Engine

- [microbiomedata/nmdc-geoloc-tools](https://github.com/microbiomedata/nmdc-geoloc-tools) - Current elevation lookup used by nmdc-server (single Google Maps provider)

- [microbiomedata/submission-schema](https://github.com/microbiomedata/submission-schema) - LinkML schema defining all biosample metadata slots

- [microbiomedata/nmdc-schema](https://github.com/microbiomedata/nmdc-schema) - Core NMDC data model schema

## Contact and Collaboration

For questions about this integration:

- **biosample-enricher**: Mark Miller (@mamillerpa), Justin Reese (@justaddcoffee)
- **nmdc-server suggester**: Patrick Kalita (@pkalita), Olivia Hess (@olivia.hess)
- **NMDC schema/metadata**: Chris Mungall (@cjmungall), Montana Smith (@montana.smith)
