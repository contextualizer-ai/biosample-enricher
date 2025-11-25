"""
Tests for the CLI that wraps get_submission_values() for NMDC metadata suggestions.

Tests the CLI interface for get_submission_values() including:
- get command with various options
- info command
- slots/providers/strategies helper commands
- error handling
"""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from biosample_enricher.cli import main


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


class TestCLIHelp:
    """Test help commands work correctly."""

    def test_main_help(self, runner: CliRunner) -> None:
        """Test main CLI help."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Get NMDC submission-schema values" in result.output
        assert "get" in result.output
        assert "info" in result.output

    def test_get_help(self, runner: CliRunner) -> None:
        """Test get command help."""
        result = runner.invoke(main, ["get", "--help"])
        assert result.exit_code == 0
        assert "--lat" in result.output
        assert "--lon" in result.output
        assert "--slots" in result.output
        assert "--datetime" in result.output
        assert "--strategy" in result.output
        assert "--providers" in result.output

    def test_info_help(self, runner: CliRunner) -> None:
        """Test info command help."""
        result = runner.invoke(main, ["info", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output

    def test_version(self, runner: CliRunner) -> None:
        """Test version option."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        # Should show version number


class TestInfoCommand:
    """Test the info command."""

    def test_info_text_format(self, runner: CliRunner) -> None:
        """Test info command with default text format."""
        result = runner.invoke(main, ["info"])
        assert result.exit_code == 0
        assert "SUPPORTED SLOTS" in result.output
        assert "CLIMATE" in result.output
        assert "annual_precpt" in result.output
        assert "annual_temp" in result.output
        assert "CONSENSUS STRATEGIES" in result.output
        assert "mean" in result.output

    def test_info_json_format(self, runner: CliRunner) -> None:
        """Test info command with JSON format."""
        result = runner.invoke(main, ["info", "--format", "json"])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "slots" in data
        assert "climate" in data["slots"]
        assert "annual_precpt" in data["slots"]["climate"]["names"]
        assert "consensus_strategies" in data
        assert "mean" in data["consensus_strategies"]


class TestSlotsCommand:
    """Test the slots helper command."""

    def test_slots_lists_all(self, runner: CliRunner) -> None:
        """Test slots command lists all slots."""
        result = runner.invoke(main, ["slots"])
        assert result.exit_code == 0

        slots = result.output.strip().split("\n")
        assert "annual_precpt" in slots
        assert "annual_temp" in slots
        assert "elev" in slots
        assert len(slots) >= 10  # Should have at least 10 slots


class TestProvidersCommand:
    """Test the providers helper command."""

    def test_providers_all(self, runner: CliRunner) -> None:
        """Test providers command lists all."""
        result = runner.invoke(main, ["providers"])
        assert result.exit_code == 0
        assert "climate:meteostat" in result.output
        assert "climate:nasa_power" in result.output
        assert "elevation:" in result.output

    def test_providers_climate_only(self, runner: CliRunner) -> None:
        """Test providers command with climate filter."""
        result = runner.invoke(main, ["providers", "--category", "climate"])
        assert result.exit_code == 0
        assert "climate:meteostat" in result.output
        assert "climate:nasa_power" in result.output
        assert "elevation:" not in result.output

    def test_providers_elevation_only(self, runner: CliRunner) -> None:
        """Test providers command with elevation filter."""
        result = runner.invoke(main, ["providers", "--category", "elevation"])
        assert result.exit_code == 0
        assert "elevation:" in result.output
        assert "climate:" not in result.output


class TestStrategiesCommand:
    """Test the strategies helper command."""

    def test_strategies_lists_all(self, runner: CliRunner) -> None:
        """Test strategies command lists all strategies."""
        result = runner.invoke(main, ["strategies"])
        assert result.exit_code == 0

        strategies = result.output.strip().split("\n")
        assert "mean" in strategies
        assert "median" in strategies
        assert "first" in strategies
        assert "best_quality" in strategies


