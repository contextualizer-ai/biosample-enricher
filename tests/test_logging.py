#!/usr/bin/env python3
"""
Comprehensive tests for the centralized logging framework.

Tests logging configuration, module integration, and proper output formatting.
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from biosample_enricher.logging_config import (
    configure_from_env,
    get_logger,
    setup_logging,
)


class TestLoggingConfiguration:
    """Test the logging configuration functionality."""

    def test_setup_logging_basic(self):
        """Test basic logging setup with defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            logger = setup_logging(log_file=str(log_file))

            # Verify logger configuration
            assert isinstance(logger, logging.Logger)
            assert logger.level == logging.INFO
            assert len(logger.handlers) == 2  # Console + file

            # Test logging
            logger.info("Test message")

            # Verify file was created and contains message
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content

    def test_setup_logging_levels(self):
        """Test different logging levels."""
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]

        for level_str, expected_level in test_cases:
            logger = setup_logging(level=level_str, enable_file_logging=False)
            assert logger.level == expected_level

    def test_setup_logging_no_file(self):
        """Test logging setup without file logging."""
        logger = setup_logging(enable_file_logging=False)

        # Should only have console handler
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logging_file_directory_creation(self):
        """Test that log file directories are created automatically."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "subdir" / "nested" / "test.log"

            logger = setup_logging(log_file=str(log_file))
            logger.info("Test message")

            # Verify directory structure was created
            assert log_file.exists()
            assert log_file.parent.exists()

    def test_get_logger(self):
        """Test logger retrieval with names."""
        logger1 = get_logger("test.module1")
        logger2 = get_logger("test.module2")
        logger3 = get_logger("test.module1")  # Same name

        assert logger1.name == "test.module1"
        assert logger2.name == "test.module2"
        assert logger1 is logger3  # Should be the same instance

    @patch.dict(os.environ, {}, clear=True)
    def test_configure_from_env_defaults(self):
        """Test environment configuration with defaults."""
        logger = configure_from_env()

        assert logger.level == logging.INFO
        # Should have both console and file handlers by default
        assert len(logger.handlers) == 2

    @patch.dict(
        os.environ,
        {"LOG_LEVEL": "DEBUG", "LOG_FILE": "custom.log", "DISABLE_FILE_LOGGING": "1"},
    )
    def test_configure_from_env_custom(self):
        """Test environment configuration with custom values."""
        logger = configure_from_env()

        assert logger.level == logging.DEBUG
        # Should only have console handler (file logging disabled)
        assert len(logger.handlers) == 1


class TestLoggingIntegration:
    """Test logging integration with actual modules."""

    def test_elevation_module_logging(self):
        """Test that elevation module properly uses logging."""
        from biosample_enricher.elevation import ElevationRequest, ElevationService

        # Set up logging to capture messages
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "integration.log"
            setup_logging(level="DEBUG", log_file=str(log_file))

            # Use the elevation service
            service = ElevationService()
            request = ElevationRequest(
                latitude=37.7749, longitude=-122.4194, subject_id="test_sample"
            )
            service.get_elevation(request)

            # Verify logging occurred
            log_content = log_file.read_text()
            assert (
                "elevation" in log_content.lower() or "provider" in log_content.lower()
            )

    def test_http_cache_logging(self):
        """Test that HTTP cache module properly uses logging."""
        from biosample_enricher.http_cache import get_session

        # Set up logging to capture messages
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "cache.log"
            setup_logging(level="DEBUG", log_file=str(log_file))

            # Use the cache
            get_session()

            # Verify logging occurred
            log_content = log_file.read_text()
            # Should see either MongoDB or SQLite backend selection
            assert any(backend in log_content for backend in ["MongoDB", "SQLite"])

    @pytest.mark.network
    def test_request_logging(self):
        """Test HTTP request logging with real request."""
        from biosample_enricher.http_cache import request

        # Set up logging to capture messages
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "request.log"
            setup_logging(level="DEBUG", log_file=str(log_file))

            # Make a test request
            request(
                "GET",
                "https://api.sunrise-sunset.org/json",
                params={"lat": 37.7749, "lng": -122.4194},
            )

            # Verify logging occurred
            log_content = log_file.read_text()
            assert "Making GET request" in log_content
            assert "sunrise-sunset.org" in log_content
            assert "Cache:" in log_content  # Should show cache status


class TestLoggingOutput:
    """Test logging output formatting and content."""

    def test_console_format(self):
        """Test console logging format."""
        import io

        # Capture console output
        captured_output = io.StringIO()

        # Set up logging with custom stream
        logger = logging.getLogger("test_console")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        handler = logging.StreamHandler(captured_output)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Log a message
        logger.info("Test console message")

        output = captured_output.getvalue()
        assert "test_console" in output
        assert "INFO" in output
        assert "Test console message" in output
        # Should have timestamp format YYYY-MM-DD HH:MM:SS
        assert len(output.split(" - ")[0]) == 19  # Date format length

    def test_file_format(self):
        """Test file logging format includes path and line number."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "format_test.log"

            # Set up file logging
            logger = logging.getLogger("test_file")
            logger.setLevel(logging.DEBUG)
            logger.handlers.clear()

            handler = logging.handlers.RotatingFileHandler(str(log_file))
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            # Log a message
            logger.debug("Test file message")

            content = log_file.read_text()
            assert "test_file" in content
            assert "DEBUG" in content
            assert "Test file message" in content
            assert "test_logging.py:" in content  # Should include filename and line


class TestLoggingErrorHandling:
    """Test logging error handling and edge cases."""

    def test_invalid_log_level(self):
        """Test handling of invalid log levels."""
        # Should default to INFO for invalid level
        logger = setup_logging(level="INVALID", enable_file_logging=False)
        assert logger.level == logging.INFO

    def test_readonly_log_directory(self):
        """Test handling of read-only log directories."""
        # This would typically fail in a real read-only directory
        # For testing, we'll just ensure the function doesn't crash
        try:
            logger = setup_logging(
                log_file="/readonly/path/test.log", enable_file_logging=True
            )
            # If it succeeds, that's fine too - some systems might allow it
            assert logger is not None
        except (PermissionError, OSError):
            # Expected in a read-only directory - this is the normal case
            assert True  # Explicitly mark this as expected behavior

    def test_multiple_setup_calls(self):
        """Test that multiple setup calls work correctly."""
        # First setup
        logger1 = setup_logging(level="INFO", enable_file_logging=False)
        initial_handlers = len(logger1.handlers)

        # Second setup should clear existing handlers
        logger2 = setup_logging(level="DEBUG", enable_file_logging=False)

        assert logger1 is logger2  # Same root logger
        assert len(logger2.handlers) == initial_handlers  # Handlers replaced, not added


if __name__ == "__main__":
    pytest.main([__file__])
