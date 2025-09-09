"""Tests for the CLI interface."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from biosample_enricher.cli import main
from biosample_enricher.core import BiosampleMetadata


@pytest.fixture
def runner() -> CliRunner:
    """Fixture providing a Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_metadata() -> BiosampleMetadata:
    """Fixture providing sample metadata for tests."""
    return BiosampleMetadata(
        sample_id="SAMN123456",
        source="ncbi",
        metadata={
            "organism": "Homo sapiens",
            "tissue": "blood",
        },
        confidence=0.9,
    )


class TestMainCommand:
    """Test the main CLI command group."""

    def test_main_help(self, runner: CliRunner) -> None:
        """Test the main help command."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Biosample Enricher" in result.output

    def test_main_version(self, runner: CliRunner) -> None:
        """Test the version option."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_main_timeout_option(self, runner: CliRunner) -> None:
        """Test the timeout option is passed through."""
        result = runner.invoke(main, ["--timeout", "60", "--help"])
        assert result.exit_code == 0


class TestEnrichCommand:
    """Test the enrich command."""

    @patch("biosample_enricher.cli.BiosampleEnricher")
    def test_enrich_basic(
        self,
        mock_enricher_class: Mock,
        runner: CliRunner,
        sample_metadata: BiosampleMetadata,
    ) -> None:
        """Test basic enrich command."""
        mock_enricher = Mock()
        mock_enricher_class.return_value.__enter__.return_value = mock_enricher
        mock_enricher.enrich_sample.return_value = [sample_metadata]

        result = runner.invoke(main, ["enrich", "--sample-id", "SAMN123456"])

        assert result.exit_code == 0
        mock_enricher.enrich_sample.assert_called_once_with("SAMN123456", None)

    @patch("biosample_enricher.cli.BiosampleEnricher")
    def test_enrich_with_sources(
        self,
        mock_enricher_class: Mock,
        runner: CliRunner,
        sample_metadata: BiosampleMetadata,
    ) -> None:
        """Test enrich command with specific sources."""
        mock_enricher = Mock()
        mock_enricher_class.return_value.__enter__.return_value = mock_enricher
        mock_enricher.enrich_sample.return_value = [sample_metadata]

        result = runner.invoke(
            main,
            [
                "enrich",
                "--sample-id",
                "SAMN123456",
                "--sources",
                "ncbi",
                "--sources",
                "ebi",
            ],
        )

        assert result.exit_code == 0
        mock_enricher.enrich_sample.assert_called_once_with(
            "SAMN123456", ["ncbi", "ebi"]
        )

    @patch("biosample_enricher.cli.BiosampleEnricher")
    def test_enrich_json_output(
        self,
        mock_enricher_class: Mock,
        runner: CliRunner,
        sample_metadata: BiosampleMetadata,
    ) -> None:
        """Test enrich command with JSON output."""
        mock_enricher = Mock()
        mock_enricher_class.return_value.__enter__.return_value = mock_enricher
        mock_enricher.enrich_sample.return_value = [sample_metadata]

        result = runner.invoke(
            main, ["enrich", "--sample-id", "SAMN123456", "--output-format", "json"]
        )

        assert result.exit_code == 0
        assert "SAMN123456" in result.output
        assert "ncbi" in result.output

    @patch("biosample_enricher.cli.BiosampleEnricher")
    def test_enrich_csv_output(
        self,
        mock_enricher_class: Mock,
        runner: CliRunner,
        sample_metadata: BiosampleMetadata,
    ) -> None:
        """Test enrich command with CSV output."""
        mock_enricher = Mock()
        mock_enricher_class.return_value.__enter__.return_value = mock_enricher
        mock_enricher.enrich_sample.return_value = [sample_metadata]

        result = runner.invoke(
            main, ["enrich", "--sample-id", "SAMN123456", "--output-format", "csv"]
        )

        assert result.exit_code == 0
        assert "sample_id,source,confidence,metadata" in result.output

    def test_enrich_missing_sample_id(self, runner: CliRunner) -> None:
        """Test enrich command without sample ID."""
        result = runner.invoke(main, ["enrich"])
        assert result.exit_code != 0
        assert "Missing option" in result.output


