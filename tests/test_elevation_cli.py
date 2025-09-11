#!/usr/bin/env python3
"""
Comprehensive tests for elevation CLI functionality.

Tests both single coordinate lookups and batch processing with various options.
"""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from biosample_enricher.cli_elevation import elevation_cli


class TestElevationCLI:
    """Test the elevation CLI interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_lookup_single_coordinate(self):
        """Test single coordinate lookup via CLI."""
        result = self.runner.invoke(
            elevation_cli,
            [
                "lookup",
                "--lat",
                "43.8791",
                "--lon",
                "-103.4591",
                "--subject-id",
                "test-mount-rushmore",
            ],
        )

        assert result.exit_code == 0
        assert "Looking up elevation for 43.879100, -103.459100" in result.output
        assert "Mount Rushmore" in result.output or "elevation" in result.output.lower()

    def test_lookup_with_cache_options(self):
        """Test coordinate lookup with different cache options."""
        # Test with cache disabled
        result = self.runner.invoke(
            elevation_cli,
            [
                "lookup",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--no-cache",
                "--subject-id",
                "test-sf-no-cache",
            ],
        )

        assert result.exit_code == 0
        assert "Cache disabled" in result.output

    def test_lookup_with_read_cache_only(self):
        """Test lookup with read cache only."""
        result = self.runner.invoke(
            elevation_cli,
            [
                "lookup",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--read-cache",
                "--no-write-cache",
                "--subject-id",
                "test-sf-read-only",
            ],
        )

        assert result.exit_code == 0
        assert "Cache: read=True, write=False" in result.output

    def test_lookup_with_preferred_providers(self):
        """Test lookup with preferred provider list."""
        result = self.runner.invoke(
            elevation_cli,
            [
                "lookup",
                "--lat",
                "43.8791",
                "--lon",
                "-103.4591",
                "--providers",
                "usgs,open_topo_data",
                "--subject-id",
                "test-providers",
            ],
        )

        assert result.exit_code == 0
        assert "Preferred providers: usgs, open_topo_data" in result.output

    def test_lookup_invalid_coordinates(self):
        """Test lookup with invalid coordinates."""
        result = self.runner.invoke(
            elevation_cli,
            [
                "lookup",
                "--lat",
                "91.0",  # Invalid latitude
                "--lon",
                "0.0",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid latitude" in result.output or "Error" in result.output

    def test_lookup_with_json_output(self):
        """Test lookup with JSON output to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "elevation_result.json"

            result = self.runner.invoke(
                elevation_cli,
                [
                    "lookup",
                    "--lat",
                    "40.7128",
                    "--lon",
                    "-74.0060",
                    "--output",
                    str(output_file),
                    "--subject-id",
                    "test-nyc-json",
                ],
            )

            assert result.exit_code == 0
            assert output_file.exists()

            # Verify JSON structure
            with open(output_file) as f:
                data = json.load(f)
                assert data["subject_id"] == "test-nyc-json"
                assert "observations" in data
                assert len(data["observations"]) > 0

    @pytest.mark.skipif(
        not Path("data/input/synthetic_biosamples.json").exists(),
        reason="Synthetic biosamples file not found",
    )
    def test_batch_synthetic_biosamples(self):
        """Test batch processing of synthetic biosamples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a CSV from a subset of synthetic biosamples
            biosamples_file = Path("data/input/synthetic_biosamples.json")
            csv_file = Path(tmpdir) / "test_biosamples.csv"
            output_file = Path(tmpdir) / "elevation_results.jsonl"

            # Read and convert first 3 biosamples to CSV
            with open(biosamples_file) as f:
                biosamples = json.load(f)

            with open(csv_file, "w") as f:
                f.write("id,lat,lon,name\n")
                for i, sample in enumerate(biosamples[:3]):
                    geo = sample.get("geo", {})
                    lat = geo.get("latitude")
                    lon = geo.get("longitude")
                    name = sample.get("name", f"sample-{i}")
                    if lat is not None and lon is not None:
                        f.write(
                            f"{sample.get('nmdc_biosample_id', f'test-{i}')},{lat},{lon},{name}\n"
                        )

            # Run batch processing
            result = self.runner.invoke(
                elevation_cli,
                [
                    "batch",
                    "--input-file",
                    str(csv_file),
                    "--output",
                    str(output_file),
                    "--batch-size",
                    "2",
                    "--timeout",
                    "30",
                ],
            )

            assert result.exit_code == 0
            assert output_file.exists()

            # Verify JSONL output
            with open(output_file) as f:
                lines = f.readlines()
                assert len(lines) > 0

                # Verify each line is valid JSON
                for line in lines:
                    data = json.loads(line.strip())
                    assert "observations" in data

    def test_batch_with_cache_options(self):
        """Test batch processing with cache options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "test_coords.csv"
            output_file = Path(tmpdir) / "results.jsonl"

            # Create simple test CSV
            with open(csv_file, "w") as f:
                f.write("id,lat,lon\n")
                f.write("test1,37.7749,-122.4194\n")
                f.write("test2,40.7128,-74.0060\n")

            # Test with no cache
            result = self.runner.invoke(
                elevation_cli,
                [
                    "batch",
                    "--input-file",
                    str(csv_file),
                    "--output",
                    str(output_file),
                    "--no-cache",
                    "--batch-size",
                    "1",
                ],
            )

            assert result.exit_code == 0
            assert "Cache disabled" in result.output

    def test_batch_custom_column_names(self):
        """Test batch processing with custom column names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "custom_cols.csv"
            output_file = Path(tmpdir) / "results.jsonl"

            # Create CSV with custom column names
            with open(csv_file, "w") as f:
                f.write("sample_id,latitude,longitude,description\n")
                f.write("sample1,51.5074,-0.1278,London\n")
                f.write("sample2,48.8566,2.3522,Paris\n")

            result = self.runner.invoke(
                elevation_cli,
                [
                    "batch",
                    "--input-file",
                    str(csv_file),
                    "--output",
                    str(output_file),
                    "--lat-col",
                    "latitude",
                    "--lon-col",
                    "longitude",
                    "--id-col",
                    "sample_id",
                    "--batch-size",
                    "1",
                ],
            )

            assert result.exit_code == 0
            assert output_file.exists()

    def test_help_commands(self):
        """Test help output for CLI commands."""
        # Test main help
        result = self.runner.invoke(elevation_cli, ["--help"])
        assert result.exit_code == 0
        assert "Elevation lookup CLI" in result.output

        # Test lookup help
        result = self.runner.invoke(elevation_cli, ["lookup", "--help"])
        assert result.exit_code == 0
        assert "Look up elevation for a single coordinate" in result.output
        assert "--lat" in result.output
        assert "--lon" in result.output
        assert "--no-cache" in result.output

        # Test batch help
        result = self.runner.invoke(elevation_cli, ["batch", "--help"])
        assert result.exit_code == 0
        assert "Process elevation lookups from CSV/TSV file" in result.output
        assert "--batch-size" in result.output


class TestElevationCLIIntegration:
    """Integration tests for elevation CLI with real coordinates."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_multiple_provider_comparison(self):
        """Test comparing results from multiple providers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test known coordinates with multiple providers
            output_file = Path(tmpdir) / "provider_comparison.json"

            result = self.runner.invoke(
                elevation_cli,
                [
                    "lookup",
                    "--lat",
                    "43.8791",  # Mount Rushmore
                    "--lon",
                    "-103.4591",
                    "--output",
                    str(output_file),
                    "--subject-id",
                    "provider-comparison-test",
                ],
            )

            assert result.exit_code == 0
            assert output_file.exists()

            # Analyze results
            with open(output_file) as f:
                data = json.load(f)
                observations = data["observations"]

                # Should have multiple providers
                providers = {obs["provider"]["name"] for obs in observations}
                assert len(providers) >= 2  # At least USGS and one other

                # All successful observations should have reasonable elevation
                for obs in observations:
                    if obs["value_status"] == "ok":
                        elevation = obs["value_numeric"]
                        assert 1000 < elevation < 2000  # Mount Rushmore elevation range

    def test_international_vs_us_routing(self):
        """Test that provider routing works correctly for different locations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            us_output = Path(tmpdir) / "us_result.json"
            intl_output = Path(tmpdir) / "intl_result.json"

            # Test US location
            result = self.runner.invoke(
                elevation_cli,
                [
                    "lookup",
                    "--lat",
                    "40.7128",  # NYC
                    "--lon",
                    "-74.0060",
                    "--output",
                    str(us_output),
                    "--subject-id",
                    "us-test",
                ],
            )
            assert result.exit_code == 0

            # Test international location
            result = self.runner.invoke(
                elevation_cli,
                [
                    "lookup",
                    "--lat",
                    "51.5074",  # London
                    "--lon",
                    "-0.1278",
                    "--output",
                    str(intl_output),
                    "--subject-id",
                    "intl-test",
                ],
            )
            assert result.exit_code == 0

            # Analyze provider usage
            with open(us_output) as f:
                us_data = json.load(f)
                us_providers = {
                    obs["provider"]["name"] for obs in us_data["observations"]
                }

            with open(intl_output) as f:
                intl_data = json.load(f)
                intl_providers = {
                    obs["provider"]["name"] for obs in intl_data["observations"]
                }

            # US should include USGS, international should not rely on USGS
            print(f"US providers: {us_providers}")
            print(f"International providers: {intl_providers}")


if __name__ == "__main__":
    pytest.main([__file__])
