"""
Comprehensive tests for weather enrichment functionality.

Tests cover multiple providers, schema mapping, temporal precision,
and before/after metrics for weather field coverage.
"""

from datetime import date
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from biosample_enricher.weather.models import (
    TemporalPrecision,
    TemporalQuality,
    WeatherObservation,
    WeatherResult,
)
from biosample_enricher.weather.providers.open_meteo import OpenMeteoProvider
from biosample_enricher.weather.service import WeatherService


class TestWeatherModels:
    """Test weather data models and schema mapping."""

    def test_weather_observation_creation(self):
        """Test basic WeatherObservation creation."""
        temporal_precision = TemporalPrecision(
            method="hourly_aggregation",
            target_date="2018-07-12",
            data_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
        )

        observation = WeatherObservation(
            value=22.5,
            unit="Celsius",
            temporal_precision=temporal_precision,
            quality_score=95,
        )

        assert observation.value == 22.5
        assert observation.unit == "Celsius"
        assert observation.quality_score == 95
        assert (
            observation.temporal_precision.data_quality
            == TemporalQuality.DAY_SPECIFIC_COMPLETE
        )

    def test_weather_observation_aggregated_value(self):
        """Test WeatherObservation with aggregated temperature data."""
        temporal_precision = TemporalPrecision(
            method="hourly_aggregation",
            target_date="2018-07-12",
            data_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
        )

        observation = WeatherObservation(
            value={"min": 15.2, "max": 28.7, "avg": 22.1},
            unit="Celsius",
            temporal_precision=temporal_precision,
        )

        assert observation.value["min"] == 15.2
        assert observation.value["max"] == 28.7
        assert observation.value["avg"] == 22.1

    def test_weather_result_nmdc_schema_mapping(self):
        """Test mapping weather result to NMDC schema fields."""
        temporal_precision = TemporalPrecision(
            method="hourly_aggregation",
            target_date="2018-07-12",
            data_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
        )

        weather_result = WeatherResult(
            location={"lat": 42.5, "lon": -85.4},
            collection_date="2018-07-12",
            temperature=WeatherObservation(
                value={"min": 15.2, "max": 28.7, "avg": 22.1},
                unit="Celsius",
                temporal_precision=temporal_precision,
            ),
            wind_speed=WeatherObservation(
                value={"min": 2.1, "max": 8.5, "avg": 4.8},
                unit="m/s",
                temporal_precision=temporal_precision,
            ),
            humidity=WeatherObservation(
                value=68.5, unit="percent", temporal_precision=temporal_precision
            ),
        )

        nmdc_mapping = weather_result.get_schema_mapping("nmdc")

        # Test temperature mapping
        assert "temp" in nmdc_mapping
        temp_data = nmdc_mapping["temp"]
        assert temp_data["has_numeric_value"] == 22.1
        assert temp_data["has_unit"] == "Celsius"
        assert temp_data["type"] == "nmdc:QuantityValue"
        assert temp_data["temp_min"] == 15.2
        assert temp_data["temp_max"] == 28.7

        # Test wind speed mapping
        assert "wind_speed" in nmdc_mapping
        wind_data = nmdc_mapping["wind_speed"]
        assert wind_data["has_numeric_value"] == 4.8  # avg value
        assert wind_data["has_unit"] == "m/s"

        # Test humidity mapping
        assert "humidity" in nmdc_mapping
        humidity_data = nmdc_mapping["humidity"]
        assert humidity_data["has_numeric_value"] == 68.5
        assert humidity_data["has_unit"] == "percent"

    def test_weather_result_gold_schema_mapping(self):
        """Test mapping weather result to GOLD schema fields."""
        temporal_precision = TemporalPrecision(
            method="hourly_aggregation",
            target_date="2018-07-12",
            data_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
        )

        weather_result = WeatherResult(
            location={"lat": 42.5, "lon": -85.4},
            collection_date="2018-07-12",
            temperature=WeatherObservation(
                value=22.1, unit="Celsius", temporal_precision=temporal_precision
            ),
            pressure=WeatherObservation(
                value=101.3, unit="kPa", temporal_precision=temporal_precision
            ),
        )

        gold_mapping = weather_result.get_schema_mapping("gold")

        assert "sampleCollectionTemperature" in gold_mapping
        assert gold_mapping["sampleCollectionTemperature"] == "22.1 Celsius"

        assert "pressure" in gold_mapping
        assert gold_mapping["pressure"] == "101.3 kPa"

    def test_weather_result_coverage_metrics(self):
        """Test coverage metrics generation."""
        temporal_precision = TemporalPrecision(
            method="hourly_aggregation",
            target_date="2018-07-12",
            data_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
        )

        weather_result = WeatherResult(
            location={"lat": 42.5, "lon": -85.4},
            collection_date="2018-07-12",
            temperature=WeatherObservation(
                value=22.1,
                unit="Celsius",
                temporal_precision=temporal_precision,
                quality_score=95,
            ),
            wind_speed=WeatherObservation(
                value=4.8,
                unit="m/s",
                temporal_precision=temporal_precision,
                quality_score=90,
            ),
            successful_providers=["open_meteo"],
            overall_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
        )

        metrics = weather_result.get_coverage_metrics()

        assert metrics["enriched_count"] == 2
        assert metrics["total_possible_fields"] == 7
        assert metrics["enrichment_percentage"] == (2 / 7) * 100
        assert metrics["average_quality_score"] == 92.5  # (95 + 90) / 2
        assert metrics["temporal_quality"] == "day_specific_complete"
        assert metrics["successful_providers"] == ["open_meteo"]
        assert metrics["provider_count"] == 1


