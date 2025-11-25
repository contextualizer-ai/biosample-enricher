"""
Tests for environmental metadata retrieval (Issue #191).

These tests demonstrate how to get environmental metadata
for various slots using the get_environmental_metadata() function.
"""

import logging
from datetime import datetime

import pytest

from biosample_enricher.environmental_metadata import get_environmental_metadata

logger = logging.getLogger(__name__)


def _get_values(*args, **kwargs):
    """Helper to extract values from new structure for backward compat in tests."""
    result = get_environmental_metadata(*args, **kwargs)
    return result["values"]


@pytest.mark.network
def test_get_annual_climate_values():
    """Test retrieving annual climate values (annual_precpt, annual_temp)."""
    values = _get_values(
        lat=37.7749,  # San Francisco
        lon=-122.4194,
        slots=["annual_precpt", "annual_temp"],
    )

    assert "annual_precpt" in values, "annual_precpt should be returned"
    assert "annual_temp" in values, "annual_temp should be returned"

    # annual_precpt should be a float in millimeters
    assert isinstance(values["annual_precpt"], float), "annual_precpt should be float"
    assert 400 < values["annual_precpt"] < 700, (
        f"SF annual_precpt={values['annual_precpt']:.1f}mm outside expected [400,700]"
    )

    # annual_temp should be a float in degrees Celsius
    assert isinstance(values["annual_temp"], float), "annual_temp should be float"
    assert 13 < values["annual_temp"] < 16, (
        f"SF annual_temp={values['annual_temp']:.1f}°C outside expected [13,16]"
    )

    logger.info(
        "San Francisco climate: annual_precpt=%.1f mm/year, annual_temp=%.1f °C",
        values["annual_precpt"],
        values["annual_temp"],
    )


@pytest.mark.network
def test_get_climate_with_strategy():
    """Test that strategy parameter works for climate slots."""
    # Get climate with different strategies
    result_mean = get_environmental_metadata(
        lat=37.7749,  # San Francisco
        lon=-122.4194,
        slots=["annual_precpt", "annual_temp"],
        strategy="mean",
    )
    result_median = get_environmental_metadata(
        lat=37.7749,
        lon=-122.4194,
        slots=["annual_precpt", "annual_temp"],
        strategy="median",
    )

    # Both should return values
    assert "annual_precpt" in result_mean["values"], "mean should return annual_precpt"
    assert "annual_precpt" in result_median["values"], (
        "median should return annual_precpt"
    )

    # Metadata should reflect the strategy used
    assert result_mean["metadata"]["climate_normals"]["consensus_strategy"] == "mean"
    assert (
        result_median["metadata"]["climate_normals"]["consensus_strategy"] == "median"
    )

    logger.info(
        "Climate with mean: %.1f mm, with median: %.1f mm",
        result_mean["values"]["annual_precpt"],
        result_median["values"]["annual_precpt"],
    )


@pytest.mark.network
def test_get_daily_temperature():
    """Test retrieving temperature at time of sampling (requires datetime)."""
    values = _get_values(
        lat=37.7749,  # San Francisco
        lon=-122.4194,
        slots=["temp"],
        datetime_obj=datetime(2023, 7, 15),  # July 15, 2023
    )

    assert "temp" in values, "temp should be returned when datetime provided"
    assert isinstance(values["temp"], float), "temp should be float"
    assert -50 < values["temp"] < 50, (
        f"temp={values['temp']:.1f}°C outside reasonable range [-50,50]"
    )

    logger.info("San Francisco temp on 2023-07-15: %.1f °C", values["temp"])


@pytest.mark.network
def test_get_elevation():
    """Test retrieving elevation for a location."""
    values = _get_values(
        lat=37.7749,  # San Francisco
        lon=-122.4194,
        slots=["elev"],
    )

    assert "elev" in values, "elev should be returned"
    assert isinstance(values["elev"], float), "elev should be float"
    assert 0 < values["elev"] < 200, (
        f"SF elev={values['elev']:.1f}m outside expected [0,200]"
    )

    logger.info("San Francisco elevation: %.1f m", values["elev"])


