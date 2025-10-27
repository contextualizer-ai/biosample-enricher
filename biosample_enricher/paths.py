"""Path utilities for consistent project-relative path resolution."""

from importlib.resources import files
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory.

    Returns:
        Path to the project root (containing pyproject.toml, README.md, etc.)

    Note:
        This only works in development mode. For installed packages,
        use get_package_data_dir() to access package data files.
    """
    return Path(__file__).parent.parent


def get_package_data_dir() -> Path:
    """Get the package data directory.

    Returns:
        Path to biosample_enricher/data/ directory

    Note:
        This works both in development and when installed via pip/uv or other package managers.
        Use this for accessing config files and other package data.
        Requires Python 3.9+ (importlib.resources.files).
    """
    # Use importlib.resources to get package data directory
    # This works both in development and installed packages
    data_files = files("biosample_enricher") / "data"
    return Path(str(data_files))


def get_config_dir() -> Path:
    """Get the config directory.

    Returns:
        Path to config/ directory (development) or biosample_enricher/data/ (installed)

    Note:
        Tries package data directory first (works when installed),
        falls back to project root config/ (development mode).
    """
    try:
        # Try package data directory (works for installed packages)
        return get_package_data_dir()
    except (FileNotFoundError, ModuleNotFoundError):
        # Fallback to development mode
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