class TestOpenMeteoProvider:
    """Test Open-Meteo weather provider functionality."""

    def test_provider_initialization(self):
        """Test provider initialization and metadata."""
        provider = OpenMeteoProvider()

        assert provider.provider_name == "open_meteo"
        assert provider.timeout == 30

        info = provider.get_provider_info()
        assert info["name"] == "open_meteo"
        assert info["temporal_resolution"] == "hourly"
        assert info["spatial_resolution"] == "11km"

        coverage = provider.get_coverage_period()
        assert coverage["start"] == "1959-01-01"
        assert coverage["end"] == "present"

    def test_provider_availability(self):
        """Test provider data availability checks."""
        provider = OpenMeteoProvider()

        # Test dates within coverage
        assert provider.is_available(42.5, -85.4, date(2018, 7, 12))
        assert provider.is_available(42.5, -85.4, date(1980, 1, 1))

        # Test dates outside coverage
        assert not provider.is_available(42.5, -85.4, date(1950, 1, 1))

    @patch("biosample_enricher.weather.providers.open_meteo.request")
    def test_fetch_hourly_data_success(self, mock_request):
        """Test successful hourly data fetching."""
        provider = OpenMeteoProvider()

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hourly": {
                "time": [f"2018-07-12T{hour:02d}:00" for hour in range(24)],
                "temperature_2m": [15.2 + hour * 0.8 for hour in range(24)],
                "precipitation": [0.0] * 24,
                "wind_speed_10m": [3.0 + hour * 0.2 for hour in range(24)],
                "relative_humidity_2m": [70.0 - hour * 1.0 for hour in range(24)],
            }
        }
        mock_request.return_value = mock_response

        target_date = date(2018, 7, 12)
        result = provider.get_daily_weather(42.5, -85.4, target_date)

        assert result.overall_quality == TemporalQuality.DAY_SPECIFIC_COMPLETE
        assert len(result.successful_providers) == 1
        assert "open_meteo" in result.successful_providers

        # Check temperature data
        assert result.temperature is not None
        assert isinstance(result.temperature.value, dict)
        assert "min" in result.temperature.value
        assert "max" in result.temperature.value
        assert "avg" in result.temperature.value

        # Check other parameters
        assert result.wind_speed is not None
        assert result.humidity is not None

    @patch("biosample_enricher.weather.providers.open_meteo.request")
    def test_fetch_hourly_data_api_error(self, mock_request):
        """Test handling of API errors."""
        provider = OpenMeteoProvider()

        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_request.return_value = mock_response

        target_date = date(2018, 7, 12)
        result = provider.get_daily_weather(42.5, -85.4, target_date)

        assert result.overall_quality == TemporalQuality.NO_DATA
        assert len(result.successful_providers) == 0
        assert "open_meteo" in result.failed_providers

    def test_hourly_aggregation_complete_coverage(self):
        """Test hourly to daily aggregation with complete coverage."""
        provider = OpenMeteoProvider()

        # Create mock hourly DataFrame with 24 hours of data
        hourly_data = pd.DataFrame(
            {
                "temperature_2m": [15.2 + hour * 0.8 for hour in range(24)],
                "precipitation": [0.1] * 12 + [0.0] * 12,  # Rain in first half of day
                "wind_speed_10m": [3.0 + hour * 0.2 for hour in range(24)],
                "wind_direction_10m": [180 + hour * 5 for hour in range(24)],
                "relative_humidity_2m": [70.0 - hour * 1.0 for hour in range(24)],
                "surface_pressure": [101325] * 24,  # Pa
                "shortwave_radiation": [0] * 6
                + [200] * 12
                + [0] * 6,  # Daytime radiation
            }
        )

        target_date = date(2018, 7, 12)
        aggregates = provider._aggregate_hourly_to_daily(hourly_data, target_date)

        assert aggregates["coverage"] == "complete"
        assert aggregates["available_hours"] == 24

        # Test temperature aggregation
        temp_data = aggregates["aggregates"]["temperature"]
        assert temp_data["min"] == 15.2
        assert temp_data["max"] == 15.2 + 23 * 0.8  # Last hour value
        assert (
            abs(temp_data["avg"] - (15.2 + 23 * 0.8 / 2)) < 1.0
        )  # Approximate average

        # Test precipitation sum
        precip_data = aggregates["aggregates"]["precipitation"]
        assert (
            abs(precip_data["sum"] - 1.2) < 1e-10
        )  # 12 hours * 0.1 mm (floating point precision)

        # Test pressure conversion (Pa to kPa)
        pressure_data = aggregates["aggregates"]["pressure"]
        assert abs(pressure_data["avg"] - 101.325) < 0.001  # 101325 Pa = 101.325 kPa

    def test_hourly_aggregation_partial_coverage(self):
        """Test hourly to daily aggregation with partial coverage."""
        provider = OpenMeteoProvider()

        # Create mock hourly DataFrame with only 12 hours of data (partial coverage)
        hourly_data = pd.DataFrame(
            {"temperature_2m": [20.0] * 12, "wind_speed_10m": [5.0] * 12}
        )

        target_date = date(2018, 7, 12)
        aggregates = provider._aggregate_hourly_to_daily(hourly_data, target_date)

        assert aggregates["coverage"] == "partial"
        assert aggregates["available_hours"] == 12
        assert aggregates["coverage_fraction"] == 0.5