class TestBatchCommand:
    """Test the batch command."""

    @patch("biosample_enricher.cli.BiosampleEnricher")
    def test_batch_basic(
        self,
        mock_enricher_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
        sample_metadata: BiosampleMetadata,
    ) -> None:
        """Test basic batch command."""
        # Create input file
        input_file = tmp_path / "samples.txt"
        input_file.write_text("SAMN123456\nSAMN789012\n")

        mock_enricher = Mock()
        mock_enricher_class.return_value.__enter__.return_value = mock_enricher
        mock_enricher.enrich_multiple.return_value = {
            "SAMN123456": [sample_metadata],
            "SAMN789012": [sample_metadata],
        }

        result = runner.invoke(main, ["batch", "--input-file", str(input_file)])

        assert result.exit_code == 0
        mock_enricher.enrich_multiple.assert_called_once()
        call_args = mock_enricher.enrich_multiple.call_args[0]
        assert "SAMN123456" in call_args[0]
        assert "SAMN789012" in call_args[0]

    @patch("biosample_enricher.cli.BiosampleEnricher")
    def test_batch_with_output_file(
        self,
        mock_enricher_class: Mock,
        runner: CliRunner,
        tmp_path: Path,
        sample_metadata: BiosampleMetadata,
    ) -> None:
        """Test batch command with output file."""
        # Create input file
        input_file = tmp_path / "samples.txt"
        input_file.write_text("SAMN123456\n")

        output_file = tmp_path / "results.json"

        mock_enricher = Mock()
        mock_enricher_class.return_value.__enter__.return_value = mock_enricher
        mock_enricher.enrich_multiple.return_value = {"SAMN123456": [sample_metadata]}

        result = runner.invoke(
            main,
            [
                "batch",
                "--input-file",
                str(input_file),
                "--output-file",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "SAMN123456" in content

    def test_batch_missing_input_file(self, runner: CliRunner) -> None:
        """Test batch command without input file."""
        result = runner.invoke(main, ["batch"])
        assert result.exit_code != 0

    def test_batch_nonexistent_input_file(self, runner: CliRunner) -> None:
        """Test batch command with nonexistent input file."""
        result = runner.invoke(main, ["batch", "--input-file", "nonexistent.txt"])
        assert result.exit_code != 0

    def test_batch_empty_input_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test batch command with empty input file."""
        input_file = tmp_path / "empty.txt"
        input_file.write_text("")

        result = runner.invoke(main, ["batch", "--input-file", str(input_file)])
        assert result.exit_code != 0

    def test_batch_input_file_with_comments(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test batch command with input file containing comments."""
        input_file = tmp_path / "samples.txt"
        input_file.write_text(
            "# This is a comment\nSAMN123456\n# Another comment\nSAMN789012\n"
        )

        with patch("biosample_enricher.cli.BiosampleEnricher") as mock_enricher_class:
            mock_enricher = Mock()
            mock_enricher_class.return_value.__enter__.return_value = mock_enricher
            mock_enricher.enrich_multiple.return_value = {}

            result = runner.invoke(main, ["batch", "--input-file", str(input_file)])

            assert result.exit_code == 0
            call_args = mock_enricher.enrich_multiple.call_args[0]
            sample_ids = call_args[0]
            assert len(sample_ids) == 2
            assert "SAMN123456" in sample_ids
            assert "SAMN789012" in sample_ids


class TestValidateCommand:
    """Test the validate command."""

    def test_validate_basic(self, runner: CliRunner) -> None:
        """Test basic validate command."""
        result = runner.invoke(main, ["validate", "--sample-id", "SAMN123456"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_missing_sample_id(self, runner: CliRunner) -> None:
        """Test validate command without sample ID."""
        result = runner.invoke(main, ["validate"])
        assert result.exit_code != 0
