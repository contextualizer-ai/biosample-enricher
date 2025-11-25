"""
Tests for submission-schema value retrieval (Issue #191).

These tests demonstrate how to get NMDC submission-schema compliant values
for various environmental slots using the get_submission_values() function.
"""

from datetime import datetime

import pytest

from biosample_enricher.submission_values import get_submission_values


def _get_values(*args, **kwargs):
    """Helper to extract values from new structure for backward compat in tests."""
    result = get_submission_values(*args, **kwargs)
    return result["values"]


@pytest.mark.network
def test_get_annual_climate_values():
    """
    Test retrieving annual climate values (annual_precpt, annual_temp).

    These values come from 30-year climate normals and don't require a datetime.
    """
    values = _get_values(
        lat=37.7749,  # San Francisco
        lon=-122.4194,
        slots=["annual_precpt", "annual_temp"],
    )

    # Should get both values
    assert "annual_precpt" in values
    assert "annual_temp" in values

    # annual_precpt should be a float in millimeters
    assert isinstance(values["annual_precpt"], float)
    assert 400 < values["annual_precpt"] < 700  # SF gets ~450-550mm/year

    # annual_temp should be a float in degrees Celsius
    assert isinstance(values["annual_temp"], float)
    assert 13 < values["annual_temp"] < 16  # SF averages ~14-15°C

    print("\nSan Francisco climate (1991-2020):")
    print(f"  annual_precpt: {values['annual_precpt']:.1f} mm/year")
    print(f"  annual_temp: {values['annual_temp']:.1f} °C")


@pytest.mark.network
def test_get_daily_temperature():
    """
    Test retrieving temperature at time of sampling.

    Requires a datetime for collection date.
    """
    values = _get_values(
        lat=37.7749,  # San Francisco
        lon=-122.4194,
        slots=["temp"],
        datetime_obj=datetime(2023, 7, 15),  # July 15, 2023
    )

    # Should get temperature value
    assert "temp" in values

    # temp should be a float in degrees Celsius
    assert isinstance(values["temp"], float)
    assert -50 < values["temp"] < 50  # Reasonable temperature range

    print("\nSan Francisco temperature on 2023-07-15:")
    print(f"  temp: {values['temp']:.1f} °C")


@pytest.mark.network
def test_get_elevation():
    """
    Test retrieving elevation for a location.
    """
    values = _get_values(
        lat=37.7749,  # San Francisco
        lon=-122.4194,
        slots=["elev"],
    )

    # Should get elevation value
    assert "elev" in values

    # elev should be a float in meters
    assert isinstance(values["elev"], float)
    assert 0 < values["elev"] < 200  # SF is near sea level but hilly

    print("\nSan Francisco elevation:")
    print(f"  elev: {values['elev']:.1f} m")


@pytest.mark.network
def test_get_multiple_slots():
    """
    Test retrieving multiple slots in a single call.

    Demonstrates mixing annual climate data with location data.
    """
    values = _get_values(
        lat=40.7128,  # New York City
        lon=-74.0060,
        slots=["annual_precpt", "annual_temp", "elev"],
    )

    # Should get all three values
    assert "annual_precpt" in values
    assert "annual_temp" in values
    assert "elev" in values

    # Verify types
    assert isinstance(values["annual_precpt"], float)
    assert isinstance(values["annual_temp"], float)
    assert isinstance(values["elev"], float)

    # Verify NYC climate ranges
    assert 1000 < values["annual_precpt"] < 1400  # NYC gets ~1100-1200mm/year
    assert 10 < values["annual_temp"] < 15  # NYC averages ~12-13°C
    assert 0 < values["elev"] < 100  # NYC is near sea level

    print("\nNew York City:")
    print(f"  annual_precpt: {values['annual_precpt']:.1f} mm/year")
    print(f"  annual_temp: {values['annual_temp']:.1f} °C")
    print(f"  elev: {values['elev']:.1f} m")


@pytest.mark.network
def test_get_daily_and_annual_together():
    """
    Test getting both annual climate normals and day-specific weather.

    When datetime is provided, we can get both types of data.
    """
    values = _get_values(
        lat=33.4484,  # Phoenix, AZ
        lon=-112.0740,
        slots=["annual_precpt", "annual_temp", "temp"],
        datetime_obj=datetime(2023, 7, 15),
    )

    # Should get all three values
    assert "annual_precpt" in values
    assert "annual_temp" in values
    assert "temp" in values

    # Phoenix climate checks
    assert 150 < values["annual_precpt"] < 300  # Phoenix is very dry
    assert 20 < values["annual_temp"] < 25  # Phoenix is hot

    # Day-specific temp should be even hotter in July
    assert values["temp"] > values["annual_temp"]

    print("\nPhoenix climate and weather:")
    print(f"  annual_precpt: {values['annual_precpt']:.1f} mm/year (30-year avg)")
    print(f"  annual_temp: {values['annual_temp']:.1f} °C (30-year avg)")
    print(f"  temp: {values['temp']:.1f} °C (2023-07-15)")


@pytest.mark.network
def test_missing_datetime_for_daily_weather():
    """
    Test that requesting daily weather without datetime doesn't fail.

    Should log a warning and omit the day-specific slots.
    """
    values = _get_values(
        lat=37.7749,
        lon=-122.4194,
        slots=["annual_precpt", "temp"],  # temp needs datetime but it's not provided
    )

    # Should still get annual_precpt
    assert "annual_precpt" in values

    # temp should be missing since no datetime provided
    assert "temp" not in values

    print("\nWithout datetime (only annual values retrieved):")
    print(f"  annual_precpt: {values['annual_precpt']:.1f} mm/year")
    print("  temp: not retrieved (datetime required)")


