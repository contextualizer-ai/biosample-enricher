"""
Comprehensive tests for marine enrichment functionality.

Tests cover multiple providers, schema mapping, data quality assessment,
and before/after metrics for marine field coverage.
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from biosample_enricher.marine.models import (
    MarineObservation,
    MarinePrecision,
    MarineQuality,
    MarineResult,
)
from biosample_enricher.marine.providers.esa_cci import ESACCIProvider
from biosample_enricher.marine.providers.gebco import GEBCOProvider
from biosample_enricher.marine.providers.noaa_oisst import NOAAOISSTProvider
from biosample_enricher.marine.service import MarineService


class TestMarineModels:
    """Test marine data models and schema mapping."""

    def test_marine_observation_creation(self):
        """Test basic MarineObservation creation."""
        precision = MarinePrecision(
            method="satellite_composite",
            target_date="2018-07-12",
            data_quality=MarineQuality.SATELLITE_L3,
        )

        observation = MarineObservation(
            value=22.5,
            unit="Celsius",
            precision=precision,
            quality_score=85,
        )

        assert observation.value == 22.5
        assert observation.unit == "Celsius"
        assert observation.quality_score == 85
        assert observation.precision.data_quality == MarineQuality.SATELLITE_L3

    def test_marine_observation_aggregated_value(self):
        """Test MarineObservation with aggregated data."""
        precision = MarinePrecision(
            method="satellite_composite",
            target_date="2018-07-12",
            data_quality=MarineQuality.SATELLITE_L4,
        )

        observation = MarineObservation(
            value={"min": 18.2, "max": 26.7, "avg": 22.1},
            unit="Celsius",
            precision=precision,
        )

        assert observation.value["min"] == 18.2
        assert observation.value["max"] == 26.7
        assert observation.value["avg"] == 22.1

    def test_marine_result_nmdc_schema_mapping(self):
        """Test mapping marine result to NMDC schema fields."""
        precision = MarinePrecision(
            method="satellite_composite",
            target_date="2018-07-12",
            data_quality=MarineQuality.SATELLITE_L4,
        )

        marine_result = MarineResult(
            location={"lat": 42.5, "lon": -85.4},
            collection_date="2018-07-12",
            sea_surface_temperature=MarineObservation(
                value={"min": 18.2, "max": 26.7, "avg": 22.1},
                unit="Celsius",
                precision=precision,
            ),
            bathymetry=MarineObservation(
                value=-1250.5,
                unit="meters",
                precision=precision,
            ),
            chlorophyll_a=MarineObservation(
                value=0.85, unit="mg/m³", precision=precision
            ),
        )

        nmdc_mapping = marine_result.get_schema_mapping("nmdc")

        # Test temperature mapping
        assert "temp" in nmdc_mapping
        temp_data = nmdc_mapping["temp"]
        assert temp_data["has_numeric_value"] == 22.1
        assert temp_data["has_unit"] == "Celsius"
        assert temp_data["type"] == "nmdc:QuantityValue"

        # Test bathymetry mapping
        assert "tot_depth_water_col" in nmdc_mapping
        depth_data = nmdc_mapping["tot_depth_water_col"]
        assert depth_data["has_numeric_value"] == 1250.5  # Positive depth

        assert "elev" in nmdc_mapping
        elev_data = nmdc_mapping["elev"]
        assert elev_data["has_numeric_value"] == -1250.5  # Negative elevation

        # Test chlorophyll mapping
        assert "chlorophyll" in nmdc_mapping
        chl_data = nmdc_mapping["chlorophyll"]
        assert chl_data["has_numeric_value"] == 0.85
        assert chl_data["has_unit"] == "mg/m³"

    def test_marine_result_gold_schema_mapping(self):
        """Test mapping marine result to GOLD schema fields."""
        precision = MarinePrecision(
            method="satellite_interpolation",
            target_date="2018-07-12",
            data_quality=MarineQuality.SATELLITE_L4,
        )

        marine_result = MarineResult(
            location={"lat": 42.5, "lon": -85.4},
            collection_date="2018-07-12",
            sea_surface_temperature=MarineObservation(
                value=22.1, unit="Celsius", precision=precision
            ),
            salinity=MarineObservation(value=35.2, unit="PSU", precision=precision),
            bathymetry=MarineObservation(
                value=-850.0, unit="meters", precision=precision
            ),
        )

        gold_mapping = marine_result.get_schema_mapping("gold")

        assert "sampleCollectionTemperature" in gold_mapping
        assert gold_mapping["sampleCollectionTemperature"] == "22.1 Celsius"

        assert "salinity" in gold_mapping
        assert gold_mapping["salinity"] == "35.2 PSU"

        assert "depthInMeters" in gold_mapping
        assert gold_mapping["depthInMeters"] == 850.0  # Positive depth

        assert "elevationInMeters" in gold_mapping
        assert gold_mapping["elevationInMeters"] == -850.0  # Negative elevation

    def test_marine_result_coverage_metrics(self):
        """Test coverage metrics generation."""
        precision = MarinePrecision(
            method="satellite_composite",
            target_date="2018-07-12",
            data_quality=MarineQuality.SATELLITE_L4,
        )

        marine_result = MarineResult(
            location={"lat": 42.5, "lon": -85.4},
            collection_date="2018-07-12",
            sea_surface_temperature=MarineObservation(
                value=22.1,
                unit="Celsius",
                precision=precision,
                quality_score=90,
            ),
            bathymetry=MarineObservation(
                value=-1200.0,
                unit="meters",
                precision=precision,
                quality_score=95,
            ),
            chlorophyll_a=MarineObservation(
                value=0.75,
                unit="mg/m³",
                precision=precision,
                quality_score=85,
            ),
            successful_providers=["noaa_oisst", "gebco", "esa_cci"],
            overall_quality=MarineQuality.SATELLITE_L4,
        )

        metrics = marine_result.get_coverage_metrics()

        assert metrics["enriched_count"] == 3
        assert metrics["total_possible_fields"] == 9
        assert metrics["enrichment_percentage"] == (3 / 9) * 100
        assert metrics["average_quality_score"] == 90.0  # (90 + 95 + 85) / 3
        assert metrics["data_quality"] == "satellite_l4"
        assert metrics["successful_providers"] == ["noaa_oisst", "gebco", "esa_cci"]
        assert metrics["provider_count"] == 3


class TestNOAAOISSTProvider:
    """Test NOAA OISST provider functionality."""

    def test_provider_initialization(self):
        """Test provider initialization and metadata."""
        provider = NOAAOISSTProvider()

        assert provider.provider_name == "noaa_oisst"
        assert provider.timeout == 30

        info = provider.get_provider_info()
        assert info["name"] == "noaa_oisst"
        assert info["spatial_resolution"] == "0.25 degrees"
        assert info["temporal_resolution"] == "daily"

        coverage = provider.get_coverage_period()
        assert coverage["start"] == "1981-09-01"
        assert coverage["end"] == "present"

    def test_provider_availability(self):
        """Test provider data availability checks."""
        provider = NOAAOISSTProvider()

        # Test dates within coverage
        assert provider.is_available(42.5, -85.4, date(2018, 7, 12))
        assert provider.is_available(42.5, -85.4, date(1990, 1, 1))

        # Test dates outside coverage
        assert not provider.is_available(42.5, -85.4, date(1980, 1, 1))

    @patch("biosample_enricher.marine.providers.noaa_oisst.request")
    def test_fetch_sst_data_success(self, mock_request):
        """Test successful SST data fetching."""
        provider = NOAAOISSTProvider()

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = (
            "time,zlev,latitude,longitude,sst\n2018-07-12T12:00:00Z,0.0,42.5,-85.4,22.5"
        )
        mock_response.raise_for_status = Mock()

        mock_request.return_value = mock_response

        target_date = date(2018, 7, 12)
        result = provider.get_marine_data(42.5, -85.4, target_date)

        assert result.overall_quality == MarineQuality.SATELLITE_L4
        assert len(result.successful_providers) == 1
        assert "noaa_oisst" in result.successful_providers

        # Check SST data
        assert result.sea_surface_temperature is not None
        assert result.sea_surface_temperature.value == 22.5
        assert result.sea_surface_temperature.unit == "Celsius"

    @patch("biosample_enricher.marine.providers.noaa_oisst.request")
    def test_fetch_sst_data_api_error(self, mock_request):
        """Test handling of API errors."""
        provider = NOAAOISSTProvider()

        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("API Error")

        mock_request.return_value = mock_response

        target_date = date(2018, 7, 12)
        result = provider.get_marine_data(42.5, -85.4, target_date)

        assert result.overall_quality == MarineQuality.NO_DATA
        assert len(result.successful_providers) == 0
        assert "noaa_oisst" in result.failed_providers


class TestGEBCOProvider:
    """Test GEBCO bathymetry provider functionality."""

    def test_provider_initialization(self):
        """Test provider initialization and metadata."""
        provider = GEBCOProvider()

        assert provider.provider_name == "gebco"

        info = provider.get_provider_info()
        assert info["name"] == "gebco"
        assert info["spatial_resolution"] == "15 arc-seconds (~450m)"
        assert info["temporal_resolution"] == "static"

    def test_provider_availability(self):
        """Test provider availability (always available for valid coordinates)."""
        provider = GEBCOProvider()

        # Valid coordinates should always be available
        assert provider.is_available(42.5, -85.4, date(2018, 7, 12))
        assert provider.is_available(-30.0, 150.0, date(2000, 1, 1))

        # Invalid coordinates should not be available
        assert not provider.is_available(91.0, 0.0, date(2018, 7, 12))  # Invalid lat

    def test_bathymetry_estimation(self):
        """Test bathymetry data estimation (fallback implementation)."""
        provider = GEBCOProvider()

        target_date = date(2018, 7, 12)
        result = provider.get_marine_data(42.5, -85.4, target_date)

        # Should return some depth estimate
        assert result.bathymetry is not None
        assert result.bathymetry.value < 0  # Should be negative (below sea level)
        assert result.bathymetry.unit == "meters"
        assert result.overall_quality == MarineQuality.STATIC_DATASET


class TestESACCIProvider:
    """Test ESA CCI chlorophyll provider functionality."""

    def test_provider_initialization(self):
        """Test provider initialization and metadata."""
        provider = ESACCIProvider()

        assert provider.provider_name == "esa_cci"

        info = provider.get_provider_info()
        assert info["name"] == "esa_cci"
        assert info["spatial_resolution"] == "~1 km (0.0104 degrees)"
        assert info["temporal_resolution"] == "daily"

    def test_provider_availability(self):
        """Test provider data availability checks."""
        provider = ESACCIProvider()

        # Test dates within coverage
        assert provider.is_available(42.5, -85.4, date(2018, 7, 12))
        assert provider.is_available(42.5, -85.4, date(2000, 1, 1))

        # Test dates outside coverage
        assert not provider.is_available(42.5, -85.4, date(1995, 1, 1))

    def test_chlorophyll_estimation_fallback(self):
        """Test chlorophyll estimation fallback."""
        provider = ESACCIProvider()

        # Test estimation at different latitudes
        tropical_chl = provider._estimate_chlorophyll_fallback(5.0, -85.0)
        temperate_chl = provider._estimate_chlorophyll_fallback(45.0, -85.0)
        polar_chl = provider._estimate_chlorophyll_fallback(70.0, -85.0)

        assert tropical_chl is not None
        assert temperate_chl is not None
        assert polar_chl is not None

        # Polar regions should generally have higher chlorophyll
        assert polar_chl > tropical_chl


class TestMarineService:
    """Test marine service orchestration and multi-provider functionality."""

    def test_service_initialization(self):
        """Test marine service initialization."""
        service = MarineService()

        assert len(service.providers) == 3  # Default OISST + GEBCO + ESA CCI providers
        assert isinstance(service.providers[0], NOAAOISSTProvider)

        # Test with custom providers
        custom_providers = [NOAAOISSTProvider()]
        service = MarineService(providers=custom_providers)
        assert len(service.providers) == 1

    def test_extract_location_nmdc_format(self):
        """Test location extraction from NMDC biosample format."""
        service = MarineService()

        nmdc_biosample = {"lat_lon": {"latitude": 42.5, "longitude": -85.4}}

        location = service._extract_location(nmdc_biosample)
        assert location is not None
        assert location["lat"] == 42.5
        assert location["lon"] == -85.4

    def test_extract_location_gold_format(self):
        """Test location extraction from GOLD biosample format."""
        service = MarineService()

        gold_biosample = {"latitude": 42.5, "longitude": -85.4}

        location = service._extract_location(gold_biosample)
        assert location is not None
        assert location["lat"] == 42.5
        assert location["lon"] == -85.4

    def test_extract_location_missing(self):
        """Test location extraction when coordinates are missing."""
        service = MarineService()

        biosample_no_coords = {"sample_id": "test_sample"}

        location = service._extract_location(biosample_no_coords)
        assert location is None

    def test_extract_collection_date_nmdc_format(self):
        """Test collection date extraction from NMDC biosample format."""
        service = MarineService()

        nmdc_biosample = {"collection_date": {"has_raw_value": "2018-07-12T07:10Z"}}

        collection_date = service._extract_collection_date(nmdc_biosample)
        assert collection_date is not None
        assert collection_date == date(2018, 7, 12)

    def test_extract_collection_date_gold_format(self):
        """Test collection date extraction from GOLD biosample format."""
        service = MarineService()

        gold_biosample = {"dateCollected": "2018-07-12"}

        collection_date = service._extract_collection_date(gold_biosample)
        assert collection_date is not None
        assert collection_date == date(2018, 7, 12)

    def test_extract_collection_date_missing(self):
        """Test collection date extraction when date is missing."""
        service = MarineService()

        biosample_no_date = {"sample_id": "test_sample"}

        collection_date = service._extract_collection_date(biosample_no_date)
        assert collection_date is None

    @patch.object(NOAAOISSTProvider, "get_marine_data")
    @patch.object(GEBCOProvider, "get_marine_data")
    def test_get_comprehensive_marine_data_success(self, mock_gebco, mock_oisst):
        """Test successful marine retrieval through service."""
        service = MarineService()

        # Mock successful provider responses
        precision = MarinePrecision(
            method="satellite_interpolation",
            target_date="2018-07-12",
            data_quality=MarineQuality.SATELLITE_L4,
        )

        mock_oisst_result = MarineResult(
            location={"lat": 42.5, "lon": -85.4},
            collection_date="2018-07-12",
            sea_surface_temperature=MarineObservation(
                value=22.1,
                unit="Celsius",
                precision=precision,
            ),
            successful_providers=["noaa_oisst"],
            overall_quality=MarineQuality.SATELLITE_L4,
        )
        mock_oisst.return_value = mock_oisst_result

        mock_gebco_result = MarineResult(
            location={"lat": 42.5, "lon": -85.4},
            collection_date="2018-07-12",
            bathymetry=MarineObservation(
                value=-1200.0,
                unit="meters",
                precision=precision,
            ),
            successful_providers=["gebco"],
            overall_quality=MarineQuality.STATIC_DATASET,
        )
        mock_gebco.return_value = mock_gebco_result

        result = service.get_comprehensive_marine_data(42.5, -85.4, date(2018, 7, 12))

        assert result.overall_quality == MarineQuality.SATELLITE_L4  # Best quality
        assert len(result.successful_providers) >= 2  # Both providers successful
        assert result.sea_surface_temperature is not None
        assert result.bathymetry is not None

    def test_get_marine_data_for_biosample_complete(self):
        """Test complete biosample marine enrichment workflow."""
        service = MarineService()

        # Mock the providers to return successful results
        with patch.object(service.providers[0], "get_marine_data") as mock_oisst:
            precision = MarinePrecision(
                method="satellite_interpolation",
                target_date="2018-07-12",
                data_quality=MarineQuality.SATELLITE_L4,
            )

            mock_marine_result = MarineResult(
                location={"lat": 42.5, "lon": -85.4},
                collection_date="2018-07-12",
                sea_surface_temperature=MarineObservation(
                    value={"min": 18.2, "max": 26.7, "avg": 22.1},
                    unit="Celsius",
                    precision=precision,
                ),
                successful_providers=["noaa_oisst"],
                overall_quality=MarineQuality.SATELLITE_L4,
            )
            mock_oisst.return_value = mock_marine_result

            nmdc_biosample = {
                "sample_id": "nmdc:bsm-11-test123",
                "lat_lon": {"latitude": 42.5, "longitude": -85.4},
                "collection_date": {"has_raw_value": "2018-07-12T07:10Z"},
            }

            result = service.get_marine_data_for_biosample(
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
            assert coverage_metrics["enriched_count"] >= 1  # At least SST enriched
            assert coverage_metrics["data_quality"] == "satellite_l4"

    def test_get_marine_data_for_biosample_missing_data(self):
        """Test biosample enrichment with missing location or date."""
        service = MarineService()

        # Test missing coordinates
        biosample_no_coords = {
            "sample_id": "test_sample",
            "collection_date": {"has_raw_value": "2018-07-12"},
        }

        result = service.get_marine_data_for_biosample(biosample_no_coords)
        assert result["error"] == "no_coordinates"
        assert result["enrichment"] == {}

        # Test missing collection date
        biosample_no_date = {
            "sample_id": "test_sample",
            "lat_lon": {"latitude": 42.5, "longitude": -85.4},
        }

        result = service.get_marine_data_for_biosample(biosample_no_date)
        assert result["error"] == "no_collection_date"
        assert result["enrichment"] == {}


class TestMarineEnrichmentIntegration:
    """Integration tests for complete marine enrichment workflows."""

    @pytest.mark.integration
    def test_complete_enrichment_workflow(self):
        """Test complete marine enrichment workflow with mock data."""

        # Create realistic biosample data
        nmdc_biosample = {
            "id": "nmdc:bsm-11-test123",
            "lat_lon": {"latitude": 42.5, "longitude": -85.4},
            "collection_date": {"has_raw_value": "2018-07-12T14:30Z"},
            "env_broad_scale": {
                "term": {"id": "ENVO:01000324", "name": "marine biome"}
            },
        }

        # Run enrichment
        service = MarineService()
        result = service.get_marine_data_for_biosample(
            nmdc_biosample, target_schema="nmdc"
        )

        # Verify workflow runs without errors (results may vary based on mock implementations)
        assert "enrichment_success" in result
        assert "marine_result" in result
        assert "schema_mapping" in result
        assert "coverage_metrics" in result

        if result["enrichment_success"]:
            # Check marine result quality
            marine_result = result["marine_result"]
            assert marine_result.overall_quality != MarineQuality.NO_DATA

            # Check coverage metrics
            coverage_metrics = result["coverage_metrics"]
            assert coverage_metrics["enriched_count"] >= 0
            assert coverage_metrics["total_possible_fields"] == 9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
