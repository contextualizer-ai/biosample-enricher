"""Tests for the main CLI entry point."""

from click.testing import CliRunner

from biosample_enricher import __version__
from biosample_enricher.cli import main, show_version


class TestMainCLI:
    """Test the main CLI interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_help(self):
        """Test main CLI help output."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Biosample Enricher" in result.output
        assert "elevation" in result.output  # Should show elevation subcommand

    def test_main_version(self):
        """Test version flag."""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_show_version_function(self):
        """Test the show_version function directly."""
        # Capture stdout
        result = self.runner.invoke(main, ["--version"])
        assert __version__ in result.output

        # Test function directly
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output
        show_version()
        sys.stdout = sys.__stdout__
        assert captured_output.getvalue().strip() == __version__

    def test_elevation_subcommand_available(self):
        """Test that elevation subcommand is available."""
        result = self.runner.invoke(main, ["elevation", "--help"])
        assert result.exit_code == 0
        assert "Elevation lookup CLI" in result.output

    def test_invalid_command(self):
        """Test invalid command shows error."""
        result = self.runner.invoke(main, ["invalid-command"])
        assert result.exit_code != 0
        assert "Error" in result.output or "No such command" in result.output

    def test_no_arguments_shows_help(self):
        """Test that running with no arguments shows help."""
        result = self.runner.invoke(main, [])
        # Click groups exit with code 2 when no command is provided
        assert result.exit_code in [0, 2]
        assert "Usage:" in result.output
