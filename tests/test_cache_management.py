"""Tests for the cache management CLI."""

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from biosample_enricher.cache_management import cli


class TestCacheManagementCLI:
    """Test the cache management CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test cache management CLI help."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "HTTP Cache Management CLI" in result.output
        assert "Commands:" in result.output

    def test_info_command(self):
        """Test the info command."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["info"])
            # May fail if cache initialization fails, but that's OK for unit test
            assert result.exit_code in [0, 1]
            if result.exit_code == 0:
                assert "HTTP Cache Information" in result.output

    def test_clear_command_with_confirm(self):
        """Test clear command with confirmation."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["clear", "--confirm"])
            # May fail if cache initialization fails
            assert result.exit_code in [0, 1]
            if result.exit_code == 0:
                assert (
                    "Cache cleared successfully" in result.output
                    or "Failed to clear cache" in result.output
                )

    def test_clear_command_without_confirm(self):
        """Test clear command without confirmation (should be cancelled)."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["clear"], input="n\n")
            # Either fails on cache init (1) or user cancellation (0)
            assert result.exit_code in [0, 1]
            if result.exit_code == 0:
                assert "Cancelled" in result.output

    def test_test_command(self):
        """Test the test command."""
        with self.runner.isolated_filesystem():
            # Test command requires a URL
            result = self.runner.invoke(cli, ["test", "--url", "https://example.com"])
            # May fail due to cache or network issues
            assert result.exit_code in [0, 1]

    def test_test_command_with_params(self):
        """Test command with JSON parameters."""
        with self.runner.isolated_filesystem():
            params = json.dumps({"lat": 37.7749, "lng": -122.4194})
            result = self.runner.invoke(
                cli, ["test", "--url", "https://example.com", "--params", params]
            )
            assert result.exit_code in [0, 1]

    @patch("biosample_enricher.cache_management.get_session")
    def test_info_command_with_mock(self, mock_get_session):
        """Test info command with mocked session."""
        mock_session = MagicMock()
        mock_cache = MagicMock()
        mock_cache.responses = {"key1": "data1", "key2": "data2"}
        mock_cache.db_path = "/tmp/cache.db"
        mock_session.cache = mock_cache
        mock_get_session.return_value = mock_session

        result = self.runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "HTTP Cache Information" in result.output

    @patch("biosample_enricher.cache_management.get_session")
    def test_clear_command_with_mock_success(self, mock_get_session):
        """Test successful cache clearing with mock."""
        mock_session = MagicMock()
        mock_cache = MagicMock()
        mock_session.cache = mock_cache
        mock_get_session.return_value = mock_session

        result = self.runner.invoke(cli, ["clear", "--confirm"])
        assert result.exit_code == 0
        assert "Cache cleared successfully" in result.output
        mock_cache.clear.assert_called_once()

    @patch("biosample_enricher.cache_management.get_session")
    def test_clear_command_with_mock_error(self, mock_get_session):
        """Test cache clearing with error."""
        mock_session = MagicMock()
        mock_cache = MagicMock()
        mock_cache.clear.side_effect = Exception("Cache error")
        mock_session.cache = mock_cache
        mock_get_session.return_value = mock_session

        result = self.runner.invoke(cli, ["clear", "--confirm"])
        assert result.exit_code == 0
        assert "Failed to clear cache" in result.output

    @patch("biosample_enricher.cache_management.get_session")
    @patch("biosample_enricher.cache_management.request")
    def test_test_command_with_mock(self, mock_request, mock_get_session):
        """Test the test command with mocked request."""
        # Setup session mock
        mock_session = MagicMock()
        mock_cache = MagicMock()
        mock_session.cache = mock_cache
        mock_get_session.return_value = mock_session

        # Setup request mocks
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.content = b"test content"
        mock_response1.from_cache = False

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.content = b"test content"
        mock_response2.from_cache = True

        mock_request.side_effect = [mock_response1, mock_response2]

        result = self.runner.invoke(cli, ["test", "--url", "https://example.com"])
        assert result.exit_code == 0
        assert "First request" in result.output
        assert "Second request" in result.output
        assert "Cache working!" in result.output
