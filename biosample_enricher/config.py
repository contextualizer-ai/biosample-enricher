"""Configuration management for biosample-enricher.

This module provides centralized configuration loading from YAML files and environment variables.
All hardcoded configuration values have been externalized to config/ directory.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


# Settings models for typed configuration
class CacheSettings(BaseModel):
    """HTTP cache configuration."""
    backend: str = "sqlite"
    cache_name: str = "http_cache"
    allowable_codes: tuple[int, ...] = (200,)
    ttl_seconds: int = 86400


class AppSettings(BaseModel):
    """Main application settings."""
    cache: CacheSettings = CacheSettings()


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Get application settings with environment override support.
    
    This is the single source of truth for configuration.
    Uses lazy loading to avoid import-time dependencies.
    """
    # Load .env file if present (but not at import time)
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
    except ImportError:
        pass  # dotenv not available
    
    # For now, return basic settings - will expand in future PRs
    return AppSettings()


def clear_settings_cache() -> None:
    """Clear settings cache to force reload from current environment."""
    get_settings.cache_clear()


class ProviderConfig(BaseModel):
    """Configuration for an external API provider."""

    endpoint: str
    timeout_s: float = 20.0
    enabled: bool = True
    api_key_env: str | None = None
    rate_limit_qps: int | None = None
    rate_limit_delay_s: float | None = None
    retry_on_errors: list[int] = Field(default_factory=list)
    max_batch_size: int | None = None
    vertical_datum: str | None = None
    default_resolution_m: float | None = None
    no_data_values: list[float] = Field(default_factory=list)


class DatabaseConfig(BaseModel):
    """Configuration for database connections and collections."""

    database_name: str
    collections: dict[str, str]
    queries: dict[str, Any] | None = None


class ValidationConfig(BaseModel):
    """Configuration for data validation rules."""

    coordinates: dict[str, Any]
    elevation: dict[str, Any]
    dates: dict[str, Any]
    coverage_thresholds: dict[str, Any]


class AppConfig(BaseModel):
    """Main application configuration."""

    providers: dict[str, dict[str, ProviderConfig]]
    databases: dict[str, DatabaseConfig]
    validation: ValidationConfig
    field_mappings: dict[str, Any]
    defaults: dict[str, Any]


@lru_cache(maxsize=1)
def get_config_dir() -> Path:
    """Get the configuration directory path."""
    # Find config directory relative to this module
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    config_dir = project_root / "config"

    if not config_dir.exists():
        raise FileNotFoundError(f"Configuration directory not found: {config_dir}")

    return config_dir


def load_yaml_config(filename: str) -> dict[str, Any]:
    """Load a YAML configuration file."""
    config_dir = get_config_dir()
    config_file = config_dir / filename

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    try:
        with open(config_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        logger.debug(f"Loaded configuration from {config_file}")
        return data or {}

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_file}: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to load {config_file}: {e}") from e


@lru_cache(maxsize=1)
def get_providers_config() -> dict[str, Any]:
    """Load provider configuration."""
    return load_yaml_config("providers.yaml")


@lru_cache(maxsize=1)
def get_databases_config() -> dict[str, Any]:
    """Load database configuration."""
    return load_yaml_config("databases.yaml")


@lru_cache(maxsize=1)
def get_validation_config() -> dict[str, Any]:
    """Load validation configuration."""
    return load_yaml_config("validation.yaml")


@lru_cache(maxsize=1)
def get_field_mappings_config() -> dict[str, Any]:
    """Load field mappings configuration."""
    return load_yaml_config("field_mappings.yaml")


@lru_cache(maxsize=1)
def get_defaults_config() -> dict[str, Any]:
    """Load defaults configuration."""
    return load_yaml_config("defaults.yaml")


@lru_cache(maxsize=1)
def get_host_detection_config() -> dict[str, Any]:
    """Load host detection configuration."""
    return load_yaml_config("host_detection.yaml")


def get_database_connection_string(database_type: str) -> str | None:
    """Get database connection string from environment variables.

    Args:
        database_type: Type of database ('nmdc', 'gold', 'cache', 'default')

    Returns:
        Connection string from environment variable, or None if not set
    """
    db_config = get_databases_config()
    env_vars = db_config.get("mongodb", {}).get("connection_env_vars", {})

    env_var_name = env_vars.get(database_type)
    if not env_var_name:
        logger.warning(
            f"No environment variable mapping for database type: {database_type}"
        )
        return None

    connection_string = os.getenv(env_var_name)
    if not connection_string:
        logger.warning(
            f"Environment variable {env_var_name} not set for {database_type}"
        )
        return None

    return connection_string