class TestWeatherService:
    """Test weather service orchestration and multi-provider functionality."""

    def test_service_initialization(self):
        """Test weather service initialization."""
        service = WeatherService()

        assert len(service.providers) == 2  # Default Open-Meteo + MeteoStat providers
        assert isinstance(service.providers[0], OpenMeteoProvider)

        # Test with custom providers
        custom_providers = [OpenMeteoProvider()]
        service = WeatherService(providers=custom_providers)
        assert len(service.providers) == 1

    def test_extract_location_nmdc_format(self):
        """Test location extraction from NMDC biosample format."""
        service = WeatherService()

        nmdc_biosample = {"lat_lon": {"latitude": 42.5, "longitude": -85.4}}

        location = service._extract_location(nmdc_biosample)
        assert location is not None
        assert location["lat"] == 42.5
        assert location["lon"] == -85.4

    def test_extract_location_gold_format(self):
        """Test location extraction from GOLD biosample format."""
        service = WeatherService()

        gold_biosample = {"latitude": 42.5, "longitude": -85.4}

        location = service._extract_location(gold_biosample)
        assert location is not None
        assert location["lat"] == 42.5
        assert location["lon"] == -85.4

    def test_extract_location_missing(self):
        """Test location extraction when coordinates are missing."""
        service = WeatherService()

        biosample_no_coords = {"sample_id": "test_sample"}

        location = service._extract_location(biosample_no_coords)
        assert location is None

    def test_extract_collection_date_nmdc_format(self):
        """Test collection date extraction from NMDC biosample format."""
        service = WeatherService()

        nmdc_biosample = {"collection_date": {"has_raw_value": "2018-07-12T07:10Z"}}

        collection_date = service._extract_collection_date(nmdc_biosample)
        assert collection_date is not None
        assert collection_date == date(2018, 7, 12)

    def test_extract_collection_date_gold_format(self):
        """Test collection date extraction from GOLD biosample format."""
        service = WeatherService()

        gold_biosample = {"dateCollected": "2018-07-12"}

        collection_date = service._extract_collection_date(gold_biosample)
        assert collection_date is not None
        assert collection_date == date(2018, 7, 12)

    def test_extract_collection_date_missing(self):
        """Test collection date extraction when date is missing."""
        service = WeatherService()

        biosample_no_date = {"sample_id": "test_sample"}

        collection_date = service._extract_collection_date(biosample_no_date)
        assert collection_date is None

    @patch.object(OpenMeteoProvider, "get_daily_weather")
    def test_get_daily_weather_success(self, mock_provider_method):
        """Test successful weather retrieval through service."""
        service = WeatherService()

        # Mock successful provider response
        mock_weather_result = WeatherResult(
            location={"lat": 42.5, "lon": -85.4},
            collection_date="2018-07-12",
            temperature=WeatherObservation(
                value=22.1,
                unit="Celsius",
                temporal_precision=TemporalPrecision(
                    method="hourly_aggregation",
                    target_date="2018-07-12",
                    data_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
                ),
            ),
            successful_providers=["open_meteo"],
            overall_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
        )
        mock_provider_method.return_value = mock_weather_result

        result = service.get_daily_weather(42.5, -85.4, date(2018, 7, 12))

        assert result.overall_quality == TemporalQuality.DAY_SPECIFIC_COMPLETE
        assert (
            len(result.successful_providers) >= 1
        )  # Can be 1 or 2 depending on provider availability
        assert result.temperature is not None
        assert result.temperature.value == 22.1

    @patch.object(OpenMeteoProvider, "get_daily_weather")
    @patch.object(OpenMeteoProvider, "is_available")
    def test_get_daily_weather_provider_unavailable(
        self, mock_is_available, _mock_provider_method
    ):
        """Test weather retrieval when all providers are unavailable."""
        service = WeatherService()

        # Mock all providers unavailable (now we try both Open-Meteo and MeteoStat)
        mock_is_available.return_value = False

        result = service.get_daily_weather(42.5, -85.4, date(1950, 1, 1))

        assert result.overall_quality == TemporalQuality.NO_DATA
        assert len(result.successful_providers) == 0
        assert len(result.failed_providers) == 2  # Both providers should fail

    def test_get_weather_for_biosample_complete(self):
        """Test complete biosample weather enrichment workflow."""
        service = WeatherService()

        # Mock the provider to return successful result
        with patch.object(service.providers[0], "get_daily_weather") as mock_method:
            mock_weather_result = WeatherResult(
                location={"lat": 42.5, "lon": -85.4},
                collection_date="2018-07-12",
                temperature=WeatherObservation(
                    value={"min": 15.2, "max": 28.7, "avg": 22.1},
                    unit="Celsius",
                    temporal_precision=TemporalPrecision(
                        method="hourly_aggregation",
                        target_date="2018-07-12",
                        data_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
                    ),
                ),
                successful_providers=["open_meteo"],
                overall_quality=TemporalQuality.DAY_SPECIFIC_COMPLETE,
            )
            mock_method.return_value = mock_weather_result

            nmdc_biosample = {
                "sample_id": "nmdc:bsm-11-test123",
                "lat_lon": {"latitude": 42.5, "longitude": -85.4},
                "collection_date": {"has_raw_value": "2018-07-12T07:10Z"},
            }

            result = service.get_weather_for_biosample(
                nmdc_biosample, target_schema="nmdc"
            )

            assert result["enrichment_success"] is True
            assert "schema_mapping" in result
            assert "coverage_metrics" in result

            # Test NMDC schema mapping
            schema_mapping = result["schema_mapping"]
            assert "temp" in schema_mapping
            assert schema_mapping["temp"]["has_numeric_value"] == 22.1

            # Test coverage metrics
            coverage_metrics = result["coverage_metrics"]
            assert (
                coverage_metrics["enriched_count"] >= 1
            )  # Multiple weather parameters enriched
            assert coverage_metrics["temporal_quality"] == "day_specific_complete"

    def test_get_weather_for_biosample_missing_data(self):
        """Test biosample enrichment with missing location or date."""
        service = WeatherService()

        # Test missing coordinates
        biosample_no_coords = {
            "sample_id": "test_sample",
            "collection_date": {"has_raw_value": "2018-07-12"},
        }

        result = service.get_weather_for_biosample(biosample_no_coords)
        assert result["error"] == "no_coordinates"
        assert result["enrichment"] == {}

        # Test missing collection date
        biosample_no_date = {
            "sample_id": "test_sample",
            "lat_lon": {"latitude": 42.5, "longitude": -85.4},
        }

        result = service.get_weather_for_biosample(biosample_no_date)
        assert result["error"] == "no_collection_date"
        assert result["enrichment"] == {}


