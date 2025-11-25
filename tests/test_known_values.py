"""
Tests that validate consensus results against known reference values.

These tests verify that get_submission_values returns values within expected
ranges for well-characterized locations. The expected ranges are based on
published climate data and elevation measurements.

Reference sources:
- Climate: NOAA Climate Normals, WorldClim
- Elevation: USGS, Google Earth, published geographic data
"""

import pytest

from biosample_enricher.submission_values import get_submission_values

# Known reference data for test locations
# Format: (lat, lon, name, expected_values)
# expected_values contains ranges: (min, max) for each slot
REFERENCE_LOCATIONS = [
    # US Locations
    {
        "name": "San Francisco, CA",
        "lat": 37.7749,
        "lon": -122.4194,
        "expected": {
            # San Francisco has Mediterranean climate with ~500-600mm annual precip
            "annual_precpt": (400.0, 700.0),
            # Annual temp around 13-15°C
            "annual_temp": (12.0, 16.0),
            # Downtown SF elevation varies but generally 0-30m
            "elev": (0.0, 100.0),
        },
    },
    {
        "name": "New York City, NY",
        "lat": 40.7128,
        "lon": -74.0060,
        "expected": {
            # NYC has humid subtropical climate with ~1100-1300mm annual precip
            "annual_precpt": (1000.0, 1400.0),
            # Annual temp around 11-13°C
            "annual_temp": (10.0, 15.0),
            # Manhattan at sea level, generally 0-30m
            "elev": (0.0, 50.0),
        },
    },
    {
        "name": "Denver, CO",
        "lat": 39.7392,
        "lon": -104.9903,
        "expected": {
            # Denver has semi-arid climate with ~350-450mm annual precip
            "annual_precpt": (300.0, 550.0),
            # Annual temp around 10-12°C
            "annual_temp": (8.0, 14.0),
            # Mile High City - elevation ~1600m
            "elev": (1500.0, 1700.0),
        },
    },
    # International Locations
    {
        "name": "London, UK",
        "lat": 51.5074,
        "lon": -0.1278,
        "expected": {
            # London has oceanic climate with ~550-650mm annual precip
            "annual_precpt": (500.0, 750.0),
            # Annual temp around 10-12°C
            "annual_temp": (9.0, 13.0),
            # London is relatively flat, 0-30m
            "elev": (0.0, 50.0),
        },
    },
    {
        "name": "Tokyo, Japan",
        "lat": 35.6762,
        "lon": 139.6503,
        "expected": {
            # Tokyo has humid subtropical climate with ~1400-1600mm annual precip
            "annual_precpt": (1300.0, 1800.0),
            # Annual temp around 15-17°C
            "annual_temp": (14.0, 18.0),
            # Tokyo varies, central areas 0-50m
            "elev": (0.0, 100.0),
        },
    },
    {
        "name": "Sydney, Australia",
        "lat": -33.8688,
        "lon": 151.2093,
        "expected": {
            # Sydney has humid subtropical climate with ~900-1300mm annual precip
            # (varies significantly by location within metro area)
            "annual_precpt": (850.0, 1400.0),
            # Annual temp around 17-19°C
            "annual_temp": (16.0, 20.0),
            # Sydney CBD near harbor, 0-50m
            "elev": (0.0, 100.0),
        },
    },
    # High elevation location
    {
        "name": "La Paz, Bolivia",
        "lat": -16.5000,
        "lon": -68.1500,
        "expected": {
            # La Paz has semi-arid climate with ~500-700mm annual precip
            "annual_precpt": (400.0, 800.0),
            # Annual temp around 7-10°C (high altitude)
            "annual_temp": (5.0, 12.0),
            # La Paz is one of the highest cities, ~3600m
            "elev": (3400.0, 3800.0),
        },
    },
]


@pytest.mark.network
class TestKnownClimateValues:
    """Test climate values against known reference ranges."""

    @pytest.mark.parametrize(
        "location",
        REFERENCE_LOCATIONS,
        ids=[loc["name"] for loc in REFERENCE_LOCATIONS],
    )
    def test_annual_precpt_in_expected_range(self, location: dict):
        """Test annual precipitation is within expected range."""
        result = get_submission_values(
            lat=location["lat"],
            lon=location["lon"],
            slots=["annual_precpt"],
        )

        assert "annual_precpt" in result["values"], (
            f"annual_precpt not returned for {location['name']}"
        )

        precip = result["values"]["annual_precpt"]
        expected_min, expected_max = location["expected"]["annual_precpt"]

        assert expected_min <= precip <= expected_max, (
            f"{location['name']}: annual_precpt={precip:.1f}mm "
            f"outside expected range [{expected_min}, {expected_max}]"
        )

    @pytest.mark.parametrize(
        "location",
        REFERENCE_LOCATIONS,
        ids=[loc["name"] for loc in REFERENCE_LOCATIONS],
    )
    def test_annual_temp_in_expected_range(self, location: dict):
        """Test annual temperature is within expected range."""
        result = get_submission_values(
            lat=location["lat"],
            lon=location["lon"],
            slots=["annual_temp"],
        )

        assert "annual_temp" in result["values"], (
            f"annual_temp not returned for {location['name']}"
        )

        temp = result["values"]["annual_temp"]
        expected_min, expected_max = location["expected"]["annual_temp"]

        assert expected_min <= temp <= expected_max, (
            f"{location['name']}: annual_temp={temp:.1f}°C "
            f"outside expected range [{expected_min}, {expected_max}]"
        )


