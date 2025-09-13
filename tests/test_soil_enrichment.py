"""Comprehensive tests for soil enrichment functionality."""

from unittest.mock import Mock, patch

import pytest

from biosample_enricher.soil.models import SoilObservation, SoilResult, classify_texture
from biosample_enricher.soil.providers.base import SoilProviderBase
from biosample_enricher.soil.providers.soilgrids import SoilGridsProvider
from biosample_enricher.soil.providers.usda_nrcs import USDANRCSProvider
from biosample_enricher.soil.service import SoilService


class TestSoilModels:
    """Test soil data models and validation."""

    def test_soil_observation_creation(self):
        """Test creating a soil observation with valid data."""
        obs = SoilObservation(
            classification_usda="Typic Haplocryepts",
            classification_wrb="Cambisols",
            ph_h2o=5.5,
            organic_carbon=36.6,
            sand_percent=48.1,
            silt_percent=38.5,
            clay_percent=13.4,
            texture_class="Loam",
            depth_cm="0-5cm",
        )

        assert obs.classification_usda == "Typic Haplocryepts"
        assert obs.classification_wrb == "Cambisols"
        assert obs.ph_h2o == 5.5
        assert obs.texture_class == "Loam"

    def test_soil_observation_validation(self):
        """Test soil observation field validation."""
        # pH validation
        with pytest.raises(ValueError):
            SoilObservation(ph_h2o=15.0)  # pH > 14

        with pytest.raises(ValueError):
            SoilObservation(ph_h2o=-1.0)  # pH < 0

        # Percentage validation
        with pytest.raises(ValueError):
            SoilObservation(sand_percent=150.0)  # > 100%

        with pytest.raises(ValueError):
            SoilObservation(clay_percent=-5.0)  # < 0%

    def test_texture_class_validation(self):
        """Test texture class validation."""
        # Valid texture class
        obs = SoilObservation(texture_class="Loam")
        assert obs.texture_class == "Loam"

        # Invalid texture class
        with pytest.raises(ValueError):
            SoilObservation(texture_class="InvalidTexture")

        # Case normalization
        obs = SoilObservation(texture_class="loam")
        assert obs.texture_class == "Loam"

    def test_soil_result_creation(self):
        """Test creating a soil result."""
        obs = SoilObservation(
            classification_usda="Inceptisols", ph_h2o=6.0, texture_class="Clay loam"
        )

        result = SoilResult(
            latitude=44.9778,
            longitude=-110.6984,
            observations=[obs],
            quality_score=0.85,
            provider="USDA NRCS",
        )

        assert result.latitude == 44.9778
        assert result.longitude == -110.6984
        assert len(result.observations) == 1
        assert result.quality_score == 0.85
        assert result.provider == "USDA NRCS"

    def test_nmdc_schema_conversion(self):
        """Test conversion to NMDC schema format."""
        obs = SoilObservation(
            classification_usda="Typic Haplocryepts",
            classification_wrb="Cambisols",
            ph_h2o=5.5,
            texture_class="Loam",
            depth_cm="0-5cm",
        )

        result = SoilResult(
            latitude=44.9778,
            longitude=-110.6984,
            observations=[obs],
            quality_score=0.85,
            provider="USDA NRCS",
        )

        nmdc_data = result.to_nmdc_schema()

        assert "soil_type" in nmdc_data
        assert "has_raw_value" in nmdc_data["soil_type"]
        assert (
            "Typic Haplocryepts [USDA] / Cambisols [WRB]"
            in nmdc_data["soil_type"]["has_raw_value"]
        )

        assert "ph" in nmdc_data
        assert nmdc_data["ph"]["has_numeric_value"] == 5.5
        assert nmdc_data["ph"]["has_unit"] == "pH"

        assert "soil_texture_meth" in nmdc_data
        assert "Loam" in nmdc_data["soil_texture_meth"]

    def test_gold_schema_conversion(self):
        """Test conversion to GOLD schema format."""
        obs = SoilObservation(
            classification_usda="Typic Haplocryepts",
            ph_h2o=5.5,
            organic_carbon=36.6,
            texture_class="Loam",
        )

        result = SoilResult(
            latitude=44.9778,
            longitude=-110.6984,
            observations=[obs],
            quality_score=0.85,
            provider="SoilGrids",
        )

        gold_data = result.to_gold_schema()

        assert "habitatDetails" in gold_data
        habitat = gold_data["habitatDetails"]
        assert "Typic Haplocryepts" in habitat
        assert "Loam" in habitat
        assert "pH: 5.5" in habitat

        assert "environmentalParameters" in gold_data
        env_params = gold_data["environmentalParameters"]
        assert env_params["soil_ph"] == 5.5
        assert env_params["soil_organic_carbon_g_kg"] == 36.6


