"""Biosample Enricher: Infer AI-friendly metadata about biosamples.

This package provides services to enrich biosample metadata by inferring
environmental and geographic information from multiple data sources.

Example:
    >>> from biosample_enricher import ElevationService, ElevationRequest
    >>> service = ElevationService()
    >>> request = ElevationRequest(latitude=40.7128, longitude=-74.0060)
    >>> observations = service.get_elevation(request)
"""

from biosample_enricher._version import __version__

# Core Services
from biosample_enricher.elevation.service import ElevationService
from biosample_enricher.forward_geocoding.service import ForwardGeocodingService
from biosample_enricher.land.service import LandService
from biosample_enricher.marine.service import MarineService

# Core Models
from biosample_enricher.models import (
    ElevationRequest,
    GeoPoint,
    Observation,
    ProviderRef,
    ValueStatus,
    Variable,
)
from biosample_enricher.osm_features.service import OSMFeaturesService
from biosample_enricher.reverse_geocoding.service import ReverseGeocodingService
from biosample_enricher.soil.service import SoilService
from biosample_enricher.weather.service import WeatherService

__all__ = [
    # Version
    "__version__",
    # Services
    "ElevationService",
    "SoilService",
    "WeatherService",
    "MarineService",
    "LandService",
    "ReverseGeocodingService",
    "ForwardGeocodingService",
    "OSMFeaturesService",
    # Models
    "GeoPoint",
    "Observation",
    "ProviderRef",
    "Variable",
    "ValueStatus",
    "ElevationRequest",
]