class TestWeatherEnrichmentIntegration:
    """Integration tests for complete weather enrichment workflows."""

    @pytest.mark.integration
    @patch("biosample_enricher.weather.providers.open_meteo.request")
    def test_complete_enrichment_workflow(self, mock_request):
        """Test complete weather enrichment workflow with realistic data."""

        # Mock realistic Open-Meteo API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hourly": {
                "time": [f"2018-07-12T{hour:02d}:00" for hour in range(24)],
                "temperature_2m": [
                    12.5,
                    13.1,
                    13.8,
                    14.5,
                    15.2,
                    16.8,
                    18.4,
                    20.1,
                    22.3,
                    24.6,
                    26.8,
                    28.1,
                    29.3,
                    28.7,
                    27.9,
                    26.3,
                    24.1,
                    21.8,
                    19.5,
                    17.2,
                    15.9,
                    14.6,
                    13.8,
                    13.1,
                ],
                "precipitation": [0.0] * 8 + [0.2, 0.1, 0.0, 0.2] + [0.0] * 12,
                "wind_speed_10m": [
                    2.1,
                    2.3,
                    2.8,
                    3.2,
                    3.8,
                    4.1,
                    4.5,
                    5.2,
                    5.8,
                    6.1,
                    6.3,
                    6.0,
                    5.7,
                    5.2,
                    4.8,
                    4.3,
                    3.9,
                    3.4,
                    3.0,
                    2.7,
                    2.4,
                    2.2,
                    2.0,
                    2.1,
                ],
                "wind_direction_10m": [
                    225,
                    230,
                    235,
                    240,
                    245,
                    250,
                    255,
                    260,
                    265,
                    270,
                    275,
                    280,
                    285,
                    290,
                    295,
                    300,
                    305,
                    310,
                    315,
                    320,
                    325,
                    330,
                    335,
                    340,
                ],
                "relative_humidity_2m": [
                    85,
                    83,
                    80,
                    78,
                    75,
                    70,
                    65,
                    58,
                    52,
                    48,
                    45,
                    43,
                    42,
                    44,
                    47,
                    52,
                    58,
                    64,
                    70,
                    75,
                    78,
                    80,
                    82,
                    84,
                ],
                "surface_pressure": [101325] * 24,
                "shortwave_radiation": [0] * 6
                + [100, 250, 400, 520, 650, 720, 680, 590, 420, 280, 150, 50]
                + [0] * 6,
            }
        }
        mock_request.return_value = mock_response

        # Create realistic biosample data
        nmdc_biosample = {
            "id": "nmdc:bsm-11-test123",
            "lat_lon": {"latitude": 42.5, "longitude": -85.4},
            "collection_date": {"has_raw_value": "2018-07-12T14:30Z"},
            "env_broad_scale": {
                "term": {"id": "ENVO:00000446", "name": "terrestrial biome"}
            },
        }

        # Run enrichment
        service = WeatherService()
        result = service.get_weather_for_biosample(nmdc_biosample, target_schema="nmdc")

        # Verify successful enrichment
        assert result["enrichment_success"] is True

        # Check weather result quality
        weather_result = result["weather_result"]
        assert weather_result.overall_quality == TemporalQuality.DAY_SPECIFIC_COMPLETE

        # Verify temperature data
        assert weather_result.temperature is not None
        temp_data = weather_result.temperature.value
        assert temp_data["min"] == 12.5
        assert temp_data["max"] == 29.3
        assert 19.0 <= temp_data["avg"] <= 22.0  # Reasonable daily average

        # Verify other weather parameters
        assert weather_result.wind_speed is not None
        assert weather_result.humidity is not None
        assert weather_result.precipitation is not None
        assert weather_result.solar_radiation is not None

        # Check NMDC schema mapping
        schema_mapping = result["schema_mapping"]
        assert "temp" in schema_mapping
        assert "wind_speed" in schema_mapping
        assert "humidity" in schema_mapping
        assert "solar_irradiance" in schema_mapping

        # Verify proper NMDC formatting
        temp_mapping = schema_mapping["temp"]
        assert temp_mapping["type"] == "nmdc:QuantityValue"
        assert temp_mapping["has_unit"] == "Celsius"
        assert temp_mapping["has_numeric_value"] == temp_data["avg"]

        # Check coverage metrics
        coverage_metrics = result["coverage_metrics"]
        assert coverage_metrics["enriched_count"] >= 5  # At least 5 weather parameters
        assert coverage_metrics["temporal_quality"] == "day_specific_complete"
        assert coverage_metrics["average_quality_score"] > 90  # High quality data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
