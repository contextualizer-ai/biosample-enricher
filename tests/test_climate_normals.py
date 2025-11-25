"""
Tests for climate normals functionality (Issue #191).

Demonstrates how to get annual precipitation averages for a lat/lon,
following Olivia's feedback about general-purpose design (Issue #199)
and submission-schema extraction (Issue #193).
"""

import pytest

from biosample_enricher.weather.providers.meteostat import MeteostatProvider
from biosample_enricher.weather.service import WeatherService


@pytest.mark.network
def test_get_annual_precipitation_for_location():
    """
    Demonstrate getting annual precipitation average for a latitude and longitude.

    This test shows the recommended pattern for Issue #191 (annual_precpt support):
    1. Use general-purpose get_climate_normals() method (Issue #199 guidance)
    2. Extract submission-schema values using to_submission_schema() (Issue #193)
    3. Or get specific values using helper methods

    Example location: San Francisco, CA
    """
    # Initialize service
    service = WeatherService()

    # Get climate normals for San Francisco
    lat, lon = 37.7749, -122.4194

    normals = service.get_climate_normals(lat, lon)

    # Verify we got valid data (now returns MultiProviderClimateNormals)
    assert normals is not None
    assert normals.location["lat"] == pytest.approx(lat, abs=0.01)
    assert normals.location["lon"] == pytest.approx(lon, abs=0.01)
    assert len(normals.successful_providers) > 0

    # Method 1: Extract for submission-schema with consensus (Issue #191, #193)
    schema_values = normals.to_submission_schema(strategy="consensus")

    assert "annual_precpt" in schema_values
    assert "annual_temp" in schema_values

    # annual_precpt is a float in millimeters (mm/year)
    annual_precip_mm = schema_values["annual_precpt"]
    assert annual_precip_mm is not None
    assert isinstance(annual_precip_mm, float)
    assert 400 < annual_precip_mm < 700  # SF gets ~500-600mm/year

    # Method 2: Get consensus values directly
    annual_precip_consensus = normals.get_consensus_precipitation()
    assert annual_precip_consensus == pytest.approx(annual_precip_mm, abs=0.01)

    # Method 3: Get result from specific provider
    for provider_name in normals.successful_providers:
        provider_result = normals.get_provider_result(provider_name)
        assert provider_result is not None
        assert len(provider_result.monthly_precipitation) == 12
        assert len(provider_result.monthly_temperature) == 12

        # Verify station metadata
        assert provider_result.station_distance_km >= 0
        assert provider_result.provider in ["meteostat", "nasa_power"]

    print("\nSan Francisco Climate (dynamic period):")
    print(
        f"  Requested period: {normals.requested_start_year}-{normals.requested_end_year}"
    )
    print(f"  Annual precipitation (consensus): {annual_precip_mm:.1f} mm/year")
    print(f"  Annual temperature (consensus): {schema_values['annual_temp']:.1f} °C")
    print(f"  Successful providers: {normals.successful_providers}")


@pytest.mark.network
def test_climate_normals_multiple_locations():
    """Test climate normals for different locations to verify general-purpose design."""
    service = WeatherService()

    test_locations = [
        {
            "name": "New York",
            "lat": 40.7128,
            "lon": -74.0060,
            "expected_precip": (1000, 1400),
        },
        {
            "name": "Phoenix",
            "lat": 33.4484,
            "lon": -112.0740,
            "expected_precip": (150, 300),
        },
        {
            "name": "Seattle",
            "lat": 47.6062,
            "lon": -122.3321,
            "expected_precip": (900, 1300),
        },
    ]

    for location in test_locations:
        normals = service.get_climate_normals(location["lat"], location["lon"])
        schema_values = normals.to_submission_schema(strategy="consensus")

        annual_precip = schema_values["annual_precpt"]
        assert annual_precip is not None

        min_precip, max_precip = location["expected_precip"]
        assert min_precip < annual_precip < max_precip, (
            f"{location['name']}: Expected {min_precip}-{max_precip}mm, "
            f"got {annual_precip:.1f}mm"
        )

        print(
            f"{location['name']}: {annual_precip:.1f} mm/year (providers: {normals.successful_providers})"
        )


@pytest.mark.network
def test_climate_normals_provider_directly():
    """Test MeteostatProvider.get_climate_normals() directly."""
    provider = MeteostatProvider()

    # Test with Philadelphia
    normals = provider.get_climate_normals(39.9526, -75.1652)

    assert normals.monthly_precipitation is not None
    assert normals.monthly_temperature is not None

    # Check we have most monthly data
    valid_precip_months = sum(1 for p in normals.monthly_precipitation if p is not None)
    valid_temp_months = sum(1 for t in normals.monthly_temperature if t is not None)

    assert valid_precip_months >= 10, (
        "Should have at least 10 months of precipitation data"
    )
    assert valid_temp_months >= 10, "Should have at least 10 months of temperature data"

    # Verify calculations
    annual_precip = normals.get_annual_precipitation()
    annual_temp = normals.get_annual_temperature()

    assert annual_precip is not None
    assert annual_temp is not None
    assert 900 < annual_precip < 1300  # Philadelphia gets ~1100mm/year
    assert 10 < annual_temp < 15  # Philadelphia averages ~12-13°C


@pytest.mark.network
def test_submission_schema_format():
    """
    Verify to_submission_schema() provides correct format for NMDC.

    Following Issue #193 guidance on submission-schema extraction helpers.
    With multi-provider support, consensus strategy returns simplified format.
    """
    service = WeatherService()

    normals = service.get_climate_normals(37.7749, -122.4194)  # San Francisco

    # Test consensus strategy (simplified format for submission)
    schema_values = normals.to_submission_schema(strategy="consensus")

    # Verify expected keys present (consensus format)
    assert "annual_precpt" in schema_values
    assert "annual_temp" in schema_values
    assert "data_strategy" in schema_values
    assert "providers_used" in schema_values

    # Verify types and values
    assert isinstance(schema_values["annual_precpt"], float)
    assert isinstance(schema_values["annual_temp"], float)
    assert schema_values["data_strategy"] == "consensus"
    assert isinstance(schema_values["providers_used"], list)

    # Verify units are appropriate for submission-schema
    # annual_precpt is a float in millimeters (mm/year), not cm or inches
    assert schema_values["annual_precpt"] > 100  # Reasonable mm value
    # annual_temp is a float in degrees Celsius (°C), not Fahrenheit
    assert -50 < schema_values["annual_temp"] < 50  # Reasonable °C value

    # Test getting specific provider result (more detailed format)
    if normals.successful_providers:
        provider_name = normals.successful_providers[0]
        provider_values = normals.to_submission_schema(provider=provider_name)

        assert "annual_precpt" in provider_values
        assert "annual_temp" in provider_values
        assert "climate_normals_period" in provider_values
        assert "station_distance_km" in provider_values
        assert "data_source" in provider_values