class TestGetCommandValidation:
    """Test get command input validation."""

    @pytest.mark.unit
    def test_missing_required_options(self, runner: CliRunner) -> None:
        """Test error when required options missing."""
        # Missing --slots
        result = runner.invoke(main, ["get", "--lat", "37.7", "--lon", "-122.4"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

        # Missing --lat
        result = runner.invoke(main, ["get", "--lon", "-122.4", "--slots", "elev"])
        assert result.exit_code != 0

        # Missing --lon
        result = runner.invoke(main, ["get", "--lat", "37.7", "--slots", "elev"])
        assert result.exit_code != 0

    @pytest.mark.unit
    def test_invalid_latitude(self, runner: CliRunner) -> None:
        """Test error for invalid latitude."""
        result = runner.invoke(
            main, ["get", "--lat", "91", "--lon", "-122.4", "--slots", "elev"]
        )
        assert result.exit_code != 0
        assert "Latitude" in result.output or "Error" in result.output

    @pytest.mark.unit
    def test_invalid_longitude(self, runner: CliRunner) -> None:
        """Test error for invalid longitude."""
        result = runner.invoke(
            main, ["get", "--lat", "37.7", "--lon", "181", "--slots", "elev"]
        )
        assert result.exit_code != 0
        assert "Longitude" in result.output or "Error" in result.output

    @pytest.mark.unit
    def test_invalid_slot(self, runner: CliRunner) -> None:
        """Test error for invalid slot name."""
        result = runner.invoke(
            main,
            ["get", "--lat", "37.7", "--lon", "-122.4", "--slots", "invalid_slot"],
        )
        assert result.exit_code != 0
        assert "Unsupported slot" in result.output or "Error" in result.output

    @pytest.mark.unit
    def test_empty_slots(self, runner: CliRunner) -> None:
        """Test error for empty slots."""
        result = runner.invoke(
            main, ["get", "--lat", "37.7", "--lon", "-122.4", "--slots", ""]
        )
        assert result.exit_code != 0

    @pytest.mark.unit
    def test_invalid_datetime_format(self, runner: CliRunner) -> None:
        """Test error for invalid datetime format."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "37.7",
                "--lon",
                "-122.4",
                "--slots",
                "temp",
                "--datetime",
                "not-a-date",
            ],
        )
        assert result.exit_code != 0
        assert "Invalid datetime" in result.output or "Error" in result.output


@pytest.mark.network
class TestGetCommandNetwork:
    """Test get command with real network calls."""

    def test_get_climate_data(self, runner: CliRunner) -> None:
        """Test getting climate data."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--slots",
                "annual_precpt,annual_temp",
            ],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "values" in data
        assert "annual_precpt" in data["values"]
        assert "annual_temp" in data["values"]
        assert isinstance(data["values"]["annual_precpt"], float)
        assert isinstance(data["values"]["annual_temp"], float)

    def test_get_elevation(self, runner: CliRunner) -> None:
        """Test getting elevation data."""
        result = runner.invoke(
            main,
            ["get", "--lat", "40.7128", "--lon", "-74.0060", "--slots", "elev"],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "values" in data
        assert "elev" in data["values"]
        assert isinstance(data["values"]["elev"], float)

    def test_get_multiple_slots(self, runner: CliRunner) -> None:
        """Test getting multiple slot types together."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "42.3601",
                "--lon",
                "-71.0589",
                "--slots",
                "annual_precpt,annual_temp,elev",
            ],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "values" in data
        assert len(data["values"]) >= 2  # Should get at least climate + elevation

    def test_get_all_slots(self, runner: CliRunner) -> None:
        """Test getting all slots with 'all' keyword."""
        result = runner.invoke(
            main,
            ["get", "--lat", "37.7749", "--lon", "-122.4194", "--slots", "all"],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "values" in data
        # Should get at least the reliable slots
        assert "annual_precpt" in data["values"] or "elev" in data["values"]

    def test_get_with_specific_provider(self, runner: CliRunner) -> None:
        """Test getting data with specific provider."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--slots",
                "annual_precpt",
                "--providers",
                "meteostat",
            ],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "values" in data
        assert "metadata" in data
        # Should only use meteostat
        if "climate_normals" in data["metadata"]:
            providers = data["metadata"]["climate_normals"]["providers_used"]
            assert "meteostat" in providers
            assert "nasa_power" not in providers

    def test_get_with_median_strategy(self, runner: CliRunner) -> None:
        """Test getting data with median consensus strategy."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--slots",
                "elev",
                "--strategy",
                "median",
            ],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "values" in data

    def test_get_values_only(self, runner: CliRunner) -> None:
        """Test --values-only flag."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--slots",
                "annual_precpt",
                "--values-only",
            ],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        # Should only have values, no metadata wrapper
        assert "annual_precpt" in data
        assert "metadata" not in data
        assert "values" not in data

    def test_get_compact_output(self, runner: CliRunner) -> None:
        """Test --compact flag produces single-line JSON."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--slots",
                "annual_precpt",
                "--compact",
            ],
        )
        assert result.exit_code == 0

        # Compact output should be single line
        lines = result.output.strip().split("\n")
        assert len(lines) == 1

        # Should still be valid JSON
        data = json.loads(result.output)
        assert "values" in data

    def test_get_output_to_file(self, runner: CliRunner) -> None:
        """Test --output flag writes to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "result.json"

            result = runner.invoke(
                main,
                [
                    "get",
                    "--lat",
                    "37.7749",
                    "--lon",
                    "-122.4194",
                    "--slots",
                    "annual_precpt",
                    "--output",
                    str(output_file),
                ],
            )
            assert result.exit_code == 0
            assert output_file.exists()

            # Verify file contents
            with open(output_file) as f:
                data = json.load(f)
                assert "values" in data
                assert "annual_precpt" in data["values"]

    def test_get_weather_with_datetime(self, runner: CliRunner) -> None:
        """Test getting weather data with datetime."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--slots",
                "temp",
                "--datetime",
                "2023-07-15",
            ],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "values" in data
        # temp should be present when datetime provided
        if "temp" in data["values"]:
            assert isinstance(data["values"]["temp"], float)

    def test_get_weather_with_datetime_and_time(self, runner: CliRunner) -> None:
        """Test datetime with full ISO format including time."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--slots",
                "temp",
                "--datetime",
                "2023-07-15T14:30:00",
            ],
        )
        assert result.exit_code == 0


@pytest.mark.network
class TestGetCommandMetadata:
    """Test metadata in get command results."""

    def test_climate_metadata_structure(self, runner: CliRunner) -> None:
        """Test climate metadata has expected structure."""
        result = runner.invoke(
            main,
            [
                "get",
                "--lat",
                "37.7749",
                "--lon",
                "-122.4194",
                "--slots",
                "annual_precpt,annual_temp",
            ],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "metadata" in data
        assert "climate_normals" in data["metadata"]

        climate_meta = data["metadata"]["climate_normals"]
        assert "providers_used" in climate_meta
        assert "provider_results" in climate_meta
        assert isinstance(climate_meta["providers_used"], list)

    def test_elevation_metadata_structure(self, runner: CliRunner) -> None:
        """Test elevation metadata has expected structure."""
        result = runner.invoke(
            main,
            ["get", "--lat", "37.7749", "--lon", "-122.4194", "--slots", "elev"],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert "metadata" in data
        # Elevation may have its own metadata section
        if "elevation" in data["metadata"]:
            elev_meta = data["metadata"]["elevation"]
            assert "providers_used" in elev_meta or "provider_results" in elev_meta