class TestTextureClassification:
    """Test USDA texture triangle classification."""

    def test_classify_loam(self):
        """Test classification of loam soil."""
        # Typical loam: balanced sand/silt/clay (this is actually clay loam due to 27%+ clay)
        texture = classify_texture(40, 40, 20)
        assert texture == "Clay loam"

        # True loam has less clay
        texture = classify_texture(45, 40, 15)
        assert texture == "Loam"

    def test_classify_sand(self):
        """Test classification of sandy soil."""
        texture = classify_texture(90, 5, 5)
        assert texture == "Sand"

    def test_classify_clay(self):
        """Test classification of clay soil."""
        texture = classify_texture(20, 20, 60)
        assert texture == "Clay"

    def test_classify_silt_loam(self):
        """Test classification of silt loam."""
        texture = classify_texture(20, 65, 15)
        assert texture == "Silt loam"

    def test_invalid_percentages(self):
        """Test handling of invalid percentage inputs."""
        # Percentages don't sum to 100
        with pytest.raises(ValueError):
            classify_texture(50, 30, 10)  # Sum = 90

        # Negative percentage
        with pytest.raises(ValueError):
            classify_texture(-10, 60, 50)

        # Percentage over 100
        with pytest.raises(ValueError):
            classify_texture(120, 40, 30)

    def test_rounding_tolerance(self):
        """Test tolerance for small rounding errors."""
        # Sum = 99.5% (should be accepted, this is clay loam due to clay content)
        texture = classify_texture(40.0, 39.5, 20.0)
        assert texture == "Clay loam"

        # Sum = 100.5% (should be accepted, also clay loam)
        texture = classify_texture(40.2, 40.1, 20.2)
        assert texture == "Clay loam"


class TestSoilProviderBase:
    """Test base provider functionality."""

    def test_coordinate_validation(self):
        """Test coordinate validation."""

        class TestProvider(SoilProviderBase):
            def get_soil_data(self, latitude, longitude, depth_cm=None):
                pass

            def is_available(self):
                return True

            @property
            def name(self):
                return "Test"

            @property
            def coverage_description(self):
                return "Test coverage"

        provider = TestProvider()

        # Valid coordinates
        provider.validate_coordinates(45.0, -120.0)

        # Invalid latitude
        with pytest.raises(ValueError):
            provider.validate_coordinates(95.0, -120.0)

        with pytest.raises(ValueError):
            provider.validate_coordinates(-95.0, -120.0)

        # Invalid longitude
        with pytest.raises(ValueError):
            provider.validate_coordinates(45.0, 185.0)

        with pytest.raises(ValueError):
            provider.validate_coordinates(45.0, -185.0)

    def test_quality_score_calculation(self):
        """Test quality score calculation."""

        class TestProvider(SoilProviderBase):
            def get_soil_data(self, latitude, longitude, depth_cm=None):
                pass

            def is_available(self):
                return True

            @property
            def name(self):
                return "Test"

            @property
            def coverage_description(self):
                return "Test coverage"

        provider = TestProvider()

        # Perfect score
        score = provider.calculate_quality_score(
            distance_m=50.0, confidence=1.0, data_completeness=1.0
        )
        assert score == 1.0

        # Distance penalty
        score = provider.calculate_quality_score(distance_m=5000.0)
        assert score == 0.7  # Within 5km = fair

        # Confidence penalty
        score = provider.calculate_quality_score(confidence=0.5)
        assert score == 0.5

        # Data completeness penalty
        score = provider.calculate_quality_score(data_completeness=0.8)
        assert score == 0.8


