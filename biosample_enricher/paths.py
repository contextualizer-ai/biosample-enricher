"""Path utilities for consistent project-relative path resolution."""

from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path to the project root (containing pyproject.toml, README.md, etc.)
    """
    return Path(__file__).parent.parent


def get_config_dir() -> Path:
    """Get the config directory.

    Returns:
        Path to config/ directory
    """
    return get_project_root() / "config"


def get_data_dir() -> Path:
    """Get the data directory.

    Returns:
        Path to data/ directory
    """
    return get_project_root() / "data"


def get_logs_dir() -> Path:
    """Get the logs directory.

    Returns:
        Path to logs/ directory
    """
    return get_project_root() / "logs"