@pytest.mark.network
def test_get_multiple_slots():
    """Test retrieving multiple slots in a single call."""
    values = _get_values(
        lat=40.7128,  # New York City
        lon=-74.0060,
        slots=["annual_precpt", "annual_temp", "elev"],
    )

    assert "annual_precpt" in values, "annual_precpt should be returned"
    assert "annual_temp" in values, "annual_temp should be returned"
    assert "elev" in values, "elev should be returned"

    assert isinstance(values["annual_precpt"], float), "annual_precpt should be float"
    assert isinstance(values["annual_temp"], float), "annual_temp should be float"
    assert isinstance(values["elev"], float), "elev should be float"

    # Verify NYC climate ranges
    assert 1000 < values["annual_precpt"] < 1400, (
        f"NYC annual_precpt={values['annual_precpt']:.1f}mm outside expected [1000,1400]"
    )
    assert 10 < values["annual_temp"] < 15, (
        f"NYC annual_temp={values['annual_temp']:.1f}°C outside expected [10,15]"
    )
    assert 0 < values["elev"] < 100, (
        f"NYC elev={values['elev']:.1f}m outside expected [0,100]"
    )

    logger.info(
        "NYC: annual_precpt=%.1f mm, annual_temp=%.1f °C, elev=%.1f m",
        values["annual_precpt"],
        values["annual_temp"],
        values["elev"],
    )


@pytest.mark.network
def test_get_daily_and_annual_together():
    """Test getting both annual climate normals and day-specific weather."""
    values = _get_values(
        lat=33.4484,  # Phoenix, AZ
        lon=-112.0740,
        slots=["annual_precpt", "annual_temp", "temp"],
        datetime_obj=datetime(2023, 7, 15),
    )

    assert "annual_precpt" in values, "annual_precpt should be returned"
    assert "annual_temp" in values, "annual_temp should be returned"
    assert "temp" in values, "temp should be returned when datetime provided"

    # Phoenix climate checks
    assert 150 < values["annual_precpt"] < 300, (
        f"Phoenix annual_precpt={values['annual_precpt']:.1f}mm outside expected [150,300]"
    )
    assert 20 < values["annual_temp"] < 25, (
        f"Phoenix annual_temp={values['annual_temp']:.1f}°C outside expected [20,25]"
    )

    # Day-specific temp should be even hotter in July
    assert values["temp"] > values["annual_temp"], (
        f"July temp ({values['temp']:.1f}°C) should exceed annual avg ({values['annual_temp']:.1f}°C)"
    )

    logger.info(
        "Phoenix: annual_precpt=%.1f mm, annual_temp=%.1f °C, July temp=%.1f °C",
        values["annual_precpt"],
        values["annual_temp"],
        values["temp"],
    )


@pytest.mark.network
def test_missing_datetime_for_daily_weather():
    """Test that requesting daily weather without datetime omits those slots."""
    values = _get_values(
        lat=37.7749,
        lon=-122.4194,
        slots=["annual_precpt", "temp"],  # temp needs datetime but it's not provided
    )

    assert "annual_precpt" in values, "annual_precpt should be returned"
    assert "temp" not in values, "temp should be omitted without datetime"

    logger.info(
        "Without datetime: annual_precpt=%.1f mm, temp omitted",
        values["annual_precpt"],
    )


@pytest.mark.network
def test_get_soil_ph():
    """Test retrieving soil pH for a location."""
    values = _get_values(
        lat=40.7128,  # New York
        lon=-74.0060,
        slots=["ph"],
    )

    # pH may or may not be available depending on provider
    if "ph" in values:
        assert isinstance(values["ph"], float), "ph should be float"
        assert 0 <= values["ph"] <= 14, (
            f"pH={values['ph']:.1f} outside valid range [0,14]"
        )
        logger.info("New York soil pH: %.1f", values["ph"])
    else:
        logger.info("Soil pH not available for this location")


@pytest.mark.network
def test_get_marine_depth():
    """Test retrieving water depth for a marine location."""
    values = _get_values(
        lat=36.7783,  # Monterey Bay, CA (ocean)
        lon=-121.8479,
        slots=["depth"],
    )

    # Depth may or may not be available depending on provider
    if "depth" in values:
        assert isinstance(values["depth"], str), "depth should be string with units"
        assert "m" in values["depth"], (
            f"depth should include 'm' unit: {values['depth']}"
        )
        logger.info("Monterey Bay depth: %s", values["depth"])
    else:
        logger.info("Depth not available for this location")