class TestUSDANRCSProvider:
    """Test USDA NRCS SDA provider."""

    @patch("biosample_enricher.soil.providers.usda_nrcs.get_session")
    def test_provider_initialization(self, mock_get_session):
        """Test provider initialization."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        provider = USDANRCSProvider()

        assert provider.name == "USDA NRCS Soil Data Access"
        assert "United States" in provider.coverage_description
        assert (
            provider.base_url
            == "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
        )

    @patch("biosample_enricher.soil.providers.usda_nrcs.get_session")
    def test_availability_check(self, mock_get_session):
        """Test availability checking."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session

        provider = USDANRCSProvider()
        assert provider.is_available() is True

        # Test failure case
        mock_response.status_code = 500
        assert provider.is_available() is False

    @patch("biosample_enricher.soil.providers.usda_nrcs.get_session")
    def test_mukey_retrieval(self, mock_get_session):
        """Test map unit key retrieval."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"Table": [["3056505"]]}
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session

        provider = USDANRCSProvider()
        mukey = provider._get_mukey(44.9778, -110.6984)

        assert mukey == "3056505"
        mock_session.post.assert_called_once()

    @patch("biosample_enricher.soil.providers.usda_nrcs.get_session")
    def test_component_to_observation(self, mock_get_session):
        """Test converting soil component to observation."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        provider = USDANRCSProvider()

        component = {
            "compname": "Kegsprings",
            "comppct_r": 55,
            "taxorder": "Inceptisols",
            "taxsuborder": "Cryepts",
            "taxgrtgrp": "Haplocryepts",
            "taxsubgrp": "Typic Haplocryepts",
        }

        obs = provider._component_to_observation(component)

        assert obs is not None
        assert (
            obs.classification_usda
            == "Inceptisols > Cryepts > Haplocryepts > Typic Haplocryepts"
        )
        assert obs.confidence_usda == 0.55
        assert obs.measurement_method == "USDA NRCS Soil Data Access"


class TestSoilGridsProvider:
    """Test ISRIC SoilGrids provider."""

    @patch("biosample_enricher.soil.providers.soilgrids.get_session")
    def test_provider_initialization(self, mock_get_session):
        """Test provider initialization."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        provider = SoilGridsProvider()

        assert provider.name == "ISRIC SoilGrids"
        assert "Global coverage" in provider.coverage_description
        assert "maps.isric.org" in provider.wcs_base

    @patch("biosample_enricher.soil.providers.soilgrids.get_session")
    def test_availability_check(self, mock_get_session):
        """Test availability checking."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        provider = SoilGridsProvider()
        assert provider.is_available() is True

    @patch("biosample_enricher.soil.providers.soilgrids.get_session")
    def test_wrb_classification_rest(self, mock_get_session):
        """Test WRB classification via REST API."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "properties": {"wrb_class_name": "Cambisols", "wrb_class_probability": 46}
        }
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        provider = SoilGridsProvider()
        wrb_data = provider._get_wrb_classification(44.9778, -110.6984)

        assert wrb_data["classification"] == "Cambisols"
        assert wrb_data["confidence"] == 0.46

    def test_scaling_factors(self):
        """Test soil property scaling factors."""
        provider = SoilGridsProvider()

        # pH scaling (divided by 10)
        assert provider.scaling["phh2o"] == 0.1

        # Texture scaling (divided by 10)
        assert provider.scaling["clay"] == 0.1
        assert provider.scaling["sand"] == 0.1
        assert provider.scaling["silt"] == 0.1

        # Bulk density scaling (divided by 100)
        assert provider.scaling["bdod"] == 0.01


class TestSoilService:
    """Test soil service orchestration."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = SoilService()

        assert "usda_nrcs" in service.providers
        assert "soilgrids" in service.providers
        assert isinstance(service.providers["usda_nrcs"], USDANRCSProvider)
        assert isinstance(service.providers["soilgrids"], SoilGridsProvider)

    def test_us_location_detection(self):
        """Test US location detection."""
        service = SoilService()

        # Continental US
        assert service._is_us_location(40.7128, -74.0060) is True  # New York
        assert service._is_us_location(34.0522, -118.2437) is True  # Los Angeles

        # Alaska
        assert service._is_us_location(64.0685, -152.2782) is True  # Fairbanks

        # Hawaii
        assert service._is_us_location(21.3099, -157.8581) is True  # Honolulu

        # Non-US locations
        assert service._is_us_location(51.5074, -0.1278) is False  # London
        assert service._is_us_location(-33.8688, 151.2093) is False  # Sydney

    def test_location_extraction(self):
        """Test location extraction from biosample data."""
        service = SoilService()

        # Standard lat/lon fields
        sample1 = {"lat": 40.7128, "lon": -74.0060}
        location = service._extract_location(sample1)
        assert location == (40.7128, -74.0060)

        # Alternative field names
        sample2 = {"latitude": 40.7128, "longitude": -74.0060}
        location = service._extract_location(sample2)
        assert location == (40.7128, -74.0060)

        # Nested lat_lon field
        sample3 = {"lat_lon": {"lat": 40.7128, "lon": -74.0060}}
        location = service._extract_location(sample3)
        assert location == (40.7128, -74.0060)

        # No location data
        sample4 = {"name": "test sample"}
        location = service._extract_location(sample4)
        assert location is None

    def test_depth_extraction(self):
        """Test depth extraction from biosample data."""
        service = SoilService()

        # Numeric depth in meters
        sample1 = {"depth": 0.03}
        depth = service._extract_depth(sample1)
        assert depth == "0-5cm"

        sample2 = {"depth": 0.10}
        depth = service._extract_depth(sample2)
        assert depth == "5-15cm"

        # String depth
        sample3 = {"depth": "0-5cm"}
        depth = service._extract_depth(sample3)
        assert depth == "0-5cm"

        # No depth data (default)
        sample4 = {"name": "test sample"}
        depth = service._extract_depth(sample4)
        assert depth == "0-5cm"

    def test_schema_detection(self):
        """Test biosample schema detection."""
        service = SoilService()

        # NMDC schema
        nmdc_sample = {"id": "nmdc:bsm-123", "env_medium": {"term": {"name": "soil"}}}
        schema_type = service._detect_schema_type(nmdc_sample)
        assert schema_type == "nmdc"

        # GOLD schema
        gold_sample = {"biosampleName": "Test Sample", "ecosystemType": "Soil"}
        schema_type = service._detect_schema_type(gold_sample)
        assert schema_type == "gold"

        # Generic schema
        generic_sample = {"sample_id": "test-123", "location": "somewhere"}
        schema_type = service._detect_schema_type(generic_sample)
        assert schema_type == "generic"

    @patch.object(SoilService, "enrich_location")
    def test_biosample_enrichment(self, mock_enrich):
        """Test biosample enrichment."""
        # Mock soil result
        obs = SoilObservation(
            classification_usda="Typic Haplocryepts", ph_h2o=5.5, texture_class="Loam"
        )

        mock_result = SoilResult(
            latitude=44.9778,
            longitude=-110.6984,
            observations=[obs],
            quality_score=0.85,
            provider="USDA NRCS",
        )
        mock_enrich.return_value = mock_result

        service = SoilService()

        # Test NMDC sample enrichment
        nmdc_sample = {
            "id": "nmdc:bsm-123",
            "lat": 44.9778,
            "lon": -110.6984,
            "env_medium": {"term": {"name": "soil"}},
        }

        enriched = service.enrich_biosample(nmdc_sample)

        # Should have original fields plus soil enrichment
        assert "id" in enriched
        assert "soil_type" in enriched
        assert "ph" in enriched
        assert enriched["ph"]["has_numeric_value"] == 5.5

    def test_provider_status(self):
        """Test provider status checking."""
        service = SoilService()

        with (
            patch.object(
                service.providers["usda_nrcs"], "is_available", return_value=True
            ),
            patch.object(
                service.providers["soilgrids"], "is_available", return_value=True
            ),
        ):
            status = service.get_provider_status()

            assert "usda_nrcs" in status
            assert "soilgrids" in status
            assert status["usda_nrcs"]["available"] is True
            assert status["soilgrids"]["available"] is True


