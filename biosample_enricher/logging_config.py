"""
Simple centralized logging configuration for biosample-enricher.

Provides a mainstream logging setup with console and file output.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    enable_file_logging: bool = True,
) -> logging.Logger:
    """
    Set up centralized logging with console and optional file output.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (defaults to biosample_enricher.log)
        enable_file_logging: Whether to enable file logging

    Returns:
        Configured root logger
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler with simple format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler with detailed format
    if enable_file_logging:
        if log_file is None:
            log_file = "biosample_enricher.log"

        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler (max 10MB, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)  # File gets all messages
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def configure_from_env() -> logging.Logger:
    """
    Configure logging from environment variables.

    Environment variables:
        LOG_LEVEL: Logging level (default: INFO)
        LOG_FILE: Log file path (default: biosample_enricher.log)
        DISABLE_FILE_LOGGING: Set to disable file logging

    Returns:
        Configured logger
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "biosample_enricher.log")
    enable_file_logging = not os.getenv("DISABLE_FILE_LOGGING")

    return setup_logging(
        level=log_level, log_file=log_file, enable_file_logging=enable_file_logging
    )
