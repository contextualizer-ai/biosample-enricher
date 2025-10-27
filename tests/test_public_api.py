"""Tests for the public API exports in __init__.py."""


class TestPublicAPIImports:
    """Test that public API can be imported from the top-level package."""

    def test_version_import(self):
        """Test that __version__ can be imported."""
        from biosample_enricher import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_services_import(self):
        """Test that all services can be imported."""
        from biosample_enricher import (
            ElevationService,
            ForwardGeocodingService,
            LandService,
            MarineService,
            OSMFeaturesService,
            ReverseGeocodingService,
            SoilService,
            WeatherService,
        )

        # Verify they are classes
        assert isinstance(ElevationService, type)
        assert isinstance(SoilService, type)
        assert isinstance(WeatherService, type)
        assert isinstance(MarineService, type)
        assert isinstance(LandService, type)
        assert isinstance(ReverseGeocodingService, type)
        assert isinstance(ForwardGeocodingService, type)
        assert isinstance(OSMFeaturesService, type)

    def test_models_import(self):
        """Test that core models can be imported."""
        from biosample_enricher import (
            ElevationRequest,
            GeoPoint,
            Observation,
            ProviderRef,
            ValueStatus,
            Variable,
        )

        # Verify they are classes
        assert isinstance(GeoPoint, type)
        assert isinstance(Observation, type)
        assert isinstance(ProviderRef, type)
        assert isinstance(Variable, type)
        assert isinstance(ValueStatus, type)
        assert isinstance(ElevationRequest, type)

    def test_all_exports(self):
        """Test that __all__ contains all expected exports."""
        import biosample_enricher

        expected_exports = {
            "__version__",
            # Services
            "ElevationService",
            "SoilService",
            "WeatherService",
            "MarineService",
            "LandService",
            "ReverseGeocodingService",
            "ForwardGeocodingService",
            "OSMFeaturesService",
            # Models
            "GeoPoint",
            "Observation",
            "ProviderRef",
            "Variable",
            "ValueStatus",
            "ElevationRequest",
        }

        assert set(biosample_enricher.__all__) == expected_exports

    def test_service_instantiation(self):
        """Test that services can be instantiated."""
        from biosample_enricher import ElevationService, SoilService, WeatherService

        # Should be able to create instances
        elev_service = ElevationService()
        assert elev_service is not None

        soil_service = SoilService()
        assert soil_service is not None

        weather_service = WeatherService()
        assert weather_service is not None

    def test_model_creation(self):
        """Test that models can be created."""
        from biosample_enricher import ElevationRequest, GeoPoint

        # Create a GeoPoint
        point = GeoPoint(lat=40.7128, lon=-74.0060)
        assert point.lat == 40.7128
        assert point.lon == -74.0060

        # Create an ElevationRequest
        request = ElevationRequest(latitude=40.7128, longitude=-74.0060)
        assert request.latitude == 40.7128
        assert request.longitude == -74.0060


class TestPublicAPIUsage:
    """Test realistic usage patterns of the public API."""

    def test_elevation_workflow(self):
        """Test a complete elevation workflow using public API."""
        from biosample_enricher import ElevationRequest, ElevationService

        service = ElevationService()
        request = ElevationRequest(latitude=40.7128, longitude=-74.0060)

        # This should work without errors
        observations = service.get_elevation(request, timeout_s=10)

        assert isinstance(observations, list)
        # Should get at least one observation (may vary based on providers)
        assert len(observations) >= 0

    def test_docstring_example(self):
        """Test the example from the module docstring."""
        from biosample_enricher import ElevationRequest, ElevationService

        service = ElevationService()
        request = ElevationRequest(latitude=40.7128, longitude=-74.0060)
        observations = service.get_elevation(request)

        # Should return a list of observations
        assert isinstance(observations, list)
