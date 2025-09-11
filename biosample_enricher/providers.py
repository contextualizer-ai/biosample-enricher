"""Provider enumeration and validation for CLI commands."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class ProviderInfo:
    """Information about a provider including limitations."""
    
    name: str
    description: str
    requires_api_key: bool
    coverage: str
    rate_limits: str
    accuracy: str


class ElevationProvider(str, Enum):
    """Available elevation data providers."""

    GOOGLE = "google"
    USGS = "usgs"
    OSM = "osm"
    OPEN_TOPO_DATA = "open_topo_data"

    @classmethod
    def choices(cls) -> list[str]:
        """Get list of provider choices for Click."""
        return [p.value for p in cls]
    
    @classmethod
    def info(cls, provider: str) -> ProviderInfo:
        """Get detailed information about a provider."""
        info_map = {
            cls.GOOGLE: ProviderInfo(
                name="Google Elevation API",
                description="Google's elevation service with global coverage",
                requires_api_key=True,
                coverage="Global",
                rate_limits="2,500 requests/day free, then pay-per-use",
                accuracy="±1-3 meters typically"
            ),
            cls.USGS: ProviderInfo(
                name="USGS National Elevation Dataset",
                description="High-resolution elevation data for US territories",
                requires_api_key=False,
                coverage="USA, Alaska, Hawaii, Puerto Rico, US territories only",
                rate_limits="No hard limits, but please be respectful",
                accuracy="±0.15-3 meters depending on dataset"
            ),
            cls.OSM: ProviderInfo(
                name="OpenStreetMap/Open-Elevation",
                description="Community-maintained open elevation service",
                requires_api_key=False,
                coverage="Global (using SRTM data)",
                rate_limits="Please limit to 1 request/second",
                accuracy="±10-30 meters (SRTM resolution)"
            ),
            cls.OPEN_TOPO_DATA: ProviderInfo(
                name="Open Topo Data",
                description="Multiple elevation datasets including SRTM, ASTER, EU-DEM",
                requires_api_key=False,
                coverage="Global (varies by dataset)",
                rate_limits="100 requests/second, 1000 locations per request",
                accuracy="±5-30 meters depending on dataset"
            ),
        }
        return info_map.get(provider, ProviderInfo(
            name=provider,
            description="Unknown provider",
            requires_api_key=False,
            coverage="Unknown",
            rate_limits="Unknown",
            accuracy="Unknown"
        ))

    @classmethod
    def description(cls) -> str:
        """Get formatted description of all available providers."""
        lines = ["Available elevation providers:"]
        lines.append("")
        
        for provider in cls:
            info = cls.info(provider)
            lines.append(f"  {provider.value}:")
            lines.append(f"    • Description: {info.description}")
            lines.append(f"    • API Key Required: {'Yes' if info.requires_api_key else 'No'}")
            lines.append(f"    • Coverage: {info.coverage}")
            lines.append(f"    • Rate Limits: {info.rate_limits}")
            lines.append(f"    • Accuracy: {info.accuracy}")
            lines.append("")
        
        return "\n".join(lines)


class ReverseGeocodingProvider(str, Enum):
    """Available reverse geocoding providers."""

    GOOGLE = "google"
    OSM = "osm"

    @classmethod
    def choices(cls) -> list[str]:
        """Get list of provider choices for Click."""
        return [p.value for p in cls]
    
    @classmethod
    def info(cls, provider: str) -> ProviderInfo:
        """Get detailed information about a provider."""
        info_map = {
            cls.GOOGLE: ProviderInfo(
                name="Google Geocoding API",
                description="Google's reverse geocoding service with detailed place information",
                requires_api_key=True,
                coverage="Global",
                rate_limits="$5 per 1000 requests, daily limits based on billing",
                accuracy="High - includes place names, administrative boundaries, postal codes"
            ),
            cls.OSM: ProviderInfo(
                name="OpenStreetMap Nominatim",
                description="Open-source reverse geocoding using OpenStreetMap data",
                requires_api_key=False,
                coverage="Global (quality varies by region)",
                rate_limits="1 request/second max (please respect!)",
                accuracy="Good - depends on OSM data completeness in the region"
            ),
        }
        return info_map.get(provider, ProviderInfo(
            name=provider,
            description="Unknown provider",
            requires_api_key=False,
            coverage="Unknown",
            rate_limits="Unknown",
            accuracy="Unknown"
        ))

    @classmethod
    def description(cls) -> str:
        """Get formatted description of all available providers."""
        lines = ["Available reverse geocoding providers:"]
        lines.append("")
        
        for provider in cls:
            info = cls.info(provider)
            lines.append(f"  {provider.value}:")
            lines.append(f"    • Description: {info.description}")
            lines.append(f"    • API Key Required: {'Yes' if info.requires_api_key else 'No'}")
            lines.append(f"    • Coverage: {info.coverage}")
            lines.append(f"    • Rate Limits: {info.rate_limits}")
            lines.append(f"    • Accuracy: {info.accuracy}")
            lines.append("")
        
        return "\n".join(lines)


def validate_elevation_providers(providers_str: Optional[str]) -> Optional[list[str]]:
    """
    Validate and parse elevation provider string.

    Args:
        providers_str: Comma-separated string of providers

    Returns:
        List of validated provider names or None

    Raises:
        ValueError: If any provider is invalid
    """
    if not providers_str:
        return None

    providers = [p.strip().lower() for p in providers_str.split(",")]
    valid_providers = ElevationProvider.choices()

    invalid = [p for p in providers if p not in valid_providers]
    if invalid:
        raise ValueError(
            f"Invalid elevation provider(s): {', '.join(invalid)}. "
            f"Valid choices are: {', '.join(valid_providers)}"
        )

    return providers


def validate_geocoding_providers(providers_str: Optional[str]) -> Optional[list[str]]:
    """
    Validate and parse reverse geocoding provider string.

    Args:
        providers_str: Comma-separated string of providers

    Returns:
        List of validated provider names or None

    Raises:
        ValueError: If any provider is invalid
    """
    if not providers_str:
        return None

    providers = [p.strip().lower() for p in providers_str.split(",")]
    valid_providers = ReverseGeocodingProvider.choices()

    invalid = [p for p in providers if p not in valid_providers]
    if invalid:
        raise ValueError(
            f"Invalid geocoding provider(s): {', '.join(invalid)}. "
            f"Valid choices are: {', '.join(valid_providers)}"
        )

    return providers