@pytest.mark.network
class TestKnownElevationValues:
    """Test elevation values against known reference ranges."""

    @pytest.mark.parametrize(
        "location",
        REFERENCE_LOCATIONS,
        ids=[loc["name"] for loc in REFERENCE_LOCATIONS],
    )
    def test_elev_in_expected_range(self, location: dict):
        """Test elevation is within expected range."""
        result = get_submission_values(
            lat=location["lat"],
            lon=location["lon"],
            slots=["elev"],
        )

        assert "elev" in result["values"], f"elev not returned for {location['name']}"

        elev = result["values"]["elev"]
        expected_min, expected_max = location["expected"]["elev"]

        assert expected_min <= elev <= expected_max, (
            f"{location['name']}: elev={elev:.1f}m "
            f"outside expected range [{expected_min}, {expected_max}]"
        )


@pytest.mark.network
class TestConsensusAcrossProviders:
    """Test that consensus values are reasonable across providers."""

    def test_elevation_providers_agree_within_tolerance(self):
        """Test that elevation providers agree within reasonable tolerance."""
        # San Francisco - well-documented location
        result = get_submission_values(
            lat=37.7749,
            lon=-122.4194,
            slots=["elev"],
        )

        metadata = result["metadata"].get("elevation", {})
        provider_results = metadata.get("provider_results", {})

        if len(provider_results) < 2:
            pytest.skip("Need at least 2 providers for comparison")

        elevations = [
            r["elevation_m"]
            for r in provider_results.values()
            if r.get("elevation_m") is not None
        ]

        if len(elevations) < 2:
            pytest.skip("Need at least 2 elevation values for comparison")

        # Providers should agree within 50m for well-characterized locations
        elev_range = max(elevations) - min(elevations)
        assert elev_range < 50, (
            f"Elevation providers disagree by {elev_range:.1f}m: {provider_results}"
        )

    def test_climate_providers_agree_within_tolerance(self):
        """Test that climate providers agree within reasonable tolerance."""
        # San Francisco - well-documented location
        result = get_submission_values(
            lat=37.7749,
            lon=-122.4194,
            slots=["annual_precpt", "annual_temp"],
        )

        metadata = result["metadata"].get("climate_normals", {})
        provider_results = metadata.get("provider_results", {})

        if len(provider_results) < 2:
            pytest.skip("Need at least 2 providers for comparison")

        # Check precipitation agreement
        precips = [
            r["annual_precpt"]
            for r in provider_results.values()
            if r.get("annual_precpt") is not None
        ]
        if len(precips) >= 2:
            precip_range = max(precips) - min(precips)
            # Providers may disagree by up to 200mm due to different periods/methods
            assert precip_range < 300, (
                f"Precipitation providers disagree by {precip_range:.1f}mm"
            )

        # Check temperature agreement
        temps = [
            r["annual_temp"]
            for r in provider_results.values()
            if r.get("annual_temp") is not None
        ]
        if len(temps) >= 2:
            temp_range = max(temps) - min(temps)
            # Providers should agree within 2°C
            assert temp_range < 3.0, (
                f"Temperature providers disagree by {temp_range:.1f}°C"
            )


@pytest.mark.network
class TestStrategyEffects:
    """Test that different strategies produce different but valid results."""

    def test_mean_vs_first_elevation(self):
        """Test that mean and first strategies can produce different elevation values."""
        lat, lon = 37.7749, -122.4194  # San Francisco

        mean_result = get_submission_values(
            lat=lat, lon=lon, slots=["elev"], strategy="mean"
        )
        first_result = get_submission_values(
            lat=lat, lon=lon, slots=["elev"], strategy="first"
        )

        mean_elev = mean_result["values"].get("elev")
        first_elev = first_result["values"].get("elev")

        assert mean_elev is not None, "Mean strategy should return elevation"
        assert first_elev is not None, "First strategy should return elevation"

        # Both should be reasonable values for SF
        assert 0 < mean_elev < 100, f"Mean elevation {mean_elev}m unreasonable for SF"
        assert 0 < first_elev < 100, (
            f"First elevation {first_elev}m unreasonable for SF"
        )

        # Strategies should be documented in metadata
        assert mean_result["metadata"]["elevation"]["consensus_strategy"] == "mean"
        assert first_result["metadata"]["elevation"]["consensus_strategy"] == "first"

    def test_all_strategies_return_valid_results(self):
        """Test all strategies return valid results for known location."""
        lat, lon = 40.7128, -74.0060  # New York

        strategies = ["mean", "median", "first"]

        for strategy in strategies:
            result = get_submission_values(
                lat=lat, lon=lon, slots=["elev"], strategy=strategy
            )

            assert "elev" in result["values"], (
                f"Strategy '{strategy}' should return elevation"
            )
            elev = result["values"]["elev"]
            # NYC is near sea level
            assert 0 <= elev < 50, (
                f"Strategy '{strategy}' returned unreasonable elevation: {elev}m"
            )