@pytest.mark.network
def test_get_soil_ph():
    """
    Test retrieving soil pH for a location.
    """
    values = _get_values(
        lat=40.7128,  # New York
        lon=-74.0060,
        slots=["ph"],
    )

    # Should get pH value (if soil data available for this location)
    if "ph" in values:
        # ph should be a float between 0-14
        assert isinstance(values["ph"], float)
        assert 0 <= values["ph"] <= 14

        print("\nNew York soil pH:")
        print(f"  ph: {values['ph']:.1f}")
    else:
        print("\nSoil pH not available for this location")


@pytest.mark.network
def test_get_marine_depth():
    """
    Test retrieving water depth for a marine location.
    """
    values = _get_values(
        lat=36.7783,  # Monterey Bay, CA (ocean)
        lon=-121.8479,
        slots=["depth"],
    )

    # Should get depth value for ocean location
    if "depth" in values:
        # depth should be a string with units
        assert isinstance(values["depth"], str)
        assert "m" in values["depth"]

        print("\nMonterey Bay depth:")
        print(f"  depth: {values['depth']}")
    else:
        print("\nDepth not available for this location")


@pytest.mark.network
def test_comprehensive_biosample_enrichment():
    """
    Comprehensive test showing how to enrich a biosample with multiple slots.

    This demonstrates the typical use case for NMDC submission portal.
    """
    # Simulated biosample with location and collection date
    biosample = {
        "id": "nmdc:bsm-12-abc123",
        "name": "Golden Gate Park soil sample",
        "lat_lon": {"latitude": 37.7694, "longitude": -122.4862},
        "collection_date": "2023-08-20T14:30:00Z",
    }

    # Extract coordinates and datetime
    lat = biosample["lat_lon"]["latitude"]
    lon = biosample["lat_lon"]["longitude"]
    collection_dt = datetime.fromisoformat(
        biosample["collection_date"].replace("Z", "+00:00")
    )

    # Request multiple environmental slots
    values = _get_values(
        lat=lat,
        lon=lon,
        slots=[
            "annual_precpt",  # 30-year climate
            "annual_temp",  # 30-year climate
            "temp",  # Day-specific
            "elev",  # Location
            "ph",  # Soil
        ],
        datetime_obj=collection_dt,
    )

    # Should get most values (some might fail gracefully)
    assert len(values) >= 3  # At least annual climate + elevation

    print(f"\nBiosample enrichment for {biosample['name']}:")
    print(f"  Location: ({lat}, {lon})")
    print(f"  Collection date: {biosample['collection_date']}")
    print("\nEnriched values:")
    for slot, value in sorted(values.items()):
        if isinstance(value, float):
            print(f"  {slot}: {value:.2f}")
        else:
            print(f"  {slot}: {value}")


def test_invalid_latitude():
    """Test that invalid latitude raises ValueError."""
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        get_submission_values(lat=91.0, lon=-122.0, slots=["elev"])


def test_invalid_longitude():
    """Test that invalid longitude raises ValueError."""
    with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
        get_submission_values(lat=37.0, lon=181.0, slots=["elev"])


def test_empty_slots_list():
    """Test that empty slots list raises ValueError."""
    with pytest.raises(ValueError, match="slots list cannot be empty"):
        get_submission_values(lat=37.0, lon=-122.0, slots=[])


def test_unsupported_slot():
    """Test that unsupported slot name raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported slot"):
        get_submission_values(lat=37.0, lon=-122.0, slots=["invalid_slot_name"])


def test_mixed_supported_and_unsupported_slots():
    """Test that mixing valid and invalid slots raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported slot"):
        get_submission_values(
            lat=37.0, lon=-122.0, slots=["annual_precpt", "invalid_slot", "elev"]
        )


@pytest.mark.network
def test_all_weather_slots():
    """
    Test requesting all weather-related slots at once.

    Demonstrates that the function efficiently fetches data in bulk.
    """
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

    # Should get annual climate values
    assert "annual_precpt" in values
    assert "annual_temp" in values

    # May or may not get all daily weather depending on provider availability
    # But should get at least some
    assert len(values) >= 2

    print("\nSeattle weather data:")
    for slot, value in sorted(values.items()):
        print(f"  {slot}: {value}")


@pytest.mark.network
def test_different_geographic_locations():
    """
    Test that the function works across different geographic locations.

    This verifies global coverage.
    """
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

        # Should get at least one value for each location
        assert len(values) >= 1

        print(f"\n{location['name']}: {len(values)} slots retrieved")
        if "annual_precpt" in values:
            print(f"  annual_precpt: {values['annual_precpt']:.1f} mm/year")
        if "elev" in values:
            print(f"  elev: {values['elev']:.1f} m")


@pytest.mark.network
def test_partial_success_handling():
    """
    Test that the function handles partial success gracefully.

    If some slots fail, others should still be returned.
    """
    # Request a mix of slots - some might fail
    values = _get_values(
        lat=37.7749,
        lon=-122.4194,
        slots=[
            "annual_precpt",  # Should succeed
            "elev",  # Should succeed
            "flooding",  # Not yet implemented
            "cur_vegetation",  # Not yet implemented
        ],
    )

    # Should get the implemented slots even if others fail
    assert "annual_precpt" in values
    assert "elev" in values

    # Unimplemented slots should be omitted (not None)
    assert "flooding" not in values
    assert "cur_vegetation" not in values

    print("\nPartial success test:")
    print(f"  Retrieved: {list(values.keys())}")
    print("  Omitted: flooding, cur_vegetation (not yet implemented)")
