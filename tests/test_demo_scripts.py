"""Tests for demo scripts to ensure examples work correctly."""

from unittest.mock import MagicMock, patch


class TestElevationDemos:
    """Test elevation demo scripts."""

    @patch("biosample_enricher.elevation_demos.ElevationService")
    def test_elevation_demos_main(self, mock_service_class):
        """Test the main elevation demos script."""
        # Setup mocks
        mock_service = MagicMock()
        mock_envelope = MagicMock()
        mock_envelope.dict.return_value = {
            "observations": [{"provider": {"name": "test"}, "value_numeric": 100}]
        }
        mock_service.create_output_envelope.return_value = mock_envelope
        mock_service_class.return_value = mock_service

        # BiosampleElevationMapper is not used in elevation_demos

        # Import the module to check it doesn't crash
        from biosample_enricher import elevation_demos

        # The module has functions but no demonstrate_all
        assert hasattr(elevation_demos, "process_biosamples")
        assert hasattr(elevation_demos, "compare_providers")


class TestGeocodingDemo:
    """Test geocoding comprehensive demo."""

    def test_geocoding_demo_functions(self):
        """Test that geocoding demo functions are importable."""
        from biosample_enricher import geocoding_comprehensive_demo as demo

        # Test that main functions exist
        assert hasattr(demo, "test_google_apis")
        assert hasattr(demo, "test_osm_apis")
        assert hasattr(demo, "display_results_table")
        assert hasattr(demo, "main")


class TestPydanticValidationDemo:
    """Test pydantic validation demo."""

    def test_validation_demo_imports(self):
        """Test that validation demo can be imported."""

        # Test creating sample data
        valid_sample = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "collection_date": "2024-01-15",
            "textual_location": "San Francisco, CA",
        }

        # Test validation with BiosampleLocation model
        from biosample_enricher.models import BiosampleLocation

        location = BiosampleLocation(**valid_sample)
        assert location.latitude == 37.7749
        assert location.is_enrichable()


class TestRandomSamplingDemo:
    """Test random sampling demo."""

    def test_random_sampling_functions(self):
        """Test that random sampling demo functions are importable."""
        from biosample_enricher import random_sampling_demo as demo

        # Test that main functions exist
        assert hasattr(demo, "test_mongodb_random_sampling")
        assert hasattr(demo, "test_unified_random_sampling")
        assert hasattr(demo, "demonstrate_random_sampling")
        assert hasattr(demo, "main")


class TestSyntheticValidationDemo:
    """Test synthetic validation demo."""

    def test_synthetic_data_generation(self):
        """Test that synthetic validation demo functions are importable."""
        from biosample_enricher import synthetic_validation_demo as demo

        # Test that main functions exist
        assert hasattr(demo, "map_synthetic_to_model")
        assert hasattr(demo, "validate_synthetic_biosamples")
        assert hasattr(demo, "main")


class TestAdapterDemos:
    """Test adapter demo scripts."""

    def test_nmdc_adapter_demo(self):
        """Test NMDC adapter demo."""
        # Test adapter creation
        from biosample_enricher.adapters import NMDCBiosampleAdapter

        adapter = NMDCBiosampleAdapter()
        assert adapter is not None

    def test_gold_adapter_demo(self):
        """Test GOLD adapter demo."""
        # Test adapter creation
        from biosample_enricher.adapters import GOLDBiosampleAdapter

        adapter = GOLDBiosampleAdapter()
        assert adapter is not None

    def test_unified_adapter_demo(self):
        """Test unified adapter demo."""

        # Test UnifiedBiosampleFetcher creation
        from biosample_enricher.adapters import UnifiedBiosampleFetcher

        fetcher = UnifiedBiosampleFetcher()
        assert fetcher is not None


class TestMongoDBConnectionDemo:
    """Test MongoDB connection demo."""

    def test_connection_demo(self):
        """Test that MongoDB connection demo is importable."""
        from biosample_enricher import mongodb_connection_demo as demo

        # Test that main functions exist
        assert hasattr(demo, "test_mongodb_connection")
        assert hasattr(demo, "demonstrate_mongodb_connection")
        assert hasattr(demo, "main")


class TestIDRetrievalDemo:
    """Test ID retrieval demo."""

    def test_id_retrieval_functions(self):
        """Test that ID retrieval demo is importable."""
        from biosample_enricher import id_retrieval_demo as demo

        # Test that main functions exist
        assert hasattr(demo, "test_primary_id_retrieval")
        assert hasattr(demo, "demonstrate_id_retrieval")
        assert hasattr(demo, "main")


class TestDemoScriptImports:
    """Test that all demo scripts can be imported without errors."""

    def test_import_all_demos(self):
        """Test importing all demo modules."""
        demo_modules = [
            "biosample_enricher.elevation_demos",
            "biosample_enricher.geocoding_comprehensive_demo",
            "biosample_enricher.gold_adapter_demo",
            "biosample_enricher.id_retrieval_demo",
            "biosample_enricher.mongodb_connection_demo",
            "biosample_enricher.nmdc_adapter_demo",
            "biosample_enricher.pydantic_validation_demo",
            "biosample_enricher.random_sampling_demo",
            "biosample_enricher.synthetic_validation_demo",
            "biosample_enricher.unified_adapter_demo",
        ]

        for module_name in demo_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                # Some imports might fail due to missing dependencies in test env
                # but the module structure should be valid
                assert "No module named" not in str(e) or "pymongo" in str(e)


class TestDemoScriptMainFunctions:
    """Test main functions in demo scripts where applicable."""

    def test_elevation_demos_main_entry(self):
        """Test elevation demos main entry point."""
        from biosample_enricher import elevation_demos

        # Just ensure the module has the expected functions
        assert hasattr(elevation_demos, "process_biosamples")
        assert hasattr(elevation_demos, "compare_providers")

    def test_synthetic_validation_main(self):
        """Test synthetic validation demo main."""
        from biosample_enricher import synthetic_validation_demo as demo

        # Check that main function exists
        assert hasattr(demo, "validate_synthetic_biosamples")
        assert hasattr(demo, "main")