@pytest.mark.network
def test_comprehensive_biosample_enrichment():
    """Comprehensive test showing typical NMDC submission portal use case."""
    # Simulated biosample with location and collection date
    biosample = {
        "id": "nmdc:bsm-12-abc123",
        "name": "Golden Gate Park soil sample",
        "lat_lon": {"latitude": 37.7694, "longitude": -122.4862},
        "collection_date": "2023-08-20T14:30:00Z",
    }

    lat = biosample["lat_lon"]["latitude"]
    lon = biosample["lat_lon"]["longitude"]
    collection_dt = datetime.fromisoformat(
        biosample["collection_date"].replace("Z", "+00:00")
    )

    values = _get_values(
        lat=lat,
        lon=lon,
        slots=["annual_precpt", "annual_temp", "temp", "elev", "ph"],
        datetime_obj=collection_dt,
    )

    assert len(values) >= 3, (
        f"Should get at least 3 slots, got {len(values)}: {list(values.keys())}"
    )

    logger.info(
        "Biosample '%s' enriched with %d slots: %s",
        biosample["name"],
        len(values),
        list(values.keys()),
    )


@pytest.mark.unit
def test_invalid_latitude():
    """Test that invalid latitude raises ValueError."""
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        get_environmental_metadata(lat=91.0, lon=-122.0, slots=["elev"])


@pytest.mark.unit
def test_invalid_longitude():
    """Test that invalid longitude raises ValueError."""
    with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
        get_environmental_metadata(lat=37.0, lon=181.0, slots=["elev"])


@pytest.mark.unit
def test_empty_slots_list():
    """Test that empty slots list raises ValueError."""
    with pytest.raises(ValueError, match="slots list cannot be empty"):
        get_environmental_metadata(lat=37.0, lon=-122.0, slots=[])


@pytest.mark.unit
def test_unsupported_slot():
    """Test that unsupported slot name raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported slot"):
        get_environmental_metadata(lat=37.0, lon=-122.0, slots=["invalid_slot_name"])


@pytest.mark.unit
def test_mixed_supported_and_unsupported_slots():
    """Test that mixing valid and invalid slots raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported slot"):
        get_environmental_metadata(
            lat=37.0, lon=-122.0, slots=["annual_precpt", "invalid_slot", "elev"]
        )


@pytest.mark.network
def test_all_weather_slots():
    """Test requesting all weather-related slots at once."""
    values = _get_values(
        lat=47.6062,  # Seattle
        lon=-122.3321,
        slots=[
            "annual_precpt",
            "annual_temp",
            "temp",
            "air_temp",
            "humidity",
            "wind_speed",
            "wind_direction",
        ],
        datetime_obj=datetime(2023, 7, 15),
    )

    assert "annual_precpt" in values, "annual_precpt should be returned"
    assert "annual_temp" in values, "annual_temp should be returned"
    assert len(values) >= 2, f"Should get at least 2 slots, got {len(values)}"

    logger.info(
        "Seattle weather: %d slots retrieved: %s", len(values), list(values.keys())
    )


@pytest.mark.network
def test_different_geographic_locations():
    """Test that the function works across different geographic locations."""
    test_locations = [
        {"name": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503},
        {"name": "Sydney, Australia", "lat": -33.8688, "lon": 151.2093},
        {"name": "London, UK", "lat": 51.5074, "lon": -0.1278},
        {"name": "São Paulo, Brazil", "lat": -23.5505, "lon": -46.6333},
    ]

    for location in test_locations:
        values = _get_values(
            lat=location["lat"],
            lon=location["lon"],
            slots=["annual_precpt", "elev"],
        )

        assert len(values) >= 1, (
            f"{location['name']}: should get at least 1 slot, got {len(values)}"
        )

        logger.info(
            "%s: %d slots - %s",
            location["name"],
            len(values),
            {k: f"{v:.1f}" if isinstance(v, float) else v for k, v in values.items()},
        )


@pytest.mark.network
def test_partial_success_handling():
    """Test that partial provider failures don't crash the function."""
    values = _get_values(
        lat=37.7749,
        lon=-122.4194,
        slots=["annual_precpt", "annual_temp", "elev", "ph"],
    )

    # Climate and elevation should succeed (reliable providers)
    assert "annual_precpt" in values, "annual_precpt should succeed"
    assert "annual_temp" in values, "annual_temp should succeed"
    assert "elev" in values, "elev should succeed"

    # Soil pH may fail but should not crash
    if "ph" in values:
        assert isinstance(values["ph"], float), "ph should be float if present"

    logger.info("Partial success: retrieved %s", list(values.keys()))