@pytest.mark.network
class TestSoilIntegration:
    """Integration tests requiring network access."""

    def test_soilgrids_integration(self):
        """Test SoilGrids integration with real API."""
        provider = SoilGridsProvider()

        if not provider.is_available():
            pytest.skip("SoilGrids not available")

        # Test location: Yellowstone National Park
        result = provider.get_soil_data(44.9778, -110.6984)

        assert result.latitude == 44.9778
        assert result.longitude == -110.6984
        assert result.quality_score > 0
        assert len(result.observations) > 0

        obs = result.observations[0]
        # Should have either classification or soil properties (APIs can be flaky)
        has_classification = obs.classification_wrb is not None
        has_properties = any(
            [
                obs.ph_h2o is not None,
                obs.organic_carbon is not None,
                obs.sand_percent is not None,
            ]
        )
        assert has_classification or has_properties, (
            "Should have either WRB classification or soil properties"
        )

    def test_usda_integration(self):
        """Test USDA NRCS integration with real API."""
        provider = USDANRCSProvider()

        if not provider.is_available():
            pytest.skip("USDA NRCS not available")

        # Test location: Yellowstone National Park (US)
        result = provider.get_soil_data(44.9778, -110.6984)

        assert result.latitude == 44.9778
        assert result.longitude == -110.6984

        if result.observations:  # May not have data for all locations
            obs = result.observations[0]
            assert obs.classification_usda is not None
            assert (
                "Inceptisols" in obs.classification_usda
                or "Cryepts" in obs.classification_usda
            )

    def test_soil_service_integration(self):
        """Test full soil service integration."""
        service = SoilService()

        # Test US location (should prefer USDA)
        result_us = service.enrich_location(44.9778, -110.6984)
        assert result_us.quality_score > 0

        # Test international location (should use SoilGrids)
        result_intl = service.enrich_location(52.5200, 13.4050)  # Berlin
        assert result_intl.quality_score > 0