def get_provider_config(service_type: str, provider_name: str) -> ProviderConfig | None:
    """Get configuration for a specific provider.

    Args:
        service_type: Type of service ('elevation', 'reverse_geocoding')
        provider_name: Name of provider ('google', 'usgs', 'osm', etc.)

    Returns:
        Provider configuration object, or None if not found
    """
    providers_config = get_providers_config()

    service_config = providers_config.get(service_type, {})
    provider_dict = service_config.get("providers", {}).get(provider_name)

    if not provider_dict:
        logger.warning(f"No configuration found for {service_type}.{provider_name}")
        return None

    try:
        return ProviderConfig(**provider_dict)
    except Exception as e:
        logger.error(f"Invalid configuration for {service_type}.{provider_name}: {e}")
        return None


def get_api_key(env_var_name: str) -> str | None:
    """Get API key from environment variable.

    Args:
        env_var_name: Name of environment variable containing API key

    Returns:
        API key string, or None if not set
    """
    api_key = os.getenv(env_var_name)
    if not api_key:
        logger.debug(f"API key environment variable {env_var_name} not set")
        return None

    # Don't log the actual key for security
    logger.debug(f"Loaded API key from {env_var_name}")
    return api_key


def get_field_priority_list(source: str, field_type: str) -> list[str]:
    """Get field priority list for a specific source and field type.

    Args:
        source: Data source ('nmdc', 'gold')
        field_type: Type of field ('location_text', 'id_fields', etc.)

    Returns:
        List of field names in priority order
    """
    field_mappings = get_field_mappings_config()
    priorities = field_mappings.get("field_priorities", {})
    field_config = priorities.get(field_type, {})

    # Handle both source-specific configs (dict) and direct lists
    if isinstance(field_config, dict):
        field_list = field_config.get(source, [])
    elif isinstance(field_config, list) and field_type in [
        f"{source}_id_fields",
        "gold_id_fields",
        "nmdc_id_fields",
    ]:
        # Some field types (like gold_id_fields) are direct lists without source separation
        field_list = field_config
    else:
        field_list = []

    if not field_list:
        logger.warning(f"No field priority list for {source}.{field_type}")
        return []

    logger.debug(f"Loaded {len(field_list)} priority fields for {source}.{field_type}")
    return field_list


def get_validation_rules(rule_type: str) -> dict[str, Any]:
    """Get validation rules for a specific type.

    Args:
        rule_type: Type of validation ('coordinates', 'elevation', 'dates', etc.)

    Returns:
        Dictionary of validation rules
    """
    validation_config = get_validation_config()
    rules = validation_config.get(rule_type, {})

    if not rules:
        logger.warning(f"No validation rules found for: {rule_type}")
        return {}

    return rules


def get_coverage_thresholds() -> dict[str, int]:
    """Get coverage quality thresholds.

    Returns:
        Dictionary mapping quality levels to percentage thresholds
    """
    validation_config = get_validation_config()
    thresholds = validation_config.get("coverage_thresholds", {}).get("metrics", {})

    # Provide sensible defaults if not configured
    default_thresholds = {"excellent": 75, "good": 50, "poor": 25, "failing": 0}

    return {**default_thresholds, **thresholds}


def get_default_sample_sizes() -> dict[str, int]:
    """Get default sample sizes for various operations.

    Returns:
        Dictionary mapping operation names to default sample sizes
    """
    defaults_config = get_defaults_config()
    sample_sizes = defaults_config.get("sample_sizes", {})

    # Provide sensible defaults
    default_sizes = {
        "metrics_nmdc": 5,
        "metrics_gold": 5,
        "schema_inference": 50000,
        "random_sampling": 100,
    }

    return {**default_sizes, **sample_sizes}


def validate_config() -> bool:
    """Validate all configuration files.

    Returns:
        True if all configurations are valid, False otherwise
    """
    try:
        # Try to load all configurations
        get_providers_config()
        get_databases_config()
        get_validation_config()
        get_field_mappings_config()
        get_defaults_config()
        get_host_detection_config()

        # Test some key environment variables
        required_env_vars = ["NMDC_MONGO_CONNECTION", "GOLD_MONGO_CONNECTION"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        if missing_vars:
            logger.warning(f"Missing required environment variables: {missing_vars}")
            logger.info("Some features may not work without these variables")

        logger.info("Configuration validation successful")
        return True

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


# Convenience functions for backward compatibility
def get_nmdc_connection_string() -> str | None:
    """Get NMDC database connection string."""
    return get_database_connection_string("nmdc")


def get_gold_connection_string() -> str | None:
    """Get GOLD database connection string."""
    return get_database_connection_string("gold")


def get_cache_connection_string() -> str | None:
    """Get cache database connection string."""
    return get_database_connection_string("cache")


def get_google_api_key() -> str | None:
    """Get Google API key."""
    return get_api_key("GOOGLE_MAIN_API_KEY")


def clear_config_cache() -> None:
    """Clear all cached configuration to force reload from current environment.

    This is useful in tests when environment variables are modified.
    """
    get_config_dir.cache_clear()
    get_providers_config.cache_clear()
    get_databases_config.cache_clear()
    get_validation_config.cache_clear()
    get_field_mappings_config.cache_clear()
    get_defaults_config.cache_clear()
    get_host_detection_config.cache_clear()
